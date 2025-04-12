"""
WhatsApp messaging service using Twilio's WhatsApp API
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

def send_whatsapp_message(to_phone, message):
    """
    Send a WhatsApp message using Twilio
    
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
            
        # Send the message via WhatsApp
        # Twilio's WhatsApp API requires 'whatsapp:' prefix
        message = client.messages.create(
            body=message,
            from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
            to=f'whatsapp:{to_phone}'
        )
        
        logger.info(f"WhatsApp message sent to {to_phone}: {message.sid}")
        return {
            'status': 'success',
            'message_sid': message.sid,
            'to': to_phone
        }
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to_phone}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'to': to_phone
        }

def send_appointment_confirmation(customer_phone, customer_name, appointment_date, 
                                 appointment_time, barber_name, service_name):
    """
    Send an appointment confirmation message via WhatsApp
    
    Args:
        customer_phone: Customer's phone number
        customer_name: Customer's name
        appointment_date: Date of appointment (YYYY-MM-DD)
        appointment_time: Time of appointment (HH:MM)
        barber_name: Barber's name
        service_name: Service name
        
    Returns:
        dict: Response from send_whatsapp_message function
    """
    try:
        # Format date for display
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
        
        # Türkçe gün ve ay isimleri
        turkish_days = {
            'Monday': 'Pazartesi',
            'Tuesday': 'Salı',
            'Wednesday': 'Çarşamba',
            'Thursday': 'Perşembe',
            'Friday': 'Cuma',
            'Saturday': 'Cumartesi',
            'Sunday': 'Pazar'
        }
        
        turkish_months = {
            'January': 'Ocak',
            'February': 'Şubat',
            'March': 'Mart',
            'April': 'Nisan',
            'May': 'Mayıs',
            'June': 'Haziran',
            'July': 'Temmuz',
            'August': 'Ağustos',
            'September': 'Eylül',
            'October': 'Ekim',
            'November': 'Kasım',
            'December': 'Aralık'
        }
        
        # İngilizce formatı al
        english_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Türkçe'ye çevir
        day_name = english_date.split(',')[0]
        month_name = english_date.split(' ')[1]
        day_num = english_date.split(' ')[2].replace(',', '')
        year = english_date.split(' ')[3]
        
        formatted_date = f"{turkish_days[day_name]}, {day_num} {turkish_months[month_name]} {year}"
        
        # Build message in Turkish
        message = f"Merhaba {customer_name}! Randevunuz onaylanmıştır.\n\n"
        message += f"Tarih: {formatted_date}\n"
        message += f"Saat: {appointment_time}\n"
        message += f"Hizmet: {service_name}\n"
        message += f"Berber: {barber_name}\n\n"
        message += f"{BUSINESS_NAME}'i tercih ettiğiniz için teşekkür ederiz. "
        message += "Yardım için 'YARDIM' yazabilir veya randevunuzu iptal etmek için 'İPTAL' yazabilirsiniz."
        
        return send_whatsapp_message(customer_phone, message)
    except Exception as e:
        logger.error(f"Error sending confirmation WhatsApp message: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def send_appointment_reminder(customer_phone, customer_name, appointment_date, 
                             appointment_time, barber_name, service_name, reminder_hours=24):
    """
    Send an appointment reminder message via WhatsApp
    
    Args:
        customer_phone: Customer's phone number
        customer_name: Customer's name
        appointment_date: Date of appointment (YYYY-MM-DD)
        appointment_time: Time of appointment (HH:MM)
        barber_name: Barber's name
        service_name: Service name
        reminder_hours: Hours before appointment to mention in message
        
    Returns:
        dict: Response from send_whatsapp_message function
    """
    try:
        # Format date for display
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
        
        # Türkçe gün ve ay isimleri
        turkish_days = {
            'Monday': 'Pazartesi',
            'Tuesday': 'Salı',
            'Wednesday': 'Çarşamba',
            'Thursday': 'Perşembe',
            'Friday': 'Cuma',
            'Saturday': 'Cumartesi',
            'Sunday': 'Pazar'
        }
        
        turkish_months = {
            'January': 'Ocak',
            'February': 'Şubat',
            'March': 'Mart',
            'April': 'Nisan',
            'May': 'Mayıs',
            'June': 'Haziran',
            'July': 'Temmuz',
            'August': 'Ağustos',
            'September': 'Eylül',
            'October': 'Ekim',
            'November': 'Kasım',
            'December': 'Aralık'
        }
        
        # İngilizce formatı al
        english_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Türkçe'ye çevir
        day_name = english_date.split(',')[0]
        month_name = english_date.split(' ')[1]
        day_num = english_date.split(' ')[2].replace(',', '')
        year = english_date.split(' ')[3]
        
        formatted_date = f"{turkish_days[day_name]}, {day_num} {turkish_months[month_name]} {year}"
        
        # Build message in Turkish
        message = f"Merhaba {customer_name}! Yaklaşan randevunuz hakkında bir hatırlatma.\n\n"
        message += f"Tarih: {formatted_date}\n"
        message += f"Saat: {appointment_time}\n"
        message += f"Hizmet: {service_name}\n"
        message += f"Berber: {barber_name}\n\n"
        
        if reminder_hours == 24:
            message += f"Randevunuz yarın. "
        else:
            message += f"Randevunuz {reminder_hours} saat içinde. "
            
        message += f"{BUSINESS_NAME} olarak sizi görmekten memnuniyet duyacağız. "
        message += "Yardım için 'YARDIM' yazabilir veya randevunuzu iptal etmek için 'İPTAL' yazabilirsiniz."
        
        return send_whatsapp_message(customer_phone, message)
    except Exception as e:
        logger.error(f"Error sending reminder WhatsApp message: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def send_appointment_cancelled(customer_phone, customer_name, appointment_date, appointment_time):
    """
    Send an appointment cancellation message via WhatsApp
    
    Args:
        customer_phone: Customer's phone number
        customer_name: Customer's name
        appointment_date: Date of appointment (YYYY-MM-DD)
        appointment_time: Time of appointment (HH:MM)
        
    Returns:
        dict: Response from send_whatsapp_message function
    """
    try:
        # Format date for display
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
        
        # Türkçe gün ve ay isimleri
        turkish_days = {
            'Monday': 'Pazartesi',
            'Tuesday': 'Salı',
            'Wednesday': 'Çarşamba',
            'Thursday': 'Perşembe',
            'Friday': 'Cuma',
            'Saturday': 'Cumartesi',
            'Sunday': 'Pazar'
        }
        
        turkish_months = {
            'January': 'Ocak',
            'February': 'Şubat',
            'March': 'Mart',
            'April': 'Nisan',
            'May': 'Mayıs',
            'June': 'Haziran',
            'July': 'Temmuz',
            'August': 'Ağustos',
            'September': 'Eylül',
            'October': 'Ekim',
            'November': 'Kasım',
            'December': 'Aralık'
        }
        
        # İngilizce formatı al
        english_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Türkçe'ye çevir
        day_name = english_date.split(',')[0]
        month_name = english_date.split(' ')[1]
        day_num = english_date.split(' ')[2].replace(',', '')
        year = english_date.split(' ')[3]
        
        formatted_date = f"{turkish_days[day_name]}, {day_num} {turkish_months[month_name]} {year}"
        
        # Build message in Turkish
        message = f"Merhaba {customer_name}! Randevunuz iptal edilmiştir.\n\n"
        message += f"Tarih: {formatted_date}\n"
        message += f"Saat: {appointment_time}\n\n"
        message += f"{BUSINESS_NAME}'i tercih ettiğiniz için teşekkür ederiz. "
        message += "Yeniden randevu almak isterseniz lütfen bizimle iletişime geçin."
        
        return send_whatsapp_message(customer_phone, message)
    except Exception as e:
        logger.error(f"Error sending cancellation WhatsApp message: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def send_appointment_rescheduled(customer_phone, customer_name, 
                                old_date, old_time, 
                                new_date, new_time, 
                                barber_name, service_name):
    """
    Send an appointment rescheduled message via WhatsApp
    
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
        dict: Response from send_whatsapp_message function
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
        message += "Send 'HELP' for assistance or 'CANCEL' to cancel your appointment."
        
        return send_whatsapp_message(customer_phone, message)
    except Exception as e:
        logger.error(f"Error sending rescheduled WhatsApp message: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def process_incoming_message(from_phone, message_body):
    """
    Process incoming WhatsApp messages
    
    Args:
        from_phone: Sender's phone number
        message_body: Message content
        
    Returns:
        dict: Response with action to take
    """
    try:
        # Clean up the phone number and message
        if from_phone.startswith('whatsapp:'):
            from_phone = from_phone[9:]  # Remove 'whatsapp:' prefix
            
        if from_phone.startswith('+'):
            from_phone = from_phone[1:]  # Remove '+' prefix
            
        message_upper = message_body.strip().upper()
        
        # Handle common keywords
        if message_upper == 'HELP':
            response = "Thank you for contacting us. To book an appointment, simply send 'BOOK'. "
            response += "To cancel an appointment, send 'CANCEL'. "
            response += f"For more assistance, please call {BUSINESS_NAME} directly."
            send_whatsapp_message(from_phone, response)
            return {'status': 'success', 'action': 'help_sent'}
            
        elif message_upper == 'CANCEL':
            # This would typically trigger the cancellation flow
            response = "To cancel an appointment, please provide your appointment date and time. "
            response += "For example: 'CANCEL April 15, 2:30 PM'"
            send_whatsapp_message(from_phone, response)
            return {'status': 'success', 'action': 'cancel_instructions_sent'}
            
        elif message_upper.startswith('BOOK'):
            # This would typically trigger the booking flow
            response = "Thank you for your interest in booking an appointment. "
            response += "Please let us know which service you'd like and your preferred date and time."
            send_whatsapp_message(from_phone, response)
            return {'status': 'success', 'action': 'booking_started'}
            
        else:
            # For any other message, we would typically use AI to process it
            # For now, just acknowledge the message
            response = "Thank you for your message. Our system will process your request shortly. "
            response += f"If you need immediate assistance, please call {BUSINESS_NAME} directly."
            send_whatsapp_message(from_phone, response)
            return {'status': 'success', 'action': 'message_acknowledged'}
            
    except Exception as e:
        logger.error(f"Error processing incoming WhatsApp message: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }