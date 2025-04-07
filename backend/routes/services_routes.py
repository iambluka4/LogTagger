from flask import Blueprint, jsonify, current_app
import requests
from datetime import datetime
import logging
from ..services.siem_service import SIEMService
from ..services.ml_service import MLService
from ..models import APISettings

services_bp = Blueprint('services', __name__)
logger = logging.getLogger(__name__)

@services_bp.route('/api/services/status', methods=['GET'])
def get_services_status():
    """Перевірка статусу всіх зовнішніх сервісів"""
    try:
        # Отримуємо налаштування API з бази даних
        settings = APISettings.query.first()
        
        status = {
            "siem": {
                "wazuh": check_siem_status(settings, "wazuh"),
                "splunk": check_siem_status(settings, "splunk"),
                "elastic": check_siem_status(settings, "elastic")
            },
            "ml": check_ml_status(settings)
        }
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error checking services status: {str(e)}")
        return jsonify({
            "error": f"Failed to check services status: {str(e)}"
        }), 500

def check_siem_status(settings, siem_type):
    """Перевірка статусу SIEM сервісу"""
    status = {
        "status": "not_configured",
        "lastChecked": datetime.now().isoformat()
    }
    
    api_url = getattr(settings, f"{siem_type}_api_url", None)
    api_key = getattr(settings, f"{siem_type}_api_key", None)
    
    if not api_url or not api_key:
        return status
    
    try:
        siem_service = SIEMService(api_url, api_key, siem_type)
        result = siem_service.test_connection()
        
        if result.get("success", False):
            status["status"] = "online"
        else:
            status["status"] = "offline"
            status["message"] = result.get("message", "Connection test failed")
    except Exception as e:
        logger.error(f"Error checking {siem_type} status: {str(e)}")
        status["status"] = "offline"
        status["error"] = str(e)
    
    return status

def check_ml_status(settings):
    """Перевірка статусу ML API"""
    status = {
        "status": "not_configured",
        "lastChecked": datetime.now().isoformat()
    }
    
    if not settings.ml_api_url or not settings.ml_api_key:
        return status
    
    try:
        ml_service = MLService(settings.ml_api_url, settings.ml_api_key)
        tactics = ml_service.get_mitre_tactics()
        
        if tactics is not None:
            status["status"] = "online"
        else:
            status["status"] = "offline"
    except Exception as e:
        logger.error(f"Error checking ML API status: {str(e)}")
        status["status"] = "offline"
        status["error"] = str(e)
    
    return status
