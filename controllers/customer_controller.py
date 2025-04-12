"""
Controller for customer-related routes and functions
"""
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime

from models.customer import Customer
from services import data_service, whatsapp_service

logger = logging.getLogger(__name__)

# Create blueprint
customer_bp = Blueprint('customer', __name__, url_prefix='/api/customers')

@customer_bp.route('/', methods=['GET'])
def get_customers():
    """Get all customers"""
    try:
        customers = data_service.get_customers()
        return jsonify({"status": "success", "data": customers})
        
    except Exception as e:
        logger.error(f"Error getting customers: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@customer_bp.route('/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get a specific customer by ID"""
    try:
        customer = data_service.get_customer(customer_id)
        
        if not customer:
            return jsonify({"status": "error", "message": "Customer not found"}), 404
            
        return jsonify({"status": "success", "data": customer})
        
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@customer_bp.route('/phone/<phone>', methods=['GET'])
def get_customer_by_phone(phone):
    """Get a customer by phone number"""
    try:
        # Remove any non-numeric characters for consistent lookup
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Try exact match first
        customer = data_service.get_customer_by_phone(phone)
        
        # If not found, try with the cleaned phone number
        if not customer and phone != clean_phone:
            customer = data_service.get_customer_by_phone(clean_phone)
        
        if not customer:
            return jsonify({"status": "error", "message": "Customer not found"}), 404
            
        return jsonify({"status": "success", "data": customer})
        
    except Exception as e:
        logger.error(f"Error getting customer by phone {phone}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@customer_bp.route('/', methods=['POST'])
def create_customer():
    """Create a new customer"""
    try:
        data = request.json
        
        # Check if customer with phone already exists
        if 'phone' in data and data['phone']:
            existing_customer = data_service.get_customer_by_phone(data['phone'])
            if existing_customer:
                return jsonify({
                    "status": "error", 
                    "message": "A customer with this phone number already exists"
                }), 409
        
        # Create a Customer object for validation
        customer = Customer(
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            notes=data.get('notes')
        )
        
        # Validate customer data
        errors = customer.validate()
        if errors:
            return jsonify({"status": "error", "message": errors}), 400
        
        # Create the customer
        created_customer = data_service.create_customer(customer.to_dict())
        
        if not created_customer:
            return jsonify({"status": "error", "message": "Failed to create customer"}), 500
        
        # Send welcome message if phone is provided
        if 'phone' in data and data['phone']:
            whatsapp_service.send_registration_confirmation(data['phone'], data['name'])
        
        return jsonify({"status": "success", "data": created_customer}), 201
        
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@customer_bp.route('/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update an existing customer"""
    try:
        data = request.json
        existing_customer = data_service.get_customer(customer_id)
        
        if not existing_customer:
            return jsonify({"status": "error", "message": "Customer not found"}), 404
        
        # Check if updating to a phone number that already exists with a different customer
        if 'phone' in data and data['phone']:
            phone_customer = data_service.get_customer_by_phone(data['phone'])
            if phone_customer and phone_customer.get('id') != customer_id:
                return jsonify({
                    "status": "error", 
                    "message": "Another customer with this phone number already exists"
                }), 409
        
        # Merge existing data with updates
        updated_data = {**existing_customer, **data}
        
        # Create a Customer object for validation
        customer = Customer.from_dict(updated_data)
        
        # Validate customer data
        errors = customer.validate()
        if errors:
            return jsonify({"status": "error", "message": errors}), 400
        
        # Update the customer
        updated_customer = data_service.update_customer(customer_id, customer.to_dict())
        
        if not updated_customer:
            return jsonify({"status": "error", "message": "Failed to update customer"}), 500
        
        return jsonify({"status": "success", "data": updated_customer})
        
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@customer_bp.route('/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer"""
    try:
        customer = data_service.get_customer(customer_id)
        
        if not customer:
            return jsonify({"status": "error", "message": "Customer not found"}), 404
        
        # Check if customer has any appointments
        appointments = data_service.get_appointments_by_customer(customer_id)
        if appointments:
            return jsonify({
                "status": "error", 
                "message": "Cannot delete customer with existing appointments. Please delete appointments first."
            }), 409
        
        # Delete the customer
        success = data_service.delete_customer(customer_id)
        
        if not success:
            return jsonify({"status": "error", "message": "Failed to delete customer"}), 500
        
        return jsonify({"status": "success", "message": "Customer deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@customer_bp.route('/<customer_id>/appointments', methods=['GET'])
def get_customer_appointments(customer_id):
    """Get all appointments for a customer"""
    try:
        customer = data_service.get_customer(customer_id)
        
        if not customer:
            return jsonify({"status": "error", "message": "Customer not found"}), 404
        
        appointments = data_service.get_appointments_by_customer(customer_id)
        
        return jsonify({"status": "success", "data": appointments})
        
    except Exception as e:
        logger.error(f"Error getting appointments for customer {customer_id}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
