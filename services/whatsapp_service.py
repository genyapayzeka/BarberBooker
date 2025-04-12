"""
WhatsApp service for sending and receiving messages via the WhatsApp Business API
"""
import json
import logging
from config import (
    WHATSAPP_API_TOKEN, WHATSAPP_API_BASE_URL,
    BUSINESS_NAME
)

logger = logging.getLogger(__name__)

# Mock requests module for now (to be replaced with actual implementation later)
class RequestsMock:
    def post(self, url, headers=None, data=None):
        logger.info(f"Mock HTTP POST to {url}")
        return MockResponse({"messages": [{"id": "mock-message-id"}]})

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
    
    def json(self):
        return self.json_data

# Use mock requests
requests = RequestsMock()

def send_message(to, message_text):
    """
    Send a text message to a WhatsApp user
    
    Args:
        to: Recipient's phone number with country code (e.g., "15551234567")
        message_text: Text message to send
        
    Returns:
        dict: Response from WhatsApp API
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_text
        }
    }
    
    try:
        response = requests.post(
            WHATSAPP_API_BASE_URL,
            headers=headers,
            data=json.dumps(payload)
        )
        
        if response.status_code == 200:
            logger.info(f"Message sent successfully to {to}")
            return response.json()
        else:
            logger.error(f"Failed to send message to {to}. Status code: {response.status_code}, Response: {response.text}")
            return {"error": response.text}
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return {"error": str(e)}

def send_template_message(to, template_name, language_code="en_US", components=None):
    """
    Send a template message to a WhatsApp user
    
    Args:
        to: Recipient's phone number with country code
        template_name: Name of the template
        language_code: Language code (default: "en_US")
        components: Template components (header, body, buttons)
        
    Returns:
        dict: Response from WhatsApp API
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }
    
    if components:
        payload["template"]["components"] = components
    
    try:
        response = requests.post(
            WHATSAPP_API_BASE_URL,
            headers=headers,
            data=json.dumps(payload)
        )
        
        if response.status_code == 200:
            logger.info(f"Template message sent successfully to {to}")
            return response.json()
        else:
            logger.error(f"Failed to send template message to {to}. Status code: {response.status_code}, Response: {response.text}")
            return {"error": response.text}
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp template message: {str(e)}")
        return {"error": str(e)}

def send_appointment_confirmation(to, customer_name, date, time, service, barber):
    """
    Send an appointment confirmation message
    
    Args:
        to: Customer's phone number
        customer_name: Customer's name
        date: Appointment date
        time: Appointment time
        service: Service name
        barber: Barber name
        
    Returns:
        dict: Response from WhatsApp API
    """
    message = (
        f"Hi {customer_name}! Your appointment at {BUSINESS_NAME} has been confirmed.\n\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {time}\n"
        f"💇 Service: {service}\n"
        f"👨‍💼 Barber: {barber}\n\n"
        f"Reply with 'CANCEL' to cancel this appointment or 'RESCHEDULE' to change it."
    )
    
    return send_message(to, message)

def send_appointment_reminder(to, customer_name, date, time, service, barber):
    """
    Send an appointment reminder message
    
    Args:
        to: Customer's phone number
        customer_name: Customer's name
        date: Appointment date
        time: Appointment time
        service: Service name
        barber: Barber name
        
    Returns:
        dict: Response from WhatsApp API
    """
    message = (
        f"Hi {customer_name}! This is a reminder for your appointment at {BUSINESS_NAME} tomorrow.\n\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {time}\n"
        f"💇 Service: {service}\n"
        f"👨‍💼 Barber: {barber}\n\n"
        f"Reply with 'CONFIRM' to confirm or 'CANCEL' to cancel this appointment."
    )
    
    return send_message(to, message)

def send_registration_confirmation(to, customer_name):
    """
    Send a registration confirmation message
    
    Args:
        to: Customer's phone number
        customer_name: Customer's name
        
    Returns:
        dict: Response from WhatsApp API
    """
    message = (
        f"Welcome to {BUSINESS_NAME}, {customer_name}!\n\n"
        f"You've successfully registered with our appointment system. "
        f"You can now book appointments by sending 'BOOK' or check our services with 'SERVICES'.\n\n"
        f"Need help? Just type 'HELP' for assistance."
    )
    
    return send_message(to, message)

def send_available_services(to, services):
    """
    Send a list of available services
    
    Args:
        to: Customer's phone number
        services: List of service dictionaries with name, duration, and price
        
    Returns:
        dict: Response from WhatsApp API
    """
    message = f"Here are the services we offer at {BUSINESS_NAME}:\n\n"
    
    for i, service in enumerate(services, 1):
        message += (
            f"{i}. {service['name']}\n"
            f"   ⏱️ Duration: {service['duration']} minutes\n"
            f"   💲 Price: ${service['price']}\n\n"
        )
    
    message += "To book an appointment, send 'BOOK' followed by the service number (e.g., 'BOOK 1')."
    
    return send_message(to, message)

def send_available_slots(to, date, available_slots):
    """
    Send a list of available time slots
    
    Args:
        to: Customer's phone number
        date: Date for which slots are available
        available_slots: List of available time slots
        
    Returns:
        dict: Response from WhatsApp API
    """
    message = f"Available appointment slots for {date}:\n\n"
    
    for i, slot in enumerate(available_slots, 1):
        message += f"{i}. {slot}\n"
    
    message += "\nTo book, reply with the slot number (e.g., '3' for the third option)."
    
    return send_message(to, message)

def send_help_message(to):
    """
    Send a help message with available commands
    
    Args:
        to: Customer's phone number
        
    Returns:
        dict: Response from WhatsApp API
    """
    message = (
        f"Welcome to {BUSINESS_NAME} WhatsApp Booking System!\n\n"
        f"Here are the commands you can use:\n\n"
        f"• BOOK - Start the booking process\n"
        f"• SERVICES - View our services\n"
        f"• APPOINTMENTS - View your upcoming appointments\n"
        f"• CANCEL - Cancel an appointment\n"
        f"• RESCHEDULE - Reschedule an appointment\n"
        f"• BARBERS - View our barbers\n"
        f"• HOURS - View our business hours\n"
        f"• HELP - Show this help message\n\n"
        f"You can also speak naturally, and our AI assistant will help you!"
    )
    
    return send_message(to, message)

def parse_whatsapp_webhook(request_data):
    """
    Parse incoming webhook data from WhatsApp
    
    Args:
        request_data: JSON data from webhook
        
    Returns:
        dict: Parsed message data or None if not a message
    """
    try:
        # Extract the message data
        data = request_data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {})
        
        if "messages" not in data:
            return None
            
        message = data["messages"][0]
        
        # Get the sender information
        sender = {
            "wa_id": message.get("from"),
            "name": data.get("contacts", [{}])[0].get("profile", {}).get("name", "Customer")
        }
        
        # Get the message content
        if message.get("type") == "text":
            message_content = {
                "type": "text",
                "text": message.get("text", {}).get("body", "")
            }
        else:
            message_content = {
                "type": message.get("type"),
                "data": message
            }
        
        return {
            "message_id": message.get("id"),
            "timestamp": message.get("timestamp"),
            "sender": sender,
            "content": message_content
        }
        
    except Exception as e:
        logger.error(f"Error parsing WhatsApp webhook: {str(e)}")
        return None
