"""
Controller for appointment-related routes and functions
"""
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime, timedelta
import json

from models.appointment import Appointment
from services import data_service, whatsapp_service
from utils import validators

logger = logging.getLogger(__name__)

# Create blueprint
appointment_bp = Blueprint('appointment', __name__, url_prefix='/api/appointments')

@appointment_bp.route('/', methods=['GET'])
def get_appointments():
    """Get all appointments or filter by query parameters"""
    try:
        # Get query parameters
        customer_id = request.args.get('customer_id')
        barber_id = request.args.get('barber_id')
        date = request.args.get('date')
        status = request.args.get('status')
        
        # Get all appointments
        appointments = data_service.get_appointments()
        
        # Apply filters if provided
        if customer_id:
            appointments = {k: v for k, v in appointments.items() if v.get('customer_id') == customer_id}
        if barber_id:
            appointments = {k: v for k, v in appointments.items() if v.get('barber_id') == barber_id}
        if date:
            appointments = {k: v for k, v in appointments.items() if v.get('date') == date}
        if status:
            appointments = {k: v for k, v in appointments.items() if v.get('status') == status}
        
        return jsonify({"status": "success", "data": appointments})
        
    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@appointment_bp.route('/<appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    """Get a specific appointment by ID"""
    try:
        appointment = data_service.get_appointment(appointment_id)
        
        if not appointment:
            return jsonify({"status": "error", "message": "Appointment not found"}), 404
            
        return jsonify({"status": "success", "data": appointment})
        
    except Exception as e:
        logger.error(f"Error getting appointment {appointment_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@appointment_bp.route('/', methods=['POST'])
def create_appointment():
    """Create a new appointment"""
    try:
        data = request.json
        
        # Create an Appointment object for validation
        appointment = Appointment(
            customer_id=data.get('customer_id'),
            barber_id=data.get('barber_id'),
            service_id=data.get('service_id'),
            date=data.get('date'),
            time=data.get('time'),
            duration=data.get('duration'),
            notes=data.get('notes')
        )
        
        # Validate appointment data
        errors = appointment.validate()
        if errors:
            return jsonify({"status": "error", "message": errors}), 400
        
        # Check availability
        if not data_service.check_availability(data.get('date'), data.get('time'), data.get('barber_id')):
            return jsonify({
                "status": "error", 
                "message": "This time slot is already booked. Please select a different time."
            }), 409
        
        # Create the appointment
        created_appointment = data_service.create_appointment(appointment.to_dict())
        
        if not created_appointment:
            return jsonify({"status": "error", "message": "Failed to create appointment"}), 500
        
        # Send confirmation to customer if phone is provided
        customer = data_service.get_customer(data.get('customer_id'))
        barber = data_service.get_barber(data.get('barber_id'))
        service = data_service.get_service(data.get('service_id'))
        
        if customer and 'phone' in customer and service and barber:
            whatsapp_service.send_appointment_confirmation(
                customer['phone'],
                customer['name'],
                data.get('date'),
                data.get('time'),
                service['name'],
                barber['name']
            )
        
        return jsonify({"status": "success", "data": created_appointment}), 201
        
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@appointment_bp.route('/<appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    """Update an existing appointment"""
    try:
        data = request.json
        existing_appointment = data_service.get_appointment(appointment_id)
        
        if not existing_appointment:
            return jsonify({"status": "error", "message": "Appointment not found"}), 404
        
        # Merge existing data with updates
        updated_data = {**existing_appointment, **data}
        
        # Create an Appointment object for validation
        appointment = Appointment.from_dict(updated_data)
        appointment.updated_at = datetime.now().isoformat()
        
        # Validate appointment data
        errors = appointment.validate()
        if errors:
            return jsonify({"status": "error", "message": errors}), 400
        
        # Check availability if date or time changed
        if (data.get('date') and data.get('date') != existing_appointment.get('date')) or \
           (data.get('time') and data.get('time') != existing_appointment.get('time')):
            if not data_service.check_availability(
                updated_data.get('date'), 
                updated_data.get('time'), 
                updated_data.get('barber_id')
            ):
                return jsonify({
                    "status": "error", 
                    "message": "This time slot is already booked. Please select a different time."
                }), 409
        
        # Update the appointment
        updated_appointment = data_service.update_appointment(appointment_id, appointment.to_dict())
        
        if not updated_appointment:
            return jsonify({"status": "error", "message": "Failed to update appointment"}), 500
        
        # If rescheduled, send notification to customer
        if (data.get('date') and data.get('date') != existing_appointment.get('date')) or \
           (data.get('time') and data.get('time') != existing_appointment.get('time')):
            customer = data_service.get_customer(updated_data.get('customer_id'))
            barber = data_service.get_barber(updated_data.get('barber_id'))
            service = data_service.get_service(updated_data.get('service_id'))
            
            if customer and 'phone' in customer and service and barber:
                message = (
                    f"Hi {customer['name']}! Your appointment has been rescheduled:\n\n"
                    f"📅 New Date: {updated_data.get('date')}\n"
                    f"⏰ New Time: {updated_data.get('time')}\n"
                    f"💇 Service: {service['name']}\n"
                    f"👨‍💼 Barber: {barber['name']}\n\n"
                    f"Reply with 'CONFIRM' to confirm or 'CANCEL' to cancel this appointment."
                )
                whatsapp_service.send_message(customer['phone'], message)
        
        return jsonify({"status": "success", "data": updated_appointment})
        
    except Exception as e:
        logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@appointment_bp.route('/<appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    """Delete an appointment"""
    try:
        existing_appointment = data_service.get_appointment(appointment_id)
        
        if not existing_appointment:
            return jsonify({"status": "error", "message": "Appointment not found"}), 404
        
        # Notify customer about cancellation
        customer = data_service.get_customer(existing_appointment.get('customer_id'))
        if customer and 'phone' in customer:
            message = (
                f"Hi {customer['name']}! Your appointment on {existing_appointment.get('date')} "
                f"at {existing_appointment.get('time')} has been cancelled.\n\n"
                f"If you wish to book a new appointment, send 'BOOK' to start the process."
            )
            whatsapp_service.send_message(customer['phone'], message)
        
        # Delete the appointment
        success = data_service.delete_appointment(appointment_id)
        
        if not success:
            return jsonify({"status": "error", "message": "Failed to delete appointment"}), 500
        
        return jsonify({"status": "success", "message": "Appointment deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting appointment {appointment_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@appointment_bp.route('/check-availability', methods=['GET'])
def check_availability():
    """Check appointment availability"""
    try:
        date = request.args.get('date')
        time = request.args.get('time')
        barber_id = request.args.get('barber_id')
        
        if not date or not time:
            return jsonify({"status": "error", "message": "Date and time are required"}), 400
        
        # Validate date format
        if not validators.validate_date(date):
            return jsonify({"status": "error", "message": "Invalid date format (must be YYYY-MM-DD)"}), 400
        
        # Validate time format
        if not validators.validate_time(time):
            return jsonify({"status": "error", "message": "Invalid time format (must be HH:MM in 24-hour format)"}), 400
        
        is_available = data_service.check_availability(date, time, barber_id)
        
        return jsonify({
            "status": "success", 
            "data": {"available": is_available}
        })
        
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@appointment_bp.route('/available-slots', methods=['GET'])
def get_available_slots():
    """Get available appointment slots for a date"""
    try:
        date = request.args.get('date')
        barber_id = request.args.get('barber_id')
        
        if not date:
            return jsonify({"status": "error", "message": "Date is required"}), 400
        
        # Validate date format
        if not validators.validate_date(date):
            return jsonify({"status": "error", "message": "Invalid date format (must be YYYY-MM-DD)"}), 400
        
        # Get barber's working hours
        barber = None
        if barber_id:
            barber = data_service.get_barber(barber_id)
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
            if data_service.check_availability(date, time_str, barber_id):
                slots.append(time_str)
            current_time += timedelta(minutes=30)
        
        return jsonify({
            "status": "success", 
            "data": {"slots": slots}
        })
        
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@appointment_bp.route('/status/<appointment_id>', methods=['PATCH'])
def update_appointment_status(appointment_id):
    """Update appointment status (completed, cancelled, no-show)"""
    try:
        data = request.json
        status = data.get('status')
        
        if not status:
            return jsonify({"status": "error", "message": "Status is required"}), 400
        
        valid_statuses = ["scheduled", "completed", "cancelled", "no-show"]
        if status not in valid_statuses:
            return jsonify({
                "status": "error", 
                "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }), 400
        
        existing_appointment = data_service.get_appointment(appointment_id)
        
        if not existing_appointment:
            return jsonify({"status": "error", "message": "Appointment not found"}), 404
        
        # Update status
        existing_appointment['status'] = status
        existing_appointment['updated_at'] = datetime.now().isoformat()
        
        updated_appointment = data_service.update_appointment(appointment_id, existing_appointment)
        
        if not updated_appointment:
            return jsonify({"status": "error", "message": "Failed to update appointment status"}), 500
        
        # Notify customer if appointment is cancelled
        if status == "cancelled":
            customer = data_service.get_customer(existing_appointment.get('customer_id'))
            if customer and 'phone' in customer:
                message = (
                    f"Hi {customer['name']}! Your appointment on {existing_appointment.get('date')} "
                    f"at {existing_appointment.get('time')} has been cancelled.\n\n"
                    f"If you wish to book a new appointment, send 'BOOK' to start the process."
                )
                whatsapp_service.send_message(customer['phone'], message)
        
        return jsonify({"status": "success", "data": updated_appointment})
        
    except Exception as e:
        logger.error(f"Error updating appointment status {appointment_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@appointment_bp.route('/reminders', methods=['POST'])
def send_appointment_reminders():
    """Send reminders for upcoming appointments"""
    try:
        # Get all scheduled appointments
        appointments = data_service.get_appointments()
        scheduled_appointments = {k: v for k, v in appointments.items() if v.get('status') == 'scheduled'}
        
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        
        # Filter appointments for tomorrow
        tomorrow_appointments = {
            k: v for k, v in scheduled_appointments.items() 
            if v.get('date') == tomorrow_str
        }
        
        sent_count = 0
        for appt_id, appt in tomorrow_appointments.items():
            customer = data_service.get_customer(appt.get('customer_id'))
            barber = data_service.get_barber(appt.get('barber_id'))
            service = data_service.get_service(appt.get('service_id'))
            
            if customer and 'phone' in customer and service and barber:
                # Send reminder
                whatsapp_service.send_appointment_reminder(
                    customer['phone'],
                    customer['name'],
                    appt.get('date'),
                    appt.get('time'),
                    service['name'],
                    barber['name']
                )
                sent_count += 1
        
        return jsonify({
            "status": "success", 
            "message": f"Sent {sent_count} appointment reminders for {tomorrow_str}"
        })
        
    except Exception as e:
        logger.error(f"Error sending appointment reminders: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
