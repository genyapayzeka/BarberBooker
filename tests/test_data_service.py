"""
Tests for the data service module
"""
import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Import the module under test
from services import data_service
from config import CUSTOMERS_FILE, APPOINTMENTS_FILE, BARBERS_FILE, SERVICES_FILE


class TestDataService(unittest.TestCase):
    """Test cases for the data service module"""

    def setUp(self):
        """Setup test environment before each test"""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Save original file paths
        self.original_customers_file = CUSTOMERS_FILE
        self.original_appointments_file = APPOINTMENTS_FILE
        self.original_barbers_file = BARBERS_FILE
        self.original_services_file = SERVICES_FILE
        
        # Set test file paths
        self.test_customers_file = os.path.join(self.test_dir, "customers.json")
        self.test_appointments_file = os.path.join(self.test_dir, "appointments.json")
        self.test_barbers_file = os.path.join(self.test_dir, "barbers.json")
        self.test_services_file = os.path.join(self.test_dir, "services.json")
        
        # Patch file paths for testing
        data_service.CUSTOMERS_FILE = self.test_customers_file
        data_service.APPOINTMENTS_FILE = self.test_appointments_file
        data_service.BARBERS_FILE = self.test_barbers_file
        data_service.SERVICES_FILE = self.test_services_file
        
        # Initialize file locks for test files
        data_service._file_locks = {
            self.test_customers_file: data_service.threading.Lock(),
            self.test_appointments_file: data_service.threading.Lock(),
            self.test_barbers_file: data_service.threading.Lock(),
            self.test_services_file: data_service.threading.Lock()
        }
        
        # Initialize data cache
        data_service._data_cache = {
            "customers": {},
            "appointments": {},
            "barbers": {},
            "services": {}
        }
        
        # Create test data files
        self._create_test_files()
        
        # Initialize data service
        data_service.initialize()
        
    def tearDown(self):
        """Clean up after each test"""
        # Restore original file paths
        data_service.CUSTOMERS_FILE = self.original_customers_file
        data_service.APPOINTMENTS_FILE = self.original_appointments_file
        data_service.BARBERS_FILE = self.original_barbers_file
        data_service.SERVICES_FILE = self.original_services_file
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def _create_test_files(self):
        """Create test data files"""
        # Test customers
        customers_data = {
            "customers": {
                "1": {
                    "id": "1",
                    "name": "John Doe",
                    "phone": "+1234567890",
                    "email": "john.doe@example.com",
                    "created_at": "2023-05-01T10:00:00"
                },
                "2": {
                    "id": "2",
                    "name": "Jane Smith",
                    "phone": "+1987654321",
                    "email": "jane.smith@example.com",
                    "created_at": "2023-05-02T11:00:00"
                }
            }
        }
        
        # Test appointments
        appointments_data = {
            "appointments": {
                "101": {
                    "id": "101",
                    "customer_id": "1",
                    "barber_id": "201",
                    "service_id": "301",
                    "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "time": "10:00",
                    "duration": 30,
                    "status": "scheduled",
                    "created_at": "2023-05-03T12:00:00"
                },
                "102": {
                    "id": "102",
                    "customer_id": "2",
                    "barber_id": "202",
                    "service_id": "302",
                    "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "time": "14:00",
                    "duration": 45,
                    "status": "scheduled",
                    "created_at": "2023-05-04T13:00:00"
                }
            }
        }
        
        # Test barbers
        barbers_data = {
            "barbers": {
                "201": {
                    "id": "201",
                    "name": "Bob Johnson",
                    "email": "bob.johnson@example.com",
                    "bio": "Experienced barber with 10 years of experience",
                    "specialties": ["Haircuts", "Beard Trims"],
                    "working_hours": {
                        "monday": {"start": "09:00", "end": "17:00"},
                        "tuesday": {"start": "09:00", "end": "17:00"},
                        "wednesday": {"start": "09:00", "end": "17:00"},
                        "thursday": {"start": "09:00", "end": "17:00"},
                        "friday": {"start": "09:00", "end": "17:00"},
                        "saturday": {"start": "10:00", "end": "16:00"},
                        "sunday": None
                    },
                    "is_active": True,
                    "created_at": "2023-05-05T14:00:00"
                },
                "202": {
                    "id": "202",
                    "name": "Alice Williams",
                    "email": "alice.williams@example.com",
                    "bio": "Specialized in modern hair styling",
                    "specialties": ["Modern Cuts", "Styling"],
                    "working_hours": {
                        "monday": {"start": "10:00", "end": "18:00"},
                        "tuesday": {"start": "10:00", "end": "18:00"},
                        "wednesday": {"start": "10:00", "end": "18:00"},
                        "thursday": {"start": "10:00", "end": "18:00"},
                        "friday": {"start": "10:00", "end": "18:00"},
                        "saturday": None,
                        "sunday": None
                    },
                    "is_active": True,
                    "created_at": "2023-05-06T15:00:00"
                }
            }
        }
        
        # Test services
        services_data = {
            "services": {
                "301": {
                    "id": "301",
                    "name": "Regular Haircut",
                    "description": "Basic haircut service",
                    "price": 25.0,
                    "duration": 30,
                    "category": "Hair",
                    "is_active": True,
                    "created_at": "2023-05-07T16:00:00"
                },
                "302": {
                    "id": "302",
                    "name": "Haircut & Beard Trim",
                    "description": "Combo haircut and beard trim service",
                    "price": 35.0,
                    "duration": 45,
                    "category": "Combo",
                    "is_active": True,
                    "created_at": "2023-05-08T17:00:00"
                }
            }
        }
        
        # Write test data to files
        with open(self.test_customers_file, 'w') as f:
            json.dump(customers_data, f)
        
        with open(self.test_appointments_file, 'w') as f:
            json.dump(appointments_data, f)
        
        with open(self.test_barbers_file, 'w') as f:
            json.dump(barbers_data, f)
        
        with open(self.test_services_file, 'w') as f:
            json.dump(services_data, f)
    
    def test_get_customers(self):
        """Test get_customers function"""
        customers = data_service.get_customers()
        self.assertEqual(len(customers), 2)
        self.assertEqual(customers["1"]["name"], "John Doe")
        self.assertEqual(customers["2"]["name"], "Jane Smith")

    def test_get_customer(self):
        """Test get_customer function"""
        customer = data_service.get_customer("1")
        self.assertEqual(customer["name"], "John Doe")
        self.assertEqual(customer["phone"], "+1234567890")
        
        # Test non-existent customer
        non_existent = data_service.get_customer("999")
        self.assertIsNone(non_existent)

    def test_get_customer_by_phone(self):
        """Test get_customer_by_phone function"""
        customer = data_service.get_customer_by_phone("+1234567890")
        self.assertEqual(customer["name"], "John Doe")
        
        # Test non-existent phone
        non_existent = data_service.get_customer_by_phone("+9999999999")
        self.assertIsNone(non_existent)

    def test_create_customer(self):
        """Test create_customer function"""
        # Create a new customer
        new_customer = {
            "name": "New Customer",
            "phone": "+1234555555",
            "email": "new.customer@example.com"
        }
        
        result = data_service.create_customer(new_customer)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "New Customer")
        self.assertTrue("id" in result)
        
        # Verify it was added to the cache
        customers = data_service.get_customers()
        found = False
        for customer_id, customer in customers.items():
            if customer["name"] == "New Customer":
                found = True
                break
        
        self.assertTrue(found)
        
        # Verify it was written to file
        with open(self.test_customers_file, 'r') as f:
            file_data = json.load(f)
        
        found = False
        for customer_id, customer in file_data["customers"].items():
            if customer["name"] == "New Customer":
                found = True
                break
        
        self.assertTrue(found)

    def test_update_customer(self):
        """Test update_customer function"""
        # Update an existing customer
        updated_data = {
            "name": "John Doe Updated",
            "email": "john.updated@example.com"
        }
        
        result = data_service.update_customer("1", updated_data)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "John Doe Updated")
        self.assertEqual(result["email"], "john.updated@example.com")
        self.assertEqual(result["phone"], "+1234567890")  # Original value should be preserved
        
        # Verify it was updated in the cache
        customers = data_service.get_customers()
        self.assertEqual(customers["1"]["name"], "John Doe Updated")
        
        # Verify it was written to file
        with open(self.test_customers_file, 'r') as f:
            file_data = json.load(f)
        
        self.assertEqual(file_data["customers"]["1"]["name"], "John Doe Updated")

    def test_delete_customer(self):
        """Test delete_customer function"""
        # Delete an existing customer
        result = data_service.delete_customer("1")
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify it was removed from the cache
        customers = data_service.get_customers()
        self.assertFalse("1" in customers)
        
        # Verify it was removed from file
        with open(self.test_customers_file, 'r') as f:
            file_data = json.load(f)
        
        self.assertFalse("1" in file_data["customers"])

    def test_get_appointments(self):
        """Test get_appointments function"""
        appointments = data_service.get_appointments()
        self.assertEqual(len(appointments), 2)
        self.assertEqual(appointments["101"]["customer_id"], "1")
        self.assertEqual(appointments["102"]["customer_id"], "2")

    def test_get_appointments_by_customer(self):
        """Test get_appointments_by_customer function"""
        appointments = data_service.get_appointments_by_customer("1")
        self.assertEqual(len(appointments), 1)
        self.assertEqual(list(appointments.keys())[0], "101")
        
        # Test customer with no appointments
        no_appointments = data_service.get_appointments_by_customer("999")
        self.assertEqual(len(no_appointments), 0)

    def test_get_appointments_by_date(self):
        """Test get_appointments_by_date function"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        appointments = data_service.get_appointments_by_date(tomorrow)
        self.assertEqual(len(appointments), 1)
        self.assertEqual(list(appointments.keys())[0], "101")
        
        # Test date with no appointments
        past_date = "2000-01-01"
        no_appointments = data_service.get_appointments_by_date(past_date)
        self.assertEqual(len(no_appointments), 0)

    def test_check_availability(self):
        """Test check_availability function"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Time that's already booked
        available = data_service.check_availability(tomorrow, "10:00", "201")
        self.assertFalse(available)
        
        # Time that's free
        available = data_service.check_availability(tomorrow, "11:00", "201")
        self.assertTrue(available)
        
        # Different barber at same time
        available = data_service.check_availability(tomorrow, "10:00", "202")
        self.assertTrue(available)
        
        # Any barber at booked time
        available = data_service.check_availability(tomorrow, "10:00")
        self.assertFalse(available)


if __name__ == '__main__':
    unittest.main()
