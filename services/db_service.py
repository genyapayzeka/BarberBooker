"""
Database service for managing data storage and retrieval from PostgreSQL database
"""
import logging
from datetime import datetime
from models.database import db, Customer, Barber, Service, Appointment, ConversationState

logger = logging.getLogger(__name__)

def initialize():
    """Initialize database connection"""
    logger.info("Database service initialized")

# Customer operations
def get_customers():
    """Get all customers"""
    try:
        customers = Customer.query.all()
        return {customer.id: customer.to_dict() for customer in customers}
    except Exception as e:
        logger.error(f"Error getting customers: {str(e)}")
        return {}

def get_customer(customer_id):
    """Get a customer by ID"""
    try:
        customer = Customer.query.get(customer_id)
        if customer:
            return customer.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {str(e)}")
        return None

def get_customer_by_phone(phone):
    """Get a customer by phone number"""
    try:
        customer = Customer.query.filter_by(phone=phone).first()
        if customer:
            return customer.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting customer by phone {phone}: {str(e)}")
        return None

def create_customer(customer_data):
    """Create a new customer"""
    try:
        customer = Customer(
            name=customer_data.get('name'),
            phone=customer_data.get('phone'),
            email=customer_data.get('email'),
            notes=customer_data.get('notes'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return customer.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating customer: {str(e)}")
        return None

def update_customer(customer_id, customer_data):
    """Update an existing customer"""
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return None
        
        if 'name' in customer_data:
            customer.name = customer_data.get('name')
        if 'phone' in customer_data:
            customer.phone = customer_data.get('phone')
        if 'email' in customer_data:
            customer.email = customer_data.get('email')
        if 'notes' in customer_data:
            customer.notes = customer_data.get('notes')
        if 'last_visit' in customer_data:
            customer.last_visit = customer_data.get('last_visit')
        
        db.session.commit()
        
        return customer.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating customer {customer_id}: {str(e)}")
        return None

def delete_customer(customer_id):
    """Delete a customer"""
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return False
        
        db.session.delete(customer)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting customer {customer_id}: {str(e)}")
        return False

# Appointment operations
def get_appointments():
    """Get all appointments"""
    try:
        appointments = Appointment.query.all()
        return {appointment.id: appointment.to_dict() for appointment in appointments}
    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        return {}

def get_appointment(appointment_id):
    """Get an appointment by ID"""
    try:
        appointment = Appointment.query.get(appointment_id)
        if appointment:
            return appointment.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting appointment {appointment_id}: {str(e)}")
        return None

def get_appointments_by_customer(customer_id):
    """Get all appointments for a customer"""
    try:
        appointments = Appointment.query.filter_by(customer_id=customer_id).all()
        return {appointment.id: appointment.to_dict() for appointment in appointments}
    except Exception as e:
        logger.error(f"Error getting appointments for customer {customer_id}: {str(e)}")
        return {}

def get_appointments_by_date(date):
    """Get all appointments for a specific date"""
    try:
        appointments = Appointment.query.filter_by(date=date).all()
        return {appointment.id: appointment.to_dict() for appointment in appointments}
    except Exception as e:
        logger.error(f"Error getting appointments for date {date}: {str(e)}")
        return {}

def get_appointments_by_barber(barber_id):
    """Get all appointments for a barber"""
    try:
        appointments = Appointment.query.filter_by(barber_id=barber_id).all()
        return {appointment.id: appointment.to_dict() for appointment in appointments}
    except Exception as e:
        logger.error(f"Error getting appointments for barber {barber_id}: {str(e)}")
        return {}

def create_appointment(appointment_data):
    """Create a new appointment"""
    try:
        # Parse date string if needed
        date_str = appointment_data.get('date')
        date_obj = None
        if isinstance(date_str, str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        appointment = Appointment(
            customer_id=appointment_data.get('customer_id'),
            barber_id=appointment_data.get('barber_id'),
            service_id=appointment_data.get('service_id'),
            date=date_obj,
            time=appointment_data.get('time'),
            duration=appointment_data.get('duration'),
            status=appointment_data.get('status', 'scheduled'),
            notes=appointment_data.get('notes'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return appointment.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating appointment: {str(e)}")
        return None

def update_appointment(appointment_id, appointment_data):
    """Update an existing appointment"""
    try:
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        # Parse date string if needed
        if 'date' in appointment_data and isinstance(appointment_data['date'], str):
            appointment.date = datetime.strptime(appointment_data['date'], '%Y-%m-%d').date()
            
        if 'customer_id' in appointment_data:
            appointment.customer_id = appointment_data.get('customer_id')
        if 'barber_id' in appointment_data:
            appointment.barber_id = appointment_data.get('barber_id')
        if 'service_id' in appointment_data:
            appointment.service_id = appointment_data.get('service_id')
        if 'time' in appointment_data:
            appointment.time = appointment_data.get('time')
        if 'duration' in appointment_data:
            appointment.duration = appointment_data.get('duration')
        if 'status' in appointment_data:
            appointment.status = appointment_data.get('status')
        if 'notes' in appointment_data:
            appointment.notes = appointment_data.get('notes')
            
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return appointment.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
        return None

def delete_appointment(appointment_id):
    """Delete an appointment"""
    try:
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return False
        
        db.session.delete(appointment)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting appointment {appointment_id}: {str(e)}")
        return False

# Barber operations
def get_barbers():
    """Get all barbers"""
    try:
        barbers = Barber.query.all()
        return {barber.id: barber.to_dict() for barber in barbers}
    except Exception as e:
        logger.error(f"Error getting barbers: {str(e)}")
        return {}

def get_barber(barber_id):
    """Get a barber by ID"""
    try:
        barber = Barber.query.get(barber_id)
        if barber:
            return barber.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting barber {barber_id}: {str(e)}")
        return None

def create_barber(barber_data):
    """Create a new barber"""
    try:
        barber = Barber(
            name=barber_data.get('name'),
            email=barber_data.get('email'),
            phone=barber_data.get('phone'),
            bio=barber_data.get('bio'),
            specialties=barber_data.get('specialties'),
            working_hours=barber_data.get('working_hours'),
            profile_image=barber_data.get('profile_image'),
            is_active=barber_data.get('is_active', True),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(barber)
        db.session.commit()
        
        return barber.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating barber: {str(e)}")
        return None

def update_barber(barber_id, barber_data):
    """Update an existing barber"""
    try:
        barber = Barber.query.get(barber_id)
        if not barber:
            return None
        
        if 'name' in barber_data:
            barber.name = barber_data.get('name')
        if 'email' in barber_data:
            barber.email = barber_data.get('email')
        if 'phone' in barber_data:
            barber.phone = barber_data.get('phone')
        if 'bio' in barber_data:
            barber.bio = barber_data.get('bio')
        if 'specialties' in barber_data:
            barber.specialties = barber_data.get('specialties')
        if 'working_hours' in barber_data:
            barber.working_hours = barber_data.get('working_hours')
        if 'profile_image' in barber_data:
            barber.profile_image = barber_data.get('profile_image')
        if 'is_active' in barber_data:
            barber.is_active = barber_data.get('is_active')
            
        barber.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return barber.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating barber {barber_id}: {str(e)}")
        return None

def delete_barber(barber_id):
    """Delete a barber"""
    try:
        barber = Barber.query.get(barber_id)
        if not barber:
            return False
        
        db.session.delete(barber)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting barber {barber_id}: {str(e)}")
        return False

# Service operations
def get_services():
    """Get all services"""
    try:
        services = Service.query.all()
        return {service.id: service.to_dict() for service in services}
    except Exception as e:
        logger.error(f"Error getting services: {str(e)}")
        return {}

def get_service(service_id):
    """Get a service by ID"""
    try:
        service = Service.query.get(service_id)
        if service:
            return service.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting service {service_id}: {str(e)}")
        return None

def create_service(service_data):
    """Create a new service"""
    try:
        service = Service(
            name=service_data.get('name'),
            description=service_data.get('description'),
            price=service_data.get('price'),
            duration=service_data.get('duration'),
            category=service_data.get('category'),
            is_active=service_data.get('is_active', True),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(service)
        db.session.commit()
        
        return service.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating service: {str(e)}")
        return None

def update_service(service_id, service_data):
    """Update an existing service"""
    try:
        service = Service.query.get(service_id)
        if not service:
            return None
        
        if 'name' in service_data:
            service.name = service_data.get('name')
        if 'description' in service_data:
            service.description = service_data.get('description')
        if 'price' in service_data:
            service.price = service_data.get('price')
        if 'duration' in service_data:
            service.duration = service_data.get('duration')
        if 'category' in service_data:
            service.category = service_data.get('category')
        if 'is_active' in service_data:
            service.is_active = service_data.get('is_active')
            
        service.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return service.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating service {service_id}: {str(e)}")
        return None

def delete_service(service_id):
    """Delete a service"""
    try:
        service = Service.query.get(service_id)
        if not service:
            return False
        
        db.session.delete(service)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting service {service_id}: {str(e)}")
        return False

# Conversation state operations
def get_conversation_state(phone_number):
    """Get conversation state for a phone number"""
    try:
        state = ConversationState.query.get(phone_number)
        if state:
            return state.state
        return None
    except Exception as e:
        logger.error(f"Error getting conversation state for {phone_number}: {str(e)}")
        return None

def update_conversation_state(phone_number, state_data):
    """Update or create conversation state for a phone number"""
    try:
        state = ConversationState.query.get(phone_number)
        
        if state:
            state.state = state_data
            state.last_updated = datetime.utcnow()
        else:
            state = ConversationState(phone_number=phone_number, state=state_data)
            db.session.add(state)
            
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating conversation state for {phone_number}: {str(e)}")
        return False

def delete_conversation_state(phone_number):
    """Delete conversation state for a phone number"""
    try:
        state = ConversationState.query.get(phone_number)
        if not state:
            return False
        
        db.session.delete(state)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting conversation state for {phone_number}: {str(e)}")
        return False

# Availability checking
def check_availability(date, time, barber_id=None):
    """Check if a time slot is available"""
    try:
        # Convert date string to date object if needed
        date_obj = None
        if isinstance(date, str):
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            date_obj = date
            
        # Query for appointments at the same date and time
        query = Appointment.query.filter_by(date=date_obj, time=time, status='scheduled')
        
        # Filter by barber if specified
        if barber_id:
            query = query.filter_by(barber_id=barber_id)
            
        existing_appointments = query.count()
        
        # If barber specified, only one appointment can be scheduled at that time
        # If no barber specified, check if all barbers are booked
        if barber_id:
            return existing_appointments == 0
        else:
            barber_count = Barber.query.filter_by(is_active=True).count()
            return existing_appointments < barber_count
    except Exception as e:
        logger.error(f"Error checking availability for {date} at {time}: {str(e)}")
        return False