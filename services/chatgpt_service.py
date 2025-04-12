"""
ChatGPT service for natural language processing using OpenAI API
"""
import os
import json
import logging
from datetime import datetime, timedelta
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_message(message, context=None):
    """
    Analyze a message using ChatGPT to determine intent and extract relevant information
    
    Args:
        message: Message content to analyze
        context: Optional dictionary with additional context (customer info, etc.)
        
    Returns:
        dict: Analysis results including intent and extracted data
    """
    try:
        # Define the system prompt with instructions
        system_prompt = """
        You are an assistant for a barber shop. Your job is to understand messages from customers 
        and identify their intent. Possible intents include:
        - booking: Customer wants to book an appointment
        - cancel: Customer wants to cancel an existing appointment
        - reschedule: Customer wants to reschedule an existing appointment
        - info: Customer is asking for information
        - greeting: Customer is just saying hello
        - other: Cannot determine the intent
        
        For booking, cancel, and reschedule intents, extract the following information if present:
        - date: Any mentioned date for the appointment
        - time: Any mentioned time for the appointment
        - service: Any mentioned service (haircut, beard trim, etc.)
        - barber: Any mentioned barber's name
        
        Format your response as a JSON object with the following structure:
        {
            "intent": "one of the intents listed above",
            "date": "extracted date or null",
            "time": "extracted time or null",
            "service": "extracted service or null",
            "barber": "extracted barber name or null",
            "needs_followup": true/false,
            "followup_question": "question to ask if more information is needed"
        }
        
        The response should be a valid JSON object, nothing else.
        """
        
        # Create the user message, including context if provided
        user_message = message
        if context:
            user_message += "\n\nContext: " + json.dumps(context)
        
        # Make API call to ChatGPT
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Message analysis result: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing message with ChatGPT: {str(e)}")
        # Return a default response in case of error
        return {
            "intent": "other",
            "date": None,
            "time": None,
            "service": None,
            "barber": None,
            "needs_followup": True,
            "followup_question": "I'm sorry, I'm having trouble understanding. Could you please rephrase your request?"
        }

def generate_response(analysis_result, customer_name=None, business_name=None):
    """
    Generate a natural language response based on the analysis result
    
    Args:
        analysis_result: Result from analyze_message function
        customer_name: Optional customer name to personalize the response
        business_name: Optional business name to include in the response
        
    Returns:
        str: Generated response text
    """
    try:
        # Define the system prompt with instructions
        system_prompt = """
        You are a friendly assistant for a barber shop. Your job is to respond to customer messages
        in a friendly, professional tone. Be concise but helpful.
        
        Use the following guidelines:
        - For booking requests: Confirm the details that were understood and ask for any missing information
        - For cancellation requests: Confirm the cancellation intent and request appointment details if missing
        - For reschedule requests: Confirm the reschedule intent and ask for new date/time if missing
        - For information requests: Provide relevant information or ask clarifying questions
        - For greetings: Respond with a warm welcome
        - For other intents: Offer general help options
        
        Keep responses under 100 words, friendly but professional.
        """
        
        # Create the context object for the API call
        context = {
            "analysis": analysis_result
        }
        
        if customer_name:
            context["customer_name"] = customer_name
            
        if business_name:
            context["business_name"] = business_name
            
        user_message = json.dumps(context)
        
        # Make API call to ChatGPT
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        # Get the generated response
        result = response.choices[0].message.content
        logger.info(f"Generated response: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Error generating response with ChatGPT: {str(e)}")
        # Return a default response in case of error
        if customer_name:
            return f"Hello {customer_name}, I'm sorry, I'm having trouble processing your request. Please call our shop directly for assistance."
        else:
            return "I'm sorry, I'm having trouble processing your request. Please call our shop directly for assistance."

def process_whatsapp_message(message, customer_info=None, business_name=None):
    """
    Process a WhatsApp message using ChatGPT to analyze and generate a response
    
    Args:
        message: The incoming message text
        customer_info: Optional dictionary with customer information
        business_name: Optional business name to include in the response
        
    Returns:
        dict: Processing result with analysis and response
    """
    try:
        # Analyze the message
        analysis = analyze_message(message, customer_info)
        
        # Generate a response
        customer_name = customer_info.get('name') if customer_info else None
        response_text = generate_response(analysis, customer_name, business_name)
        
        return {
            'status': 'success',
            'analysis': analysis,
            'response': response_text
        }
    except Exception as e:
        logger.error(f"Error processing WhatsApp message with ChatGPT: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }