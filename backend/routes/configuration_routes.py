from flask import Blueprint, jsonify, request, current_app
from models import db, Configuration
import json
import os

configuration_bp = Blueprint('configuration_bp', __name__)

@configuration_bp.route('/api/system-config', methods=['GET'])
def get_system_config():
    # Returns data from Configuration model
    # Get all configuration items grouped by type
    config_items = Configuration.query.all()
    
    result = {
        "general": {},
        "mitre": {},
        "export": {}
    }
    
    for item in config_items:
        # Determine which section this config item belongs to
        if item.config_type.startswith('general.'):
            key = item.config_type.replace('general.', '')
            try:
                # Handle boolean values
                if item.config_value.lower() == 'true':
                    result["general"][key] = True
                elif item.config_value.lower() == 'false':
                    result["general"][key] = False
                # Handle numeric values
                elif item.config_value.isdigit():
                    result["general"][key] = int(item.config_value)
                # Handle JSON values
                elif item.config_value.startswith('{') or item.config_value.startswith('['):
                    result["general"][key] = json.loads(item.config_value)
                else:
                    result["general"][key] = item.config_value
            except:
                result["general"][key] = item.config_value
                
        elif item.config_type.startswith('mitre.'):
            key = item.config_type.replace('mitre.', '')
            try:
                if item.config_value.lower() == 'true':
                    result["mitre"][key] = True
                elif item.config_value.lower() == 'false':
                    result["mitre"][key] = False
                elif item.config_value.isdigit():
                    result["mitre"][key] = int(item.config_value)
                elif item.config_value.startswith('{') or item.config_value.startswith('['):
                    result["mitre"][key] = json.loads(item.config_value)
                else:
                    result["mitre"][key] = item.config_value
            except:
                result["mitre"][key] = item.config_value
                
        elif item.config_type.startswith('export.'):
            key = item.config_type.replace('export.', '')
            try:
                if item.config_value.lower() == 'true':
                    result["export"][key] = True
                elif item.config_value.lower() == 'false':
                    result["export"][key] = False
                elif item.config_value.isdigit():
                    result["export"][key] = int(item.config_value)
                elif item.config_value.startswith('{') or item.config_value.startswith('['):
                    result["export"][key] = json.loads(item.config_value)
                else:
                    result["export"][key] = item.config_value
            except:
                result["export"][key] = item.config_value
    
    # Fill in defaults for any missing configuration
    if 'data_retention_days' not in result["general"]:
        result["general"]["data_retention_days"] = 90
    if 'auto_tagging_enabled' not in result["general"]:
        result["general"]["auto_tagging_enabled"] = True
    if 'ml_classification_enabled' not in result["general"]:
        result["general"]["ml_classification_enabled"] = True
    if 'refresh_interval_minutes' not in result["general"]:
        result["general"]["refresh_interval_minutes"] = 30
        
    if 'mitre_version' not in result["mitre"]:
        result["mitre"]["mitre_version"] = 'v10'
    if 'use_custom_mappings' not in result["mitre"]:
        result["mitre"]["use_custom_mappings"] = False
    if 'custom_mappings_path' not in result["mitre"]:
        result["mitre"]["custom_mappings_path"] = ''
        
    if 'default_export_format' not in result["export"]:
        result["export"]["default_export_format"] = 'csv'
    if 'include_raw_logs' not in result["export"]:
        result["export"]["include_raw_logs"] = False
    if 'max_records_per_export' not in result["export"]:
        result["export"]["max_records_per_export"] = 5000
    
    return jsonify(result)

@configuration_bp.route('/api/system-config', methods=['POST'])
def update_system_config():
    # Updates Configuration model
    data = request.json
    
    if not data:
        return jsonify({"error": "No configuration data provided"}), 400
    
    try:
        # Process general settings
        if "general" in data:
            for key, value in data["general"].items():
                config_type = f"general.{key}"
                config_item = Configuration.query.filter_by(config_type=config_type).first()
                
                # Convert value to string for storage
                if isinstance(value, bool):
                    config_value = str(value).lower()
                elif isinstance(value, (dict, list)):
                    config_value = json.dumps(value)
                else:
                    config_value = str(value)
                    
                if config_item:
                    config_item.config_value = config_value
                else:
                    new_config = Configuration(
                        name=key,
                        config_type=config_type,
                        config_value=config_value,
                        description=f"General setting: {key}"
                    )
                    db.session.add(new_config)
        
        # Process MITRE settings
        if "mitre" in data:
            for key, value in data["mitre"].items():
                config_type = f"mitre.{key}"
                config_item = Configuration.query.filter_by(config_type=config_type).first()
                
                # Convert value to string for storage
                if isinstance(value, bool):
                    config_value = str(value).lower()
                elif isinstance(value, (dict, list)):
                    config_value = json.dumps(value)
                else:
                    config_value = str(value)
                    
                if config_item:
                    config_item.config_value = config_value
                else:
                    new_config = Configuration(
                        name=key,
                        config_type=config_type,
                        config_value=config_value,
                        description=f"MITRE setting: {key}"
                    )
                    db.session.add(new_config)
        
        # Process export settings
        if "export" in data:
            for key, value in data["export"].items():
                config_type = f"export.{key}"
                config_item = Configuration.query.filter_by(config_type=config_type).first()
                
                # Convert value to string for storage
                if isinstance(value, bool):
                    config_value = str(value).lower()
                elif isinstance(value, (dict, list)):
                    config_value = json.dumps(value)
                else:
                    config_value = str(value)
                    
                if config_item:
                    config_item.config_value = config_value
                else:
                    new_config = Configuration(
                        name=key,
                        config_type=config_type,
                        config_value=config_value,
                        description=f"Export setting: {key}"
                    )
                    db.session.add(new_config)
        
        db.session.commit()
        return jsonify({"message": "Configuration updated successfully"})
    
    except Exception as e:
        current_app.logger.error(f"Error updating configuration: {str(e)}")
        return jsonify({"error": f"Error updating configuration: {str(e)}"}), 500

@configuration_bp.route('/config', methods=['GET'])
def get_configuration():
    # Returns data from Configuration model
    # Get all configuration items grouped by type
    config_items = Configuration.query.all()
    
    result = {
        "general": {},
        "mitre": {},
        "export": {}
    }
    
    for item in config_items:
        # Determine which section this config item belongs to
        if item.config_type.startswith('general.'):
            key = item.config_type.replace('general.', '')
            try:
                # Handle boolean values
                if item.config_value.lower() == 'true':
                    result["general"][key] = True
                elif item.config_value.lower() == 'false':
                    result["general"][key] = False
                # Handle numeric values
                elif item.config_value.isdigit():
                    result["general"][key] = int(item.config_value)
                # Handle JSON values
                elif item.config_value.startswith('{') or item.config_value.startswith('['):
                    result["general"][key] = json.loads(item.config_value)
                else:
                    result["general"][key] = item.config_value
            except:
                result["general"][key] = item.config_value
                
        elif item.config_type.startswith('mitre.'):
            key = item.config_type.replace('mitre.', '')
            try:
                if item.config_value.lower() == 'true':
                    result["mitre"][key] = True
                elif item.config_value.lower() == 'false':
                    result["mitre"][key] = False
                elif item.config_value.isdigit():
                    result["mitre"][key] = int(item.config_value)
                elif item.config_value.startswith('{') or item.config_value.startswith('['):
                    result["mitre"][key] = json.loads(item.config_value)
                else:
                    result["mitre"][key] = item.config_value
            except:
                result["mitre"][key] = item.config_value
                
        elif item.config_type.startswith('export.'):
            key = item.config_type.replace('export.', '')
            try:
                if item.config_value.lower() == 'true':
                    result["export"][key] = True
                elif item.config_value.lower() == 'false':
                    result["export"][key] = False
                elif item.config_value.isdigit():
                    result["export"][key] = int(item.config_value)
                elif item.config_value.startswith('{') or item.config_value.startswith('['):
                    result["export"][key] = json.loads(item.config_value)
                else:
                    result["export"][key] = item.config_value
            except:
                result["export"][key] = item.config_value
    
    # Fill in defaults for any missing configuration
    if 'data_retention_days' not in result["general"]:
        result["general"]["data_retention_days"] = 90
    if 'auto_tagging_enabled' not in result["general"]:
        result["general"]["auto_tagging_enabled"] = True
    if 'ml_classification_enabled' not in result["general"]:
        result["general"]["ml_classification_enabled"] = True
    if 'refresh_interval_minutes' not in result["general"]:
        result["general"]["refresh_interval_minutes"] = 30
        
    if 'mitre_version' not in result["mitre"]:
        result["mitre"]["mitre_version"] = 'v10'
    if 'use_custom_mappings' not in result["mitre"]:
        result["mitre"]["use_custom_mappings"] = False
    if 'custom_mappings_path' not in result["mitre"]:
        result["mitre"]["custom_mappings_path"] = ''
        
    if 'default_export_format' not in result["export"]:
        result["export"]["default_export_format"] = 'csv'
    if 'include_raw_logs' not in result["export"]:
        result["export"]["include_raw_logs"] = False
    if 'max_records_per_export' not in result["export"]:
        result["export"]["max_records_per_export"] = 5000
    
    # Переконатись, що demo_mode_enabled включено у відповідь
    config_data = result
    if 'general' not in config_data:
        config_data['general'] = {}
    if 'demo_mode_enabled' not in config_data['general']:
        config_data['general']['demo_mode_enabled'] = False
    
    return jsonify(config_data)
