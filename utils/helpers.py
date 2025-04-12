"""
Helper utilities for the Barber Appointment System
"""
import json
import re
from datetime import datetime, timedelta
import time
import pytz

def format_date(date_str, input_format='%Y-%m-%d', output_format='%A, %B %d, %Y'):
    """
    Format a date string from one format to another
    
    Args:
        date_str: Date string to format
        input_format: Input date format
        output_format: Output date format
        
    Returns:
        str: Formatted date string
    """
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except (ValueError, TypeError):
        return date_str

def format_time(time_str, input_format='%H:%M', output_format='%I:%M %p'):
    """
    Format a time string from 24-hour to 12-hour format
    
    Args:
        time_str: Time string to format
        input_format: Input time format
        output_format: Output time format
        
    Returns:
        str: Formatted time string
    """
    try:
        time_obj = datetime.strptime(time_str, input_format)
        return time_obj.strftime(output_format)
    except (ValueError, TypeError):
        return time_str

def generate_id():
    """
    Generate a unique ID based on timestamp
    
    Returns:
        str: Unique ID
    """
    return str(int(time.time() * 1000))

def format_phone(phone):
    """
    Format a phone number for display
    
    Args:
        phone: Phone number to format
        
    Returns:
        str: Formatted phone number
    """
    if not phone:
        return ""
    
    # Strip non-numeric characters
    clean_phone = re.sub(r'\D', '', phone)
    
    # Format based on length (US numbers)
    if len(clean_phone) == 10:
        return f"({clean_phone[:3]}) {clean_phone[3:6]}-{clean_phone[6:]}"
    elif len(clean_phone) == 11 and clean_phone.startswith('1'):
        return f"+1 ({clean_phone[1:4]}) {clean_phone[4:7]}-{clean_phone[7:]}"
    elif clean_phone.startswith('+'):
        return phone  # Keep international format as is
    else:
        return phone  # Return original if we can't format it

def sanitize_phone(phone):
    """
    Sanitize phone number for storage (strip formatting)
    
    Args:
        phone: Phone number to sanitize
        
    Returns:
        str: Sanitized phone number
    """
    if not phone:
        return ""
    
    # Keep only digits and the plus sign for international numbers
    return re.sub(r'[^\d+]', '', phone)

def get_day_of_week(date_str):
    """
    Get day of week from a date string
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        str: Day of week (lowercase)
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%A').lower()
    except (ValueError, TypeError):
        return None

def get_next_business_days(num_days=7, exclude_days=None):
    """
    Get a list of the next business days
    
    Args:
        num_days: Number of days to return
        exclude_days: List of days to exclude (e.g. ['sunday'])
        
    Returns:
        list: List of date strings in YYYY-MM-DD format
    """
    if exclude_days is None:
        exclude_days = ['sunday']
    
    days = []
    current_date = datetime.now().date()
    
    while len(days) < num_days:
        current_date += timedelta(days=1)
        day_name = current_date.strftime('%A').lower()
        
        if day_name not in exclude_days:
            days.append(current_date.strftime('%Y-%m-%d'))
    
    return days

def mask_phone_partial(phone):
    """
    Partially mask a phone number for privacy
    
    Args:
        phone: Phone number to mask
        
    Returns:
        str: Masked phone number
    """
    if not phone:
        return ""
    
    # Strip non-numeric characters
    clean_phone = re.sub(r'\D', '', phone)
    
    # Keep first 3 and last 2 digits visible
    if len(clean_phone) > 5:
        visible_chars = 5
        masked_length = max(0, len(clean_phone) - visible_chars)
        return clean_phone[:3] + '*' * masked_length + clean_phone[-2:]
    else:
        return phone  # Too short to mask effectively

def parse_duration_to_minutes(duration_str):
    """
    Parse a duration string to minutes
    
    Args:
        duration_str: Duration string (e.g., "1h 30m", "45m")
        
    Returns:
        int: Duration in minutes
    """
    try:
        hours = 0
        minutes = 0
        
        # Extract hours
        hour_match = re.search(r'(\d+)h', duration_str)
        if hour_match:
            hours = int(hour_match.group(1))
        
        # Extract minutes
        minute_match = re.search(r'(\d+)m', duration_str)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        # If no pattern matched but it's just a number, assume minutes
        if not hour_match and not minute_match and duration_str.isdigit():
            minutes = int(duration_str)
        
        return hours * 60 + minutes
    except (ValueError, TypeError, AttributeError):
        return 0

def format_minutes_to_duration(minutes):
    """
    Format minutes to a readable duration
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        str: Formatted duration
    """
    try:
        minutes = int(minutes)
        if minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours > 1 else ''} {remaining_minutes} min"
    except (ValueError, TypeError):
        return f"{minutes} min"

def calculate_end_time(start_time, duration_minutes):
    """
    Calculate the end time given a start time and duration
    
    Args:
        start_time: Start time in 24-hour format (HH:MM)
        duration_minutes: Duration in minutes
        
    Returns:
        str: End time in 24-hour format
    """
    try:
        start_time_obj = datetime.strptime(start_time, '%H:%M')
        end_time_obj = start_time_obj + timedelta(minutes=duration_minutes)
        return end_time_obj.strftime('%H:%M')
    except (ValueError, TypeError):
        return None

def is_appointment_overlapping(start_time1, duration1, start_time2, duration2):
    """
    Check if two appointments overlap
    
    Args:
        start_time1: Start time of first appointment (HH:MM)
        duration1: Duration of first appointment in minutes
        start_time2: Start time of second appointment (HH:MM)
        duration2: Duration of second appointment in minutes
        
    Returns:
        bool: True if appointments overlap, False otherwise
    """
    try:
        start1 = datetime.strptime(start_time1, '%H:%M')
        end1 = start1 + timedelta(minutes=duration1)
        
        start2 = datetime.strptime(start_time2, '%H:%M')
        end2 = start2 + timedelta(minutes=duration2)
        
        return start1 < end2 and start2 < end1
    except (ValueError, TypeError):
        return False

def truncate_text(text, max_length=100, suffix='...'):
    """
    Truncate text to a maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_currency(amount):
    """
    Format a number as currency
    
    Args:
        amount: Amount to format
        
    Returns:
        str: Formatted currency string
    """
    try:
        return f"${float(amount):.2f}"
    except (ValueError, TypeError):
        return f"${amount}"

def clean_json(json_str):
    """
    Clean invalid JSON string
    
    Args:
        json_str: Potentially invalid JSON string
        
    Returns:
        str: Cleaned JSON string
    """
    try:
        # Try to parse the JSON
        parsed = json.loads(json_str)
        # If it parses, return the original string
        return json_str
    except json.JSONDecodeError:
        # Remove common problems like trailing commas and unquoted keys
        cleaned = re.sub(r',\s*}', '}', json_str)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        # Try to fix unquoted keys
        cleaned = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', cleaned)
        
        # Replace single quotes with double quotes
        cleaned = cleaned.replace("'", '"')
        
        return cleaned
