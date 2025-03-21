import os
from datetime import timedelta

class Config:
    # Наприклад, якщо PostgreSQL запущено локально:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://myuser:mypassword@localhost:5432/mydb') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'my-secret-key')
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # SIEM Integration settings
    WAZUH_API_REFRESH = int(os.getenv('WAZUH_API_REFRESH', '300'))  # seconds
    
    # Export settings
    EXPORT_DIR = os.getenv('EXPORT_DIR', 'exports')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logtagger.log')

class DevelopmentConfig(Config):
    DEBUG = True
    JWT_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    JWT_COOKIE_SECURE = True

def get_config(env_name='development'):
    if env_name == 'production':
        return ProductionConfig
    return DevelopmentConfig
