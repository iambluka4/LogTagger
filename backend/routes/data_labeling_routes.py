import requests
from flask import Blueprint, request, jsonify, send_file
from models import db, Alert, Label, Event, RawLog
import pandas as pd
import io

data_labeling_bp = Blueprint('data_labeling_bp', __name__)

# 1. Auto-tagging ендпоінт
@data_labeling_bp.route('/api/alerts/auto-tag', methods=['POST'])
def auto_tag_alerts():
    # 1) Отримати логи з Wazuh (спростимо для прикладу)
    wazuh_url = "https://wazuh.example/api/logs"
    headers = {"Authorization": "Bearer <YOUR_WAZUH_TOKEN>"}
    response = requests.get(wazuh_url, headers=headers, timeout=10)
    # Припустимо, Wazuh повертає JSON з полями message, severity, rule_name...
    if response.status_code == 200:
        logs = response.json().get("data", [])

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
        db.session.commit()
        return jsonify({"status": "ok", "count": len(logs)})
    else:
        return jsonify({"status": "error", "detail": "Cannot fetch logs"}), 400

# 2. Розширені фільтри
@data_labeling_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
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

    alerts = query.all()
    result = []
    for a in alerts:
        result.append({
            "id": a.id,
            "message": a.message,
            "severity": a.severity,
            "rule_name": a.rule_name,
            "auto_tags": a.auto_tags
        })
    return jsonify(result)

@data_labeling_bp.route('/api/alerts/<int:alert_id>/label', methods=['POST'])
def label_alert(alert_id):
    data = request.json
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({"message": "Alert not found"}), 404

    label = Label(
        alert_id=alert.id,
        detected_rule=data.get('detected_rule', ""),
        true_positive=data.get('true_positive', False),
        event_chain_id=data.get('event_chain_id', ""),
        attack_type=data.get('attack_type', ""),
        manual_tag=data.get('manual_tag', ""),
        event_severity=data.get('event_severity', alert.severity)
    )
    db.session.add(label)
    db.session.commit()
    return jsonify({"message": "Label added successfully"})

# 3. Експорт датасету
@data_labeling_bp.route('/api/dataset/export', methods=['GET'])
def export_dataset():
    events = Event.query.all()
    dataset = []

    for event in events:
        raw_log = RawLog.query.filter_by(event_id=event.id).first()
        dataset.append({
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "source_ip": event.source_ip,
            "severity": event.severity,
            "siem_source": event.siem_source,
            "labels": event.labels,
            "raw_log": raw_log.raw_log if raw_log else {}
        })

    df = pd.DataFrame(dataset)
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, mimetype='text/csv', download_name='dataset.csv', as_attachment=True)

# 4. Об'єднання подій в Event Chain
@data_labeling_bp.route('/api/event_chain', methods=['POST'])
def create_event_chain():
    data = request.json
    event_ids = data.get('event_ids', [])
    event_chain_id = data.get('event_chain_id', '')

    for event_id in event_ids:
        event = Event.query.get(event_id)
        if event:
            event.labels['event_chain_id'] = event_chain_id
            db.session.commit()

    return jsonify({"message": "Event Chain created successfully"})
