"""
Logging utility for the Barber Appointment System
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Configure a logger with specified name, log file, and level
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log file is provided
    if log_file:
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create rotating file handler (max 10MB per file, keep 10 backup files)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_request(logger, request, level=logging.DEBUG):
    """
    Log details of a Flask request
    
    Args:
        logger: Logger instance
        request: Flask request object
        level: Logging level for the request
    """
    logger.log(
        level,
        f"Request: {request.method} {request.url} - "
        f"Headers: {dict(request.headers)} - "
        f"Data: {request.get_data(as_text=True)}"
    )

def log_response(logger, response, level=logging.DEBUG):
    """
    Log details of a Flask response
    
    Args:
        logger: Logger instance
        response: Flask response object
        level: Logging level for the response
    """
    logger.log(
        level,
        f"Response: {response.status_code} - "
        f"Headers: {dict(response.headers)} - "
        f"Data: {response.get_data(as_text=True)}"
    )

def log_error(logger, error, additional_info=None):
    """
    Log an error with additional context information
    
    Args:
        logger: Logger instance
        error: Exception object
        additional_info: Additional context information (optional)
    """
    error_message = f"Error: {type(error).__name__} - {str(error)}"
    
    if additional_info:
        error_message += f" - Context: {additional_info}"
    
    logger.error(error_message, exc_info=True)

def log_appointment_activity(logger, action, appointment_id, details=None):
    """
    Log appointment-related activity
    
    Args:
        logger: Logger instance
        action: Action performed (create, update, cancel, etc.)
        appointment_id: ID of the affected appointment
        details: Additional details about the activity (optional)
    """
    message = f"Appointment {action}: ID={appointment_id}"
    
    if details:
        message += f" - Details: {details}"
    
    logger.info(message)

def log_customer_activity(logger, action, customer_id, details=None):
    """
    Log customer-related activity
    
    Args:
        logger: Logger instance
        action: Action performed (create, update, delete, etc.)
        customer_id: ID of the affected customer
        details: Additional details about the activity (optional)
    """
    message = f"Customer {action}: ID={customer_id}"
    
    if details:
        message += f" - Details: {details}"
    
    logger.info(message)

def log_whatsapp_message(logger, direction, phone_number, message_content, message_id=None):
    """
    Log WhatsApp message activity
    
    Args:
        logger: Logger instance
        direction: Message direction ('incoming' or 'outgoing')
        phone_number: Customer's phone number
        message_content: Content of the message
        message_id: Message ID (optional)
    """
    message = f"WhatsApp {direction} message: To/From={phone_number}"
    
    if message_id:
        message += f" - Message ID={message_id}"
    
    # Truncate message content if too long
    if len(message_content) > 100:
        truncated_content = message_content[:97] + "..."
        message += f" - Content: {truncated_content}"
    else:
        message += f" - Content: {message_content}"
    
    logger.info(message)
