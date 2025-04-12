"""
Service model class for the Barber Appointment System
"""
from dataclasses import dataclass, asdict
import json
from datetime import datetime

@dataclass
class Service:
    """Service model representing a barbershop service"""
    id: str = None
    name: str = None
    description: str = None
    price: float = None
    duration: int = None  # Duration in minutes
    category: str = None
    is_active: bool = True
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        """Initialize fields after creation"""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert service object to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data):
        """Create service object from dictionary"""
        return cls(**data)
    
    def validate(self):
        """Validate service data"""
        errors = []
        
        if not self.name or len(self.name.strip()) < 2:
            errors.append("Name is required and must be at least 2 characters")
        
        if self.price is None or self.price < 0:
            errors.append("Price is required and must be a non-negative number")
        
        if not self.duration or self.duration <= 0:
            errors.append("Duration is required and must be a positive number")
        
        return errors
    
    def to_json(self):
        """Convert service object to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str):
        """Create service object from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
