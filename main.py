"""
Main entry point for the Barber Appointment System
"""
import logging
from app import app
import os
from config import DEBUG

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import controllers to register routes
from controllers import appointment_controller, customer_controller, whatsapp_controller, admin_controller

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=DEBUG)
