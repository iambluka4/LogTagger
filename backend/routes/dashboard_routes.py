from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from models import db, Event
from sqlalchemy import func
import datetime

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get general statistics for the dashboard"""
    # Total events count
    total_events = Event.query.count()
    
    # Events today
    today = datetime.datetime.now().date()
    today_start = datetime.datetime.combine(today, datetime.time.min)
    today_end = datetime.datetime.combine(today, datetime.time.max)
    events_today = Event.query.filter(Event.timestamp >= today_start, Event.timestamp <= today_end).count()
    
    # Labeled events count
    labeled_events = Event.query.filter(Event.manual_review == True).count()
    
    # True positives count
    true_positives = Event.query.filter(Event.true_positive == True).count()
    
    # SIEM sources distribution
    sources = db.session.query(
        Event.siem_source,
        func.count(Event.id).label('count')
    ).group_by(Event.siem_source).all()
    
    siem_sources = [{"name": source[0], "count": source[1]} for source in sources]
    
    return jsonify({
        "total_events": total_events,
        "events_today": events_today,
        "labeled_events": labeled_events,
        "true_positives": true_positives,
        "siem_sources": siem_sources
    })

@dashboard_bp.route('/api/dashboard/top-attacks', methods=['GET'])
@jwt_required()
def get_top_attacks():
    """Get top attack types distribution"""
    # Get query parameters
    limit = request.args.get('limit', default=5, type=int)
    
    # Query top attack types
    top_attacks = db.session.query(
        Event.attack_type,
        func.count(Event.id).label('count')
    ).filter(Event.attack_type != None).group_by(Event.attack_type).order_by(func.count(Event.id).desc()).limit(limit).all()
    
    # Calculate total events with attack type
    total_classified = Event.query.filter(Event.attack_type != None).count()
    
    result = []
    for attack in top_attacks:
        attack_type, count = attack
        percentage = (count / total_classified * 100) if total_classified > 0 else 0
        result.append({
            "attack_type": attack_type,
            "count": count,
            "percentage": round(percentage, 1)
        })
    
    return jsonify(result)

@dashboard_bp.route('/api/dashboard/severity', methods=['GET'])
@jwt_required()
def get_severity_distribution():
    """Get severity distribution of events"""
    # Query severity distribution
    severity_distribution = db.session.query(
        Event.severity,
        func.count(Event.id).label('count')
    ).group_by(Event.severity).all()
    
    result = {}
    for severity, count in severity_distribution:
        result[severity] = count
    
    return jsonify(result)

@dashboard_bp.route('/api/dashboard/timeline', methods=['GET'])
@jwt_required()
def get_event_timeline():
    """Get event timeline data"""
    # Get time range parameter
    range_param = request.args.get('range', default='7days')
    
    # Calculate date range
    now = datetime.datetime.now()
    if range_param == '24hours':
        start_date = now - datetime.timedelta(hours=24)
        interval = 'hour'
    elif range_param == '7days':
        start_date = now - datetime.timedelta(days=7)
        interval = 'day'
    elif range_param == '30days':
        start_date = now - datetime.timedelta(days=30)
        interval = 'day'
    elif range_param == '90days':
        start_date = now - datetime.timedelta(days=90)
        interval = 'week'
    else:
        start_date = now - datetime.timedelta(days=7)
        interval = 'day'
    
    # Query events in time range
    events = Event.query.filter(Event.timestamp >= start_date).order_by(Event.timestamp).all()
    
    # Format data for timeline
    timeline_data = {}
    for event in events:
        # Format date string based on interval
        if interval == 'hour':
            date_key = event.timestamp.strftime('%Y-%m-%d %H:00')
        elif interval == 'day':
            date_key = event.timestamp.strftime('%Y-%m-%d')
        elif interval == 'week':
            # Calculate week start (Monday)
            week_start = event.timestamp - datetime.timedelta(days=event.timestamp.weekday())
            date_key = week_start.strftime('%Y-%m-%d')
        
        # Initialize if this is a new date
        if date_key not in timeline_data:
            timeline_data[date_key] = {
                'total': 0,
                'severity': {
                    'low': 0,
                    'medium': 0,
                    'high': 0,
                    'critical': 0
                }
            }
        
        # Increment counters
        timeline_data[date_key]['total'] += 1
        severity = event.severity.lower() if event.severity else 'low'
        if severity in timeline_data[date_key]['severity']:
            timeline_data[date_key]['severity'][severity] += 1
    
    # Convert to list format for frontend
    result = []
    for date_key, data in timeline_data.items():
        result.append({
            'date': date_key,
            'total': data['total'],
            'low': data['severity']['low'],
            'medium': data['severity']['medium'],
            'high': data['severity']['high'],
            'critical': data['severity']['critical']
        })
    
    # Sort by date
    result.sort(key=lambda x: x['date'])
    
    return jsonify(result)

@dashboard_bp.route('/api/dashboard/mitre-distribution', methods=['GET'])
@jwt_required()
def get_mitre_distribution():
    """Get MITRE ATT&CK distribution data"""
    # Query MITRE tactics distribution
    tactics_distribution = db.session.query(
        Event.mitre_tactic,
        func.count(Event.id).label('count')
    ).filter(Event.mitre_tactic != None).group_by(Event.mitre_tactic).all()
    
    # Query MITRE techniques distribution
    techniques_distribution = db.session.query(
        Event.mitre_technique,
        func.count(Event.id).label('count')
    ).filter(Event.mitre_technique != None).group_by(Event.mitre_technique).all()
    
    result = {
        'tactics': {tactic: count for tactic, count in tactics_distribution},
        'techniques': {technique: count for technique, count in techniques_distribution},
    }
    
    return jsonify(result)
