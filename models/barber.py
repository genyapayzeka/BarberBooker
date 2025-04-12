"""
Barber model class for the Barber Appointment System
"""
from dataclasses import dataclass, asdict
import json
from datetime import datetime

@dataclass
class Barber:
    """Barber model representing a barbershop employee"""
    id: str = None
    name: str = None
    email: str = None
    phone: str = None
    bio: str = None
    specialties: list = None
    working_hours: dict = None  # {"monday": {"start": "09:00", "end": "17:00"}, ...}
    profile_image: str = None
    is_active: bool = True
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        """Initialize fields after creation"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        
        if self.specialties is None:
            self.specialties = []
        
        if self.working_hours is None:
            # Default working hours (9 AM to 5 PM, Monday through Friday)
            self.working_hours = {
                "monday": {"start": "09:00", "end": "17:00"},
                "tuesday": {"start": "09:00", "end": "17:00"},
                "wednesday": {"start": "09:00", "end": "17:00"},
                "thursday": {"start": "09:00", "end": "17:00"},
                "friday": {"start": "09:00", "end": "17:00"},
                "saturday": {"start": "10:00", "end": "16:00"},
                "sunday": None  # Off on Sunday
            }
    
    def to_dict(self):
        """Convert barber object to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data):
        """Create barber object from dictionary"""
        return cls(**data)
    
    def validate(self):
        """Validate barber data"""
        errors = []
        
        if not self.name or len(self.name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        
        # Validate working hours
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if self.working_hours:
            for day, hours in self.working_hours.items():
                if day not in days_of_week:
                    errors.append(f"Invalid day: {day}")
                elif hours is not None:
                    if "start" not in hours or "end" not in hours:
                        errors.append(f"Working hours for {day} must include 'start' and 'end' times")
        
        return errors
    
    def to_json(self):
        """Convert barber object to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str):
        """Create barber object from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_available(self, day_of_week, time):
        """
        Check if barber is available at a specific time
        
        Args:
            day_of_week: Day of the week (lowercase)
            time: Time in 24-hour format ("HH:MM")
            
        Returns:
            bool: True if available, False otherwise
        """
        if not self.is_active:
            return False
            
        day_of_week = day_of_week.lower()
        if day_of_week not in self.working_hours or not self.working_hours[day_of_week]:
            return False
            
        hours = self.working_hours[day_of_week]
        return hours["start"] <= time <= hours["end"]
