from sqlalchemy.dialects.postgresql import JSON as PostgresJSON
from datetime import datetime
from models import db

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(255), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    source_ip = db.Column(db.String(45))
    severity = db.Column(db.String(20))
    siem_source = db.Column(db.String(50))
    manual_review = db.Column(db.Boolean, default=False)
    labels_data = db.Column(PostgresJSON, default={}, nullable=False)
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=True)
    
    # Additional fields 
    attack_type = db.Column(db.String(100), nullable=True)
    mitre_tactic = db.Column(db.String(100), nullable=True)
    mitre_technique = db.Column(db.String(100), nullable=True)
    
    # Relationships
    raw_logs = db.relationship('RawLog', backref='event', lazy=True)
    
    @property
    def labels(self):
        return self.labels_data if self.labels_data else {}
    
    @labels.setter
    def labels(self, value):
        self.labels_data = value
