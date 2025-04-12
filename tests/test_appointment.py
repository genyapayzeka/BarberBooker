"""
Tests for the appointment model and related functionality
"""
import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Import the modules under test
from models.appointment import Appointment
from services import data_service
from config import APPOINTMENTS_FILE


class TestAppointment(unittest.TestCase):
    """Test cases for the Appointment model"""

    def test_appointment_initialization(self):
        """Test Appointment initialization with default values"""
        appointment = Appointment()
        self.assertIsNone(appointment.id)
        self.assertIsNone(appointment.customer_id)
        self.assertIsNone(appointment.barber_id)
        self.assertIsNone(appointment.service_id)
        self.assertIsNone(appointment.date)
        self.assertIsNone(appointment.time)
        self.assertIsNone(appointment.duration)
        self.assertEqual(appointment.status, "scheduled")
        self.assertIsNotNone(appointment.created_at)
        self.assertIsNotNone(appointment.updated_at)
        self.assertIsNone(appointment.notes)

    def test_appointment_initialization_with_values(self):
        """Test Appointment initialization with provided values"""
        appointment = Appointment(
            id="test123",
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45,
            status="completed",
            notes="Test appointment"
        )
        
        self.assertEqual(appointment.id, "test123")
        self.assertEqual(appointment.customer_id, "customer456")
        self.assertEqual(appointment.barber_id, "barber789")
        self.assertEqual(appointment.service_id, "service012")
        self.assertEqual(appointment.date, "2023-05-20")
        self.assertEqual(appointment.time, "14:30")
        self.assertEqual(appointment.duration, 45)
        self.assertEqual(appointment.status, "completed")
        self.assertEqual(appointment.notes, "Test appointment")

    def test_to_dict(self):
        """Test converting appointment to dictionary"""
        appointment = Appointment(
            id="test123",
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45,
            status="completed",
            notes="Test appointment"
        )
        
        appointment_dict = appointment.to_dict()
        
        self.assertEqual(appointment_dict["id"], "test123")
        self.assertEqual(appointment_dict["customer_id"], "customer456")
        self.assertEqual(appointment_dict["barber_id"], "barber789")
        self.assertEqual(appointment_dict["service_id"], "service012")
        self.assertEqual(appointment_dict["date"], "2023-05-20")
        self.assertEqual(appointment_dict["time"], "14:30")
        self.assertEqual(appointment_dict["duration"], 45)
        self.assertEqual(appointment_dict["status"], "completed")
        self.assertEqual(appointment_dict["notes"], "Test appointment")

    def test_from_dict(self):
        """Test creating appointment from dictionary"""
        appointment_dict = {
            "id": "test123",
            "customer_id": "customer456",
            "barber_id": "barber789",
            "service_id": "service012",
            "date": "2023-05-20",
            "time": "14:30",
            "duration": 45,
            "status": "completed",
            "notes": "Test appointment",
            "created_at": "2023-05-15T10:00:00",
            "updated_at": "2023-05-15T11:00:00"
        }
        
        appointment = Appointment.from_dict(appointment_dict)
        
        self.assertEqual(appointment.id, "test123")
        self.assertEqual(appointment.customer_id, "customer456")
        self.assertEqual(appointment.barber_id, "barber789")
        self.assertEqual(appointment.service_id, "service012")
        self.assertEqual(appointment.date, "2023-05-20")
        self.assertEqual(appointment.time, "14:30")
        self.assertEqual(appointment.duration, 45)
        self.assertEqual(appointment.status, "completed")
        self.assertEqual(appointment.notes, "Test appointment")
        self.assertEqual(appointment.created_at, "2023-05-15T10:00:00")
        self.assertEqual(appointment.updated_at, "2023-05-15T11:00:00")

    def test_validate_valid_appointment(self):
        """Test validation with valid appointment data"""
        appointment = Appointment(
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45
        )
        
        errors = appointment.validate()
        self.assertEqual(len(errors), 0)

    def test_validate_invalid_appointment(self):
        """Test validation with invalid appointment data"""
        # Missing required fields
        appointment = Appointment()
        errors = appointment.validate()
        self.assertTrue(len(errors) > 0)
        self.assertIn("Customer ID is required", errors)
        self.assertIn("Barber ID is required", errors)
        self.assertIn("Service ID is required", errors)
        self.assertIn("Date is required", errors)
        self.assertIn("Time is required", errors)
        self.assertIn("Duration must be a positive number", errors)
        
        # Invalid date format
        appointment = Appointment(
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="05/20/2023",  # Wrong format
            time="14:30",
            duration=45
        )
        errors = appointment.validate()
        self.assertTrue(len(errors) > 0)
        self.assertIn("Date must be in YYYY-MM-DD format", errors)
        
        # Invalid time format
        appointment = Appointment(
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="2:30 PM",  # Wrong format
            duration=45
        )
        errors = appointment.validate()
        self.assertTrue(len(errors) > 0)
        self.assertIn("Time must be in 24-hour format (HH:MM)", errors)
        
        # Invalid status
        appointment = Appointment(
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45,
            status="invalid_status"
        )
        errors = appointment.validate()
        self.assertTrue(len(errors) > 0)
        self.assertIn("Status must be one of: scheduled, completed, cancelled, no-show", errors)

    def test_to_json(self):
        """Test converting appointment to JSON"""
        appointment = Appointment(
            id="test123",
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45
        )
        
        json_str = appointment.to_json()
        
        # Parse JSON to verify
        appointment_dict = json.loads(json_str)
        
        self.assertEqual(appointment_dict["id"], "test123")
        self.assertEqual(appointment_dict["customer_id"], "customer456")
        self.assertEqual(appointment_dict["barber_id"], "barber789")
        self.assertEqual(appointment_dict["service_id"], "service012")
        self.assertEqual(appointment_dict["date"], "2023-05-20")
        self.assertEqual(appointment_dict["time"], "14:30")
        self.assertEqual(appointment_dict["duration"], 45)

    def test_from_json(self):
        """Test creating appointment from JSON"""
        json_str = json.dumps({
            "id": "test123",
            "customer_id": "customer456",
            "barber_id": "barber789",
            "service_id": "service012",
            "date": "2023-05-20",
            "time": "14:30",
            "duration": 45,
            "status": "scheduled",
            "created_at": "2023-05-15T10:00:00",
            "updated_at": "2023-05-15T11:00:00"
        })
        
        appointment = Appointment.from_json(json_str)
        
        self.assertEqual(appointment.id, "test123")
        self.assertEqual(appointment.customer_id, "customer456")
        self.assertEqual(appointment.barber_id, "barber789")
        self.assertEqual(appointment.service_id, "service012")
        self.assertEqual(appointment.date, "2023-05-20")
        self.assertEqual(appointment.time, "14:30")
        self.assertEqual(appointment.duration, 45)
        self.assertEqual(appointment.status, "scheduled")
        self.assertEqual(appointment.created_at, "2023-05-15T10:00:00")
        self.assertEqual(appointment.updated_at, "2023-05-15T11:00:00")

    def test_cancel(self):
        """Test cancelling an appointment"""
        appointment = Appointment(
            id="test123",
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45
        )
        
        # Save the original updated_at value
        original_updated_at = appointment.updated_at
        
        # Wait a moment to ensure the updated_at will be different
        import time
        time.sleep(0.1)
        
        # Cancel the appointment
        result = appointment.cancel()
        
        # Verify it's the same object (for chaining)
        self.assertEqual(result, appointment)
        
        # Verify status is changed
        self.assertEqual(appointment.status, "cancelled")
        
        # Verify updated_at is updated
        self.assertNotEqual(appointment.updated_at, original_updated_at)

    def test_complete(self):
        """Test completing an appointment"""
        appointment = Appointment(
            id="test123",
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45
        )
        
        # Save the original updated_at value
        original_updated_at = appointment.updated_at
        
        # Wait a moment to ensure the updated_at will be different
        import time
        time.sleep(0.1)
        
        # Complete the appointment
        result = appointment.complete()
        
        # Verify it's the same object (for chaining)
        self.assertEqual(result, appointment)
        
        # Verify status is changed
        self.assertEqual(appointment.status, "completed")
        
        # Verify updated_at is updated
        self.assertNotEqual(appointment.updated_at, original_updated_at)

    def test_mark_no_show(self):
        """Test marking an appointment as no-show"""
        appointment = Appointment(
            id="test123",
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45
        )
        
        # Save the original updated_at value
        original_updated_at = appointment.updated_at
        
        # Wait a moment to ensure the updated_at will be different
        import time
        time.sleep(0.1)
        
        # Mark as no-show
        result = appointment.mark_no_show()
        
        # Verify it's the same object (for chaining)
        self.assertEqual(result, appointment)
        
        # Verify status is changed
        self.assertEqual(appointment.status, "no-show")
        
        # Verify updated_at is updated
        self.assertNotEqual(appointment.updated_at, original_updated_at)

    def test_reschedule(self):
        """Test rescheduling an appointment"""
        appointment = Appointment(
            id="test123",
            customer_id="customer456",
            barber_id="barber789",
            service_id="service012",
            date="2023-05-20",
            time="14:30",
            duration=45
        )
        
        # Save the original values
        original_date = appointment.date
        original_time = appointment.time
        original_barber_id = appointment.barber_id
        original_updated_at = appointment.updated_at
        
        # Wait a moment to ensure the updated_at will be different
        import time
        time.sleep(0.1)
        
        # Reschedule the appointment
        new_date = "2023-05-25"
        new_time = "16:00"
        new_barber_id = "barber555"
        
        result = appointment.reschedule(new_date, new_time, new_barber_id)
        
        # Verify it's the same object (for chaining)
        self.assertEqual(result, appointment)
        
        # Verify values are changed
        self.assertEqual(appointment.date, new_date)
        self.assertEqual(appointment.time, new_time)
        self.assertEqual(appointment.barber_id, new_barber_id)
        
        # Verify values are different from original
        self.assertNotEqual(appointment.date, original_date)
        self.assertNotEqual(appointment.time, original_time)
        self.assertNotEqual(appointment.barber_id, original_barber_id)
        
        # Verify updated_at is updated
        self.assertNotEqual(appointment.updated_at, original_updated_at)

    def test_is_upcoming(self):
        """Test checking if an appointment is upcoming"""
        # Create an appointment in the future
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_date = tomorrow.strftime("%Y-%m-%d")
        tomorrow_time = tomorrow.strftime("%H:%M")
        
        future_appointment = Appointment(
            date=tomorrow_date,
            time=tomorrow_time,
            status="scheduled"
        )
        
        self.assertTrue(future_appointment.is_upcoming())
        
        # Create an appointment in the past
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_date = yesterday.strftime("%Y-%m-%d")
        yesterday_time = yesterday.strftime("%H:%M")
        
        past_appointment = Appointment(
            date=yesterday_date,
            time=yesterday_time,
            status="scheduled"
        )
        
        self.assertFalse(past_appointment.is_upcoming())
        
        # Create a cancelled future appointment
        cancelled_appointment = Appointment(
            date=tomorrow_date,
            time=tomorrow_time,
            status="cancelled"
        )
        
        self.assertFalse(cancelled_appointment.is_upcoming())


if __name__ == '__main__':
    unittest.main()
