from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import get_config
from models import db, User, Alert, Label, Settings, Configuration, Event, RawLog, ExportJob
from routes.api_config_routes import api_config_bp
from routes.data_labeling_routes import data_labeling_bp
from routes.users_routes import users_bp
from routes.auth_routes import auth_bp
from routes.events_routes import events_bp
from routes.configuration_routes import configuration_bp
from routes.dashboard_routes import dashboard_bp
from services.auth import create_admin_if_not_exists
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
    
    # Setup JWT
    jwt = JWTManager(app)
    
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
    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(configuration_bp)
    app.register_blueprint(dashboard_bp)

    # Create exports directory if it doesn't exist
    exports_dir = app.config.get('EXPORT_DIR', 'exports')
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)

    # Initialize database
    with app.app_context():
        # Check if we need to add the password column to users table
        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            columns = [column['name'] for column in inspector.get_columns('users')]
            if 'password' not in columns:
                # If table exists but password column doesn't, add it
                from sqlalchemy import text
                db.session.execute(text('ALTER TABLE users ADD COLUMN password VARCHAR(255)'))
                db.session.commit()
                app.logger.info("Added missing 'password' column to users table")
        else:
            # Create tables if they don't exist
            db.create_all()
            app.logger.info("Created database tables")

        # Create default admin user if needed
        try:
            create_admin_if_not_exists()
        except Exception as e:
            app.logger.error(f"Error creating admin user: {e}")
            # Continue app initialization even if admin creation fails

    # Root route
    @app.route('/')
    def index():
        return jsonify({"message": "LogTagger API", "version": "1.0.0"})

    return app

if __name__ == "__main__":
    app = create_app('development')
    app.run(host="0.0.0.0", port=5000, debug=True)
