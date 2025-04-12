"""
Customer model class for the Barber Appointment System
"""
from dataclasses import dataclass, asdict
import json
import re
from datetime import datetime

@dataclass
class Customer:
    """Customer model representing a barbershop customer"""
    id: str = None
    name: str = None
    phone: str = None
    email: str = None
    created_at: str = None
    last_visit: str = None
    notes: str = None
    
    def __post_init__(self):
        """Initialize fields after creation"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert customer object to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data):
        """Create customer object from dictionary"""
        return cls(**data)
    
    def validate(self):
        """Validate customer data"""
        errors = []
        
        if not self.name or len(self.name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        
        if not self.phone:
            errors.append("Phone number is required")
        elif not re.match(r'^\+?[1-9]\d{1,14}$', self.phone):
            errors.append("Phone number must be in a valid format (E.164 preferred)")
        
        if self.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
            errors.append("Email must be in a valid format")
        
        return errors
    
    def to_json(self):
        """Convert customer object to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str):
        """Create customer object from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
