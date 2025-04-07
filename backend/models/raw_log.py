from sqlalchemy.dialects.postgresql import JSON as PostgresJSON
from models import db

class RawLog(db.Model):
    __tablename__ = 'raw_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    log_data = db.Column(PostgresJSON, nullable=False)
    source = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)
