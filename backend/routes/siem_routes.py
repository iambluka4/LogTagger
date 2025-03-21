import requests
from flask import Blueprint, jsonify
from models import db, Configuration, Event, RawLog
from datetime import datetime

siem_bp = Blueprint('siem', __name__)

@siem_bp.route('/api/siem/get_alerts', methods=['GET'])
def get_alerts():
    config = Configuration.query.first()
    if not config:
        return jsonify({"status": "error", "message": "Configuration not found"}), 404

    siem_api_url = config.siem_api_url
    siem_api_token = config.siem_api_token

    headers = {
        'Authorization': f'Bearer {siem_api_token}'
    }

    response = requests.get(siem_api_url, headers=headers)
    if response.status_code != 200:
        return jsonify({"status": "error", "message": "Failed to fetch alerts from SIEM"}), response.status_code

    alerts = response.json()
    return jsonify({"status": "success", "alerts": alerts})

@siem_bp.route('/api/siem/label_alerts', methods=['POST'])
def label_alerts():
    data = request.json
    alerts = data.get('alerts', [])
    config = Configuration.query.first()
    if not config:
        return jsonify({"status": "error", "message": "Configuration not found"}), 404

    rules = config.rules

    labeled_alerts = []
    for alert in alerts:
        labels = {}
        for rule in rules.get('rules', []):
            conditions = rule.get('conditions', {})
            if all(alert.get(key) == value for key, value in conditions.items()):
                labels.update(rule.get('labels', {}))
        alert['labels'] = labels
        labeled_alerts.append(alert)

    return jsonify({"status": "success", "labeled_alerts": labeled_alerts})

@siem_bp.route('/api/siem/export', methods=['POST'])
def export_siem_logs():
    config = Configuration.query.first()
    if not config:
        return jsonify({"error": "No configuration found"}), 400

    headers = {"Authorization": f"Bearer {config.siem_api_token}"}
    response = requests.get(f"{config.siem_api_url}/alerts", headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "SIEM API error"}), 500

    alerts = response.json().get("data", [])
    for alert in alerts:
        event = Event.query.filter_by(event_id=str(alert["id"])).first()
        if not event:
            event = Event(
                event_id=str(alert["id"]),
                timestamp=datetime.strptime(alert["timestamp"], "%Y-%m-%dT%H:%M:%SZ"),
                source_ip=alert.get("source", {}).get("ip", ""),
                severity=alert.get("severity", ""),
                siem_source=config.siem_source,
                labels={"auto_tags": [config.siem_source]}
            )
            db.session.add(event)
            db.session.flush()  # отримуємо event.id для FK

            raw_log = RawLog(
                event_id=event.id,
                siem_source=config.siem_source,
                raw_log=alert
            )
            db.session.add(raw_log)
        else:
            continue  # вже є такий event, пропускаємо

    db.session.commit()
    return jsonify({"status": "success", "imported_events": len(alerts)})