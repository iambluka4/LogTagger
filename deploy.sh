#!/bin/bash

set -e  # Stop script if an error occurs

#######################
#    UTILITIES        #
#######################
# Function for logging messages
log_message() {
    echo ">>> $1"
}

# Function for error handling
handle_error() {
    echo "ERROR: $1"
    exit 1
}

# Check if directory exists
check_directory() {
    if [ ! -d "$1" ]; then
        handle_error "Directory $1 does not exist!"
    fi
}

# Function to clean temporary files
cleanup() {
    log_message "Cleaning temporary files..."
    find "$BACKEND_DIR" -name "*.pyc" -delete
    find "$BACKEND_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
}

#######################
#    VARIABLES        #
#######################
DB_NAME="logtagger"
DB_USER="logtagger"
DB_PASSWORD="logtagger"  # Use a more secure password in production

# Directory paths
PROJECT_DIR="/mnt/d/MVP_2/LogTagger"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_DIR="$PROJECT_DIR/backend"
MODE=${1:-development}

# Set execution permissions for scripts
for script in "$PROJECT_DIR"/{clean_deploy.sh,deploy.sh,run.sh,backend/manage.py}; do
    chmod +x "$script" 2>/dev/null || true
done

# Check required directories
check_directory "$BACKEND_DIR"

#######################
# 1. SYSTEM UPDATE    #
#######################
log_message "Updating system..."
sudo apt-get update
sudo apt-get -y upgrade

###########################
# 2. INSTALLING DEPENDENCIES #
###########################
log_message "Installing required packages..."
sudo apt-get install -y python3 python3-venv python3-pip build-essential \
    git curl ca-certificates postgresql postgresql-contrib libpq-dev python3-dev

#######################
# 3. INSTALLING NODE.JS #
#######################
log_message "Installing Node.js version 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Check Node.js version
node_version=$(node -v)
log_message "Installed Node.js version: $node_version"
if [[ ! $node_version == v20* ]]; then
    echo "WARNING: Installed Node.js version ($node_version) is not version 20.x"
    echo "This may cause issues with frontend dependencies"
fi

#######################
# 4. POSTGRESQL SETUP #
#######################
log_message "Setting up PostgreSQL..."
# Start and configure PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create user and database
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
fi

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
fi

sudo -u postgres psql -c "ALTER ROLE $DB_USER SUPERUSER;"

# Access configuration
sudo sed -i "s/^#listen_addresses.*/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
sudo bash -c "echo \"host all all 0.0.0.0/0 md5\" >> /etc/postgresql/*/main/pg_hba.conf"
sudo systemctl restart postgresql

#######################
# 5. BACKEND SETUP    #
#######################
log_message "Setting up Backend..."
cd "$BACKEND_DIR" || handle_error "Cannot change to directory $BACKEND_DIR"

# Create virtual environment
if [ -d "venv" ]; then
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate

# Install dependencies
log_message "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Extended dependency list
pip install sqlalchemy==1.4.46 Werkzeug==2.2.2 Flask==2.2.2 \
    flask-sqlalchemy==3.0.3 Flask-Cors==3.0.10 psycopg2-binary \
    tabulate requests python-dateutil pandas pyyaml \
    alembic flask-migrate flask-script jsonschema sqlalchemy-json

# Create configuration if needed
CONFIG_FILE="$BACKEND_DIR/config.py"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << EOF
class Config:
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_FILE = "app.log"
    LOG_LEVEL = "INFO"
    EXPORT_DIR = "exports"

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/${DB_NAME}_test"

def get_config(env_name):
    if env_name == 'production':
        return ProductionConfig
    elif env_name == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig
EOF
    log_message "Created configuration file"
fi

# Set environment variables
export FLASK_APP="$BACKEND_DIR/app.py"
export FLASK_DEBUG=$([[ "$MODE" == "development" ]] && echo 1 || echo 0)

# Create required directories
mkdir -p "$BACKEND_DIR/logs" "$BACKEND_DIR/exports"

# Create routes directory and its files
mkdir -p "$BACKEND_DIR/routes"

# Create routes/__init__.py
cat > "$BACKEND_DIR/routes/__init__.py" << 'EOF'
# Routes package initialization
EOF
echo ">>> Created routes/__init__.py"

# Create routes/auth.py (temporary file to satisfy imports)
cat > "$BACKEND_DIR/routes/auth.py" << 'EOF'
from flask import Blueprint

# This is a temporary placeholder file
# Auth functionality will be implemented later
auth_bp = Blueprint('auth', __name__)
EOF
echo ">>> Created temporary routes/auth.py"

# Create routes/events_routes.py
cat > "$BACKEND_DIR/routes/events_routes.py" << 'EOF'
from flask import Blueprint, jsonify, request, current_app
from models import db, Event, RawLog
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

events_bp = Blueprint('events', __name__)

@events_bp.route('/api/events', methods=['GET'])
def get_events():
    try:
        # Basic pagination logic
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        
        # Query with basic filters
        query = Event.query
        
        # Apply pagination
        pagination = query.paginate(page=page, per_page=page_size)
        events = pagination.items
        
        # Format response
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "source_ip": event.source_ip,
                "severity": event.severity,
                "siem_source": event.siem_source,
                "manual_review": event.manual_review,
                "labels": event.labels
            })
        
        response = {
            "events": events_data,
            "page": page,
            "page_size": page_size,
            "total_count": pagination.total,
            "total_pages": pagination.pages
        }
        
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Error in get_events: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
EOF
echo ">>> Created routes/events_routes.py"

# Create routes/config_routes.py
cat > "$BACKEND_DIR/routes/config_routes.py" << 'EOF'
from flask import Blueprint, jsonify, request, current_app
from models import db, Configuration
from sqlalchemy.exc import SQLAlchemyError

config_bp = Blueprint('config', __name__)

@config_bp.route('/api/system-config', methods=['GET'])
def get_system_config():
    try:
        config = Configuration.query.filter_by(name='system').first()
        
        if not config:
            return jsonify({"config": {}}), 200
            
        return jsonify({"config": config.config_data})
    except Exception as e:
        current_app.logger.error(f"Error in get_system_config: {str(e)}")
        return jsonify({"message": "Error retrieving configuration", "detail": str(e)}), 500

@config_bp.route('/api/system-config', methods=['POST'])
def update_system_config():
    try:
        data = request.get_json()
        
        config = Configuration.query.filter_by(name='system').first()
        
        if not config:
            config = Configuration(name='system', config_data={})
            db.session.add(config)
        
        # Update the configuration
        config.config_data = data
        
        db.session.commit()
        
        return jsonify({"message": "Configuration updated successfully"})
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_system_config: {str(e)}")
        return jsonify({"message": "Database error", "detail": str(e)}), 500
    except Exception as e:
        current_app.logger.error(f"Error in update_system_config: {str(e)}")
        return jsonify({"message": "Error updating configuration", "detail": str(e)}), 500
EOF
echo ">>> Created routes/config_routes.py"

# Backup and replace existing app.py to ensure compatibility
if [ -f "$BACKEND_DIR/app.py" ]; then
    cp "$BACKEND_DIR/app.py" "$BACKEND_DIR/app.py.bak"
    echo ">>> Backed up existing app.py to app.py.bak"
fi

# Create new app.py with correct imports
cat > "$BACKEND_DIR/app.py" << 'EOF'
from flask import Flask
from flask_cors import CORS
from models import db
from config import get_config
import logging
import os

def create_app(env_name='development'):
    """Application factory function"""
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(env_name)
    app.config.from_object(config)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(app.config.get('LOG_FILE', 'app.log')),
            logging.StreamHandler()
        ]
    )
    
    # Enable CORS
    CORS(app)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    from routes.events_routes import events_bp
    from routes.config_routes import config_bp
    from routes.auth import auth_bp
    
    app.register_blueprint(events_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(auth_bp)
    
    return app
EOF
echo ">>> Created app.py with correct imports"

# Ensure models directory exists
mkdir -p models

# Ensure models directory exists
mkdir -p models

# Create __init__.py file with proper imports
cat > models/__init__.py << 'EOF'
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy object
db = SQLAlchemy()

# Note: We will import model classes after they're created
EOF
echo ">>> Created file models/__init__.py"

# Create models/event.py
cat > models/event.py << 'EOF'
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
EOF
echo ">>> Created file models/event.py"

# Create models/alert.py
cat > models/alert.py << 'EOF'
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
echo ">>> Created file models/alert.py"

# Create models/raw_log.py
cat > models/raw_log.py << 'EOF'
from sqlalchemy.dialects.postgresql import JSON as PostgresJSON
from models import db

class RawLog(db.Model):
    __tablename__ = 'raw_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    log_data = db.Column(PostgresJSON, nullable=False)
    source = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)
EOF
echo ">>> Created file models/raw_log.py"

# Create models/user.py
cat > models/user.py << 'EOF'
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
EOF
echo ">>> Created file models/user.py"

# Create models/settings.py
cat > models/settings.py << 'EOF'
from models import db

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
EOF
echo ">>> Created file models/settings.py"

# Create models/configuration.py
cat > models/configuration.py << 'EOF'
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
EOF
echo ">>> Created file models/configuration.py"

# Create models/export_job.py
cat > models/export_job.py << 'EOF'
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
EOF
echo ">>> Created file models/export_job.py"

# Create models/ml.py (if it doesn't exist already)
# Create models/ml.py file using heredoc
if [ ! -f models/ml.py ]; then
    cat > models/ml.py << 'EOF'
from models import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from datetime import datetime

class MLPerformanceMetrics(db.Model):
    """Model for storing ML classification performance metrics"""
    
    __tablename__ = 'ml_performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    model_version = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())
    
    # Base metrics
    true_positives = db.Column(db.Integer, default=0)
    false_positives = db.Column(db.Integer, default=0)
    true_negatives = db.Column(db.Integer, default=0)
    false_negatives = db.Column(db.Integer, default=0)
    
    # Calculated metrics
    accuracy = db.Column(db.Float, default=0.0)
    precision = db.Column(db.Float, default=0.0)
    recall = db.Column(db.Float, default=0.0)
    f1_score = db.Column(db.Float, default=0.0)
    
    # Class metrics
    class_metrics = db.Column(JSON, default={})
    
    def calculate_metrics(self):
        """Calculate metrics based on base values"""
        # Total examples
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        
        # Avoid division by zero
        if total == 0:
            return
            
        # Accuracy (number of correct predictions to total)
        self.accuracy = (self.true_positives + self.true_negatives) / total
        
        # Precision (number of correct positive predictions to all positive predictions)
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        
        # Recall (number of correct positive predictions to all actual positive examples)
        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        
        # F1 Score (harmonic mean of precision and recall)
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    def to_dict(self):
        """Convert object to dictionary for API"""
        return {
            'id': self.id,
            'model_version': self.model_version,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'true_negatives': self.true_negatives,
            'false_negatives': self.false_negatives,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'class_metrics': self.class_metrics
        }
EOF
    echo ">>> Created file models/ml.py"
fi

# Now update __init__.py with the imports
cat > models/__init__.py << 'EOF'
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy object
db = SQLAlchemy()

# Import all models - after they have been created
from .event import Event
from .alert import Alert
from .raw_log import RawLog
from .user import User
from .settings import Settings
from .configuration import Configuration 
from .export_job import ExportJob
from .ml import MLPerformanceMetrics
EOF
echo ">>> Updated models/__init__.py with all imports"

# Apply migrations with modified error handling
log_message "Initializing database..."

# Check which command format is supported
if python manage.py --help | grep -q "db-init"; then
    python manage.py db-init --mode $MODE || handle_error "Failed to initialize database"
elif python manage.py --help | grep -q "db init"; then
    python manage.py db init --mode $MODE || handle_error "Failed to initialize database"
else
    handle_error "Unknown database initialization command"
fi

# Check and run migrations
if [ -d "$BACKEND_DIR/migrations/versions" ]; then
    log_message "Updating database with migrations..."
    
    # Check which upgrade command format is supported
    if python manage.py --help | grep -q "db-upgrade"; then
        python manage.py db-upgrade --mode $MODE || log_message "Warning: database upgrade returned an error, but continuing"
    elif python manage.py --help | grep -q "db upgrade"; then
        python manage.py db upgrade --mode $MODE || log_message "Warning: database upgrade returned an error, but continuing"
    fi
else
    log_message "Migration versions directory not found. Creating initial migration..."
    
    # Check which migrate command format is supported
    if python manage.py --help | grep -q "db-migrate"; then
        python manage.py db-migrate -m "Initial migration" || log_message "Warning: migration creation returned an error, but continuing"
        python manage.py db-upgrade --mode $MODE || log_message "Warning: database upgrade returned an error, but continuing"
    elif python manage.py --help | grep -q "db migrate"; then
        python manage.py db migrate -m "Initial migration" || log_message "Warning: migration creation returned an error, but continuing" 
        python manage.py db upgrade --mode $MODE || log_message "Warning: database upgrade returned an error, but continuing"
    fi
fi

# Install package in development mode
cd "$PROJECT_DIR" || handle_error "Cannot change to directory $PROJECT_DIR"

# Check if setup.py exists before installing package
if [ -f "setup.py" ]; then
    log_message "Installing package in development mode..."
    pip install -e .
else
    log_message "setup.py file not found, skipping package installation in development mode"
fi

cd "$BACKEND_DIR" || handle_error "Cannot change to directory $BACKEND_DIR"

#######################
# 6. FRONTEND SETUP   #
#######################
if [ -d "$FRONTEND_DIR" ]; then
    log_message "Setting up Frontend..."
    cd "$FRONTEND_DIR" || handle_error "Cannot change to directory $FRONTEND_DIR"
    
    npm install
    
    if [ "$MODE" == "production" ]; then
        # Production mode - build static version and configure Nginx
        log_message "Building production frontend version..."
        npm run build
        sudo apt install -y nginx
        
        # Nginx configuration
        sudo bash -c "cat > /etc/nginx/sites-available/logtagger << EOF
server {
    listen 80;
    root $FRONTEND_DIR/build;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF"
        sudo ln -sf /etc/nginx/sites-available/logtagger /etc/nginx/sites-enabled/
        sudo nginx -t && sudo systemctl restart nginx
    else
        # Development mode - add proxy to package.json
        if ! grep -q '"proxy":' package.json; then
            sed -i '$ s/}$/,\n  "proxy": "http:\/\/localhost:5000"\n}/' package.json
            log_message "Added proxy to package.json"
        fi
    fi
else
    log_message "Frontend directory not found. Skipping frontend setup."
fi

#######################
# 7. START SERVICES   #
#######################
if [ "$MODE" == "production" ]; then
    # Production server setup
    pip install gunicorn
    
    # Create systemd service
    sudo bash -c "cat > /etc/systemd/system/logtagger-backend.service << EOF
[Unit]
Description=LogTagger Backend Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment=FLASK_DEBUG=0
ExecStart=$BACKEND_DIR/venv/bin/gunicorn -b 0.0.0.0:5000 -w 4 app:create_app('production')
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

    sudo systemctl daemon-reload
    sudo systemctl enable logtagger-backend
    sudo systemctl restart logtagger-backend
    
    log_message "Services started in production mode"
    log_message "Backend running through systemd, frontend through Nginx"
else
    # Development server startup
    cd "$BACKEND_DIR" || handle_error "Cannot change to directory $BACKEND_DIR"
    source venv/bin/activate
    log_message "Starting server in development mode..."

    # Check which method is supported for running the server
    if python manage.py --help | grep -q "runserver"; then
        python manage.py runserver --mode $MODE || handle_error "Error starting server"
    elif [ -f "$BACKEND_DIR/app.py" ]; then
        # Alternative method using Flask CLI
        export FLASK_APP=app.py
        export FLASK_ENV=development
        flask run --host=0.0.0.0
    else
        handle_error "Could not find a way to start the development server"
    fi
fi

# Setup cleanup on exit
trap cleanup EXIT

log_message "Done! LogTagger MVP successfully installed."