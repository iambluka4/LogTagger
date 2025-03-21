from flask import Blueprint, request, jsonify
from models import db, Configuration
import requests
from sqlalchemy.exc import SQLAlchemyError

configuration_bp = Blueprint('configuration', __name__)

@configuration_bp.route('/api/config/load', methods=['GET'])
def load_config():
    try:
        configs = Configuration.query.all()
        return jsonify([config.to_dict() for config in configs])
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@configuration_bp.route('/api/config/save', methods=['POST'])
def save_config():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        config_id = data.get('id')
        if config_id:
            config = Configuration.query.get(config_id)
            if config:
                config.update(data)
            else:
                return jsonify({"status": "error", "message": "Configuration not found"}), 404
        else:
            # Validate required fields
            if 'name' not in data or 'config_type' not in data:
                return jsonify({"status": "error", "message": "Name and config_type are required"}), 400
                
            config = Configuration(**data)
            db.session.add(config)
            
        db.session.commit()
        return jsonify({"status": "success", "message": "Configuration saved successfully"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@configuration_bp.route('/api/config/delete/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({"status": "error", "message": "Configuration not found"}), 404
        
        db.session.delete(config)
        db.session.commit()
        return jsonify({"status": "success", "message": "Configuration deleted successfully"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@configuration_bp.route('/api/config/test_connection', methods=['POST'])
def test_connection():
    try:
        data = request.json
        siem_status = test_siem_connection(data)
        ml_status = test_ml_connection(data)
        
        return jsonify({
            "status": "success",
            "siem_connection": siem_status,
            "ml_connection": ml_status
        })
    except requests.RequestException as e:
        return jsonify({"status": "error", "message": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def test_siem_connection(config):
    # TODO: Implement actual SIEM connection test
    # Example: Make a test request to SIEM API
    try:
        # For now, we'll simulate a successful connection
        return "active"
    except:
        return "error"

def test_ml_connection(config):
    # TODO: Implement actual ML connection test
    # Example: Make a test request to ML API
    try:
        # For now, we'll simulate an inactive connection
        return "inactive"
    except:
        return "error"