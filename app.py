"""
Flask application initialization and configuration
"""
import os
import logging
from flask import Flask
from config import SECRET_KEY
from models.database import db

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", SECRET_KEY)

# Add custom Jinja2 filters
from datetime import datetime, timedelta
@app.template_filter('strptime')
def _jinja2_filter_strptime(date_str, format_str):
    """Convert a date string to a datetime object using the given format"""
    return datetime.strptime(date_str, format_str)

# Add globals to templates
app.jinja_env.globals.update(timedelta=timedelta)

# Configure database
DATABASE_URL = "postgresql://neondb_owner:npg_8hPYDn1qoRQk@ep-floral-river-a4cfy8bm.us-east-1.aws.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize directories if they don't exist
os.makedirs('data', exist_ok=True)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    from models.database import Customer, Barber, Service, Appointment, ConversationState
    db.create_all()
    logger.info("Database tables created successfully")
    
    # Initialize sample data
    from utils.db_init import init_sample_data
    init_sample_data()
    logger.info("Sample data initialization completed")

# Import and initialize services
from services import data_service, db_service
data_service.initialize()
db_service.initialize()

# Import and register blueprints
from controllers import init_app
init_app(app)

logger.info("Application initialized successfully")
