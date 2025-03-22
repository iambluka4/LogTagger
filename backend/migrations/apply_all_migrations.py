from models import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def apply_all_migrations():
    """
    Apply all necessary migrations to the database.
    This function is called during the 'migrate' command execution.
    """
    try:
        # Перевірка і міграції для Event моделі
        if not column_exists('events', 'alert_id'):
            logger.info("Adding alert_id column to events table")
            db.engine.execute(text(
                "ALTER TABLE events ADD COLUMN alert_id INTEGER REFERENCES alerts(id)"
            ))
        
        # Додавання composite unique constraint для event_id та siem_source, якщо його ще немає
        if not constraint_exists('events', '_event_id_siem_source_uc'):
            logger.info("Adding unique constraint for event_id and siem_source")
            try:
                # Спочатку видаляємо unique constraint у event_id, якщо він існує
                db.engine.execute(text(
                    "ALTER TABLE events DROP CONSTRAINT IF EXISTS events_event_id_key"
                ))
                # Далі додаємо комбінований унікальний індекс
                db.engine.execute(text(
                    "ALTER TABLE events ADD CONSTRAINT _event_id_siem_source_uc UNIQUE (event_id, siem_source)"
                ))
            except Exception as e:
                logger.error(f"Error adding constraint: {str(e)}")
        
        # Перевірка і міграції для Alert моделі
        if column_type_is('alerts', 'timestamp', 'character varying'):
            logger.info("Converting alerts.timestamp from VARCHAR to TIMESTAMP")
            # 1. Додаємо нову колонку з правильним типом
            db.engine.execute(text("ALTER TABLE alerts ADD COLUMN temp_timestamp TIMESTAMP"))
            # 2. Конвертуємо дані
            db.engine.execute(text("""
                UPDATE alerts SET temp_timestamp = 
                CASE 
                    WHEN timestamp ~ E'^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}' THEN timestamp::timestamp 
                    WHEN timestamp IS NULL THEN NULL 
                    ELSE now() 
                END
            """))
            # 3. Видаляємо стару колонку
            db.engine.execute(text("ALTER TABLE alerts DROP COLUMN timestamp"))
            # 4. Перейменовуємо нову колонку
            db.engine.execute(text("ALTER TABLE alerts RENAME COLUMN temp_timestamp TO timestamp"))
        
        # Додаємо record_count колонку в export_jobs, якщо її ще немає
        if not column_exists('export_jobs', 'record_count'):
            logger.info("Adding record_count column to export_jobs table")
            db.engine.execute(text(
                "ALTER TABLE export_jobs ADD COLUMN record_count INTEGER"
            ))
            
        logger.info("All migrations applied successfully")
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        raise

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    result = db.engine.execute(text(
        f"SELECT 1 FROM information_schema.columns "
        f"WHERE table_name = '{table_name}' AND column_name = '{column_name}'"
    ))
    return result.scalar() is not None

def column_type_is(table_name, column_name, data_type):
    """Check if a column is of a specific data type"""
    result = db.engine.execute(text(
        f"SELECT 1 FROM information_schema.columns "
        f"WHERE table_name = '{table_name}' AND column_name = '{column_name}' "
        f"AND data_type = '{data_type}'"
    ))
    return result.scalar() is not None

def constraint_exists(table_name, constraint_name):
    """Check if a constraint exists on a table"""
    result = db.engine.execute(text(
        f"SELECT 1 FROM information_schema.constraint_column_usage "
        f"WHERE table_name = '{table_name}' AND constraint_name = '{constraint_name}'"
    ))
    return result.scalar() is not None
