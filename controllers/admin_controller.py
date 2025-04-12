"""
Controller for admin-related routes and functions
"""
import logging
import os
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from datetime import datetime, timedelta
import json
import hashlib

from config import ADMIN_USERNAME, ADMIN_PASSWORD, SESSION_TIMEOUT, BUSINESS_NAME
from services import data_service, db_service
from utils import validators, helpers

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            return redirect(url_for('admin.login', next=request.url))
            
        # Check if session has expired
        if 'admin_last_activity' in session:
            last_activity = datetime.fromisoformat(session['admin_last_activity'])
            if datetime.now() - last_activity > timedelta(minutes=SESSION_TIMEOUT):
                session.pop('admin_logged_in', None)
                session.pop('admin_last_activity', None)
                flash('Session expired. Please log in again.', 'warning')
                return redirect(url_for('admin.login', next=request.url))
                
        # Update last activity
        session['admin_last_activity'] = datetime.now().isoformat()
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use password hashing)
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            session['admin_last_activity'] = datetime.now().isoformat()
            
            # Get next URL if provided, otherwise go to dashboard
            next_url = request.args.get('next') or url_for('admin.dashboard')
            return redirect(next_url)
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('admin/login.html', title='Admin Login', business_name=BUSINESS_NAME)

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    session.pop('admin_last_activity', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get counts for dashboard
    customers = db_service.get_customers()
    appointments = db_service.get_appointments()
    barbers = db_service.get_barbers()
    services = db_service.get_services()
    
    # Get upcoming appointments (next 7 days)
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    upcoming_appointments = {
        k: v for k, v in appointments.items() 
        if v.get('status') == 'scheduled' 
        and today <= datetime.strptime(v.get('date', '2000-01-01'), '%Y-%m-%d').date() <= next_week
    }
    
    # Sort upcoming appointments by date and time
    sorted_appointments = sorted(
        upcoming_appointments.items(),
        key=lambda x: (x[1].get('date', ''), x[1].get('time', ''))
    )
    
    # Group appointments by date for the calendar view
    calendar_appointments = {}
    for appt_id, appt in sorted_appointments:
        appt_date = appt.get('date')
        if appt_date not in calendar_appointments:
            calendar_appointments[appt_date] = []
        
        # Get customer, barber, and service details
        customer = data_service.get_customer(appt.get('customer_id', ''))
        barber = data_service.get_barber(appt.get('barber_id', ''))
        service = data_service.get_service(appt.get('service_id', ''))
        
        calendar_appointments[appt_date].append({
            'id': appt_id,
            'time': appt.get('time', ''),
            'customer_name': customer.get('name', 'Unknown') if customer else 'Unknown',
            'barber_name': barber.get('name', 'Unknown') if barber else 'Unknown',
            'service_name': service.get('name', 'Unknown') if service else 'Unknown',
        })
    
    # Get counts by status
    status_counts = {
        'scheduled': len([a for a in appointments.values() if a.get('status') == 'scheduled']),
        'completed': len([a for a in appointments.values() if a.get('status') == 'completed']),
        'cancelled': len([a for a in appointments.values() if a.get('status') == 'cancelled']),
        'no_show': len([a for a in appointments.values() if a.get('status') == 'no-show'])
    }
    
    return render_template(
        'admin/index.html',
        title='Admin Dashboard',
        business_name=BUSINESS_NAME,
        customer_count=len(customers),
        appointment_count=len(appointments),
        barber_count=len(barbers),
        service_count=len(services),
        upcoming_appointments=sorted_appointments[:10],  # Top 10 for dashboard
        calendar_appointments=calendar_appointments,
        status_counts=status_counts,
        today=today.strftime('%Y-%m-%d')
    )

@admin_bp.route('/appointments')
@admin_required
def appointments():
    """Admin appointments page"""
    # Get all appointments
    all_appointments = data_service.get_appointments()
    
    # Get filter parameters
    status = request.args.get('status')
    date = request.args.get('date')
    barber_id = request.args.get('barber_id')
    
    # Apply filters
    filtered_appointments = all_appointments
    if status:
        filtered_appointments = {k: v for k, v in filtered_appointments.items() if v.get('status') == status}
    if date:
        filtered_appointments = {k: v for k, v in filtered_appointments.items() if v.get('date') == date}
    if barber_id:
        filtered_appointments = {k: v for k, v in filtered_appointments.items() if v.get('barber_id') == barber_id}
    
    # Sort appointments by date (newest first)
    sorted_appointments = sorted(
        filtered_appointments.items(),
        key=lambda x: (x[1].get('date', ''), x[1].get('time', '')),
        reverse=True
    )
    
    # Prepare appointment data for display
    appointment_data = []
    for appt_id, appt in sorted_appointments:
        # Get customer, barber, and service details
        customer = data_service.get_customer(appt.get('customer_id', ''))
        barber = data_service.get_barber(appt.get('barber_id', ''))
        service = data_service.get_service(appt.get('service_id', ''))
        
        appointment_data.append({
            'id': appt_id,
            'date': appt.get('date', ''),
            'time': appt.get('time', ''),
            'status': appt.get('status', ''),
            'customer': customer,
            'barber': barber,
            'service': service,
            'created_at': appt.get('created_at', ''),
            'updated_at': appt.get('updated_at', '')
        })
    
    # Get barbers for filter
    barbers = data_service.get_barbers()
    
    return render_template(
        'admin/appointments.html',
        title='Manage Appointments',
        business_name=BUSINESS_NAME,
        appointments=appointment_data,
        barbers=barbers,
        current_status=status,
        current_date=date,
        current_barber_id=barber_id
    )

@admin_bp.route('/appointments/create', methods=['GET', 'POST'])
@admin_required
def create_appointment():
    """Create a new appointment"""
    if request.method == 'POST':
        # Get form data
        customer_id = request.form.get('customer_id')
        barber_id = request.form.get('barber_id')
        service_id = request.form.get('service_id')
        date = request.form.get('date')
        time = request.form.get('time')
        notes = request.form.get('notes', '')
        
        # Validate form data
        errors = []
        if not customer_id:
            errors.append("Customer is required")
        if not barber_id:
            errors.append("Barber is required")
        if not service_id:
            errors.append("Service is required")
        if not date:
            errors.append("Date is required")
        elif not validators.validate_date(date):
            errors.append("Invalid date format")
        if not time:
            errors.append("Time is required")
        elif not validators.validate_time(time):
            errors.append("Invalid time format")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.create_appointment'))
        
        # Check availability
        if not data_service.check_availability(date, time, barber_id):
            flash('This time slot is already booked. Please select a different time.', 'danger')
            return redirect(url_for('admin.create_appointment'))
        
        # Get service for duration
        service = data_service.get_service(service_id)
        if not service:
            flash('Invalid service selected', 'danger')
            return redirect(url_for('admin.create_appointment'))
        
        # Create appointment
        appointment_data = {
            'customer_id': customer_id,
            'barber_id': barber_id,
            'service_id': service_id,
            'date': date,
            'time': time,
            'duration': service.get('duration', 30),
            'status': 'scheduled',
            'notes': notes,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        created_appointment = data_service.create_appointment(appointment_data)
        
        if created_appointment:
            flash('Appointment created successfully', 'success')
            return redirect(url_for('admin.appointments'))
        else:
            flash('Failed to create appointment', 'danger')
            return redirect(url_for('admin.create_appointment'))
    
    # GET method - show form
    customers = data_service.get_customers()
    barbers = data_service.get_barbers()
    services = data_service.get_services()
    
    return render_template(
        'admin/appointments_form.html',
        title='Create Appointment',
        business_name=BUSINESS_NAME,
        customers=customers,
        barbers=barbers,
        services=services,
        appointment=None,
        action='create'
    )

@admin_bp.route('/appointments/edit/<appointment_id>', methods=['GET', 'POST'])
@admin_required
def edit_appointment(appointment_id):
    """Edit an existing appointment"""
    # Get appointment
    appointment = data_service.get_appointment(appointment_id)
    if not appointment:
        flash('Appointment not found', 'danger')
        return redirect(url_for('admin.appointments'))
    
    if request.method == 'POST':
        # Get form data
        customer_id = request.form.get('customer_id')
        barber_id = request.form.get('barber_id')
        service_id = request.form.get('service_id')
        date = request.form.get('date')
        time = request.form.get('time')
        status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        # Validate form data
        errors = []
        if not customer_id:
            errors.append("Customer is required")
        if not barber_id:
            errors.append("Barber is required")
        if not service_id:
            errors.append("Service is required")
        if not date:
            errors.append("Date is required")
        elif not validators.validate_date(date):
            errors.append("Invalid date format")
        if not time:
            errors.append("Time is required")
        elif not validators.validate_time(time):
            errors.append("Invalid time format")
        if not status:
            errors.append("Status is required")
        elif status not in ['scheduled', 'completed', 'cancelled', 'no-show']:
            errors.append("Invalid status")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.edit_appointment', appointment_id=appointment_id))
        
        # Check availability if date or time changed
        if (date != appointment.get('date') or time != appointment.get('time')) and not data_service.check_availability(date, time, barber_id):
            flash('This time slot is already booked. Please select a different time.', 'danger')
            return redirect(url_for('admin.edit_appointment', appointment_id=appointment_id))
        
        # Get service for duration
        service = data_service.get_service(service_id)
        if not service:
            flash('Invalid service selected', 'danger')
            return redirect(url_for('admin.edit_appointment', appointment_id=appointment_id))
        
        # Update appointment
        appointment_data = {
            'customer_id': customer_id,
            'barber_id': barber_id,
            'service_id': service_id,
            'date': date,
            'time': time,
            'duration': service.get('duration', 30),
            'status': status,
            'notes': notes,
            'updated_at': datetime.now().isoformat()
        }
        
        updated_appointment = data_service.update_appointment(appointment_id, appointment_data)
        
        if updated_appointment:
            flash('Appointment updated successfully', 'success')
            return redirect(url_for('admin.appointments'))
        else:
            flash('Failed to update appointment', 'danger')
            return redirect(url_for('admin.edit_appointment', appointment_id=appointment_id))
    
    # GET method - show form
    customers = data_service.get_customers()
    barbers = data_service.get_barbers()
    services = data_service.get_services()
    
    return render_template(
        'admin/appointments_form.html',
        title='Edit Appointment',
        business_name=BUSINESS_NAME,
        customers=customers,
        barbers=barbers,
        services=services,
        appointment=appointment,
        appointment_id=appointment_id,
        action='edit'
    )

@admin_bp.route('/appointments/delete/<appointment_id>', methods=['POST'])
@admin_required
def delete_appointment(appointment_id):
    """Delete an appointment"""
    # Get appointment
    appointment = data_service.get_appointment(appointment_id)
    if not appointment:
        flash('Appointment not found', 'danger')
        return redirect(url_for('admin.appointments'))
    
    # Delete appointment
    success = data_service.delete_appointment(appointment_id)
    
    if success:
        flash('Appointment deleted successfully', 'success')
    else:
        flash('Failed to delete appointment', 'danger')
    
    return redirect(url_for('admin.appointments'))

@admin_bp.route('/customers')
@admin_required
def customers():
    """Admin customers page"""
    # Get all customers
    all_customers = data_service.get_customers()
    
    # Sort customers by name
    sorted_customers = sorted(
        all_customers.items(),
        key=lambda x: x[1].get('name', '').lower()
    )
    
    return render_template(
        'admin/customers.html',
        title='Manage Customers',
        business_name=BUSINESS_NAME,
        customers=sorted_customers
    )

@admin_bp.route('/customers/create', methods=['GET', 'POST'])
@admin_required
def create_customer():
    """Create a new customer"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email', '')
        notes = request.form.get('notes', '')
        
        # Validate form data
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        if not phone:
            errors.append("Phone number is required")
        elif not validators.validate_phone(phone):
            errors.append("Invalid phone number format")
        if email and not validators.validate_email(email):
            errors.append("Invalid email format")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.create_customer'))
        
        # Check if customer with phone already exists
        existing_customer = data_service.get_customer_by_phone(phone)
        if existing_customer:
            flash('A customer with this phone number already exists', 'danger')
            return redirect(url_for('admin.create_customer'))
        
        # Create customer
        customer_data = {
            'name': name,
            'phone': phone,
            'email': email,
            'notes': notes,
            'created_at': datetime.now().isoformat()
        }
        
        created_customer = data_service.create_customer(customer_data)
        
        if created_customer:
            flash('Customer created successfully', 'success')
            return redirect(url_for('admin.customers'))
        else:
            flash('Failed to create customer', 'danger')
            return redirect(url_for('admin.create_customer'))
    
    # GET method - show form
    return render_template(
        'admin/customers_form.html',
        title='Create Customer',
        business_name=BUSINESS_NAME,
        customer=None,
        action='create'
    )

@admin_bp.route('/customers/edit/<customer_id>', methods=['GET', 'POST'])
@admin_required
def edit_customer(customer_id):
    """Edit an existing customer"""
    # Get customer
    customer = data_service.get_customer(customer_id)
    if not customer:
        flash('Customer not found', 'danger')
        return redirect(url_for('admin.customers'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email', '')
        notes = request.form.get('notes', '')
        
        # Validate form data
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        if not phone:
            errors.append("Phone number is required")
        elif not validators.validate_phone(phone):
            errors.append("Invalid phone number format")
        if email and not validators.validate_email(email):
            errors.append("Invalid email format")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.edit_customer', customer_id=customer_id))
        
        # Check if customer with phone already exists (other than this one)
        if phone != customer.get('phone'):
            existing_customer = data_service.get_customer_by_phone(phone)
            if existing_customer and existing_customer.get('id') != customer_id:
                flash('Another customer with this phone number already exists', 'danger')
                return redirect(url_for('admin.edit_customer', customer_id=customer_id))
        
        # Update customer
        customer_data = {
            'name': name,
            'phone': phone,
            'email': email,
            'notes': notes
        }
        
        updated_customer = data_service.update_customer(customer_id, customer_data)
        
        if updated_customer:
            flash('Customer updated successfully', 'success')
            return redirect(url_for('admin.customers'))
        else:
            flash('Failed to update customer', 'danger')
            return redirect(url_for('admin.edit_customer', customer_id=customer_id))
    
    # GET method - show form
    return render_template(
        'admin/customers_form.html',
        title='Edit Customer',
        business_name=BUSINESS_NAME,
        customer=customer,
        customer_id=customer_id,
        action='edit'
    )

@admin_bp.route('/customers/delete/<customer_id>', methods=['POST'])
@admin_required
def delete_customer(customer_id):
    """Delete a customer"""
    # Get customer
    customer = data_service.get_customer(customer_id)
    if not customer:
        flash('Customer not found', 'danger')
        return redirect(url_for('admin.customers'))
    
    # Check if customer has appointments
    appointments = data_service.get_appointments_by_customer(customer_id)
    if appointments:
        flash('Cannot delete customer with existing appointments. Please delete appointments first.', 'danger')
        return redirect(url_for('admin.customers'))
    
    # Delete customer
    success = data_service.delete_customer(customer_id)
    
    if success:
        flash('Customer deleted successfully', 'success')
    else:
        flash('Failed to delete customer', 'danger')
    
    return redirect(url_for('admin.customers'))

@admin_bp.route('/barbers')
@admin_required
def barbers():
    """Admin barbers page"""
    # Get all barbers
    all_barbers = data_service.get_barbers()
    
    # Sort barbers by name
    sorted_barbers = sorted(
        all_barbers.items(),
        key=lambda x: x[1].get('name', '').lower()
    )
    
    return render_template(
        'admin/barbers.html',
        title='Manage Barbers',
        business_name=BUSINESS_NAME,
        barbers=sorted_barbers
    )

@admin_bp.route('/barbers/create', methods=['GET', 'POST'])
@admin_required
def create_barber():
    """Create a new barber"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        bio = request.form.get('bio', '')
        specialties = request.form.getlist('specialties')
        is_active = 'is_active' in request.form
        
        # Working hours
        working_hours = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            start = request.form.get(f'{day}_start', '')
            end = request.form.get(f'{day}_end', '')
            is_working = request.form.get(f'{day}_working') == 'on'
            
            if is_working and start and end:
                working_hours[day] = {'start': start, 'end': end}
            else:
                working_hours[day] = None
        
        # Validate form data
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        if email and not validators.validate_email(email):
            errors.append("Invalid email format")
        if phone and not validators.validate_phone(phone):
            errors.append("Invalid phone number format")
        
        # Validate working hours
        for day, hours in working_hours.items():
            if hours:
                if not validators.validate_time(hours['start']):
                    errors.append(f"Invalid start time format for {day.capitalize()}")
                if not validators.validate_time(hours['end']):
                    errors.append(f"Invalid end time format for {day.capitalize()}")
                if hours['start'] >= hours['end']:
                    errors.append(f"End time must be after start time for {day.capitalize()}")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.create_barber'))
        
        # Create barber
        barber_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'bio': bio,
            'specialties': specialties,
            'working_hours': working_hours,
            'is_active': is_active,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        created_barber = data_service.create_barber(barber_data)
        
        if created_barber:
            flash('Barber created successfully', 'success')
            return redirect(url_for('admin.barbers'))
        else:
            flash('Failed to create barber', 'danger')
            return redirect(url_for('admin.create_barber'))
    
    # GET method - show form
    services = data_service.get_services()
    
    return render_template(
        'admin/barbers_form.html',
        title='Create Barber',
        business_name=BUSINESS_NAME,
        barber=None,
        services=services,
        action='create'
    )

@admin_bp.route('/barbers/edit/<barber_id>', methods=['GET', 'POST'])
@admin_required
def edit_barber(barber_id):
    """Edit an existing barber"""
    # Get barber
    barber = data_service.get_barber(barber_id)
    if not barber:
        flash('Barber not found', 'danger')
        return redirect(url_for('admin.barbers'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        bio = request.form.get('bio', '')
        specialties = request.form.getlist('specialties')
        is_active = 'is_active' in request.form
        
        # Working hours
        working_hours = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            start = request.form.get(f'{day}_start', '')
            end = request.form.get(f'{day}_end', '')
            is_working = request.form.get(f'{day}_working') == 'on'
            
            if is_working and start and end:
                working_hours[day] = {'start': start, 'end': end}
            else:
                working_hours[day] = None
        
        # Validate form data
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        if email and not validators.validate_email(email):
            errors.append("Invalid email format")
        if phone and not validators.validate_phone(phone):
            errors.append("Invalid phone number format")
        
        # Validate working hours
        for day, hours in working_hours.items():
            if hours:
                if not validators.validate_time(hours['start']):
                    errors.append(f"Invalid start time format for {day.capitalize()}")
                if not validators.validate_time(hours['end']):
                    errors.append(f"Invalid end time format for {day.capitalize()}")
                if hours['start'] >= hours['end']:
                    errors.append(f"End time must be after start time for {day.capitalize()}")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.edit_barber', barber_id=barber_id))
        
        # Update barber
        barber_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'bio': bio,
            'specialties': specialties,
            'working_hours': working_hours,
            'is_active': is_active,
            'updated_at': datetime.now().isoformat()
        }
        
        updated_barber = data_service.update_barber(barber_id, barber_data)
        
        if updated_barber:
            flash('Barber updated successfully', 'success')
            return redirect(url_for('admin.barbers'))
        else:
            flash('Failed to update barber', 'danger')
            return redirect(url_for('admin.edit_barber', barber_id=barber_id))
    
    # GET method - show form
    services = data_service.get_services()
    
    return render_template(
        'admin/barbers_form.html',
        title='Edit Barber',
        business_name=BUSINESS_NAME,
        barber=barber,
        barber_id=barber_id,
        services=services,
        action='edit'
    )

@admin_bp.route('/barbers/delete/<barber_id>', methods=['POST'])
@admin_required
def delete_barber(barber_id):
    """Delete a barber"""
    # Get barber
    barber = data_service.get_barber(barber_id)
    if not barber:
        flash('Barber not found', 'danger')
        return redirect(url_for('admin.barbers'))
    
    # Check if barber has appointments
    appointments = data_service.get_appointments_by_barber(barber_id)
    if appointments:
        flash('Cannot delete barber with existing appointments. Please delete appointments first.', 'danger')
        return redirect(url_for('admin.barbers'))
    
    # Delete barber
    success = data_service.delete_barber(barber_id)
    
    if success:
        flash('Barber deleted successfully', 'success')
    else:
        flash('Failed to delete barber', 'danger')
    
    return redirect(url_for('admin.barbers'))

@admin_bp.route('/services')
@admin_required
def services():
    """Admin services page"""
    # Get all services
    all_services = data_service.get_services()
    
    # Sort services by name
    sorted_services = sorted(
        all_services.items(),
        key=lambda x: x[1].get('name', '').lower()
    )
    
    return render_template(
        'admin/services.html',
        title='Manage Services',
        business_name=BUSINESS_NAME,
        services=sorted_services
    )

@admin_bp.route('/services/create', methods=['GET', 'POST'])
@admin_required
def create_service():
    """Create a new service"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        duration = request.form.get('duration')
        category = request.form.get('category', '')
        is_active = 'is_active' in request.form
        
        # Validate form data
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        
        try:
            price = float(price)
            if price < 0:
                errors.append("Price must be a non-negative number")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number")
        
        try:
            duration = int(duration)
            if duration <= 0:
                errors.append("Duration must be a positive number")
        except (ValueError, TypeError):
            errors.append("Duration must be a valid integer")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.create_service'))
        
        # Create service
        service_data = {
            'name': name,
            'description': description,
            'price': price,
            'duration': duration,
            'category': category,
            'is_active': is_active,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        created_service = data_service.create_service(service_data)
        
        if created_service:
            flash('Service created successfully', 'success')
            return redirect(url_for('admin.services'))
        else:
            flash('Failed to create service', 'danger')
            return redirect(url_for('admin.create_service'))
    
    # GET method - show form
    return render_template(
        'admin/services_form.html',
        title='Create Service',
        business_name=BUSINESS_NAME,
        service=None,
        action='create'
    )

@admin_bp.route('/services/edit/<service_id>', methods=['GET', 'POST'])
@admin_required
def edit_service(service_id):
    """Edit an existing service"""
    # Get service
    service = data_service.get_service(service_id)
    if not service:
        flash('Service not found', 'danger')
        return redirect(url_for('admin.services'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        price = request.form.get('price')
        duration = request.form.get('duration')
        category = request.form.get('category', '')
        is_active = 'is_active' in request.form
        
        # Validate form data
        errors = []
        if not name or len(name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        
        try:
            price = float(price)
            if price < 0:
                errors.append("Price must be a non-negative number")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number")
        
        try:
            duration = int(duration)
            if duration <= 0:
                errors.append("Duration must be a positive number")
        except (ValueError, TypeError):
            errors.append("Duration must be a valid integer")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('admin.edit_service', service_id=service_id))
        
        # Update service
        service_data = {
            'name': name,
            'description': description,
            'price': price,
            'duration': duration,
            'category': category,
            'is_active': is_active,
            'updated_at': datetime.now().isoformat()
        }
        
        updated_service = data_service.update_service(service_id, service_data)
        
        if updated_service:
            flash('Service updated successfully', 'success')
            return redirect(url_for('admin.services'))
        else:
            flash('Failed to update service', 'danger')
            return redirect(url_for('admin.edit_service', service_id=service_id))
    
    # GET method - show form
    return render_template(
        'admin/services_form.html',
        title='Edit Service',
        business_name=BUSINESS_NAME,
        service=service,
        service_id=service_id,
        action='edit'
    )

@admin_bp.route('/services/delete/<service_id>', methods=['POST'])
@admin_required
def delete_service(service_id):
    """Delete a service"""
    # Get service
    service = data_service.get_service(service_id)
    if not service:
        flash('Service not found', 'danger')
        return redirect(url_for('admin.services'))
    
    # Check if service has appointments
    appointments = data_service.get_appointments()
    service_appointments = {k: v for k, v in appointments.items() if v.get('service_id') == service_id}
    
    if service_appointments:
        flash('Cannot delete service with existing appointments. Please delete appointments first.', 'danger')
        return redirect(url_for('admin.services'))
    
    # Delete service
    success = data_service.delete_service(service_id)
    
    if success:
        flash('Service deleted successfully', 'success')
    else:
        flash('Failed to delete service', 'danger')
    
    return redirect(url_for('admin.services'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Admin settings page"""
    if request.method == 'POST':
        # Change admin password
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate passwords
        if current_password != ADMIN_PASSWORD:
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('admin.settings'))
        
        if not new_password or len(new_password) < 8:
            flash('New password must be at least 8 characters', 'danger')
            return redirect(url_for('admin.settings'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('admin.settings'))
        
        # In a real implementation, we would update the password in a database
        # Here we just show a success message
        flash('Password would be updated in a real implementation', 'success')
        return redirect(url_for('admin.settings'))
    
    # GET method - show form
    # Define business hours
    business_hours = {
        'monday': '9:00 AM - 6:00 PM',
        'tuesday': '9:00 AM - 6:00 PM',
        'wednesday': '9:00 AM - 6:00 PM',
        'thursday': '9:00 AM - 6:00 PM',
        'friday': '9:00 AM - 6:00 PM',
        'saturday': '10:00 AM - 4:00 PM',
        'sunday': 'Closed'
    }
    
    # Get API configuration status
    twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
    whatsapp_verify_token = os.environ.get('WHATSAPP_VERIFY_TOKEN')
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    # Generate the webhook URL for WhatsApp
    host_url = request.host_url.rstrip('/')
    webhook_url = f"{host_url}/webhook/whatsapp"
    
    # Get stats for system information
    customer_count = len(db_service.get_customers())
    appointment_count = len(db_service.get_appointments())
    barber_count = len(db_service.get_barbers())
    service_count = len(db_service.get_services())
    version = "1.0.0"  # App version
    data_dir = os.path.abspath('data')  # Data directory path
    
    return render_template(
        'admin/settings.html',
        title='Admin Settings',
        business_name=BUSINESS_NAME,
        business_hours=business_hours,
        twilio_account_sid=twilio_account_sid,
        twilio_auth_token=twilio_auth_token,
        twilio_phone_number=twilio_phone_number,
        whatsapp_verify_token=whatsapp_verify_token,
        openai_api_key=openai_api_key,
        webhook_url=webhook_url,
        customer_count=customer_count,
        appointment_count=appointment_count,
        barber_count=barber_count,
        service_count=service_count,
        version=version,
        data_dir=data_dir
    )

@admin_bp.route('/send-reminders', methods=['POST'])
@admin_required
def send_reminders():
    """Send appointment reminders"""
    try:
        # This would typically be handled by a scheduled task
        # But we provide a manual trigger for demonstration
        
        # Get appointments scheduled for today and tomorrow
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        today_str = today.strftime('%Y-%m-%d')
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        sent_count = 0
        error_count = 0
        appointments = db_service.get_appointments()
        
        # Check if WhatsApp integration is configured
        has_whatsapp = all([
            os.environ.get('TWILIO_ACCOUNT_SID'),
            os.environ.get('TWILIO_AUTH_TOKEN'),
            os.environ.get('TWILIO_PHONE_NUMBER')
        ])
        
        for appt_id, appt in appointments.items():
            if appt.get('status') == 'scheduled':
                appt_date = appt.get('date')
                
                # Only send reminders for today and tomorrow
                if appt_date == today_str or appt_date == tomorrow_str:
                    # Get customer, barber and service details
                    customer_id = appt.get('customer_id')
                    barber_id = appt.get('barber_id')
                    service_id = appt.get('service_id')
                    
                    customer = db_service.get_customer(customer_id)
                    barber = db_service.get_barber(barber_id)
                    service = db_service.get_service(service_id)
                    
                    if customer and barber and service:
                        # Calculate reminder hours
                        reminder_hours = 24 if appt_date == tomorrow_str else 2
                        
                        if has_whatsapp:
                            try:
                                # Import here to avoid circular imports
                                from services import whatsapp_service
                                
                                # Send WhatsApp reminder
                                result = whatsapp_service.send_appointment_reminder(
                                    customer_phone=customer.get('phone'),
                                    customer_name=customer.get('name'),
                                    appointment_date=appt_date,
                                    appointment_time=appt.get('time'),
                                    barber_name=barber.get('name'),
                                    service_name=service.get('name'),
                                    reminder_hours=reminder_hours
                                )
                                
                                if result.get('status') == 'success':
                                    sent_count += 1
                                    logger.info(f"Sent reminder for appointment {appt_id} to {customer.get('name')}")
                                else:
                                    error_count += 1
                                    logger.error(f"Failed to send reminder for appointment {appt_id}: {result.get('error')}")
                            except Exception as e:
                                error_count += 1
                                logger.error(f"Error sending WhatsApp reminder: {str(e)}")
                        else:
                            # WhatsApp not configured, just count them
                            sent_count += 1
                            logger.info(f"Would send reminder for appointment {appt_id} to {customer.get('name')} (WhatsApp not configured)")
        
        if error_count > 0:
            flash(f'Sent {sent_count} reminders with {error_count} errors. Check logs for details.', 'warning')
        elif sent_count > 0:
            flash(f'Successfully sent {sent_count} reminders for upcoming appointments', 'success')
        else:
            flash('No upcoming appointments found to send reminders', 'info')
    except Exception as e:
        logger.error(f"Error sending reminders: {str(e)}")
        flash(f'Error sending reminders: {str(e)}', 'danger')
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/check-availability', methods=['GET'])
@admin_required
def check_availability_ajax():
    """Check appointment availability (AJAX endpoint)"""
    date = request.args.get('date')
    time = request.args.get('time')
    barber_id = request.args.get('barber_id')
    
    if not date or not time:
        return jsonify({"status": "error", "message": "Date and time are required"}), 400
    
    # Validate date and time formats
    if not validators.validate_date(date):
        return jsonify({"status": "error", "message": "Invalid date format"}), 400
    
    if not validators.validate_time(time):
        return jsonify({"status": "error", "message": "Invalid time format"}), 400
    
    # Check availability
    is_available = db_service.check_availability(date, time, barber_id)
    
    return jsonify({
        "status": "success",
        "data": {"available": is_available}
    })

@admin_bp.route('/get-available-slots', methods=['GET'])
@admin_required
def get_available_slots_ajax():
    """Get available appointment slots (AJAX endpoint)"""
    date = request.args.get('date')
    barber_id = request.args.get('barber_id')
    
    if not date:
        return jsonify({"status": "error", "message": "Date is required"}), 400
    
    # Validate date format
    if not validators.validate_date(date):
        return jsonify({"status": "error", "message": "Invalid date format"}), 400
    
    # Get barber's working hours
    barber = None
    if barber_id:
        barber = db_service.get_barber(barber_id)
        if not barber:
            return jsonify({"status": "error", "message": "Barber not found"}), 404
    
    # Get day of week
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    day_of_week = date_obj.strftime("%A").lower()
    
    # Define time slots based on barber's working hours or business hours
    start_time = "09:00"
    end_time = "17:00"
    
    if barber and 'working_hours' in barber and barber['working_hours'].get(day_of_week):
        hours = barber['working_hours'][day_of_week]
        if hours:
            start_time = hours['start']
            end_time = hours['end']
        else:
            return jsonify({
                "status": "success", 
                "data": {"slots": [], "message": f"The barber is not available on {day_of_week.capitalize()}"}
            })
    
    # Generate time slots (30-minute intervals)
    slots = []
    current_time = datetime.strptime(start_time, "%H:%M")
    end_time_obj = datetime.strptime(end_time, "%H:%M")
    
    while current_time < end_time_obj:
        time_str = current_time.strftime("%H:%M")
        if db_service.check_availability(date, time_str, barber_id):
            slots.append(time_str)
        current_time += timedelta(minutes=30)
    
    return jsonify({
        "status": "success", 
        "data": {"slots": slots}
    })
