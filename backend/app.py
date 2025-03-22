from flask import Flask, jsonify
from flask_cors import CORS
from config import get_config
from models import db, Alert, Label, Settings, Configuration, Event, RawLog, ExportJob
# Імпортуємо тільки потрібні маршрути
from routes.api_config_routes import api_config_bp
from routes.data_labeling_routes import data_labeling_bp
from routes.events_routes import events_bp
from routes.configuration_routes import configuration_bp
from routes.dashboard_routes import dashboard_bp
import logging
import os
from sqlalchemy import inspect
import time

def validate_db_connection(app, retries=3, delay=5):
    """Validate database connection with retries"""
    with app.app_context():
        for attempt in range(retries):
            try:
                # Try to connect to the database
                db.engine.connect()
                logging.info("Database connection established successfully!")
                return True
            except Exception as e:
                logging.error(f"Database connection failed (attempt {attempt+1}/{retries}): {str(e)}")
                if attempt < retries - 1:
                    logging.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logging.error("Max retries reached. Could not connect to database!")
                    return False

def create_app(env_name='development'):
    app = Flask(__name__)
    app.config.from_object(get_config(env_name))
    
    # Setup database
    db.init_app(app)
    
    # Setup CORS
    CORS(app)
    
    # Setup logging
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logging.basicConfig(
        filename=os.path.join('logs', app.config['LOG_FILE']),
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register routes
    app.register_blueprint(api_config_bp)
    app.register_blueprint(data_labeling_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(configuration_bp)
    app.register_blueprint(dashboard_bp)

    # Create exports directory if it doesn't exist
    exports_dir = app.config.get('EXPORT_DIR', 'exports')
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)

    # Перевірка з'єднання з базою даних
    with app.app_context():
        try:
            # Просто перевіряємо з'єднання з базою даних
            db.engine.connect()
            app.logger.info("Connected to database successfully")
        except Exception as e:
            app.logger.error(f"Database connection error: {str(e)}")
            app.logger.error("Please check database configuration and connection")

    # After db initialization, validate the connection
    validate_db_connection(app, 
                         retries=app.config.get('DATABASE_RETRY_LIMIT', 3),
                         delay=app.config.get('DATABASE_RETRY_DELAY', 5))

    # Root route
    @app.route('/')
    def index():
        return jsonify({"message": "LogTagger API", "version": "1.0.0 (MVP)"})

    return app

if __name__ == "__main__":
    app = create_app('development')
    app.run(host="0.0.0.0", port=5000, debug=True)
