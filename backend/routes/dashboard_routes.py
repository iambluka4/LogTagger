from flask import Blueprint, jsonify, request
from models import db, Event, Alert, Label
from sqlalchemy import func
import datetime

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    # Проста статистика для MVP
    events_count = Event.query.count()
    alerts_count = Alert.query.count()
    labels_count = Label.query.count()
    
    return jsonify({
        "events_count": events_count,
        "alerts_count": alerts_count, 
        "labels_count": labels_count
    })

@dashboard_bp.route('/top-attacks', methods=['GET'])
def get_top_attacks():
    # Заглушка для MVP
    return jsonify({"attacks": []})

@dashboard_bp.route('/timeline', methods=['GET'])
def get_timeline():
    # Заглушка для MVP
    return jsonify({"timeline": []})

@dashboard_bp.route('/severity', methods=['GET'])
def get_severity():
    # Заглушка для MVP
    return jsonify({
        "high": 0,
        "medium": 0,
        "low": 0
    })

@dashboard_bp.route('/mitre-distribution', methods=['GET'])
def get_mitre_distribution():
    # Заглушка для MVP
    return jsonify({"tactics": []})
