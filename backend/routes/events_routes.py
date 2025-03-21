import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import db, Event, RawLog, Settings, User, ExportJob
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.auth import analyst_required
from services.siem_service import SIEMService
from services.ml_service import MLService
import pandas as pd
import os

events_bp = Blueprint('events_bp', __name__)

@events_bp.route('/api/events', methods=['GET'])
@jwt_required()
def get_events():
    # Get query parameters for filtering
    severity = request.args.get('severity')
    source_ip = request.args.get('source_ip')
    siem_source = request.args.get('siem_source')
    attack_type = request.args.get('attack_type')
    mitre_tactic = request.args.get('mitre_tactic')
    mitre_technique = request.args.get('mitre_technique')
    true_positive = request.args.get('true_positive')
    manual_review = request.args.get('manual_review')
    manual_tags = request.args.get('manual_tags')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    
    # Start building the query
    query = Event.query
    
    # Apply filters if they exist
    if severity:
        query = query.filter(Event.severity == severity)
    if source_ip:
        query = query.filter(Event.source_ip.like(f"%{source_ip}%"))
    if siem_source:
        query = query.filter(Event.siem_source == siem_source)
    if attack_type:
        query = query.filter(Event.attack_type == attack_type)
    if mitre_tactic:
        query = query.filter(Event.mitre_tactic == mitre_tactic)
    if mitre_technique:
        query = query.filter(Event.mitre_technique == mitre_technique)
    if true_positive is not None:
        query = query.filter(Event.true_positive == (true_positive.lower() == 'true'))
    if manual_review is not None:
        query = query.filter(Event.manual_review == (manual_review.lower() == 'true'))
    if manual_tags:
        query = query.filter(Event.manual_tags.like(f"%{manual_tags}%"))
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            query = query.filter(Event.timestamp >= from_date)
        except ValueError:
            return jsonify({"error": "Invalid date_from format"}), 400
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to)
            query = query.filter(Event.timestamp <= to_date)
        except ValueError:
            return jsonify({"error": "Invalid date_to format"}), 400
    
    # Apply pagination
    total_count = query.count()
    events = query.order_by(Event.timestamp.desc()).paginate(page=page, per_page=page_size)
    
    # Format the response
    result = {
        "events": [event.to_dict() for event in events.items],
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": events.pages
    }
    
    return jsonify(result)

@events_bp.route('/api/events/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    # Get the raw logs associated with this event
    raw_logs = [raw_log.to_dict() for raw_log in event.raw_logs]
    
    # Prepare the response with both event and raw logs
    result = event.to_dict()
    result['raw_logs'] = raw_logs
    
    return jsonify(result)

@events_bp.route('/api/events/<int:event_id>/label', methods=['POST'])
@jwt_required()
@analyst_required
def label_event(event_id):
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    data = request.json
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    
    # Update event with manual labels
    if 'true_positive' in data:
        event.true_positive = data['true_positive']
    if 'attack_type' in data:
        event.attack_type = data['attack_type']
    if 'mitre_tactic' in data:
        event.mitre_tactic = data['mitre_tactic']
    if 'mitre_technique' in data:
        event.mitre_technique = data['mitre_technique']
    if 'manual_tags' in data:
        event.manual_tags = ','.join(data['manual_tags']) if isinstance(data['manual_tags'], list) else data['manual_tags']
    
    # Mark as manually reviewed
    event.manual_review = True
    event.reviewed_by = user.id
    event.review_timestamp = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({"message": "Event labeled successfully", "event": event.to_dict()})

@events_bp.route('/api/events/fetch', methods=['POST'])
@jwt_required()
@analyst_required
def fetch_events():
    settings = Settings.query.first()
    
    if not settings:
        return jsonify({"error": "No SIEM settings configured"}), 400
    
    data = request.json or {}
    siem_type = data.get('siem_type', 'wazuh')
    
    if siem_type == 'wazuh' and (not settings.wazuh_api_url or not settings.wazuh_api_key):
        return jsonify({"error": "Wazuh API not configured"}), 400
    elif siem_type == 'splunk' and (not settings.splunk_api_url or not settings.splunk_api_key):
        return jsonify({"error": "Splunk API not configured"}), 400
    elif siem_type == 'elastic' and (not settings.elastic_api_url or not settings.elastic_api_key):
        return jsonify({"error": "Elastic API not configured"}), 400
    
    # Create appropriate SIEM service based on the type
    if siem_type == 'wazuh':
        siem_service = SIEMService(settings.wazuh_api_url, settings.wazuh_api_key, 'wazuh')
    elif siem_type == 'splunk':
        siem_service = SIEMService(settings.splunk_api_url, settings.splunk_api_key, 'splunk')
    elif siem_type == 'elastic':
        siem_service = SIEMService(settings.elastic_api_url, settings.elastic_api_key, 'elastic')
    else:
        return jsonify({"error": f"Unsupported SIEM type: {siem_type}"}), 400
    
    # Fetch logs from the SIEM
    logs = siem_service.fetch_logs(data.get('params', {}))
    
    if not logs:
        return jsonify({"message": "No new logs found", "count": 0})
    
    # Store events and raw logs
    saved_count = 0
    for log in logs:
        # Check if event already exists
        existing_event = Event.query.filter_by(event_id=log['event_id'], siem_source=log['siem_source']).first()
        
        if existing_event:
            continue
            
        # Create new event
        new_event = Event(
            event_id=log['event_id'],
            timestamp=datetime.fromisoformat(log['timestamp']) if isinstance(log['timestamp'], str) else log['timestamp'],
            source_ip=log['source_ip'],
            severity=log['severity'],
            siem_source=log['siem_source'],
            labels={}
        )
        
        db.session.add(new_event)
        db.session.flush()  # Get the ID assigned to the new event
        
        # Store the raw log
        raw_log = RawLog(
            event_id=new_event.id,
            siem_source=log['siem_source'],
            raw_log=log['raw_log']
        )
        db.session.add(raw_log)
        
        saved_count += 1
    
    db.session.commit()
    
    # Apply ML classification if a model is configured
    if settings.ml_api_url and settings.ml_api_key:
        try:
            ml_service = MLService(settings.ml_api_url, settings.ml_api_key)
            # Classify newly added events (this would be implemented in a background task in production)
            # For simplicity, we'll skip the actual classification here
            current_app.logger.info("ML classification would be applied here")
        except Exception as e:
            current_app.logger.error(f"Error applying ML classification: {str(e)}")
    
    return jsonify({
        "message": "Events fetched and stored successfully",
        "total_logs": len(logs),
        "new_logs": saved_count
    })

@events_bp.route('/api/events/export', methods=['POST'])
@jwt_required()
def export_events():
    data = request.json or {}
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Create export job
    export_job = ExportJob(
        user_id=user.id,
        format=data.get('format', 'csv'),
        filters=data.get('filters', {}),
        status='pending'
    )
    
    db.session.add(export_job)
    db.session.commit()
    
    # In a real implementation, you would initiate a background task here
    # For simplicity, we'll execute the export synchronously
    
    # Apply filters from the export job
    filters = export_job.filters or {}
    query = Event.query
    
    if 'severity' in filters:
        query = query.filter(Event.severity == filters['severity'])
    if 'siem_source' in filters:
        query = query.filter(Event.siem_source == filters['siem_source'])
    if 'manual_review' in filters:
        query = query.filter(Event.manual_review == filters['manual_review'])
    # Add other filters as needed
    
    events = query.all()
    events_data = [event.to_dict() for event in events]
    
    # Ensure export directory exists
    export_dir = current_app.config.get('EXPORT_DIR', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = os.path.join(export_dir, f'export_{timestamp}.{export_job.format.lower()}')
    
    # Export data
    try:
        if export_job.format.lower() == 'csv':
            df = pd.DataFrame(events_data)
            df.to_csv(file_path, index=False)
        elif export_job.format.lower() == 'json':
            with open(file_path, 'w') as f:
                json.dump(events_data, f)
        else:
            export_job.status = 'failed'
            db.session.commit()
            return jsonify({"error": f"Unsupported export format: {export_job.format}"}), 400
        
        # Update export job status
        export_job.status = 'completed'
        export_job.file_path = file_path
        export_job.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Export completed successfully",
            "export_job_id": export_job.id,
            "file_path": file_path,
            "record_count": len(events_data)
        })
        
    except Exception as e:
        export_job.status = 'failed'
        db.session.commit()
        current_app.logger.error(f"Export failed: {str(e)}")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500
