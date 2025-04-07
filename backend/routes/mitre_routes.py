from flask import Blueprint, jsonify, request, current_app
from models import db
import json
import os

mitre_bp = Blueprint('mitre_bp', __name__)

# Додаємо перевірку існування директорії
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

MITRE_DATA_FILE = os.path.join(data_dir, 'mitre_attack.json')

def load_mitre_data():
    """Завантаження даних MITRE ATT&CK з JSON-файлу"""
    try:
        if os.path.exists(MITRE_DATA_FILE):
            with open(MITRE_DATA_FILE, 'r') as f:
                return json.load(f)
        
        # Якщо файл відсутній, повернути базові дані
        return {
            "tactics": [
                {"id": "TA0001", "name": "Initial Access", "description": "Initial access techniques..."},
                {"id": "TA0002", "name": "Execution", "description": "Execution techniques..."},
                {"id": "TA0003", "name": "Persistence", "description": "Persistence techniques..."},
                {"id": "TA0004", "name": "Privilege Escalation", "description": "Privilege Escalation techniques..."},
                {"id": "TA0005", "name": "Defense Evasion", "description": "Defense Evasion techniques..."},
                {"id": "TA0006", "name": "Credential Access", "description": "Credential Access techniques..."},
                {"id": "TA0007", "name": "Discovery", "description": "Discovery techniques..."},
                {"id": "TA0008", "name": "Lateral Movement", "description": "Lateral Movement techniques..."},
                {"id": "TA0009", "name": "Collection", "description": "Collection techniques..."},
                {"id": "TA0010", "name": "Exfiltration", "description": "Exfiltration techniques..."},
                {"id": "TA0011", "name": "Command and Control", "description": "Command and Control techniques..."},
                {"id": "TA0040", "name": "Impact", "description": "Impact techniques..."}
            ],
            "techniques": [
                {"id": "T1566", "name": "Phishing", "tactic_ids": ["TA0001"], "description": "Phishing techniques..."},
                {"id": "T1204", "name": "User Execution", "tactic_ids": ["TA0002"], "description": "User execution..."},
                {"id": "T1078", "name": "Valid Accounts", "tactic_ids": ["TA0001"], "description": "Valid Accounts..."},
                {"id": "T1059", "name": "Command Line Interface", "tactic_ids": ["TA0002"], "description": "Command Line..."},
                {"id": "T1053", "name": "Scheduled Task", "tactic_ids": ["TA0003"], "description": "Scheduled Task..."},
                {"id": "T1548", "name": "Bypass User Account Control", "tactic_ids": ["TA0004"], "description": "UAC Bypass..."},
                {"id": "T1562", "name": "Disable Security Tools", "tactic_ids": ["TA0005"], "description": "Disable Security Tools..."},
                {"id": "T1110", "name": "Brute Force", "tactic_ids": ["TA0006"], "description": "Brute Force..."},
                {"id": "T1046", "name": "Network Service Scanning", "tactic_ids": ["TA0007"], "description": "Network Scanning..."},
                {"id": "T1021", "name": "Remote Services", "tactic_ids": ["TA0008"], "description": "Remote Services..."},
                {"id": "T1560", "name": "Data Transfer Size Limits", "tactic_ids": ["TA0010"], "description": "Size Limits..."},
                {"id": "T1071", "name": "Web Service", "tactic_ids": ["TA0011"], "description": "Web Service..."},
                {"id": "T1485", "name": "Data Destruction", "tactic_ids": ["TA0040"], "description": "Data Destruction..."}
            ]
        }
    except Exception as e:
        current_app.logger.error(f"Error loading MITRE data: {e}")
        return {"tactics": [], "techniques": []}

@mitre_bp.route('/api/mitre/tactics', methods=['GET'])
def get_tactics():
    """Отримання тактик MITRE ATT&CK"""
    mitre_data = load_mitre_data()
    return jsonify(mitre_data["tactics"])

@mitre_bp.route('/api/mitre/techniques', methods=['GET'])
def get_techniques():
    """Отримання технік MITRE ATT&CK"""
    tactic_id = request.args.get('tactic_id')
    mitre_data = load_mitre_data()
    
    # Якщо вказаний tactic_id, фільтруємо техніки
    if tactic_id:
        filtered_techniques = [
            tech for tech in mitre_data["techniques"] 
            if tactic_id in tech.get("tactic_ids", [])
        ]
        return jsonify(filtered_techniques)
    
    # Інакше повертаємо всі техніки
    return jsonify(mitre_data["techniques"])
