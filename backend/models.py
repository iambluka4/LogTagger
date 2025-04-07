from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index, func
from sqlalchemy.dialects.postgresql import JSON, JSONB, ARRAY

db = SQLAlchemy()

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    wazuh_id = db.Column(db.String(100), nullable=True)
    rule_name = db.Column(db.String(200), nullable=True)
    severity = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    message = db.Column(db.Text, nullable=True)
    auto_tags = db.Column(db.String(250), default="")
    
    # Визначаємо чітку one-to-many відносини з Event
    events = db.relationship('Event', backref='alert', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Alert {self.id}: {self.rule_name}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "wazuh_id": self.wazuh_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "message": self.message,
            "auto_tags": self.auto_tags
        }

class Settings(db.Model):
    __tablename__ = 'settings'
    # Stores API configurations
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
        return f"<Settings {self.id}>"
    
    def to_dict(self):
        return {
            "wazuh_api_url": self.wazuh_api_url,
            "wazuh_api_key": self.wazuh_api_key if self.wazuh_api_key else "",
            "splunk_api_url": self.splunk_api_url,
            "splunk_api_key": self.splunk_api_key if self.splunk_api_key else "",
            "elastic_api_url": self.elastic_api_url,
            "elastic_api_key": self.elastic_api_key if self.elastic_api_key else "",
            "ml_api_url": self.ml_api_url,
            "ml_api_key": self.ml_api_key if self.ml_api_key else ""
        }

class Configuration(db.Model):
    __tablename__ = 'configurations'
    # Stores system configuration
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    config_type = db.Column(db.String(50), nullable=False)
    config_value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    siem_source = db.Column(db.String(50), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "config_type": self.config_type,
            "config_value": self.config_value,
            "description": self.description,
            "is_active": self.is_active,
            "siem_source": self.siem_source
        }
    
    def update(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(255), nullable=False, unique=True)
    timestamp = db.Column(db.DateTime, nullable=True)
    source_ip = db.Column(db.String(100), nullable=True)
    severity = db.Column(db.String(50), nullable=True)
    siem_source = db.Column(db.String(50), nullable=True)
    manual_review = db.Column(db.Boolean, default=False)
    # Змінюємо тип з JSON на JSONB для кращої продуктивності та індексації
    labels_data = db.Column(JSONB, default={})
    
    # Додаємо зовнішній ключ
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=True)
    
    # Зв'язки
    raw_logs = db.relationship('RawLog', backref='event', lazy=True)
    
    # Додаємо індекси для часто використовуваних полів
    __table_args__ = (
        Index('ix_events_source_ip', source_ip),
        Index('ix_events_severity', severity),
        Index('ix_events_siem_source', siem_source),
        Index('ix_events_timestamp', timestamp),
        Index('ix_events_manual_review', manual_review),
        # Індекси для JSON-полів
        Index('ix_events_labels_attack_type', 
              func.jsonb_extract_path_text(labels_data, 'attack_type'),
              postgresql_using='btree'),
        Index('ix_events_labels_true_positive', 
              func.jsonb_extract_path_text(labels_data, 'true_positive'),
              postgresql_using='btree'),
        Index('ix_events_labels_mitre_tactic', 
              func.jsonb_extract_path_text(labels_data, 'mitre_tactic'),
              postgresql_using='btree'),
        Index('ix_events_labels_mitre_technique', 
              func.jsonb_extract_path_text(labels_data, 'mitre_technique'),
              postgresql_using='btree'),
    )
    
    # Властивості для сумісності з обома підходами
    @property
    def attack_type(self):
        """Отримати тип атаки з поля labels"""
        return self.labels_data.get('attack_type') if self.labels_data else None
        
    @attack_type.setter
    def attack_type(self, value):
        """Встановити тип атаки в полі labels"""
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['attack_type'] = value
    
    @property
    def true_positive(self):
        """Отримати прапорець істинно позитивного виявлення"""
        return self.labels_data.get('true_positive') if self.labels_data else None
        
    @true_positive.setter
    def true_positive(self, value):
        """Встановити прапорець істинно позитивного виявлення"""
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['true_positive'] = value
    
    @property
    def mitre_tactic(self):
        """Отримати тактику MITRE ATT&CK"""
        return self.labels_data.get('mitre_tactic') if self.labels_data else None
        
    @mitre_tactic.setter
    def mitre_tactic(self, value):
        """Встановити тактику MITRE ATT&CK"""
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['mitre_tactic'] = value
    
    @property
    def mitre_technique(self):
        """Отримати техніку MITRE ATT&CK"""
        return self.labels_data.get('mitre_technique') if self.labels_data else None
        
    @mitre_technique.setter
    def mitre_technique(self, value):
        """Встановити техніку MITRE ATT&CK"""
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['mitre_technique'] = value
    
    @property
    def manual_tags(self):
        """Отримати ручні теги"""
        return self.labels_data.get('manual_tags') if self.labels_data else None
        
    @manual_tags.setter
    def manual_tags(self, value):
        """Встановити ручні теги"""
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['manual_tags'] = value

    # Додаємо нові властивості для повного покриття полів з таблиці labels
    @property
    def detected_rule(self):
        """Отримати правило, яке виявило подію"""
        return self.labels_data.get('detected_rule') if self.labels_data else None
        
    @detected_rule.setter
    def detected_rule(self, value):
        """Встановити правило, яке виявило подію"""
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['detected_rule'] = value

    @property
    def event_chain_id(self):
        """Отримати ID ланцюжка подій"""
        return self.labels_data.get('event_chain_id') if self.labels_data else None
        
    @event_chain_id.setter
    def event_chain_id(self, value):
        """Встановити ID ланцюжка подій"""
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['event_chain_id'] = value

    @property
    def event_severity(self):
        """Отримати оцінену в мітці критичність події"""
        return self.labels_data.get('event_severity') if self.labels_data else None
        
    @event_severity.setter
    def event_severity(self, value):
        """Встановити оцінену критичність події"""
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['event_severity'] = value

    @property
    def ml_processed(self):
        """Чи була подія оброблена ML-алгоритмом"""
        return self.labels_data.get('ml_processed', False) if self.labels_data else False
        
    @ml_processed.setter
    def ml_processed(self, value):
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['ml_processed'] = bool(value)
    
    @property
    def ml_confidence(self):
        """Рівень впевненості ML-моделі"""
        return self.labels_data.get('ml_confidence', 0.0) if self.labels_data else 0.0
        
    @ml_confidence.setter
    def ml_confidence(self, value):
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['ml_confidence'] = float(value)
    
    @property
    def ml_timestamp(self):
        """Час останньої ML-класифікації"""
        return self.labels_data.get('ml_timestamp') if self.labels_data else None
        
    @ml_timestamp.setter
    def ml_timestamp(self, value):
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['ml_timestamp'] = value
    
    @property
    def human_verified(self):
        """Чи була ML-класифікація перевірена людиною"""
        return self.labels_data.get('human_verified', False) if self.labels_data else False
        
    @human_verified.setter
    def human_verified(self, value):
        if not self.labels_data:
            self.labels_data = {}
        self.labels_data['human_verified'] = bool(value)

    def get_label_value(self, key, default=None):
        """
        Безпечно отримати значення з labels_data
        
        Args:
            key: Ключ
            default: Значення за замовчуванням
            
        Returns:
            Значення або default
        """
        if not self.labels_data:
            return default
        return self.labels_data.get(key, default)
    
    def set_label_value(self, key, value):
        """
        Безпечно встановити значення в labels_data
        
        Args:
            key: Ключ
            value: Значення
        """
        if self.labels_data is None:
            self.labels_data = {}
        self.labels_data[key] = value

    def to_dict(self):
        """Серіалізація об'єкта в словник"""
        result = {
            "id": self.id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_ip": self.source_ip,
            "severity": self.severity,
            "siem_source": self.siem_source,
            "manual_review": self.manual_review,
            "labels": self.labels_data,
            "attack_type": self.attack_type,
            "true_positive": self.true_positive,
            "mitre_tactic": self.mitre_tactic,
            "mitre_technique": self.mitre_technique,
            "manual_tags": self.manual_tags,
            "detected_rule": self.detected_rule,
            "event_chain_id": self.event_chain_id,
            "event_severity": self.event_severity,
            "has_raw_logs": bool(self.raw_logs),
            "ml_processed": self.ml_processed,
            "ml_confidence": self.ml_confidence,
            "ml_timestamp": self.ml_timestamp,
            "human_verified": self.human_verified
        }
        return result

class RawLog(db.Model):
    __tablename__ = 'raw_logs'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    siem_source = db.Column(db.String(50))
    raw_log = db.Column(JSON)
    
    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "siem_source": self.siem_source,
            "raw_log": self.raw_log
        }

class ExportJob(db.Model):
    __tablename__ = 'export_jobs'
    id = db.Column(db.Integer, primary_key=True)
    format = db.Column(db.String(20), default="csv")  # csv, json, etc.
    filters = db.Column(JSON, nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    record_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "format": self.format,
            "filters": self.filters,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "file_path": self.file_path,
            "record_count": self.record_count
        }

# Нова модель для зберігання метрик продуктивності ML
class MLPerformanceMetrics(db.Model):
    __tablename__ = 'ml_performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    model_version = db.Column(db.String(100), nullable=True)
    
    # Метрики класифікації
    true_positives = db.Column(db.Integer, default=0)
    false_positives = db.Column(db.Integer, default=0)
    true_negatives = db.Column(db.Integer, default=0)
    false_negatives = db.Column(db.Integer, default=0)
    
    # Розраховані метрики
    precision = db.Column(db.Float, default=0.0)
    recall = db.Column(db.Float, default=0.0)
    f1_score = db.Column(db.Float, default=0.0)
    
    # Метрики по класам
    class_metrics = db.Column(JSON, default={})
    
    def calculate_metrics(self):
        """Розрахувати precision, recall, f1_score на основі TP, FP, TN, FN"""
        tp, fp, tn, fn = self.true_positives, self.false_positives, self.true_negatives, self.false_negatives
        
        # Уникаємо ділення на нуль
        self.precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        self.recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        else:
            self.f1_score = 0
            
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "model_version": self.model_version,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "class_metrics": self.class_metrics
        }

class LabelRevision(db.Model):
    __tablename__ = 'label_revisions'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.String(100), nullable=True)  # ID користувача, який зробив зміни
    action = db.Column(db.String(20), nullable=False)  # 'create', 'update', 'verify', 'reject'
    label_key = db.Column(db.String(100), nullable=False)  # Ключ мітки, яка змінилася
    old_value = db.Column(db.JSON, nullable=True)  # Попереднє значення (якщо було)
    new_value = db.Column(db.JSON, nullable=True)  # Нове значення
    source = db.Column(db.String(20), nullable=False)  # 'manual', 'ml', 'rule'
    
    event = db.relationship('Event', backref=db.backref('label_revisions', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'action': self.action,
            'label_key': self.label_key,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'source': self.source
        }
