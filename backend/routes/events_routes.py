from flask import Blueprint, jsonify, request, current_app
from models import db, Event, RawLog
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

events_bp = Blueprint('events', __name__)

@events_bp.route('/api/events', methods=['GET'])
def get_events():
    try:
        # Basic pagination logic
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        
        # Query with basic filters
        query = Event.query
        
        # Apply pagination
        pagination = query.paginate(page=page, per_page=page_size)
        events = pagination.items
        
        # Format response
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "source_ip": event.source_ip,
                "severity": event.severity,
                "siem_source": event.siem_source,
                "manual_review": event.manual_review,
                "labels": event.labels
            })
        
        response = {
            "events": events_data,
            "page": page,
            "page_size": page_size,
            "total_count": pagination.total,
            "total_pages": pagination.pages
        }
        
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Error in get_events: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
