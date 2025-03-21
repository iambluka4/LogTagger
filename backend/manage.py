#!/usr/bin/env python3
"""
Утиліта для керування базою даних, міграціями та запуском застосунку (MVP версія без аутентифікації).
"""
import click
import os
import sys
import logging
from flask import Flask
from sqlalchemy import text
from config import get_config
from app import create_app
from models import db

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('manage')

@click.group()
def cli():
    """Утиліта для керування LogTagger."""
    pass

@cli.command('db-init')
@click.option('--mode', default='development', help='Mode: development, production, testing')
def db_init(mode):
    """Ініціалізація бази даних - створення схеми та базових даних."""
    app = create_app(mode)
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()
        logger.info("Database initialized successfully")

@cli.command('migrate')
@click.option('--mode', default='development', help='Mode: development, production, testing')
def migrate(mode):
    """Застосувати міграції до бази даних."""
    app = create_app(mode)
    with app.app_context():
        try:
            # Виконуємо всі міграції
            logger.info("Running apply_all_migrations.py...")
            from migrations.apply_all_migrations import apply_all_migrations
            apply_all_migrations()
            logger.info("Migrations completed successfully")
        except Exception as e:
            logger.error(f"Migration error: {str(e)}", exc_info=True)
            sys.exit(1)

@cli.command('check-db')
@click.option('--mode', default='development', help='Mode: development, production, testing')
def check_db(mode):
    """Перевірити стан бази даних."""
    app = create_app(mode)
    with app.app_context():
        try:
            from tools.check_models import check_models_vs_tables
            check_models_vs_tables(app)
        except Exception as e:
            logger.error(f"Error checking database: {str(e)}")
            sys.exit(1)

@cli.command('runserver')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, type=int, help='Port to bind to')
@click.option('--mode', default='development', help='Mode: development, production, testing')
def runserver(host, port, mode):
    """Запустити сервер Flask."""
    app = create_app(mode)
    app.run(host=host, port=port, debug=mode=='development')

@cli.command('check-env')
def check_env():
    """Перевірити середовище виконання."""
    import sys
    import os
    
    try:
        # Перевірка версії Python
        print(f"Python: {sys.version}")
        
        # Перевірка виконання у venv
        in_venv = sys.prefix != sys.base_prefix
        print(f"In venv: {'✓' if in_venv else '✗'}")
        
        # Перевірка наявності ключових бібліотек
        for lib in ['flask', 'sqlalchemy', 'psycopg2', 'click']:
            try:
                __import__(lib)
                status = "✓"
            except ImportError:
                status = "✗"
            print(f"{lib}: {status}")
        
        # Перевірка підключення до PostgreSQL
        app = create_app('development')
        with app.app_context():
            try:
                db.engine.connect()
                print("Database connection: ✓")
            except Exception as e:
                print(f"Database connection: ✗ ({str(e)})")
    except Exception as e:
        print(f"Error during environment check: {str(e)}")

if __name__ == '__main__':
    cli()
