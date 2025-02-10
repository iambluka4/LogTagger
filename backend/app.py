from flask import Flask
from flask_cors import CORS
from config import get_config
from models import db
from routes.api_config_routes import api_config_bp
from routes.data_labeling_routes import data_labeling_bp
from routes.users_routes import users_bp

def create_app(env_name='development'):
    app = Flask(__name__)
    app.config.from_object(get_config(env_name))
    db.init_app(app)
    CORS(app)

    # Реєстрація blueprint-ів
    app.register_blueprint(api_config_bp)
    app.register_blueprint(data_labeling_bp)
    app.register_blueprint(users_bp)

    # Ініціалізація БД (створення таблиць, якщо їх немає)
    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app('development')
    app.run(host="0.0.0.0", port=5000, debug=True)
