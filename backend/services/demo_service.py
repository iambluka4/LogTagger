"""
Сервіс для генерації та управління демонстраційними даними
"""
import random
import json
from datetime import datetime, timedelta
import ipaddress
from models import Event, RawLog, db
import os
import uuid

# Шлях до файлу з демо-даними
DEMO_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'demo_data.json')

class DemoService:
    """Сервіс для генерації та управління демонстраційними даними"""
    
    @staticmethod
    def load_demo_data():
        """Завантажує демонстраційні дані з файлу або генерує нові"""
        if os.path.exists(DEMO_DATA_FILE):
            try:
                with open(DEMO_DATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading demo data: {e}")
        
        # Якщо файл відсутній або пошкоджений, генеруємо нові дані
        return DemoService.generate_demo_data()
    
    @staticmethod
    def save_demo_data(data):
        """Зберігає демонстраційні дані у файл"""
        try:
            # Створюємо директорію для даних, якщо вона не існує
            os.makedirs(os.path.dirname(DEMO_DATA_FILE), exist_ok=True)
            
            with open(DEMO_DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving demo data: {e}")
            return False
    
    @staticmethod
    def generate_demo_data(num_events=50):
        """Генерує демонстраційні дані для логів безпеки"""
        demo_data = []
        
        # Приклади типів атак
        attack_types = [
            "Brute Force", "SQL Injection", "Cross-Site Scripting", 
            "Denial of Service", "Phishing", "Malware", 
            "Command Injection", "Directory Traversal"
        ]
        
        # Приклади серйозності
        severities = ["low", "medium", "high", "critical"]
        severity_weights = [40, 30, 20, 10]  # Розподіл ваг для генерації
        
        # Приклади тактик MITRE
        mitre_tactics = [
            "Initial Access", "Execution", "Persistence", "Privilege Escalation",
            "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement"
        ]
        
        # Приклади технік MITRE відповідно до тактик
        mitre_techniques = {
            "Initial Access": ["Phishing", "Valid Accounts", "Supply Chain Compromise"],
            "Execution": ["Command Line Interface", "PowerShell", "Scripting"],
            "Persistence": ["Registry Run Keys", "Scheduled Task", "Create Account"],
            "Privilege Escalation": ["Access Token Manipulation", "Bypass User Account Control"],
            "Defense Evasion": ["Disable Security Tools", "Masquerading", "Rootkit"],
            "Credential Access": ["Brute Force", "Credential Dumping", "Password Spraying"],
            "Discovery": ["Account Discovery", "Network Service Scanning"],
            "Lateral Movement": ["Remote Services", "Internal Spearphishing", "Pass the Hash"]
        }
        
        # Генеруємо випадкові IP-адреси
        source_ips = [
            str(ipaddress.IPv4Address(random.randint(0x01000000, 0xCFFFFFFF))) 
            for _ in range(10)
        ]
        
        # Генеруємо події
        now = datetime.utcnow()
        for i in range(num_events):
            # Випадковий час в межах останнього місяця
            event_time = now - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Випадкова серйозність з урахуванням ваг розподілу
            severity = random.choices(severities, weights=severity_weights)[0]
            
            # Випадковий тип атаки, тактика і техніка
            attack_type = random.choice(attack_types)
            mitre_tactic = random.choice(mitre_tactics)
            mitre_technique = random.choice(mitre_techniques.get(mitre_tactic, ["Unknown"]))
            
            # Випадкова IP-адреса джерела
            source_ip = random.choice(source_ips)
            
            # Створюємо унікальний ідентифікатор для події
            event_id = f"demo-event-{uuid.uuid4()}"
            
            # Генеруємо вихідний лог залежно від типу атаки
            raw_log = DemoService._generate_raw_log_for_attack(
                attack_type, source_ip, event_time
            )
            
            # Створюємо подію
            event = {
                "id": i + 1,
                "event_id": event_id,
                "timestamp": event_time.isoformat(),
                "source_ip": source_ip,
                "severity": severity,
                "siem_source": "demo",
                "attack_type": attack_type,
                "mitre_tactic": mitre_tactic,
                "mitre_technique": mitre_technique,
                "manual_review": random.random() < 0.3,  # 30% шанс, що подія переглянута
                "true_positive": random.random() < 0.8 if random.random() < 0.3 else None,  # 80% true positives серед переглянутих
                "manual_tags": random.sample(["suspicious", "verified", "false-positive", "needs-investigation", "remediated"], 
                                         k=random.randint(0, 3)) if random.random() < 0.3 else [],
                "has_raw_logs": True,
                "raw_logs": [{"id": i + 1, "event_id": i + 1, "siem_source": "demo", "raw_log": raw_log}]
            }
            
            demo_data.append(event)
        
        # Сортуємо події за часом (найновіші спочатку)
        demo_data.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"events": demo_data}
    
    @staticmethod
    def _generate_raw_log_for_attack(attack_type, source_ip, event_time):
        """Генерує вихідні логи для конкретного типу атаки"""
        templates = {
            "Brute Force": {
                "type": "authentication_failure",
                "user": f"user_{random.randint(1, 100)}",
                "attempts": random.randint(5, 20),
                "source_ip": source_ip,
                "dest_ip": f"10.0.0.{random.randint(1, 254)}",
                "service": random.choice(["ssh", "ftp", "rdp", "web"]),
                "protocol": random.choice(["tcp", "udp"]),
                "port": random.randint(20, 10000),
                "message": "Multiple failed login attempts detected",
                "timestamp": event_time.isoformat()
            },
            "SQL Injection": {
                "type": "web_attack",
                "source_ip": source_ip,
                "dest_ip": f"10.0.0.{random.randint(1, 254)}",
                "url": f"/api/{random.choice(['users', 'products', 'orders'])}.php?id=1' OR '1'='1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "http_method": "GET",
                "status_code": random.choice([200, 500]),
                "message": "Possible SQL injection attempt detected in request parameters",
                "timestamp": event_time.isoformat()
            },
            "Cross-Site Scripting": {
                "type": "web_attack",
                "source_ip": source_ip,
                "dest_ip": f"10.0.0.{random.randint(1, 254)}",
                "url": f"/page.php?param=<script>alert('XSS')</script>",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "http_method": "GET",
                "status_code": random.choice([200, 400]),
                "message": "Possible XSS attack detected in request parameters",
                "timestamp": event_time.isoformat()
            },
            "Denial of Service": {
                "type": "network_attack",
                "source_ip": source_ip,
                "dest_ip": f"10.0.0.{random.randint(1, 254)}",
                "protocol": "TCP",
                "port": 80,
                "packets_per_second": random.randint(1000, 10000),
                "bandwidth": f"{random.randint(100, 1000)} Mbps",
                "message": "Abnormal traffic pattern detected, possible DoS attack",
                "timestamp": event_time.isoformat()
            },
            "Phishing": {
                "type": "email_threat",
                "source_ip": source_ip,
                "from": f"attacker{random.randint(1, 100)}@malicious-domain.com",
                "to": f"user{random.randint(1, 100)}@example.com",
                "subject": "Urgent: Your account will be suspended",
                "attachment": random.choice([True, False]),
                "attachment_name": "invoice.docx" if random.choice([True, False]) else None,
                "has_url": random.choice([True, False]),
                "url": "https://malicious-site.com/fake-login.html" if random.choice([True, False]) else None,
                "message": "Suspected phishing email detected by content analysis",
                "timestamp": event_time.isoformat()
            },
            "Malware": {
                "type": "malware_detection",
                "source_ip": source_ip,
                "dest_ip": f"10.0.0.{random.randint(1, 254)}",
                "file_name": f"suspicious-file-{random.randint(1000, 9999)}.exe",
                "file_hash": uuid.uuid4().hex,
                "malware_type": random.choice(["trojan", "ransomware", "spyware", "adware"]),
                "detection_engine": random.choice(["AV1", "AV2", "AV3"]),
                "message": "Malware detected in file operation",
                "timestamp": event_time.isoformat()
            },
            "Command Injection": {
                "type": "web_attack",
                "source_ip": source_ip,
                "dest_ip": f"10.0.0.{random.randint(1, 254)}",
                "url": f"/search.php?q=test;cat /etc/passwd",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "http_method": "GET",
                "status_code": random.choice([200, 500]),
                "message": "Possible command injection detected in request parameters",
                "timestamp": event_time.isoformat()
            },
            "Directory Traversal": {
                "type": "web_attack",
                "source_ip": source_ip,
                "dest_ip": f"10.0.0.{random.randint(1, 254)}",
                "url": f"/download.php?file=../../../../etc/passwd",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "http_method": "GET",
                "status_code": random.choice([200, 403, 404]),
                "message": "Possible directory traversal detected in request parameters",
                "timestamp": event_time.isoformat()
            }
        }
        
        # Якщо для типу атаки не знайдено шаблон, використовуємо загальний
        return templates.get(attack_type, {
            "type": "generic_security_event",
            "source_ip": source_ip,
            "message": f"Security event detected: {attack_type}",
            "timestamp": event_time.isoformat()
        })
    
    @staticmethod
    def initialize_demo_database():
        """Ініціалізує базу даних демонстраційними даними"""
        try:
            # Завантажуємо демо-дані
            demo_data = DemoService.load_demo_data()
            
            # Перевіряємо, чи є вже демо-події в базі
            existing_count = Event.query.filter_by(siem_source='demo').count()
            
            # Якщо є демо-події, не додаємо нові
            if existing_count > 0:
                print(f"Demo database already contains {existing_count} events. Skipping initialization.")
                return
            
            # Додаємо події до бази
            for event_data in demo_data.get("events", []):
                # Створюємо подію
                event = Event(
                    event_id=event_data["event_id"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    source_ip=event_data["source_ip"],
                    severity=event_data["severity"],
                    siem_source="demo",
                    attack_type=event_data.get("attack_type"),
                    mitre_tactic=event_data.get("mitre_tactic"),
                    mitre_technique=event_data.get("mitre_technique"),
                    manual_review=event_data.get("manual_review", False),
                    true_positive=event_data.get("true_positive"),
                    manual_tags=event_data.get("manual_tags", [])
                )
                db.session.add(event)
                db.session.flush()  # Отримуємо ID події
                
                # Додаємо raw logs, якщо вони є
                for raw_log_data in event_data.get("raw_logs", []):
                    raw_log = RawLog(
                        event_id=event.id,
                        siem_source="demo",
                        raw_log=raw_log_data["raw_log"]
                    )
                    db.session.add(raw_log)
            
            db.session.commit()
            print(f"Added {len(demo_data.get('events', []))} demo events to database.")
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing demo database: {e}")

# Генеруємо демо-дані при імпорті модуля
if not os.path.exists(DEMO_DATA_FILE):
    demo_data = DemoService.generate_demo_data()
    DemoService.save_demo_data(demo_data)
