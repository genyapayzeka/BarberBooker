"""
Controller for handling WhatsApp webhook endpoints
"""
import logging
import os
import json
from flask import Blueprint, request, jsonify
from config import BUSINESS_NAME
from services import whatsapp_service, chatgpt_service, db_service

logger = logging.getLogger(__name__)

# Create blueprint
webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

@webhook_bp.route('/whatsapp', methods=['GET'])
def verify_whatsapp_webhook():
    """
    Verify webhook for WhatsApp API integration
    
    This endpoint is called by WhatsApp when setting up the webhook
    """
    # WhatsApp sends a verification token
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    verify_token = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'barber_shop_webhook_token')
    
    # Check if the mode and token sent are correct
    if mode == 'subscribe' and token == verify_token:
        logger.info('WhatsApp webhook verified')
        return challenge
    else:
        logger.warning('WhatsApp webhook verification failed')
        return jsonify({"status": "error", "message": "Verification failed"}), 403

@webhook_bp.route('/whatsapp', methods=['POST'])
def process_whatsapp_webhook():
    """
    Process incoming WhatsApp messages
    
    This endpoint receives all incoming messages from WhatsApp
    """
    try:
        # Check if the request has a JSON content type
        if request.is_json:
            data = request.json
        else:
            # If not JSON, try to parse from form data or raw data
            data = {}
            if request.form:
                # Try to get data from form
                for key in request.form:
                    if key == 'Body':
                        # This is likely a direct Twilio SMS/WhatsApp POST
                        from_phone = request.form.get('From', '').replace('whatsapp:', '')
                        sender_name = request.form.get('ProfileName', 'Customer')
                        message_text = request.form.get('Body', '')
                        
                        # Process the message directly
                        if from_phone and message_text:
                            process_message(from_phone, sender_name, message_text)
                            return jsonify({"status": "success"})
                    try:
                        # Try to parse any JSON strings in the form
                        data[key] = json.loads(request.form[key])
                    except:
                        data[key] = request.form[key]
            elif request.data:
                # Try to parse raw data as JSON
                try:
                    data = json.loads(request.data.decode('utf-8'))
                except:
                    logger.warning("Could not parse request data as JSON")
        
        logger.info(f"Received WhatsApp webhook data: {json.dumps(data)}")
        
        # Handle direct Twilio webhook format
        if 'Body' in data and 'From' in data:
            from_phone = data['From'].replace('whatsapp:', '')
            sender_name = data.get('ProfileName', 'Customer')
            message_text = data['Body']
            
            # Process the message
            process_message(from_phone, sender_name, message_text)
            return jsonify({"status": "success"})
        
        # Handle Facebook/WhatsApp API format
        if data and 'object' in data:
            if data['object'] != 'whatsapp_business_account':
                return jsonify({"status": "error", "message": "Invalid object type"}), 400
                
            # Process all entries
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') != 'messages':
                        continue
                        
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    
                    for message in messages:
                        # Only process text messages for now
                        if message.get('type') != 'text':
                            continue
                            
                        # Get message details
                        phone_number = value.get('contacts', [{}])[0].get('wa_id')
                        sender_name = value.get('contacts', [{}])[0].get('profile', {}).get('name', 'Customer')
                        message_text = message.get('text', {}).get('body', '')
                        
                        # Process the message
                        if phone_number and message_text:
                            process_message(phone_number, sender_name, message_text)
            
            # Return a 200 OK response to acknowledge receipt
            return jsonify({"status": "success"})
        
        # If we get here, we didn't recognize the webhook format
        logger.warning(f"Unrecognized webhook format: {json.dumps(data)}")
        return jsonify({"status": "success"})  # Still return success to avoid retries
    
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def process_message(phone_number, sender_name, message_text):
    """
    Process an incoming WhatsApp message and generate a response
    
    Args:
        phone_number: Sender's phone number
        sender_name: Sender's name
        message_text: Message text
    """
    try:
        logger.info(f"Processing message from {sender_name} ({phone_number}): {message_text}")
        
        # Check if customer exists, create if not
        customer = db_service.get_customer_by_phone(phone_number)
        
        if not customer:
            # Create a new customer
            customer_data = {
                'name': sender_name,
                'phone': phone_number,
                'email': None,
                'notes': 'Created from WhatsApp interaction'
            }
            
            customer = db_service.create_customer(customer_data)
            
            # Send a welcome message in Turkish
            welcome_message = f"Merhaba {sender_name}! {BUSINESS_NAME}'e hoş geldiniz. "
            welcome_message += "Ben sizin sanal asistanınızım, randevu almanıza ve sorularınızı yanıtlamanıza yardımcı olmak için buradayım. "
            welcome_message += "Bugün size nasıl yardımcı olabilirim?"
            
            whatsapp_service.send_whatsapp_message(phone_number, welcome_message)
        
        # Process message with AI
        context = {"customer": customer}
        ai_result = chatgpt_service.process_whatsapp_message(message_text, context, BUSINESS_NAME)
        
        if ai_result['status'] == 'success':
            # Send the response back to the customer
            response = ai_result['response']
            whatsapp_service.send_whatsapp_message(phone_number, response)
            
            # Handle booking intent if detected
            if ai_result['analysis']['intent'] == 'booking':
                handle_booking_intent(phone_number, customer, ai_result['analysis'])
            
            # Handle cancel intent if detected
            elif ai_result['analysis']['intent'] == 'cancel':
                handle_cancel_intent(phone_number, customer, ai_result['analysis'])
            
        else:
            # AI processing failed, send default message in Turkish
            default_message = f"Merhaba {sender_name}, mesajınız için teşekkür ederiz. "
            default_message += "Şu anda bazı teknik sorunlar yaşıyorum. "
            default_message += f"Lütfen yardım için doğrudan {BUSINESS_NAME} ile iletişime geçin."
            
            whatsapp_service.send_whatsapp_message(phone_number, default_message)
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")

def handle_booking_intent(phone_number, customer, analysis):
    """
    Handle a booking intent from a WhatsApp message
    
    Args:
        phone_number: Customer's phone number
        customer: Customer data
        analysis: Message analysis result from ChatGPT
    """
    # For now, just log the intent - you can expand this to actually create appointments
    logger.info(f"Booking intent detected for {customer['name']}: {json.dumps(analysis)}")
    
    # Example of how to check for missing information
    if analysis['needs_followup']:
        followup = analysis['followup_question']
        whatsapp_service.send_whatsapp_message(phone_number, followup)

def handle_cancel_intent(phone_number, customer, analysis):
    """
    Handle a cancellation intent from a WhatsApp message
    
    Args:
        phone_number: Customer's phone number
        customer: Customer data
        analysis: Message analysis result from ChatGPT
    """
    # For now, just log the intent - you can expand this to actually cancel appointments
    logger.info(f"Cancel intent detected for {customer['name']}: {json.dumps(analysis)}")
    
    # Example of how to check for missing information
    if analysis['needs_followup']:
        followup = analysis['followup_question']
        whatsapp_service.send_whatsapp_message(phone_number, followup)