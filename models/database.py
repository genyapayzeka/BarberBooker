"""
Database models for the Barber Appointment System
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import uuid

# Initialize database
db = SQLAlchemy()

class Customer(db.Model):
    """Customer model representing a barbershop customer"""
    __tablename__ = 'customers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_visit = db.Column(db.DateTime, nullable=True)
    
    # Relationship with appointments
    appointments = db.relationship('Appointment', backref='customer', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert customer object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_visit': self.last_visit.isoformat() if self.last_visit else None
        }

class Barber(db.Model):
    """Barber model representing a barbershop employee"""
    __tablename__ = 'barbers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    specialties = db.Column(db.JSON, nullable=True)
    working_hours = db.Column(db.JSON, nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with appointments
    appointments = db.relationship('Appointment', backref='barber', lazy=True)
    
    def to_dict(self):
        """Convert barber object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'bio': self.bio,
            'specialties': self.specialties,
            'working_hours': self.working_hours,
            'profile_image': self.profile_image,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Service(db.Model):
    """Service model representing a barbershop service"""
    __tablename__ = 'services'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    category = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with appointments
    appointments = db.relationship('Appointment', backref='service', lazy=True)
    
    def to_dict(self):
        """Convert service object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'duration': self.duration,
            'category': self.category,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Appointment(db.Model):
    """Appointment model representing a barber appointment"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    barber_id = db.Column(db.String(36), db.ForeignKey('barbers.id'), nullable=False)
    service_id = db.Column(db.String(36), db.ForeignKey('services.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(5), nullable=False)  # Format: HH:MM (24-hour)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no-show
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert appointment object to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'barber_id': self.barber_id,
            'service_id': self.service_id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'time': self.time,
            'duration': self.duration,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ConversationState(db.Model):
    """Conversation state model for WhatsApp interactions"""
    __tablename__ = 'conversation_states'
    
    phone_number = db.Column(db.String(20), primary_key=True)
    state = db.Column(db.JSON, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)