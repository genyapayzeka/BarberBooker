"""
Appointment model class for the Barber Appointment System
"""
from dataclasses import dataclass, asdict
import json
import re
from datetime import datetime

@dataclass
class Appointment:
    """Appointment model representing a barber appointment"""
    id: str = None
    customer_id: str = None
    barber_id: str = None
    service_id: str = None
    date: str = None  # Format: YYYY-MM-DD
    time: str = None  # Format: HH:MM (24-hour)
    duration: int = None  # Duration in minutes
    status: str = "scheduled"  # scheduled, completed, cancelled, no-show
    created_at: str = None
    updated_at: str = None
    notes: str = None
    
    def __post_init__(self):
        """Initialize fields after creation"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert appointment object to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data):
        """Create appointment object from dictionary"""
        return cls(**data)
    
    def validate(self):
        """Validate appointment data"""
        errors = []
        
        if not self.customer_id:
            errors.append("Customer ID is required")
        
        if not self.barber_id:
            errors.append("Barber ID is required")
        
        if not self.service_id:
            errors.append("Service ID is required")
        
        if not self.date:
            errors.append("Date is required")
        elif not re.match(r'^\d{4}-\d{2}-\d{2}$', self.date):
            errors.append("Date must be in YYYY-MM-DD format")
        
        if not self.time:
            errors.append("Time is required")
        elif not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', self.time):
            errors.append("Time must be in 24-hour format (HH:MM)")
        
        if not self.duration or self.duration <= 0:
            errors.append("Duration must be a positive number")
        
        valid_statuses = ["scheduled", "completed", "cancelled", "no-show"]
        if self.status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return errors
    
    def to_json(self):
        """Convert appointment object to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str):
        """Create appointment object from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_upcoming(self):
        """Check if appointment is in the future"""
        now = datetime.now()
        appointment_datetime = datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M")
        return appointment_datetime > now and self.status == "scheduled"
    
    def cancel(self):
        """Cancel the appointment"""
        self.status = "cancelled"
        self.updated_at = datetime.now().isoformat()
        return self
    
    def complete(self):
        """Mark the appointment as completed"""
        self.status = "completed"
        self.updated_at = datetime.now().isoformat()
        return self
    
    def mark_no_show(self):
        """Mark the appointment as no-show"""
        self.status = "no-show"
        self.updated_at = datetime.now().isoformat()
        return self
    
    def reschedule(self, new_date, new_time, new_barber_id=None):
        """Reschedule the appointment"""
        self.date = new_date
        self.time = new_time
        if new_barber_id:
            self.barber_id = new_barber_id
        self.updated_at = datetime.now().isoformat()
        return self
