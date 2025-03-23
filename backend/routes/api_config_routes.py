from flask import Blueprint, request, jsonify
from models import db, Settings

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

    # Update all API configuration fields
    config.wazuh_api_url = data.get("wazuh_api_url", config.wazuh_api_url)
    config.wazuh_api_key = data.get("wazuh_api_key", config.wazuh_api_key)
    config.splunk_api_url = data.get("splunk_api_url", config.splunk_api_url)  
    config.splunk_api_key = data.get("splunk_api_key", config.splunk_api_key)
    config.elastic_api_url = data.get("elastic_api_url", config.elastic_api_url)
    config.elastic_api_key = data.get("elastic_api_key", config.elastic_api_key)
    config.ml_api_url = data.get("ml_api_url", config.ml_api_url)
    config.ml_api_key = data.get("ml_api_key", config.ml_api_key)

    # Only update API key if a new one is provided (not empty string)
    if not data.get("wazuh_api_key"):
        config.wazuh_api_key = config.wazuh_api_key
    if not data.get("splunk_api_key"):
        config.splunk_api_key = config.splunk_api_key
    if not data.get("elastic_api_key"):
        config.elastic_api_key = config.elastic_api_key
    if not data.get("ml_api_key"):
        config.ml_api_key = config.ml_api_key

    db.session.add(config)
    db.session.commit()
    return jsonify({"message": "Config updated successfully"})
