from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy object
db = SQLAlchemy()

# Import all models - after they have been created
from .event import Event
from .alert import Alert
from .raw_log import RawLog
from .user import User
from .settings import Settings
from .configuration import Configuration 
from .export_job import ExportJob
from .ml import MLPerformanceMetrics
