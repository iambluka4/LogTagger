from flask import Blueprint, request, jsonify, current_app
from models import db, Settings
from services.siem_service import SIEMService
import traceback

api_config_bp = Blueprint('api_config_bp', __name__)

@api_config_bp.route('/api/config', methods=['GET'])
def get_config():
    # Returns data from Settings model
    config = Settings.query.first()
    if config:
        return jsonify(config.to_dict())
    else:
        return jsonify({"message": "Config not found"}), 404

@api_config_bp.route('/api/config', methods=['POST'])
def update_config():
    # Updates Settings model
    data = request.json
    config = Settings.query.first()

    if config is None:
        config = Settings()

    # Regular fields update
    config.wazuh_api_url = data.get("wazuh_api_url", config.wazuh_api_url)
    config.splunk_api_url = data.get("splunk_api_url", config.splunk_api_url)
    config.elastic_api_url = data.get("elastic_api_url", config.elastic_api_url)
    config.ml_api_url = data.get("ml_api_url", config.ml_api_url)

    # API keys update with proper empty string handling
    if "wazuh_api_key" in data:
        config.wazuh_api_key = data["wazuh_api_key"]
    if "splunk_api_key" in data:
        config.splunk_api_key = data["splunk_api_key"]
    if "elastic_api_key" in data:
        config.elastic_api_key = data["elastic_api_key"]
    if "ml_api_key" in data:
        config.ml_api_key = data["ml_api_key"]

    db.session.add(config)
    db.session.commit()
    return jsonify({"message": "Config updated successfully"})

@api_config_bp.route('/api/config/test-connection', methods=['POST'])
def test_connection():
    """
    Enhanced endpoint for testing connection to external APIs
    with detailed diagnostics
    """
    data = request.json
    connection_type = data.get('type')
    
    if not connection_type:
        return jsonify({
            "success": False,
            "message": "Connection type not specified",
            "details": {
                "required_fields": ["type", "api_url", "api_key"]
            }
        }), 400
    
    api_url = data.get("api_url")
    api_key = data.get("api_key")
    
    if not api_url:
        return jsonify({
            "success": False,
            "message": f"API URL not provided for {connection_type}",
            "details": {
                "connection_type": connection_type
            }
        }), 400
    
    try:
        current_app.logger.info(f"Testing connection to {connection_type} at {api_url}")
        
        # Create appropriate service based on connection type
        if connection_type in ['wazuh', 'splunk', 'elastic']:
            siem_service = SIEMService(api_url, api_key, connection_type)
            result = siem_service.test_connection()
            return jsonify(result)
        elif connection_type == 'ml_api':
            # Test ML API connection
            # This is a placeholder - you'd need to implement the actual ML API test
            return jsonify({
                "success": True,
                "message": "ML API connection test is not fully implemented yet",
                "details": {
                    "api_url": api_url
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Unsupported connection type: {connection_type}",
                "details": {
                    "supported_types": ["wazuh", "splunk", "elastic", "ml_api"]
                }
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Connection test error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "details": {
                "error_type": type(e).__name__,
                "connection_type": connection_type,
                "api_url": api_url
            }
        }), 500
