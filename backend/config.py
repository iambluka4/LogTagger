import os
from datetime import timedelta

class Config:
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'my-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    WAZUH_API_REFRESH = int(os.getenv('WAZUH_API_REFRESH', '300'))  # seconds
    EXPORT_DIR = os.getenv('EXPORT_DIR', 'exports')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logtagger.log')
    DATABASE_RETRY_LIMIT = 3
    DATABASE_RETRY_DELAY = 5  # seconds

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "postgresql://logtagger:logtagger@localhost:5432/logtagger"
    LOG_LEVEL = "DEBUG"
    JWT_COOKIE_SECURE = False

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "postgresql://logtagger:logtagger@localhost:5432/logtagger"
    JWT_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or "postgresql://logtagger:logtagger@localhost:5432/logtagger_test"

def get_config(env_name):
    if env_name == 'production':
        return ProductionConfig
    elif env_name == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig
