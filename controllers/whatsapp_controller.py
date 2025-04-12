"""
Controller for handling WhatsApp webhook and message processing
"""
import logging
import json
from flask import Blueprint, request, jsonify, abort
from datetime import datetime, timedelta
import re

from config import WHATSAPP_VERIFY_TOKEN, BUSINESS_HOURS, BUSINESS_NAME
from services import data_service, whatsapp_service, chatgpt_service
from models.customer import Customer
from utils import validators

logger = logging.getLogger(__name__)

# Create blueprint
whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/webhook')

# In-memory store for conversation state
conversation_state = {}

@whatsapp_bp.route('/', methods=['GET'])
def verify_webhook():
    """
    Verify webhook for WhatsApp API integration
    
    This endpoint is called by WhatsApp when setting up the webhook
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == WHATSAPP_VERIFY_TOKEN:
            logger.info('Webhook verified successfully')
            return challenge, 200
        else:
            logger.warning('Webhook verification failed')
            return 'Verification token mismatch', 403
    
    return 'Invalid request', 400

@whatsapp_bp.route('/', methods=['POST'])
def process_webhook():
    """
    Process incoming WhatsApp messages
    
    This endpoint receives all incoming messages from WhatsApp
    """
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        logger.debug(f"Received webhook data: {json.dumps(data)}")
        
        # Parse the message data
        message_data = whatsapp_service.parse_whatsapp_webhook(data)
        
        if not message_data:
            logger.debug("No message data found in webhook")
            return jsonify({"status": "success"}), 200
        
        # Process the message
        phone_number = message_data['sender']['wa_id']
        sender_name = message_data['sender']['name']
        
        if message_data['content']['type'] == 'text':
            message_text = message_data['content']['text']
            logger.info(f"Received message from {phone_number} ({sender_name}): {message_text}")
            
            # Process the message and send a response
            process_message(phone_number, sender_name, message_text)
        else:
            # Handle non-text messages
            message_type = message_data['content']['type']
            logger.info(f"Received {message_type} message from {phone_number} ({sender_name})")
            
            # Send a response for unsupported message types
            whatsapp_service.send_message(
                phone_number,
                f"I received your {message_type}, but I can only process text messages at the moment. "
                f"Please send a text message with your request."
            )
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
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
        # Check if the user exists, create if not
        customer = data_service.get_customer_by_phone(phone_number)
        
        if not customer:
            # Create a new customer
            customer = data_service.create_customer({
                "name": sender_name,
                "phone": phone_number,
                "created_at": datetime.now().isoformat()
            })
            
            # Send welcome message
            whatsapp_service.send_registration_confirmation(phone_number, sender_name)
            return
        
        # Get the current conversation state or initialize new one
        state = conversation_state.get(phone_number, {
            "step": "idle",
            "data": {},
            "history": []
        })
        
        # Convert message to uppercase for command matching
        message_upper = message_text.upper().strip()
        
        # Process the message based on the current state and message content
        if state["step"] == "idle":
            process_idle_state(phone_number, customer, message_upper, message_text, state)
        elif state["step"] == "booking_service":
            process_booking_service(phone_number, customer, message_text, state)
        elif state["step"] == "booking_date":
            process_booking_date(phone_number, customer, message_text, state)
        elif state["step"] == "booking_time":
            process_booking_time(phone_number, customer, message_text, state)
        elif state["step"] == "booking_barber":
            process_booking_barber(phone_number, customer, message_text, state)
        elif state["step"] == "booking_confirmation":
            process_booking_confirmation(phone_number, customer, message_upper, state)
        elif state["step"] == "cancel_select":
            process_cancel_select(phone_number, customer, message_text, state)
        elif state["step"] == "cancel_confirmation":
            process_cancel_confirmation(phone_number, customer, message_upper, state)
        else:
            # Use ChatGPT to handle other requests
            process_with_chatgpt(phone_number, customer, message_text, state)
        
        # Update conversation state with history
        if "history" not in state:
            state["history"] = []
        
        # Add message to history
        state["history"].append({"role": "user", "content": message_text})
        
        # Store updated state
        conversation_state[phone_number] = state
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error while processing your request. Please try again later."
        )

def process_idle_state(phone_number, customer, message_upper, message_text, state):
    """Process message when user is in idle state"""
    if message_upper == "BOOK":
        # Start booking process
        state["step"] = "booking_service"
        
        # Get available services
        services = list(data_service.get_services().values())
        
        if not services:
            whatsapp_service.send_message(
                phone_number,
                "I'm sorry, we don't have any services available at the moment. Please try again later."
            )
            state["step"] = "idle"
            return
        
        # Send available services
        whatsapp_service.send_available_services(phone_number, services)
        
    elif message_upper == "SERVICES":
        # Send available services
        services = list(data_service.get_services().values())
        
        if not services:
            whatsapp_service.send_message(
                phone_number,
                "I'm sorry, we don't have any services available at the moment. Please try again later."
            )
            return
        
        whatsapp_service.send_available_services(phone_number, services)
        
    elif message_upper == "APPOINTMENTS":
        # Get customer's appointments
        appointments = data_service.get_appointments_by_customer(customer["id"])
        upcoming_appointments = {
            k: v for k, v in appointments.items() 
            if v["status"] == "scheduled" and v["date"] >= datetime.now().strftime("%Y-%m-%d")
        }
        
        if not upcoming_appointments:
            whatsapp_service.send_message(
                phone_number,
                "You don't have any upcoming appointments. Send 'BOOK' to schedule one."
            )
            return
        
        # Format appointments
        message = "Your upcoming appointments:\n\n"
        
        for i, (appt_id, appt) in enumerate(upcoming_appointments.items(), 1):
            # Get service and barber details
            service = data_service.get_service(appt["service_id"])
            barber = data_service.get_barber(appt["barber_id"])
            
            message += (
                f"{i}. Appointment #{appt_id}\n"
                f"   📅 Date: {appt['date']}\n"
                f"   ⏰ Time: {appt['time']}\n"
                f"   💇 Service: {service['name'] if service else 'Unknown'}\n"
                f"   👨‍💼 Barber: {barber['name'] if barber else 'Unknown'}\n\n"
            )
        
        message += "To cancel an appointment, send 'CANCEL'."
        
        whatsapp_service.send_message(phone_number, message)
        
    elif message_upper == "CANCEL":
        # Start cancellation process
        appointments = data_service.get_appointments_by_customer(customer["id"])
        upcoming_appointments = {
            k: v for k, v in appointments.items() 
            if v["status"] == "scheduled" and v["date"] >= datetime.now().strftime("%Y-%m-%d")
        }
        
        if not upcoming_appointments:
            whatsapp_service.send_message(
                phone_number,
                "You don't have any upcoming appointments to cancel. Send 'BOOK' to schedule one."
            )
            return
        
        # Format appointments for selection
        message = "Please select an appointment to cancel by replying with its number:\n\n"
        
        for i, (appt_id, appt) in enumerate(upcoming_appointments.items(), 1):
            # Get service and barber details
            service = data_service.get_service(appt["service_id"])
            barber = data_service.get_barber(appt["barber_id"])
            
            message += (
                f"{i}. {appt['date']} at {appt['time']}\n"
                f"   Service: {service['name'] if service else 'Unknown'}\n"
                f"   Barber: {barber['name'] if barber else 'Unknown'}\n\n"
            )
        
        state["step"] = "cancel_select"
        state["data"]["appointments"] = list(upcoming_appointments.items())
        
        whatsapp_service.send_message(phone_number, message)
        
    elif message_upper == "BARBERS":
        # Send barber information
        barbers = list(data_service.get_barbers().values())
        
        if not barbers:
            whatsapp_service.send_message(
                phone_number,
                "I'm sorry, we don't have any barbers available at the moment. Please try again later."
            )
            return
        
        message = f"Our talented barbers at {BUSINESS_NAME}:\n\n"
        
        for i, barber in enumerate(barbers, 1):
            specialties = ", ".join(barber.get("specialties", []))
            message += (
                f"{i}. {barber['name']}\n"
                f"   Specialties: {specialties if specialties else 'All services'}\n\n"
            )
        
        message += "To book an appointment, send 'BOOK'."
        
        whatsapp_service.send_message(phone_number, message)
        
    elif message_upper == "HOURS":
        # Send business hours
        message = f"{BUSINESS_NAME} Business Hours:\n\n"
        
        for day, hours in BUSINESS_HOURS.items():
            message += f"{day.capitalize()}: {hours}\n"
        
        whatsapp_service.send_message(phone_number, message)
        
    elif message_upper == "HELP":
        # Send help message
        whatsapp_service.send_help_message(phone_number)
        
    elif message_upper.startswith("BOOK "):
        # Attempt to book a specific service directly
        try:
            service_num = int(message_upper.replace("BOOK ", "").strip())
            services = list(data_service.get_services().values())
            
            if 1 <= service_num <= len(services):
                selected_service = services[service_num - 1]
                
                # Store the selected service and move to date selection
                state["step"] = "booking_date"
                state["data"]["service_id"] = selected_service["id"]
                state["data"]["service_name"] = selected_service["name"]
                
                # Ask for preferred date
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                next_week = today + timedelta(days=7)
                
                message = (
                    f"You selected: {selected_service['name']} (${selected_service['price']})\n\n"
                    f"Please enter your preferred date for the appointment (MM/DD/YYYY).\n\n"
                    f"We're available from {tomorrow.strftime('%m/%d/%Y')} to {next_week.strftime('%m/%d/%Y')}."
                )
                
                whatsapp_service.send_message(phone_number, message)
            else:
                whatsapp_service.send_message(
                    phone_number,
                    f"Invalid service number. Please select a number between 1 and {len(services)}."
                )
        except (ValueError, IndexError):
            # Use ChatGPT for understanding
            process_with_chatgpt(phone_number, customer, message_text, state)
    else:
        # Use ChatGPT for other messages
        process_with_chatgpt(phone_number, customer, message_text, state)

def process_booking_service(phone_number, customer, message_text, state):
    """Process service selection during booking"""
    try:
        # Try to parse a service number
        services = list(data_service.get_services().values())
        
        try:
            service_num = int(message_text.strip())
            
            if 1 <= service_num <= len(services):
                selected_service = services[service_num - 1]
                
                # Store the selected service and move to date selection
                state["step"] = "booking_date"
                state["data"]["service_id"] = selected_service["id"]
                state["data"]["service_name"] = selected_service["name"]
                
                # Ask for preferred date
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                next_week = today + timedelta(days=7)
                
                message = (
                    f"You selected: {selected_service['name']} (${selected_service['price']})\n\n"
                    f"Please enter your preferred date for the appointment (MM/DD/YYYY).\n\n"
                    f"We're available from {tomorrow.strftime('%m/%d/%Y')} to {next_week.strftime('%m/%d/%Y')}."
                )
                
                whatsapp_service.send_message(phone_number, message)
            else:
                whatsapp_service.send_message(
                    phone_number,
                    f"Invalid service number. Please select a number between 1 and {len(services)}."
                )
        except ValueError:
            # Try to match by service name
            message_lower = message_text.lower().strip()
            matched_service = None
            
            for service in services:
                if message_lower in service["name"].lower():
                    matched_service = service
                    break
            
            if matched_service:
                # Store the selected service and move to date selection
                state["step"] = "booking_date"
                state["data"]["service_id"] = matched_service["id"]
                state["data"]["service_name"] = matched_service["name"]
                
                # Ask for preferred date
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                next_week = today + timedelta(days=7)
                
                message = (
                    f"You selected: {matched_service['name']} (${matched_service['price']})\n\n"
                    f"Please enter your preferred date for the appointment (MM/DD/YYYY).\n\n"
                    f"We're available from {tomorrow.strftime('%m/%d/%Y')} to {next_week.strftime('%m/%d/%Y')}."
                )
                
                whatsapp_service.send_message(phone_number, message)
            else:
                # Could not identify service
                whatsapp_service.send_message(
                    phone_number,
                    "I couldn't identify which service you want. Please reply with the service number (e.g., '1')."
                )
                
                # Re-send service options
                whatsapp_service.send_available_services(phone_number, services)
    except Exception as e:
        logger.error(f"Error processing booking service: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error processing your service selection. Please try again."
        )

def process_booking_date(phone_number, customer, message_text, state):
    """Process date selection during booking"""
    try:
        # Try to parse date from various formats
        date_str = message_text.strip()
        parsed_date = None
        
        # Try MM/DD/YYYY format
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            try:
                parsed_date = datetime.strptime(date_str, "%m/%d/%Y").date()
            except ValueError:
                pass
                
        # Try YYYY-MM-DD format
        if not parsed_date and re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        # Try other common formats if needed
        if not parsed_date and re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', date_str):
            try:
                parsed_date = datetime.strptime(date_str, "%d-%m-%Y").date()
            except ValueError:
                pass
        
        if not parsed_date:
            whatsapp_service.send_message(
                phone_number,
                "Invalid date format. Please enter the date in MM/DD/YYYY format (e.g., 06/15/2023)."
            )
            return
        
        # Check if date is valid (not in the past and within reasonable future)
        today = datetime.now().date()
        
        if parsed_date <= today:
            whatsapp_service.send_message(
                phone_number,
                "Please select a future date. We need at least one day's notice for appointments."
            )
            return
            
        if parsed_date > today + timedelta(days=30):
            whatsapp_service.send_message(
                phone_number,
                "Please select a date within the next 30 days."
            )
            return
        
        # Convert to YYYY-MM-DD format for storage
        formatted_date = parsed_date.strftime("%Y-%m-%d")
        
        # Store the selected date and move to time selection
        state["step"] = "booking_time"
        state["data"]["date"] = formatted_date
        
        # Get available time slots for the date
        response = get_available_slots(formatted_date)
        available_slots = response.get("data", {}).get("slots", [])
        
        if not available_slots:
            whatsapp_service.send_message(
                phone_number,
                f"I'm sorry, we don't have any available slots on {parsed_date.strftime('%A, %B %d')}. "
                f"Please select a different date."
            )
            state["step"] = "booking_date"
            return
        
        # Send available time slots
        whatsapp_service.send_available_slots(phone_number, formatted_date, available_slots)
        
    except Exception as e:
        logger.error(f"Error processing booking date: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error processing your date selection. Please try again."
        )

def process_booking_time(phone_number, customer, message_text, state):
    """Process time selection during booking"""
    try:
        # Get available time slots
        response = get_available_slots(state["data"]["date"])
        available_slots = response.get("data", {}).get("slots", [])
        
        if not available_slots:
            whatsapp_service.send_message(
                phone_number,
                f"I'm sorry, we don't have any available slots on {state['data']['date']}. "
                f"Please select a different date."
            )
            state["step"] = "booking_date"
            return
        
        # Try to parse slot number
        try:
            slot_num = int(message_text.strip())
            
            if 1 <= slot_num <= len(available_slots):
                selected_time = available_slots[slot_num - 1]
                
                # Store the selected time and move to barber selection
                state["step"] = "booking_barber"
                state["data"]["time"] = selected_time
                
                # Get available barbers
                barbers = list(data_service.get_barbers().values())
                active_barbers = [b for b in barbers if b.get("is_active", True)]
                
                if not active_barbers:
                    whatsapp_service.send_message(
                        phone_number,
                        "I'm sorry, we don't have any barbers available at the moment. Please try again later."
                    )
                    state["step"] = "idle"
                    return
                
                # Format barber selection message
                message = "Please select a barber by replying with their number:\n\n"
                
                for i, barber in enumerate(active_barbers, 1):
                    specialties = ", ".join(barber.get("specialties", []))
                    message += (
                        f"{i}. {barber['name']}\n"
                        f"   Specialties: {specialties if specialties else 'All services'}\n\n"
                    )
                
                state["data"]["barbers"] = active_barbers
                
                whatsapp_service.send_message(phone_number, message)
            else:
                whatsapp_service.send_message(
                    phone_number,
                    f"Invalid time slot number. Please select a number between 1 and {len(available_slots)}."
                )
                
                # Re-send available slots
                whatsapp_service.send_available_slots(phone_number, state["data"]["date"], available_slots)
        except ValueError:
            # Try to match time directly
            message_text = message_text.strip().upper()
            
            # Look for exact match
            if message_text in available_slots:
                selected_time = message_text
                
                # Store the selected time and move to barber selection
                state["step"] = "booking_barber"
                state["data"]["time"] = selected_time
                
                # Get available barbers
                barbers = list(data_service.get_barbers().values())
                active_barbers = [b for b in barbers if b.get("is_active", True)]
                
                if not active_barbers:
                    whatsapp_service.send_message(
                        phone_number,
                        "I'm sorry, we don't have any barbers available at the moment. Please try again later."
                    )
                    state["step"] = "idle"
                    return
                
                # Format barber selection message
                message = "Please select a barber by replying with their number:\n\n"
                
                for i, barber in enumerate(active_barbers, 1):
                    specialties = ", ".join(barber.get("specialties", []))
                    message += (
                        f"{i}. {barber['name']}\n"
                        f"   Specialties: {specialties if specialties else 'All services'}\n\n"
                    )
                
                state["data"]["barbers"] = active_barbers
                
                whatsapp_service.send_message(phone_number, message)
            else:
                whatsapp_service.send_message(
                    phone_number,
                    "I couldn't identify which time slot you want. Please reply with the slot number (e.g., '3')."
                )
                
                # Re-send available slots
                whatsapp_service.send_available_slots(phone_number, state["data"]["date"], available_slots)
    except Exception as e:
        logger.error(f"Error processing booking time: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error processing your time selection. Please try again."
        )

def process_booking_barber(phone_number, customer, message_text, state):
    """Process barber selection during booking"""
    try:
        barbers = state["data"].get("barbers", [])
        
        if not barbers:
            whatsapp_service.send_message(
                phone_number,
                "I'm sorry, we don't have any barbers available at the moment. Please try again later."
            )
            state["step"] = "idle"
            return
        
        # Try to parse barber number
        try:
            barber_num = int(message_text.strip())
            
            if 1 <= barber_num <= len(barbers):
                selected_barber = barbers[barber_num - 1]
                
                # Store the selected barber and move to confirmation
                state["step"] = "booking_confirmation"
                state["data"]["barber_id"] = selected_barber["id"]
                state["data"]["barber_name"] = selected_barber["name"]
                
                # Get service details
                service = data_service.get_service(state["data"]["service_id"])
                
                # Format confirmation message
                date_obj = datetime.strptime(state["data"]["date"], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
                
                message = (
                    f"Please confirm your appointment details:\n\n"
                    f"📅 Date: {formatted_date}\n"
                    f"⏰ Time: {state['data']['time']}\n"
                    f"💇 Service: {state['data']['service_name']}\n"
                    f"⏱️ Duration: {service['duration']} minutes\n"
                    f"💲 Price: ${service['price']}\n"
                    f"👨‍💼 Barber: {state['data']['barber_name']}\n\n"
                    f"Reply with 'CONFIRM' to book this appointment or 'CANCEL' to start over."
                )
                
                whatsapp_service.send_message(phone_number, message)
            else:
                whatsapp_service.send_message(
                    phone_number,
                    f"Invalid barber number. Please select a number between 1 and {len(barbers)}."
                )
                
                # Re-send barber options
                message = "Please select a barber by replying with their number:\n\n"
                
                for i, barber in enumerate(barbers, 1):
                    specialties = ", ".join(barber.get("specialties", []))
                    message += (
                        f"{i}. {barber['name']}\n"
                        f"   Specialties: {specialties if specialties else 'All services'}\n\n"
                    )
                
                whatsapp_service.send_message(phone_number, message)
        except ValueError:
            # Try to match barber name
            message_lower = message_text.lower().strip()
            matched_barber = None
            
            for barber in barbers:
                if message_lower in barber["name"].lower():
                    matched_barber = barber
                    break
            
            if matched_barber:
                # Store the selected barber and move to confirmation
                state["step"] = "booking_confirmation"
                state["data"]["barber_id"] = matched_barber["id"]
                state["data"]["barber_name"] = matched_barber["name"]
                
                # Get service details
                service = data_service.get_service(state["data"]["service_id"])
                
                # Format confirmation message
                date_obj = datetime.strptime(state["data"]["date"], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
                
                message = (
                    f"Please confirm your appointment details:\n\n"
                    f"📅 Date: {formatted_date}\n"
                    f"⏰ Time: {state['data']['time']}\n"
                    f"💇 Service: {state['data']['service_name']}\n"
                    f"⏱️ Duration: {service['duration']} minutes\n"
                    f"💲 Price: ${service['price']}\n"
                    f"👨‍💼 Barber: {state['data']['barber_name']}\n\n"
                    f"Reply with 'CONFIRM' to book this appointment or 'CANCEL' to start over."
                )
                
                whatsapp_service.send_message(phone_number, message)
            else:
                whatsapp_service.send_message(
                    phone_number,
                    "I couldn't identify which barber you want. Please reply with the barber number (e.g., '2')."
                )
                
                # Re-send barber options
                message = "Please select a barber by replying with their number:\n\n"
                
                for i, barber in enumerate(barbers, 1):
                    specialties = ", ".join(barber.get("specialties", []))
                    message += (
                        f"{i}. {barber['name']}\n"
                        f"   Specialties: {specialties if specialties else 'All services'}\n\n"
                    )
                
                whatsapp_service.send_message(phone_number, message)
    except Exception as e:
        logger.error(f"Error processing booking barber: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error processing your barber selection. Please try again."
        )

def process_booking_confirmation(phone_number, customer, message_upper, state):
    """Process appointment confirmation"""
    try:
        if message_upper == "CONFIRM":
            # Create appointment
            service = data_service.get_service(state["data"]["service_id"])
            
            appointment_data = {
                "customer_id": customer["id"],
                "barber_id": state["data"]["barber_id"],
                "service_id": state["data"]["service_id"],
                "date": state["data"]["date"],
                "time": state["data"]["time"],
                "duration": service["duration"],
                "status": "scheduled",
                "created_at": datetime.now().isoformat()
            }
            
            # Create the appointment
            created_appointment = data_service.create_appointment(appointment_data)
            
            if not created_appointment:
                whatsapp_service.send_message(
                    phone_number,
                    "I'm sorry, there was an error creating your appointment. Please try again later."
                )
                state["step"] = "idle"
                return
            
            # Send confirmation message
            whatsapp_service.send_appointment_confirmation(
                phone_number,
                customer["name"],
                state["data"]["date"],
                state["data"]["time"],
                state["data"]["service_name"],
                state["data"]["barber_name"]
            )
            
            # Reset conversation state
            state["step"] = "idle"
            state["data"] = {}
            
        elif message_upper == "CANCEL":
            whatsapp_service.send_message(
                phone_number,
                "Appointment booking cancelled. You can start over by sending 'BOOK' when you're ready."
            )
            
            # Reset conversation state
            state["step"] = "idle"
            state["data"] = {}
            
        else:
            whatsapp_service.send_message(
                phone_number,
                "Please reply with 'CONFIRM' to book the appointment or 'CANCEL' to start over."
            )
    except Exception as e:
        logger.error(f"Error processing booking confirmation: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error confirming your appointment. Please try again."
        )

def process_cancel_select(phone_number, customer, message_text, state):
    """Process appointment selection for cancellation"""
    try:
        appointments = state["data"].get("appointments", [])
        
        if not appointments:
            whatsapp_service.send_message(
                phone_number,
                "You don't have any upcoming appointments to cancel. Send 'BOOK' to schedule one."
            )
            state["step"] = "idle"
            return
        
        # Try to parse appointment number
        try:
            appt_num = int(message_text.strip())
            
            if 1 <= appt_num <= len(appointments):
                selected_appt_id, selected_appt = appointments[appt_num - 1]
                
                # Store the selected appointment and move to confirmation
                state["step"] = "cancel_confirmation"
                state["data"]["appointment_id"] = selected_appt_id
                
                # Get service and barber details
                service = data_service.get_service(selected_appt["service_id"])
                barber = data_service.get_barber(selected_appt["barber_id"])
                
                # Format confirmation message
                date_obj = datetime.strptime(selected_appt["date"], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
                
                message = (
                    f"Are you sure you want to cancel this appointment?\n\n"
                    f"📅 Date: {formatted_date}\n"
                    f"⏰ Time: {selected_appt['time']}\n"
                    f"💇 Service: {service['name'] if service else 'Unknown'}\n"
                    f"👨‍💼 Barber: {barber['name'] if barber else 'Unknown'}\n\n"
                    f"Reply with 'YES' to confirm cancellation or 'NO' to keep the appointment."
                )
                
                whatsapp_service.send_message(phone_number, message)
            else:
                whatsapp_service.send_message(
                    phone_number,
                    f"Invalid appointment number. Please select a number between 1 and {len(appointments)}."
                )
                
                # Re-send appointment options
                message = "Please select an appointment to cancel by replying with its number:\n\n"
                
                for i, (appt_id, appt) in enumerate(appointments, 1):
                    # Get service and barber details
                    service = data_service.get_service(appt["service_id"])
                    barber = data_service.get_barber(appt["barber_id"])
                    
                    message += (
                        f"{i}. {appt['date']} at {appt['time']}\n"
                        f"   Service: {service['name'] if service else 'Unknown'}\n"
                        f"   Barber: {barber['name'] if barber else 'Unknown'}\n\n"
                    )
                
                whatsapp_service.send_message(phone_number, message)
        except ValueError:
            whatsapp_service.send_message(
                phone_number,
                "Please reply with the appointment number you wish to cancel (e.g., '1')."
            )
            
            # Re-send appointment options
            message = "Please select an appointment to cancel by replying with its number:\n\n"
            
            for i, (appt_id, appt) in enumerate(appointments, 1):
                # Get service and barber details
                service = data_service.get_service(appt["service_id"])
                barber = data_service.get_barber(appt["barber_id"])
                
                message += (
                    f"{i}. {appt['date']} at {appt['time']}\n"
                    f"   Service: {service['name'] if service else 'Unknown'}\n"
                    f"   Barber: {barber['name'] if barber else 'Unknown'}\n\n"
                )
            
            whatsapp_service.send_message(phone_number, message)
    except Exception as e:
        logger.error(f"Error processing cancel select: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error processing your appointment selection. Please try again."
        )

def process_cancel_confirmation(phone_number, customer, message_upper, state):
    """Process appointment cancellation confirmation"""
    try:
        if message_upper in ["YES", "Y", "CONFIRM"]:
            appointment_id = state["data"].get("appointment_id")
            
            if not appointment_id:
                whatsapp_service.send_message(
                    phone_number,
                    "I'm sorry, I couldn't find the appointment you want to cancel. Please try again."
                )
                state["step"] = "idle"
                return
            
            # Get appointment details before cancellation for the message
            appointment = data_service.get_appointment(appointment_id)
            
            if not appointment:
                whatsapp_service.send_message(
                    phone_number,
                    "I'm sorry, I couldn't find the appointment you want to cancel. It may have already been cancelled."
                )
                state["step"] = "idle"
                return
            
            # Update appointment status to cancelled
            appointment["status"] = "cancelled"
            appointment["updated_at"] = datetime.now().isoformat()
            
            updated_appointment = data_service.update_appointment(appointment_id, appointment)
            
            if not updated_appointment:
                whatsapp_service.send_message(
                    phone_number,
                    "I'm sorry, there was an error cancelling your appointment. Please try again later."
                )
                state["step"] = "idle"
                return
            
            # Format confirmation message
            date_obj = datetime.strptime(appointment["date"], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            
            message = (
                f"Your appointment on {formatted_date} at {appointment['time']} has been cancelled.\n\n"
                f"You can book a new appointment any time by sending 'BOOK'."
            )
            
            whatsapp_service.send_message(phone_number, message)
            
            # Reset conversation state
            state["step"] = "idle"
            state["data"] = {}
            
        elif message_upper in ["NO", "N", "KEEP"]:
            whatsapp_service.send_message(
                phone_number,
                "Your appointment has not been cancelled and remains scheduled."
            )
            
            # Reset conversation state
            state["step"] = "idle"
            state["data"] = {}
            
        else:
            whatsapp_service.send_message(
                phone_number,
                "Please reply with 'YES' to confirm cancellation or 'NO' to keep the appointment."
            )
    except Exception as e:
        logger.error(f"Error processing cancel confirmation: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error cancelling your appointment. Please try again."
        )

def process_with_chatgpt(phone_number, customer, message_text, state):
    """Process message using ChatGPT for natural language understanding"""
    try:
        # Get conversation history
        history = state.get("history", [])
        
        # Process message with ChatGPT
        response = chatgpt_service.process_message(message_text, {"history": history})
        
        # Check if GPT has extracted any booking-related entities
        entities = response.get("entities", {})
        
        if (entities.get("service_type") or 
            entities.get("date") or 
            entities.get("time") or 
            entities.get("barber")):
            
            # Store extracted entities for potential future use
            if "extracted_entities" not in state["data"]:
                state["data"]["extracted_entities"] = {}
            
            state["data"]["extracted_entities"].update(entities)
            
            # If we have a service type, date, and time, we can suggest booking
            if entities.get("service_type") and entities.get("date") and entities.get("time"):
                # Append suggestion to the response
                response_text = response["text"]
                
                # Add suggestion to book
                response_text += (
                    f"\n\nIt looks like you want to book an appointment for a {entities['service_type']} "
                    f"on {entities['date']} at {entities['time']}. "
                    f"You can start the booking process by sending 'BOOK'."
                )
                
                # Send the response
                whatsapp_service.send_message(phone_number, response_text)
                
                # Add response to history
                if "history" not in state:
                    state["history"] = []
                
                state["history"].append({"role": "assistant", "content": response_text})
                return
        
        # Send the ChatGPT response
        whatsapp_service.send_message(phone_number, response["text"])
        
        # Add response to history
        if "history" not in state:
            state["history"] = []
        
        state["history"].append({"role": "assistant", "content": response["text"]})
        
    except Exception as e:
        logger.error(f"Error processing with ChatGPT: {str(e)}")
        whatsapp_service.send_message(
            phone_number,
            "I'm sorry, I encountered an error processing your message. Please try sending a simple command like 'HELP'."
        )

def get_available_slots(date, barber_id=None):
    """Get available time slots for a date"""
    try:
        # Get day of week
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = date_obj.strftime("%A").lower()
        
        # Define time slots based on business hours
        start_time = "09:00"
        end_time = "17:00"
        
        # Get barber's working hours if specified
        if barber_id:
            barber = data_service.get_barber(barber_id)
            if barber and 'working_hours' in barber and barber['working_hours'].get(day_of_week):
                hours = barber['working_hours'][day_of_week]
                if hours:
                    start_time = hours['start']
                    end_time = hours['end']
                else:
                    return {"data": {"slots": []}}
        
        # Generate time slots (30-minute intervals)
        slots = []
        current_time = datetime.strptime(start_time, "%H:%M")
        end_time_obj = datetime.strptime(end_time, "%H:%M")
        
        while current_time < end_time_obj:
            time_str = current_time.strftime("%H:%M")
            if data_service.check_availability(date, time_str, barber_id):
                slots.append(time_str)
            current_time += timedelta(minutes=30)
        
        return {"data": {"slots": slots}}
        
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        return {"data": {"slots": []}}
