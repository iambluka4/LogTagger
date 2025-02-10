from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    # Пароль, роль користувача тощо можна додати
    # password = db.Column(db.String(128), nullable=False)
    # role = db.Column(db.String(50), default="analyst")

    def __repr__(self):
        return f"<User {self.username}>"

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)        # Внутрішній ID
    wazuh_id = db.Column(db.String(100), nullable=True) # ID із SIEM (наприклад)
    rule_name = db.Column(db.String(200), nullable=True)
    severity = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Alert {self.rule_name}, severity={self.severity}>"

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

    # Зв'язок з Alert
    alert = db.relationship('Alert', backref='labels', lazy=True)

    def __repr__(self):
        return f"<Label alert_id={self.alert_id}, true_positive={self.true_positive}>"

class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    wazuh_api_url = db.Column(db.String(255), nullable=True)
    wazuh_api_key = db.Column(db.String(255), nullable=True)
    # Додаткові поля: freq, інші SIEM, etc.

    def __repr__(self):
        return f"<Settings id={self.id}>"
