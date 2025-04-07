from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from models import db, Event
import logging
from datetime import datetime  # Додаємо імпорт datetime для можливих майбутніх розширень

batch_bp = Blueprint('batch_bp', __name__)

@batch_bp.route('/api/events/batch-label', methods=['POST'])
def batch_label_events():
    """
    Масове маркування подій за спільними критеріями.
    
    Request body:
    {
        "filters": {
            "severity": "high",
            "source_ip": "192.168.1.1",
            "siem_source": "wazuh",
            "date_from": "2023-01-01T00:00:00",
            "date_to": "2023-01-31T23:59:59"
        },
        "labels": {
            "true_positive": true,
            "attack_type": "bruteforce",
            "mitre_tactic": "TA0006",
            "mitre_technique": "T1110",
            "manual_tags": ["mass_labeled", "reviewed"]
        }
    }
    
    Returns:
        JSON: Кількість оновлених подій та статус операції
    """
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        filters = data.get('filters', {})
        labels = data.get('labels', {})
        
        if not filters or not labels:
            return jsonify({"message": "Both filters and labels are required"}), 400
        
        # Будуємо запит з фільтрами
        query = Event.query
        
        if filters.get('severity'):
            query = query.filter(Event.severity == filters['severity'])
        
        if filters.get('source_ip'):
            query = query.filter(Event.source_ip == filters['source_ip'])
            
        if filters.get('siem_source'):
            query = query.filter(Event.siem_source == filters['siem_source'])
        
        # Додавання інших фільтрів...
        
        # Виконуємо оновлення
        updated_count = 0
        events = query.all()
        
        for event in events:
            if not event.labels_data:
                event.labels_data = {}
                
            # Оновлюємо мітки
            for key, value in labels.items():
                if key == 'manual_tags' and isinstance(value, list):
                    # Додаємо нові теги до існуючих
                    current_tags = event.manual_tags
                    for tag in value:
                        if tag not in current_tags:
                            current_tags.append(tag)
                    event.manual_tags = current_tags
                else:
                    event.labels_data[key] = value
            
            event.manual_review = True
            db.session.add(event)
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            "message": "Batch labeling completed successfully",
            "updated_count": updated_count
        })
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in batch_label_events: {str(e)}")
        return jsonify({"message": "Database error", "detail": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error in batch labeling: {str(e)}")
        return jsonify({"message": "Error processing batch labeling", "detail": str(e)}), 500
