from flask import Blueprint, request, jsonify
from models import db, Settings

api_config_bp = Blueprint('api_config_bp', __name__)

@api_config_bp.route('/api/config', methods=['GET'])
def get_config():
    config = Settings.query.first()
    if config:
        return jsonify({
            "wazuh_api_url": config.wazuh_api_url,
            "wazuh_api_key": config.wazuh_api_key
        })
    else:
        return jsonify({"message": "Config not found"}), 404

@api_config_bp.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    config = Settings.query.first()

    if config is None:
        config = Settings()

    config.wazuh_api_url = data.get("wazuh_api_url")
    config.wazuh_api_key = data.get("wazuh_api_key")

    db.session.add(config)
    db.session.commit()
    return jsonify({"message": "Config updated successfully"})
