"""
ChatGPT service for natural language processing and generating responses
"""
import os
import json
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS, BUSINESS_NAME, BUSINESS_HOURS

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt template for the barber shop assistant
SYSTEM_PROMPT = f"""
You are a helpful virtual assistant for {BUSINESS_NAME}, a barber shop. Your role is to assist customers with booking appointments, providing information about services, 
and answering general questions about the business. Use a friendly, professional tone in your responses.

Business Information:
- Name: {BUSINESS_NAME}
- Business Hours: {json.dumps(BUSINESS_HOURS)}

Key functions you can help with:
1. Booking, rescheduling, or canceling appointments
2. Providing information about services and prices
3. Answering questions about barbers and their availability
4. Explaining business hours and location details
5. Handling general inquiries about the barber shop

Please respond to the customer's message in a helpful way. If they are trying to book an appointment, extract the relevant details like service type, 
preferred date/time, and preferred barber if mentioned. If they are requesting information, provide it clearly and concisely.

Important: Do not make up information. If you don't know something, acknowledge it and offer to connect them with a staff member who can help.
"""

def process_message(message, context=None):
    """
    Process a message using GPT-4o and generate a response
    
    Args:
        message: User's message text
        context: Optional dictionary with contextual information
        
    Returns:
        dict: Response with text and extracted entities
    """
    try:
        # Build the messages array for the API call
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add context messages if available
        if context and "history" in context:
            for msg in context["history"]:
                messages.append(msg)
        
        # Add the current user message
        messages.append({"role": "user", "content": message})
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=0.7,
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content
        
        # Extract entities for appointment booking
        entities = extract_entities(message)
        
        return {
            "text": response_text,
            "entities": entities
        }
        
    except Exception as e:
        logger.error(f"Error processing message with GPT-4o: {str(e)}")
        return {
            "text": "I'm sorry, I'm having trouble processing your request. Could you please try again or contact our staff directly?",
            "entities": {}
        }

def extract_entities(message):
    """
    Extract entities related to appointment booking from a message
    
    Args:
        message: User's message text
        
    Returns:
        dict: Extracted entities (service_type, date, time, barber)
    """
    try:
        # Call the OpenAI API with a specific prompt for entity extraction
        prompt = f"""
Extract the following entities from this message about booking a barber appointment, if present:
1. Service type (haircut, beard trim, etc.)
2. Date (in YYYY-MM-DD format)
3. Time (in HH:MM format, 24-hour)
4. Barber name

Message: "{message}"

Respond with a JSON object containing these keys: service_type, date, time, barber. 
Use null for any entity not found in the message.
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        entities = json.loads(response.choices[0].message.content)
        
        return entities
        
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        return {
            "service_type": None,
            "date": None,
            "time": None,
            "barber": None
        }

def generate_appointment_summary(appointment_data):
    """
    Generate a human-readable summary of an appointment
    
    Args:
        appointment_data: Dictionary with appointment details
        
    Returns:
        str: Human-readable appointment summary
    """
    try:
        prompt = f"""
Generate a brief, friendly summary of this barber appointment:
- Customer: {appointment_data.get('customer_name')}
- Date: {appointment_data.get('date')}
- Time: {appointment_data.get('time')}
- Service: {appointment_data.get('service_name')}
- Barber: {appointment_data.get('barber_name')}

Keep it concise but personable.
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating appointment summary: {str(e)}")
        return f"Appointment for {appointment_data.get('customer_name')} on {appointment_data.get('date')} at {appointment_data.get('time')} with {appointment_data.get('barber_name')} for a {appointment_data.get('service_name')}."
