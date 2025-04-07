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
