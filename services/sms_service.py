"""
SMS service for sending text messages using Twilio
"""
import os
import logging
from datetime import datetime, timedelta
from twilio.rest import Client
from config import BUSINESS_NAME

logger = logging.getLogger(__name__)

# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_sms(to_phone, message):
    """
    Send an SMS message using Twilio
    
    Args:
        to_phone: Recipient's phone number
        message: Message content
        
    Returns:
        dict: Response from Twilio
    """
    try:
        # Format the phone number if needed
        if not to_phone.startswith('+'):
            to_phone = '+' + to_phone
            
        # Send the message
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        logger.info(f"SMS sent to {to_phone}: {message.sid}")
        return {
            'status': 'success',
            'message_sid': message.sid,
            'to': to_phone
        }
    except Exception as e:
        logger.error(f"Error sending SMS to {to_phone}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'to': to_phone
        }

def send_appointment_confirmation(customer_phone, customer_name, appointment_date, 
                                 appointment_time, barber_name, service_name):
    """
    Send an appointment confirmation message
    
    Args:
        customer_phone: Customer's phone number
        customer_name: Customer's name
        appointment_date: Date of appointment (YYYY-MM-DD)
        appointment_time: Time of appointment (HH:MM)
        barber_name: Barber's name
        service_name: Service name
        
    Returns:
        dict: Response from send_sms function
    """
    try:
        # Format date for display
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Build message
        message = f"Hello {customer_name}! Your appointment has been confirmed.\n\n"
        message += f"Date: {formatted_date}\n"
        message += f"Time: {appointment_time}\n"
        message += f"Service: {service_name}\n"
        message += f"Barber: {barber_name}\n\n"
        message += f"Thank you for choosing {BUSINESS_NAME}. "
        message += "Reply 'HELP' for assistance or 'CANCEL' to cancel your appointment."
        
        return send_sms(customer_phone, message)
    except Exception as e:
        logger.error(f"Error sending confirmation SMS: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def send_appointment_reminder(customer_phone, customer_name, appointment_date, 
                             appointment_time, barber_name, service_name, reminder_hours=24):
    """
    Send an appointment reminder message
    
    Args:
        customer_phone: Customer's phone number
        customer_name: Customer's name
        appointment_date: Date of appointment (YYYY-MM-DD)
        appointment_time: Time of appointment (HH:MM)
        barber_name: Barber's name
        service_name: Service name
        reminder_hours: Hours before appointment to mention in message
        
    Returns:
        dict: Response from send_sms function
    """
    try:
        # Format date for display
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Build message
        message = f"Hello {customer_name}! This is a reminder about your upcoming appointment.\n\n"
        message += f"Date: {formatted_date}\n"
        message += f"Time: {appointment_time}\n"
        message += f"Service: {service_name}\n"
        message += f"Barber: {barber_name}\n\n"
        
        if reminder_hours == 24:
            message += f"Your appointment is tomorrow. "
        else:
            message += f"Your appointment is in {reminder_hours} hours. "
            
        message += f"We look forward to seeing you at {BUSINESS_NAME}. "
        message += "Reply 'HELP' for assistance or 'CANCEL' to cancel your appointment."
        
        return send_sms(customer_phone, message)
    except Exception as e:
        logger.error(f"Error sending reminder SMS: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def send_appointment_cancelled(customer_phone, customer_name, appointment_date, appointment_time):
    """
    Send an appointment cancellation message
    
    Args:
        customer_phone: Customer's phone number
        customer_name: Customer's name
        appointment_date: Date of appointment (YYYY-MM-DD)
        appointment_time: Time of appointment (HH:MM)
        
    Returns:
        dict: Response from send_sms function
    """
    try:
        # Format date for display
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Build message
        message = f"Hello {customer_name}! Your appointment has been cancelled.\n\n"
        message += f"Date: {formatted_date}\n"
        message += f"Time: {appointment_time}\n\n"
        message += f"Thank you for choosing {BUSINESS_NAME}. "
        message += "Please contact us if you would like to reschedule."
        
        return send_sms(customer_phone, message)
    except Exception as e:
        logger.error(f"Error sending cancellation SMS: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def send_appointment_rescheduled(customer_phone, customer_name, 
                                old_date, old_time, 
                                new_date, new_time, 
                                barber_name, service_name):
    """
    Send an appointment rescheduled message
    
    Args:
        customer_phone: Customer's phone number
        customer_name: Customer's name
        old_date: Original date of appointment (YYYY-MM-DD)
        old_time: Original time of appointment (HH:MM)
        new_date: New date of appointment (YYYY-MM-DD)
        new_time: New time of appointment (HH:MM)
        barber_name: Barber's name
        service_name: Service name
        
    Returns:
        dict: Response from send_sms function
    """
    try:
        # Format dates for display
        old_date_obj = datetime.strptime(old_date, '%Y-%m-%d')
        new_date_obj = datetime.strptime(new_date, '%Y-%m-%d')
        
        old_formatted_date = old_date_obj.strftime('%A, %B %d, %Y')
        new_formatted_date = new_date_obj.strftime('%A, %B %d, %Y')
        
        # Build message
        message = f"Hello {customer_name}! Your appointment has been rescheduled.\n\n"
        message += f"Original: {old_formatted_date} at {old_time}\n\n"
        message += f"New Date: {new_formatted_date}\n"
        message += f"New Time: {new_time}\n"
        message += f"Service: {service_name}\n"
        message += f"Barber: {barber_name}\n\n"
        message += f"Thank you for choosing {BUSINESS_NAME}. "
        message += "Reply 'HELP' for assistance or 'CANCEL' to cancel your appointment."
        
        return send_sms(customer_phone, message)
    except Exception as e:
        logger.error(f"Error sending rescheduled SMS: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }