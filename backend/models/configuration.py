from sqlalchemy.dialects.postgresql import JSON as PostgresJSON
from models import db

class Configuration(db.Model):
    __tablename__ = 'configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    config_data = db.Column(PostgresJSON, default={})
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
