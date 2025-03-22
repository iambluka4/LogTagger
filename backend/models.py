from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    wazuh_id = db.Column(db.String(100), nullable=True)
    rule_name = db.Column(db.String(200), nullable=True)
    severity = db.Column(db.String(50), nullable=True)
    # Change timestamp from String to DateTime for consistency
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    message = db.Column(db.Text, nullable=True)
    auto_tags = db.Column(db.String(250), default="")
    
    # Add relationship to Event
    events = db.relationship('Event', backref='alert', lazy=True)

    def __repr__(self):
        return f"<Alert id={self.id} severity={self.severity}>"
    
    # Add standardized to_dict method
    def to_dict(self):
        return {
            'id': self.id,
            'wazuh_id': self.wazuh_id,
            'rule_name': self.rule_name,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'message': self.message,
            'auto_tags': self.auto_tags.split(',') if self.auto_tags else []
        }

class Label(db.Model):
    __tablename__ = 'labels'
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=False)
    detected_rule = db.Column(db.String(200), nullable=True)
    true_positive = db.Column(db.Boolean, default=False)
    event_chain_id = db.Column(db.String(100), nullable=True)
    attack_type = db.Column(db.String(100), nullable=True)
    manual_tag = db.Column(db.String(200), nullable=True)
    event_severity = db.Column(db.String(50), nullable=True)

    alert = db.relationship('Alert', backref='labels', lazy=True)

    def __repr__(self):
        return f"<Label alert_id={self.alert_id}, true_positive={self.true_positive}>"
    
    # Додаємо to_dict метод для узгодженості з іншими моделями
    def to_dict(self):
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'detected_rule': self.detected_rule,
            'true_positive': self.true_positive,
            'event_chain_id': self.event_chain_id,
            'attack_type': self.attack_type,
            'manual_tag': self.manual_tag,
            'event_severity': self.event_severity
        }

class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    wazuh_api_url = db.Column(db.String(255), nullable=True)
    wazuh_api_key = db.Column(db.String(255), nullable=True)
    splunk_api_url = db.Column(db.String(255), nullable=True)
    splunk_api_key = db.Column(db.String(255), nullable=True)
    elastic_api_url = db.Column(db.String(255), nullable=True)
    elastic_api_key = db.Column(db.String(255), nullable=True)
    ml_api_url = db.Column(db.String(255), nullable=True)
    ml_api_key = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Settings id={self.id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'wazuh_api_url': self.wazuh_api_url,
            'wazuh_api_key': '****' if self.wazuh_api_key else None,
            'splunk_api_url': self.splunk_api_url,
            'splunk_api_key': '****' if self.splunk_api_key else None,
            'elastic_api_url': self.elastic_api_url,
            'elastic_api_key': '****' if self.elastic_api_key else None,
            'ml_api_url': self.ml_api_url,
            'ml_api_key': '****' if self.ml_api_key else None
        }

class Configuration(db.Model):
    __tablename__ = 'configurations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    config_type = db.Column(db.String(50), nullable=False)
    config_value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    siem_source = db.Column(db.String(50), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'config_type': self.config_type,
            'config_value': self.config_value,
            'description': self.description,
            'is_active': self.is_active,
            'siem_source': self.siem_source
        }
    
    def update(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    # Додаємо уточнення унікальності для комбінації event_id + siem_source
    event_id = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source_ip = db.Column(db.String(50))
    severity = db.Column(db.String(50))
    siem_source = db.Column(db.String(50), nullable=False)
    # Додаємо складений унікальний індекс
    __table_args__ = (db.UniqueConstraint('event_id', 'siem_source', name='_event_id_siem_source_uc'),)
    event_chain_id = db.Column(db.String(100), nullable=True)
    labels = db.Column(JSON)
    true_positive = db.Column(db.Boolean, nullable=True)
    attack_type = db.Column(db.String(100), nullable=True)
    mitre_tactic = db.Column(db.String(100), nullable=True)
    mitre_technique = db.Column(db.String(100), nullable=True)
    detection_confidence = db.Column(db.Float, nullable=True)
    manual_review = db.Column(db.Boolean, default=False)
    manual_tags = db.Column(db.String(500), nullable=True)

    raw_logs = db.relationship('RawLog', backref='event', lazy=True)
    # Add relationship to Alert
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source_ip': self.source_ip,
            'severity': self.severity,
            'siem_source': self.siem_source,
            'event_chain_id': self.event_chain_id,
            'labels': self.labels,
            'true_positive': self.true_positive,
            'attack_type': self.attack_type,
            'mitre_tactic': self.mitre_tactic,
            'mitre_technique': self.mitre_technique,
            'detection_confidence': self.detection_confidence,
            'manual_review': self.manual_review,
            'manual_tags': self.manual_tags.split(',') if self.manual_tags else [],
            'alert_id': self.alert_id
        }

class RawLog(db.Model):
    __tablename__ = 'raw_logs'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    siem_source = db.Column(db.String(50))
    raw_log = db.Column(JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'siem_source': self.siem_source,
            'raw_log': self.raw_log
        }

class ExportJob(db.Model):
    __tablename__ = 'export_jobs'
    id = db.Column(db.Integer, primary_key=True)
    format = db.Column(db.String(20), nullable=False)  # CSV, JSON
    filters = db.Column(JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    record_count = db.Column(db.Integer, nullable=True)  # Додаємо поле для кількості записів
    
    # Додаємо to_dict метод для узгодженості з іншими моделями
    def to_dict(self):
        return {
            'id': self.id,
            'format': self.format,
            'filters': self.filters,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'file_path': self.file_path,
            'record_count': self.record_count
        }
