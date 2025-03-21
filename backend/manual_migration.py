from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from config import get_config

app = Flask(__name__)
app.config.from_object(get_config('development'))
db = SQLAlchemy(app)

with app.app_context():
    connection = db.engine.connect()
    try:
        # Додавання стовпця siem_source до таблиці configuration
        connection.execute(text('ALTER TABLE configuration ADD COLUMN siem_source VARCHAR(50);'))
        print("Column 'siem_source' added to 'configuration' table.")
    except Exception as e:
        print(f"Error adding column 'siem_source' to 'configuration' table: {e}")

    try:
        # Додавання стовпця message до таблиці alerts
        connection.execute(text('ALTER TABLE alerts ADD COLUMN message TEXT;'))
        print("Column 'message' added to 'alerts' table.")
    except Exception as e:
        print(f"Error adding column 'message' to 'alerts' table: {e}")

    connection.close()