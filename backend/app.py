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

    # Root route
    @app.route('/')
    def index():
        return jsonify({"message": "LogTagger API", "version": "1.0.0 (MVP)"})

    return app

if __name__ == "__main__":
    app = create_app('development')
    app.run(host="0.0.0.0", port=5000, debug=True)
