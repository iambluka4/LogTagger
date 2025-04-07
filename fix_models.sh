#!/bin/bash

# Fix the syntax error in alert.py
cat > /mnt/d/MVP_2/LogTagger/backend/models/alert.py << 'EOF'
from datetime import datetime
from sqlalchemy.sql import func
from models import db

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(255), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=func.now(), index=True)
    rule_name = db.Column(db.String(255), nullable=True)
    severity = db.Column(db.String(20), nullable=True)
    source = db.Column(db.String(100), nullable=True)
    
    # Relationships
    events = db.relationship('Event', backref='alert', lazy=True)
EOF

# Fix deploy.sh to use primary_key=True in all model files for future executions
sed -i 's/primary key=True/primary_key=True/g' /mnt/d/MVP_2/LogTagger/deploy.sh

echo "Fixed alert.py and updated deploy.sh"
