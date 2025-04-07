import logging
from app import create_app, db
from models.alert import Alert
from models.event import Event
from models.user import User
# Імпортуйте інші моделі за необхідності

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Ініціалізує базу даних"""
    logger.info("Initializing database...")
    try:
        # Створення всіх таблиць
        db.create_all()
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

def reset_db():
    """Видаляє і повторно створює всі таблиці (обережно - всі дані будуть втрачені)"""
    logger.warning("Resetting database - ALL DATA WILL BE LOST!")
    try:
        db.drop_all()
        db.create_all()
        logger.info("Database reset successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reset database: {str(e)}")
        return False

def seed_db():
    """Наповнює базу даних початковими даними"""
    logger.info("Seeding database with initial data...")
    try:
        # Приклад створення адміністратора
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin"
        )
        admin.set_password("change_me_immediately")
        db.session.add(admin)
        db.session.commit()
        logger.info("Database seeded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to seed database: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Ініціалізація бази даних
        init_db()
        
        # Розкоментуйте наступний рядок, якщо потрібно наповнити базу початковими даними
        # seed_db()
