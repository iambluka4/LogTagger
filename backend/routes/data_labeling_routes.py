from flask import Blueprint, request, jsonify
from models import db, Alert, Label

data_labeling_bp = Blueprint('data_labeling_bp', __name__)

@data_labeling_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    alerts = Alert.query.all()
    result = []
    for alert in alerts:
        labels = [label.__dict__ for label in alert.labels]
        result.append({
            "alert_id": alert.id,
            "wazuh_id": alert.wazuh_id,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "timestamp": alert.timestamp,
            "labels": labels
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
