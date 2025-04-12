"""
Database initialization utilities
"""
import logging
from datetime import datetime
from models.database import db, Customer, Barber, Service

logger = logging.getLogger(__name__)

def init_sample_data():
    """Initialize sample data for the database"""
    try:
        # Check if data already exists
        if Barber.query.count() > 0 or Service.query.count() > 0:
            logger.info("Sample data already exists. Skipping initialization.")
            return
            
        # Create sample barbers
        barbers = [
            {
                'name': 'John Smith',
                'email': 'john@moderncuts.com',
                'phone': '555-123-4567',
                'bio': 'Experienced barber with 10+ years in classic cuts and modern styles.',
                'specialties': ['Classic Cuts', 'Fades', 'Beard Trimming'],
                'working_hours': {
                    'monday': {'start': '09:00', 'end': '17:00'},
                    'tuesday': {'start': '09:00', 'end': '17:00'},
                    'wednesday': {'start': '09:00', 'end': '17:00'},
                    'thursday': {'start': '09:00', 'end': '17:00'},
                    'friday': {'start': '09:00', 'end': '17:00'},
                    'saturday': {'start': '10:00', 'end': '16:00'},
                    'sunday': None
                }
            },
            {
                'name': 'Mike Johnson',
                'email': 'mike@moderncuts.com',
                'phone': '555-234-5678',
                'bio': 'Specializing in modern styles and precision fades.',
                'specialties': ['Modern Styles', 'Skin Fades', 'Hair Coloring'],
                'working_hours': {
                    'monday': {'start': '09:00', 'end': '17:00'},
                    'tuesday': {'start': '09:00', 'end': '17:00'},
                    'wednesday': {'start': '09:00', 'end': '17:00'},
                    'thursday': {'start': '09:00', 'end': '17:00'},
                    'friday': {'start': '09:00', 'end': '17:00'},
                    'saturday': {'start': '10:00', 'end': '16:00'},
                    'sunday': None
                }
            }
        ]
        
        for barber_data in barbers:
            barber = Barber(
                name=barber_data['name'],
                email=barber_data['email'],
                phone=barber_data['phone'],
                bio=barber_data['bio'],
                specialties=barber_data['specialties'],
                working_hours=barber_data['working_hours'],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(barber)
        
        # Create sample services
        services = [
            {
                'name': 'Classic Haircut',
                'description': 'Traditional haircut with scissors and clippers.',
                'price': 25.00,
                'duration': 30,
                'category': 'Haircuts'
            },
            {
                'name': 'Fade Haircut',
                'description': 'Modern fade haircut with clippers and blending.',
                'price': 30.00,
                'duration': 45,
                'category': 'Haircuts'
            },
            {
                'name': 'Beard Trim',
                'description': 'Beard shaping and trimming.',
                'price': 15.00,
                'duration': 20,
                'category': 'Facial Hair'
            },
            {
                'name': 'Shave',
                'description': 'Traditional straight razor shave with hot towel.',
                'price': 25.00,
                'duration': 30,
                'category': 'Facial Hair'
            },
            {
                'name': 'Haircut & Beard Trim',
                'description': 'Full service haircut and beard trim package.',
                'price': 40.00,
                'duration': 60,
                'category': 'Packages'
            }
        ]
        
        for service_data in services:
            service = Service(
                name=service_data['name'],
                description=service_data['description'],
                price=service_data['price'],
                duration=service_data['duration'],
                category=service_data['category'],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(service)
        
        db.session.commit()
        logger.info("Sample data initialized successfully")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error initializing sample data: {str(e)}")