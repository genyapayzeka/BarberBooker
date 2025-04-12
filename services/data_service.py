"""
Data service for managing data storage and retrieval from JSON files
"""
import json
import os
import logging
import time
import threading
from config import CUSTOMERS_FILE, APPOINTMENTS_FILE, BARBERS_FILE, SERVICES_FILE

logger = logging.getLogger(__name__)

# In-memory cache for data
_data_cache = {
    "customers": {},
    "appointments": {},
    "barbers": {},
    "services": {}
}

# File locks to prevent concurrent writes
_file_locks = {
    CUSTOMERS_FILE: threading.Lock(),
    APPOINTMENTS_FILE: threading.Lock(),
    BARBERS_FILE: threading.Lock(),
    SERVICES_FILE: threading.Lock()
}

def initialize():
    """Initialize data files if they don't exist"""
    files = {
        CUSTOMERS_FILE: {"customers": {}},
        APPOINTMENTS_FILE: {"appointments": {}},
        BARBERS_FILE: {"barbers": {}},
        SERVICES_FILE: {"services": {}}
    }
    
    for file_path, default_data in files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=2)
            logger.info(f"Created data file: {file_path}")
        else:
            # Load existing data into cache
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if file_path == CUSTOMERS_FILE:
                        _data_cache["customers"] = data.get("customers", {})
                    elif file_path == APPOINTMENTS_FILE:
                        _data_cache["appointments"] = data.get("appointments", {})
                    elif file_path == BARBERS_FILE:
                        _data_cache["barbers"] = data.get("barbers", {})
                    elif file_path == SERVICES_FILE:
                        _data_cache["services"] = data.get("services", {})
            except json.JSONDecodeError:
                logger.error(f"Error parsing JSON in {file_path}, creating new file")
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=2)
            except Exception as e:
                logger.error(f"Error loading data from {file_path}: {str(e)}")

def _read_file(file_path):
    """Read data from JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return {}

def _write_file(file_path, data):
    """Write data to JSON file with locking for thread safety"""
    with _file_locks[file_path]:
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {str(e)}")
            return False

# Customer CRUD operations
def get_customers():
    """Get all customers"""
    return _data_cache["customers"]

def get_customer(customer_id):
    """Get a customer by ID"""
    return _data_cache["customers"].get(customer_id)

def get_customer_by_phone(phone):
    """Get a customer by phone number"""
    for cust_id, customer in _data_cache["customers"].items():
        if customer.get("phone") == phone:
            return customer
    return None

def create_customer(customer_data):
    """Create a new customer"""
    # Generate a new ID
    customer_id = str(int(time.time() * 1000))
    customer_data["id"] = customer_id
    
    # Add to cache
    _data_cache["customers"][customer_id] = customer_data
    
    # Save to file
    file_data = {"customers": _data_cache["customers"]}
    if _write_file(CUSTOMERS_FILE, file_data):
        return customer_data
    return None

def update_customer(customer_id, customer_data):
    """Update an existing customer"""
    if customer_id not in _data_cache["customers"]:
        return None
    
    # Update cache
    _data_cache["customers"][customer_id].update(customer_data)
    
    # Save to file
    file_data = {"customers": _data_cache["customers"]}
    if _write_file(CUSTOMERS_FILE, file_data):
        return _data_cache["customers"][customer_id]
    return None

def delete_customer(customer_id):
    """Delete a customer"""
    if customer_id not in _data_cache["customers"]:
        return False
    
    # Remove from cache
    del _data_cache["customers"][customer_id]
    
    # Save to file
    file_data = {"customers": _data_cache["customers"]}
    return _write_file(CUSTOMERS_FILE, file_data)

# Appointment CRUD operations
def get_appointments():
    """Get all appointments"""
    return _data_cache["appointments"]

def get_appointment(appointment_id):
    """Get an appointment by ID"""
    return _data_cache["appointments"].get(appointment_id)

def get_appointments_by_customer(customer_id):
    """Get all appointments for a customer"""
    return {
        appt_id: appt for appt_id, appt in _data_cache["appointments"].items()
        if appt.get("customer_id") == customer_id
    }

def get_appointments_by_date(date):
    """Get all appointments for a specific date"""
    return {
        appt_id: appt for appt_id, appt in _data_cache["appointments"].items()
        if appt.get("date") == date
    }

def get_appointments_by_barber(barber_id):
    """Get all appointments for a barber"""
    return {
        appt_id: appt for appt_id, appt in _data_cache["appointments"].items()
        if appt.get("barber_id") == barber_id
    }

def create_appointment(appointment_data):
    """Create a new appointment"""
    # Generate a new ID
    appointment_id = str(int(time.time() * 1000))
    appointment_data["id"] = appointment_id
    
    # Add to cache
    _data_cache["appointments"][appointment_id] = appointment_data
    
    # Save to file
    file_data = {"appointments": _data_cache["appointments"]}
    if _write_file(APPOINTMENTS_FILE, file_data):
        return appointment_data
    return None

def update_appointment(appointment_id, appointment_data):
    """Update an existing appointment"""
    if appointment_id not in _data_cache["appointments"]:
        return None
    
    # Update cache
    _data_cache["appointments"][appointment_id].update(appointment_data)
    
    # Save to file
    file_data = {"appointments": _data_cache["appointments"]}
    if _write_file(APPOINTMENTS_FILE, file_data):
        return _data_cache["appointments"][appointment_id]
    return None

def delete_appointment(appointment_id):
    """Delete an appointment"""
    if appointment_id not in _data_cache["appointments"]:
        return False
    
    # Remove from cache
    del _data_cache["appointments"][appointment_id]
    
    # Save to file
    file_data = {"appointments": _data_cache["appointments"]}
    return _write_file(APPOINTMENTS_FILE, file_data)

# Barber CRUD operations
def get_barbers():
    """Get all barbers"""
    return _data_cache["barbers"]

def get_barber(barber_id):
    """Get a barber by ID"""
    return _data_cache["barbers"].get(barber_id)

def create_barber(barber_data):
    """Create a new barber"""
    # Generate a new ID
    barber_id = str(int(time.time() * 1000))
    barber_data["id"] = barber_id
    
    # Add to cache
    _data_cache["barbers"][barber_id] = barber_data
    
    # Save to file
    file_data = {"barbers": _data_cache["barbers"]}
    if _write_file(BARBERS_FILE, file_data):
        return barber_data
    return None

def update_barber(barber_id, barber_data):
    """Update an existing barber"""
    if barber_id not in _data_cache["barbers"]:
        return None
    
    # Update cache
    _data_cache["barbers"][barber_id].update(barber_data)
    
    # Save to file
    file_data = {"barbers": _data_cache["barbers"]}
    if _write_file(BARBERS_FILE, file_data):
        return _data_cache["barbers"][barber_id]
    return None

def delete_barber(barber_id):
    """Delete a barber"""
    if barber_id not in _data_cache["barbers"]:
        return False
    
    # Remove from cache
    del _data_cache["barbers"][barber_id]
    
    # Save to file
    file_data = {"barbers": _data_cache["barbers"]}
    return _write_file(BARBERS_FILE, file_data)

# Service CRUD operations
def get_services():
    """Get all services"""
    return _data_cache["services"]

def get_service(service_id):
    """Get a service by ID"""
    return _data_cache["services"].get(service_id)

def create_service(service_data):
    """Create a new service"""
    # Generate a new ID
    service_id = str(int(time.time() * 1000))
    service_data["id"] = service_id
    
    # Add to cache
    _data_cache["services"][service_id] = service_data
    
    # Save to file
    file_data = {"services": _data_cache["services"]}
    if _write_file(SERVICES_FILE, file_data):
        return service_data
    return None

def update_service(service_id, service_data):
    """Update an existing service"""
    if service_id not in _data_cache["services"]:
        return None
    
    # Update cache
    _data_cache["services"][service_id].update(service_data)
    
    # Save to file
    file_data = {"services": _data_cache["services"]}
    if _write_file(SERVICES_FILE, file_data):
        return _data_cache["services"][service_id]
    return None

def delete_service(service_id):
    """Delete a service"""
    if service_id not in _data_cache["services"]:
        return False
    
    # Remove from cache
    del _data_cache["services"][service_id]
    
    # Save to file
    file_data = {"services": _data_cache["services"]}
    return _write_file(SERVICES_FILE, file_data)

def check_availability(date, time, barber_id=None):
    """Check if a time slot is available"""
    # Get all appointments for the date
    appointments = get_appointments_by_date(date)
    
    # Filter by barber if specified
    if barber_id:
        appointments = {
            appt_id: appt for appt_id, appt in appointments.items()
            if appt.get("barber_id") == barber_id
        }
    
    # Check if the time slot is already booked
    for appt_id, appt in appointments.items():
        if appt.get("time") == time:
            if barber_id and appt.get("barber_id") != barber_id:
                continue
            return False
    
    return True
