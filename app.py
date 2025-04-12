"""
Flask application initialization and configuration
"""
import os
import logging
from flask import Flask
from config import SECRET_KEY

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", SECRET_KEY)

# Initialize directories if they don't exist
os.makedirs('data', exist_ok=True)

# Initialize logger
logger = logging.getLogger(__name__)

# Import and initialize services
from services import data_service
data_service.initialize()

# Import models
from models import customer, appointment, barber, service

# Import and register blueprints
from controllers import init_app
init_app(app)

logger.info("Application initialized successfully")
