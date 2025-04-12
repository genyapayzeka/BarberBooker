"""
Validation utilities for the Barber Appointment System
"""
import re
from datetime import datetime

def validate_date(date_str):
    """
    Validate date in YYYY-MM-DD format
    
    Args:
        date_str: Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not date_str:
        return False
        
    # Check format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False
    
    # Check if it's a valid date
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time(time_str):
    """
    Validate time in 24-hour format (HH:MM)
    
    Args:
        time_str: Time string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not time_str:
        return False
        
    # Check format
    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', time_str):
        return False
    
    # Check if it's a valid time
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def validate_phone(phone):
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return False
    
    # Accept common formats including international
    # This is a basic validation, actual phone validation
    # should be more sophisticated in production
    return bool(re.match(r'^\+?[1-9]\d{1,14}$', phone))

def validate_email(email):
    """
    Validate email format
    
    Args:
        email: Email to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_name(name):
    """
    Validate name (not empty and minimum length)
    
    Args:
        name: Name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not name:
        return False
    
    # Name should be at least 2 characters
    return len(name.strip()) >= 2

def validate_appointment_status(status):
    """
    Validate appointment status
    
    Args:
        status: Status to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    valid_statuses = ['scheduled', 'completed', 'cancelled', 'no-show']
    return status in valid_statuses

def validate_working_hours(working_hours):
    """
    Validate working hours structure
    
    Args:
        working_hours: Working hours dictionary to validate
        
    Returns:
        (bool, list): (is_valid, error_messages)
    """
    if not isinstance(working_hours, dict):
        return False, ["Working hours must be a dictionary"]
    
    errors = []
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    # Check if all days are present
    for day in days_of_week:
        if day not in working_hours:
            errors.append(f"Missing day: {day}")
    
    # Check each day's hours
    for day, hours in working_hours.items():
        if day not in days_of_week:
            errors.append(f"Invalid day: {day}")
            continue
        
        # Hours can be None for off days
        if hours is None:
            continue
        
        # Hours should have start and end
        if not isinstance(hours, dict) or 'start' not in hours or 'end' not in hours:
            errors.append(f"Invalid hours format for {day}")
            continue
        
        # Validate start and end times
        if not validate_time(hours['start']):
            errors.append(f"Invalid start time for {day}: {hours['start']}")
        
        if not validate_time(hours['end']):
            errors.append(f"Invalid end time for {day}: {hours['end']}")
        
        # End time should be after start time
        if validate_time(hours['start']) and validate_time(hours['end']) and hours['start'] >= hours['end']:
            errors.append(f"End time must be after start time for {day}")
    
    return len(errors) == 0, errors

def validate_price(price):
    """
    Validate price value
    
    Args:
        price: Price to validate
        
    Returns:
        (bool, str): (is_valid, error_message)
    """
    try:
        price_float = float(price)
        if price_float < 0:
            return False, "Price must be a non-negative number"
        return True, None
    except (ValueError, TypeError):
        return False, "Price must be a valid number"

def validate_duration(duration):
    """
    Validate duration value
    
    Args:
        duration: Duration to validate
        
    Returns:
        (bool, str): (is_valid, error_message)
    """
    try:
        duration_int = int(duration)
        if duration_int <= 0:
            return False, "Duration must be a positive number"
        return True, None
    except (ValueError, TypeError):
        return False, "Duration must be a valid integer"

def validate_password(password):
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        (bool, str): (is_valid, error_message)
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for at least one uppercase, one lowercase, and one digit
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, None
