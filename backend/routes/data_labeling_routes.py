import requests
from flask import Blueprint, request, jsonify, send_file, current_app
from models import db, Alert, Event, RawLog  # Видалено імпорт Label
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
import pandas as pd
import io
import json
import logging
from datetime import datetime

# Створюємо Blueprint для маршрутів маркування даних
data_labeling_bp = Blueprint('data_labeling_bp', __name__)

# 1. Auto-tagging ендпоінт
@data_labeling_bp.route('/api/alerts/auto-tag', methods=['POST'])
def auto_tag_alerts():
    """
    Отримує логи з Wazuh, автоматично додає теги та зберігає в базу даних.
    
    Returns:
        JSON: Результат операції з кількістю оброблених логів
    """
    # 1) Отримати логи з Wazuh (спростимо для прикладу)
    wazuh_url = "https://wazuh.example/api/logs"
    headers = {"Authorization": "Bearer <YOUR_WAZUH_TOKEN>"}
    
    try:
        response = requests.get(wazuh_url, headers=headers, timeout=10)
        # Припустимо, Wazuh повертає JSON з полями message, severity, rule_name...
        if response.status_code == 200:
            logs = response.json().get("data", [])
            
            # Почнемо транзакцію
            try:
                for log_data in logs:
                    severity = log_data.get("severity", "")
                    rule_name = log_data.get("rule_name", "")

                    # Авто-теги за умовою
                    auto_tags_list = []
                    if severity.lower() in ("medium", "high"):
                        auto_tags_list.append("potential_threat")
                    if "brute" in rule_name.lower():
                        auto_tags_list.append("brute_force")

                    # Створити чи оновити запис
                    new_alert = Alert(
                        message = log_data.get("message", ""),
                        severity = severity,
                        rule_name = rule_name,
                        auto_tags = ",".join(auto_tags_list)
                    )
                    db.session.add(new_alert)
                
                # Один commit після всіх операцій
                db.session.commit()
                return jsonify({"status": "ok", "count": len(logs)})
            except SQLAlchemyError as db_error:
                db.session.rollback()
                current_app.logger.error(f"Database error: {str(db_error)}")
                return jsonify({"status": "error", "detail": "Database error occurred"}), 500
        else:
            return jsonify({"status": "error", "detail": "Cannot fetch logs"}), 400
    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching logs from Wazuh: {str(e)}")
        return jsonify({"status": "error", "detail": str(e)}), 500

# 2. Розширені фільтри
@data_labeling_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    Отримує список сповіщень з можливістю фільтрації.
    
    Returns:
        JSON: Список сповіщень, що відповідають критеріям фільтра
    """
    try:
        query = Alert.query

        # Фільтрація
        severity_param = request.args.get('severity')
        if severity_param:
            query = query.filter(Alert.severity.ilike(severity_param))

        rule_param = request.args.get('rule_name')
        if rule_param:
            query = query.filter(Alert.rule_name.ilike(f"%{rule_param}%"))

        auto_tag_param = request.args.get('auto_tag')
        if auto_tag_param:
            query = query.filter(Alert.auto_tags.ilike(f"%{auto_tag_param}%"))

        # Приклад фільтра по датах (якщо є поле date)
        # date_from = request.args.get('date_from')
        # date_to = request.args.get('date_to')
        # if date_from:
        #     query = query.filter(Alert.created_at >= date_from)
        # if date_to:
        #     query = query.filter(Alert.created_at <= date_to)

        # Додаємо пагінацію
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        alerts = pagination.items
        result = []
        for a in alerts:
            result.append({
                "id": a.id,
                "message": a.message,
                "severity": a.severity,
                "rule_name": a.rule_name,
                "auto_tags": a.auto_tags
            })
            
        # Додаємо інформацію про пагінацію
        meta = {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages
        }
        
        return jsonify({"data": result, "meta": meta})
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_alerts: {str(e)}")
        return jsonify({"status": "error", "detail": "Database error occurred"}), 500

@data_labeling_bp.route('/api/alerts/<int:alert_id>/label', methods=['POST'])
def label_alert(alert_id):
    """
    Додає мітку до сповіщення за його ID і створює відповідний Event.
    
    Args:
        alert_id (int): Ідентифікатор сповіщення
        
    Returns:
        JSON: Повідомлення про успіх або помилку
    """
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data provided"}), 400
        
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({"message": "Alert not found"}), 404

        # Перевірка обов'язкових полів
        required_fields = ['true_positive', 'attack_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"message": f"Missing required field: {field}"}), 400
                
        # Створюємо новий Event або оновлюємо існуючий на основі Alert
        event_id = f"alert-{alert.id}"
        event = Event.query.filter_by(event_id=event_id).first()
        
        if not event:
            # Створюємо новий Event
            event = Event(
                event_id=event_id,
                timestamp=alert.timestamp,
                source_ip="", # Можна додати, якщо доступно в Alert
                severity=alert.severity,
                siem_source="alert",
                manual_review=True,
                labels_data={},
                alert_id=alert.id
            )
            db.session.add(event)
            
        # Оновлюємо мітки події
        event.true_positive = data.get('true_positive', False)
        event.attack_type = data.get('attack_type', "")
        event.detected_rule = data.get('detected_rule', "")
        event.event_chain_id = data.get('event_chain_id', "")
        event.event_severity = data.get('event_severity', alert.severity)
        
        db.session.commit()
        return jsonify({"message": "Event labeled successfully", "event_id": event.id})
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in label_alert: {str(e)}")
        return jsonify({"message": "Database error", "detail": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in label_alert: {str(e)}")
        return jsonify({"message": "An unexpected error occurred", "detail": str(e)}), 500

# 3. Експорт датасету
@data_labeling_bp.route('/api/dataset/export', methods=['GET'])
def export_dataset():
    """
    Експортує датасет у форматі CSV.
    
    Returns:
        File: CSV файл з даними подій
    """
    try:
        # Додаємо можливість обмеження розміру вибірки
        limit = request.args.get('limit', type=int)
        query = Event.query
        
        if limit:
            query = query.limit(limit)
            
        events = query.all()
        if not events:
            return jsonify({"message": "No events found to export"}), 404
            
        dataset = []

        for event in events:
            raw_log = RawLog.query.filter_by(event_id=event.id).first()
            raw_log_data = raw_log.raw_log if raw_log else {}
            dataset.append({
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "source_ip": event.source_ip,
                "severity": event.severity,
                "siem_source": event.siem_source,
                "labels": event.labels_data,  # Виправлено з event.labels на event.labels_data
                "raw_log": raw_log_data
            })

        df = pd.DataFrame(dataset)
        buffer = io.BytesIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)

        return send_file(buffer, mimetype='text/csv', 
                         download_name=f'dataset_{len(events)}_events.csv', 
                         as_attachment=True)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in export_dataset: {str(e)}")
        return jsonify({"status": "error", "detail": f"Database error: {str(e)}"}), 500
    except Exception as e:
        current_app.logger.error(f"Error exporting dataset: {str(e)}")
        return jsonify({"status": "error", "detail": str(e)}), 500

# 4. Об'єднання подій в Event Chain
@data_labeling_bp.route('/api/event_chain', methods=['POST'])
def create_event_chain():
    """
    Об'єднує кілька подій в один ланцюжок подій.
    
    Returns:
        JSON: Повідомлення про успіх або помилку
    """
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        event_ids = data.get('event_ids', [])
        if not event_ids:
            return jsonify({"message": "No event IDs provided"}), 400
            
        event_chain_id = data.get('event_chain_id', '')
        if not event_chain_id:
            return jsonify({"message": "Event chain ID is required"}), 400

        # Перевірка існування всіх подій перед оновленням
        events = Event.query.filter(Event.id.in_(event_ids)).all()
        
        found_ids = [event.id for event in events]
        missing_ids = [str(event_id) for event_id in event_ids if event_id not in found_ids]
        
        if missing_ids:
            return jsonify({
                "message": "Some events were not found", 
                "missing_ids": missing_ids
            }), 404

        # Оновлення всіх подій в одній транзакції
        for event in events:
            event.event_chain_id = event_chain_id
            
        # Один commit для всіх оновлень
        db.session.commit()
        
        return jsonify({
            "message": "Event Chain created successfully",
            "updated_events": len(events)
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in create_event_chain: {str(e)}")
        return jsonify({"message": "Database error", "detail": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error creating event chain: {str(e)}")
        return jsonify({"message": "Error creating event chain", "detail": str(e)}), 500

