"""
Configuration settings for the Barber Appointment System
"""
import os

# Application settings
APP_NAME = "Barber Appointment System"
VERSION = "1.0.0"
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

# Secret keys and tokens
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "your-verify-token")

# Data storage paths
DATA_DIR = "data"
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
APPOINTMENTS_FILE = os.path.join(DATA_DIR, "appointments.json")
BARBERS_FILE = os.path.join(DATA_DIR, "barbers.json")
SERVICES_FILE = os.path.join(DATA_DIR, "services.json")

# Business settings
BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "Modern Cuts Barbershop")
BUSINESS_PHONE = os.environ.get("BUSINESS_PHONE", "+1234567890")
BUSINESS_ADDRESS = os.environ.get("BUSINESS_ADDRESS", "123 Main St, Anytown, USA")
BUSINESS_HOURS = {
    "Monday": "9:00 AM - 6:00 PM",
    "Tuesday": "9:00 AM - 6:00 PM",
    "Wednesday": "9:00 AM - 6:00 PM",
    "Thursday": "9:00 AM - 6:00 PM",
    "Friday": "9:00 AM - 6:00 PM",
    "Saturday": "10:00 AM - 4:00 PM",
    "Sunday": "Closed"
}

# Session timeout (in minutes)
SESSION_TIMEOUT = 30

# Admin credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")

# OpenAI configuration
OPENAI_MODEL = "gpt-4o"  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
MAX_TOKENS = 500

# WhatsApp API configuration
WHATSAPP_API_VERSION = "v17.0"
WHATSAPP_API_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
