from models import db

class ExportJob(db.Model):
    __tablename__ = 'export_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    format = db.Column(db.String(10), nullable=False)  # csv, json, etc.
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=db.func.now())
    completed_at = db.Column(db.DateTime, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    record_count = db.Column(db.Integer, nullable=True)
    filters = db.Column(db.JSON, default={})
    message = db.Column(db.Text, nullable=True)  # For error messages
