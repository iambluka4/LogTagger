import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from models import db, Event, MLPerformanceMetrics, Settings, Configuration
from services.ml_service import MLService
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
import pandas as pd
import io
import os
import traceback  # Додано для кращої обробки помилок

ml_bp = Blueprint('ml_bp', __name__)

@ml_bp.route('/api/ml/status', methods=['GET'])
def get_ml_status():
    """
    Отримати статус ML-сервісу
    
    Returns:
        JSON: Статус ML-сервісу
    """
    try:
        # Отримуємо налаштування
        settings = Settings.query.first()
        
        if not settings:
            return jsonify({"status": "error", "message": "Settings not found"}), 404
        
        # Перевіряємо чи увімкнено ML-класифікацію
        ml_config = Configuration.query.filter_by(config_type="general.ml_classification_enabled").first()
        ml_enabled = ml_config.config_value.lower() == "true" if ml_config else False
        
        # Якщо ML вимкнено, повертаємо відповідний статус
        if not ml_enabled:
            return jsonify({
                "status": "disabled",
                "message": "ML classification is disabled in system settings"
            })
        
        # Ініціалізуємо ML-сервіс
        ml_service = MLService(settings.ml_api_url, settings.ml_api_key)
        
        # Перевіряємо з'єднання
        connection_test = ml_service.test_connection()
        
        # Безпечно отримуємо дані про модель
        model_info = {"success": False, "model_info": {}}
        if ml_service.provider:
            try:
                model_info = ml_service.provider.get_model_info()
            except Exception as e:
                current_app.logger.error(f"Error getting model info: {str(e)}")
                model_info = {"success": False, "error": str(e), "model_info": {}}
        
        # Безпечно отримуємо метрики
        latest_metrics = {"success": False, "metrics": None}
        try:
            latest_metrics = ml_service.get_latest_metrics()
        except Exception as e:
            current_app.logger.error(f"Error getting metrics: {str(e)}")
            latest_metrics = {"success": False, "error": str(e)}
        
        return jsonify({
            "status": "active" if connection_test.get('success') else "error",
            "message": connection_test.get('message'),
            "model_info": model_info.get('model_info', {}),
            "connection_details": connection_test.get('details', {}),
            "latest_metrics": latest_metrics.get('metrics') if latest_metrics.get('success') else None
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting ML status: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@ml_bp.route('/api/ml/classify/<int:event_id>', methods=['POST'])
def classify_event(event_id):
    """
    Класифікувати окрему подію
    
    Args:
        event_id (int): ID події
        
    Returns:
        JSON: Результати класифікації
    """
    try:
        # Отримуємо подію з використанням eager loading для оптимізації запитів
        event = Event.query.options(joinedload(Event.raw_logs)).get_or_404(event_id)
        
        # Отримуємо налаштування
        settings = Settings.query.first()
        
        if not settings:
            return jsonify({"success": False, "message": "Settings not found"}), 404
        
        # Перевіряємо чи увімкнено ML-класифікацію
        ml_config = Configuration.query.filter_by(config_type="general.ml_classification_enabled").first()
        ml_enabled = ml_config and ml_config.config_value.lower() == "true"
        
        if not ml_enabled:
            return jsonify({"success": False, "message": "ML classification is disabled in system settings"}), 400
            
        # Ініціалізуємо ML-сервіс
        ml_service = MLService(settings.ml_api_url, settings.ml_api_key)
        
        # Класифікуємо подію
        result = ml_service.classify_event(event)
        
        # Якщо класифікація успішна і була застосована, зберігаємо зміни
        if result.get('success') and result.get('applied', False):
            db.session.commit()
        
        return jsonify(result)
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in classify_event: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error in classify_event: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ml_bp.route('/api/ml/batch-classify', methods=['POST'])
def batch_classify_events():
    """
    Класифікувати пакет подій
    
    Returns:
        JSON: Результати класифікації
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        event_ids = data.get('event_ids', [])
        if not event_ids:
            return jsonify({"success": False, "message": "No event IDs provided"}), 400
        
        # Validate event IDs
        if not all(isinstance(id, int) for id in event_ids):
            return jsonify({"success": False, "message": "All event IDs must be integers"}), 400
        
        # Отримуємо налаштування
        settings = Settings.query.first()
        
        if not settings:
            return jsonify({"success": False, "message": "Settings not found"}), 404
        
        # Перевіряємо налаштування ML
        ml_config = Configuration.query.filter_by(config_type="general.ml_classification_enabled").first()
        if not ml_config or ml_config.config_value.lower() != "true":
            return jsonify({"success": False, "message": "ML classification is disabled in system settings"}), 400
        
        # Ініціалізуємо ML-сервіс
        try:
            ml_service = MLService(settings.ml_api_url, settings.ml_api_key)
        except Exception as e:
            current_app.logger.error(f"Failed to initialize ML service: {str(e)}")
            return jsonify({"success": False, "message": f"Failed to initialize ML service: {str(e)}"}), 500
        
        # Класифікуємо події
        result = ml_service.batch_classify_events(event_ids)
        
        if not result.get('success'):
            current_app.logger.warning(f"ML batch classification warning: {result.get('error')}")
        
        return jsonify(result)
    except ValueError as e:
        current_app.logger.error(f"Value error in batch_classify_events: {str(e)}")
        return jsonify({"success": False, "message": f"Invalid input: {str(e)}"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in batch_classify_events: {str(e)}")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        current_app.logger.error(f"Error in batch_classify_events: {traceback.format_exc()}")
        return jsonify({"success": False, "message": str(e)}), 500

@ml_bp.route('/api/ml/verify-label/<int:event_id>', methods=['POST'])
def verify_label(event_id):
    """
    Верифікувати ML-мітку для події
    
    Args:
        event_id (int): ID події
        
    Returns:
        JSON: Результат верифікації
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Отримуємо подію
        event = Event.query.get_or_404(event_id)
        
        # Перевіряємо, чи була подія оброблена ML
        if not event.ml_processed or not hasattr(event, 'labels_data') or event.labels_data is None:
            return jsonify({
                "success": False,
                "message": "Event was not properly processed by ML or lacks required data"
            }), 400
        
        # Оновлюємо поле human_verified
        event.human_verified = True
        
        # Зберігаємо оригінальні ML-мітки для порівняння
        if not event.labels_data:
            event.labels_data = {}
        
        # Зберігаємо оригінальні ML-мітки з префіксом ml_ для подальшого аналізу
        event.labels_data['ml_true_positive'] = event.true_positive
        event.labels_data['ml_attack_type'] = event.attack_type
        event.labels_data['ml_mitre_tactic'] = event.mitre_tactic
        event.labels_data['ml_mitre_technique'] = event.mitre_technique
        
        # Оновлюємо мітки на основі вхідних даних
        if 'true_positive' in data:
            event.true_positive = data['true_positive']
        if 'attack_type' in data:
            event.attack_type = data['attack_type']
        if 'mitre_tactic' in data:
            event.mitre_tactic = data['mitre_tactic']
        if 'mitre_technique' in data:
            event.mitre_technique = data['mitre_technique']
        
        # Додаємо коментар верифікації
        if 'verification_comment' in data:
            event.labels_data['verification_comment'] = data['verification_comment']
        
        # Оновлюємо час верифікації
        event.labels_data['verification_timestamp'] = datetime.utcnow().isoformat()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Event label verified successfully",
            "event": event.to_dict()
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in verify_label: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error in verify_label: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ml_bp.route('/api/ml/update-metrics', methods=['POST'])
def update_metrics():
    """
    Оновити метрики продуктивності ML
    
    Returns:
        JSON: Результати оновлення метрик
    """
    try:
        data = request.json or {}
        
        # Отримання параметрів
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Отримуємо налаштування
        settings = Settings.query.first()
        
        if not settings:
            return jsonify({"success": False, "message": "Settings not found"}), 404
        
        # Ініціалізуємо ML-сервіс
        ml_service = MLService(settings.ml_api_url, settings.ml_api_key)
        
        # Оновлюємо метрики
        result = ml_service.update_performance_metrics(start_date, end_date)
        
        return jsonify(result)
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_metrics: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error in update_metrics: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ml_bp.route('/api/ml/metrics', methods=['GET'])
def get_metrics():
    """
    Отримати метрики продуктивності ML
    
    Returns:
        JSON: Метрики продуктивності
    """
    try:
        # Оптимізуємо запит - вибираємо тільки потрібні поля
        metrics = MLPerformanceMetrics.query.with_entities(
            MLPerformanceMetrics.id,
            MLPerformanceMetrics.timestamp,
            MLPerformanceMetrics.model_version,
            MLPerformanceMetrics.precision,
            MLPerformanceMetrics.recall,
            MLPerformanceMetrics.f1_score,
            MLPerformanceMetrics.true_positives,
            MLPerformanceMetrics.false_positives,
            MLPerformanceMetrics.true_negatives,
            MLPerformanceMetrics.false_negatives,
            MLPerformanceMetrics.class_metrics
        ).order_by(
            MLPerformanceMetrics.timestamp.desc()
        ).limit(10).all()
        
        # Перетворюємо результати в список словників
        results = [{
            "id": m.id,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "model_version": m.model_version,
            "precision": m.precision,
            "recall": m.recall,
            "f1_score": m.f1_score,
            "true_positives": m.true_positives,
            "false_positives": m.false_positives,
            "true_negatives": m.true_negatives,
            "false_negatives": m.false_negatives,
            "class_metrics": m.class_metrics
        } for m in metrics]
        
        return jsonify({
            "success": True,
            "metrics": results,
            "count": len(results)
        })
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_metrics: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error in get_metrics: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@ml_bp.route('/api/ml/unverified-events', methods=['GET'])
def get_unverified_events():
    """
    Отримати список подій, класифікованих ML, але не перевірених людиною
    
    Returns:
        JSON: Список неперевірених подій
    """
    try:
        # Параметри пагінації
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)
        
        # Базовий запит для подій, що були оброблені ML, але не перевірені людиною
        query = Event.query.filter(
            Event.ml_processed == True,
            Event.human_verified == False
        ).order_by(Event.timestamp.desc())
        
        # Застосовуємо пагінацію
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        
        # Підготовка даних для відповіді
        events_data = [event.to_dict() for event in pagination.items]
        
        return jsonify({
            "success": True,
            "events": events_data,
            "page": pagination.page,
            "page_size": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages
        })
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_unverified_events: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error in get_unverified_events: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
