from flask import Blueprint, jsonify, request, current_app
from models import db, Event, Alert
from sqlalchemy import func
from datetime import datetime, timedelta
import json
from sqlalchemy.engine import Engine
from sqlalchemy.dialects import postgresql

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Отримання загальної статистики для дашборду"""
    # Загальна кількість подій
    total_events = Event.query.count()
    
    # Кількість подій за останні 24 години
    day_ago = datetime.utcnow() - timedelta(days=1)
    events_24h = Event.query.filter(Event.timestamp >= day_ago).count()
    
    # Кількість переглянутих та непереглянутих подій
    reviewed_events = Event.query.filter(Event.manual_review == True).count()
    unreviewed_events = total_events - reviewed_events
    
    # Кількість true positive/negative подій
    true_positives = Event.query.filter(Event.true_positive == True).count()
    false_positives = Event.query.filter(Event.true_positive == False).count()
    
    # Кількість подій за різними SIEM-системами
    siem_stats = db.session.query(
        Event.siem_source, func.count(Event.id)
    ).group_by(Event.siem_source).all()
    
    siem_distribution = {source: count for source, count in siem_stats}
    
    return jsonify({
        "total_events": total_events,
        "events_24h": events_24h,
        "reviewed_events": reviewed_events,
        "unreviewed_events": unreviewed_events,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "siem_distribution": siem_distribution
    })

@dashboard_bp.route('/api/dashboard/top-attacks', methods=['GET'])
def get_top_attacks():
    """Отримання топ типів атак"""
    limit = int(request.args.get('limit', 5))
    
    # Отримуємо типи атак та їх кількість
    attack_stats = db.session.query(
        Event.attack_type, func.count(Event.id).label('count')
    ).filter(Event.attack_type.isnot(None)).group_by(Event.attack_type)\
    .order_by(func.count(Event.id).desc()).limit(limit).all()
    
    return jsonify([
        {"attack_type": attack_type, "count": count}
        for attack_type, count in attack_stats
    ])

@dashboard_bp.route('/api/dashboard/timeline', methods=['GET'])
def get_event_timeline():
    """Отримання даних для часової шкали подій"""
    days = int(request.args.get('days', 30))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Визначити тип бази даних
    is_postgres = db.engine.dialect.name == 'postgresql'
    
    # Вибрати відповідний запит
    if is_postgres:
        # PostgreSQL запит
        timeline_data = db.session.query(
            func.date_trunc('day', Event.timestamp).label('date'),
            func.count(Event.id).label('count')
        ).filter(Event.timestamp >= start_date)\
        .group_by(func.date_trunc('day', Event.timestamp))\
        .order_by(func.date_trunc('day', Event.timestamp)).all()
    else:
        # Загальний SQL запит для інших СУБД (SQLite, MySQL)
        timeline_data = db.session.query(
            func.strftime('%Y-%m-%d', Event.timestamp).label('date'),
            func.count(Event.id).label('count')
        ).filter(Event.timestamp >= start_date)\
        .group_by(func.strftime('%Y-%m-%d', Event.timestamp))\
        .order_by(func.strftime('%Y-%m-%d', Event.timestamp)).all()
    
    return jsonify([
        {"date": date if isinstance(date, str) else date.strftime('%Y-%m-%d'), 
         "count": count}
        for date, count in timeline_data
    ])

@dashboard_bp.route('/api/dashboard/severity', methods=['GET'])
def get_severity_distribution():
    """Отримання розподілу подій за рівнем важливості"""
    # Отримуємо кількість подій для кожного рівня важливості
    severity_stats = db.session.query(
        Event.severity, func.count(Event.id).label('count')
    ).group_by(Event.severity).all()
    
    # Перетворюємо в словник для зручності
    severity_distribution = {
        severity: count for severity, count in severity_stats
    }
    
    # Забезпечуємо наявність всіх рівнів важливості
    for sev in ['low', 'medium', 'high', 'critical']:
        if sev not in severity_distribution:
            severity_distribution[sev] = 0
    
    return jsonify(severity_distribution)

# Оновлена функція для обох маршрутів
@dashboard_bp.route('/api/dashboard/mitre-distribution', methods=['GET'])
@dashboard_bp.route('/mitre-distribution', methods=['GET'])
def get_mitre_distribution():
    """Отримання розподілу подій за MITRE тактиками та техніками"""
    try:
        # Отримуємо розподіл за тактиками
        tactic_stats = db.session.query(
            Event.mitre_tactic, func.count(Event.id).label('count')
        ).filter(Event.mitre_tactic.isnot(None))\
        .group_by(Event.mitre_tactic).all()
        
        # Формуємо результат у форматі, який очікує фронтенд
        tactics_result = [
            {"name": tactic, "count": count} 
            for tactic, count in tactic_stats
        ]
        
        # Отримуємо розподіл за техніками
        technique_stats = db.session.query(
            Event.mitre_technique, func.count(Event.id).label('count')
        ).filter(Event.mitre_technique.isnot(None))\
        .group_by(Event.mitre_technique).all()
        
        techniques_result = {technique: count for technique, count in technique_stats}
        
        # Повертаємо результат у форматі, сумісному з обома кінцевими точками
        return jsonify({
            "tactics": tactics_result,
            "techniques": techniques_result
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching MITRE distribution: {str(e)}")
        return jsonify({"tactics": [], "techniques": {}, "error": "Failed to fetch data"})
