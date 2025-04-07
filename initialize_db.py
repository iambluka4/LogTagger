import sys
import os

# Додаємо шлях до модуля backend до sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import argparse
import logging
from app import create_app
from db_init import init_db, reset_db, seed_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="LogTagger database initialization utility")
    parser.add_argument("--init", action="store_true", help="Initialize the database")
    parser.add_argument("--reset", action="store_true", help="Reset the database (warning: deletes all data)")
    parser.add_argument("--seed", action="store_true", help="Seed the database with initial data")
    
    args = parser.parse_args()
    
    app = create_app()
    
    with app.app_context():
        if args.reset:
            reset_db()
        elif args.init:
            init_db()
        
        if args.seed:
            seed_db()
    
    logger.info("Database setup completed successfully")

if __name__ == "__main__":
    main()
