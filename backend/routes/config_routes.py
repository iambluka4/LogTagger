from flask import Blueprint, jsonify, request, current_app
from models import db, Configuration
from sqlalchemy.exc import SQLAlchemyError

config_bp = Blueprint('config', __name__)

@config_bp.route('/api/system-config', methods=['GET'])
def get_system_config():
    try:
        config = Configuration.query.filter_by(name='system').first()
        
        if not config:
            return jsonify({"config": {}}), 200
            
        return jsonify({"config": config.config_data})
    except Exception as e:
        current_app.logger.error(f"Error in get_system_config: {str(e)}")
        return jsonify({"message": "Error retrieving configuration", "detail": str(e)}), 500

@config_bp.route('/api/system-config', methods=['POST'])
def update_system_config():
    try:
        data = request.get_json()
        
        config = Configuration.query.filter_by(name='system').first()
        
        if not config:
            config = Configuration(name='system', config_data={})
            db.session.add(config)
        
        # Update the configuration
        config.config_data = data
        
        db.session.commit()
        
        return jsonify({"message": "Configuration updated successfully"})
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_system_config: {str(e)}")
        return jsonify({"message": "Database error", "detail": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error in update_system_config: {str(e)}")
        return jsonify({"message": "Error updating configuration", "detail": str(e)}), 500
