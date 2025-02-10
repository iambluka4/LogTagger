import os

class Config:
    # Наприклад, якщо PostgreSQL запущено локально:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://myuser:mypassword@localhost:5432/mydb') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'my-secret-key')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

def get_config(env_name='development'):
    if env_name == 'production':
        return ProductionConfig
    return DevelopmentConfig
