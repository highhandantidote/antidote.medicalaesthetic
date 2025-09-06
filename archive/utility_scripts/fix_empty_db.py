#!/usr/bin/env python3
"""
Fix empty database by creating minimal essential data.

This script adds a minimal set of body parts, categories, and procedures
to fix server errors caused by an empty database.
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set the DATABASE_URL environment variable if not already set
if 'DATABASE_URL' not in os.environ:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

from app import db
# Try to import the models
try:
    from models import BodyPart, Category, Procedure, Doctor
except ImportError:
    logger.error("Failed to import required models")
    sys.exit(1)

def add_minimal_data():
    """Add minimal essential data to database."""
    try:
        # Add body parts
        body_parts = []
        body_part_names = ["Face", "Nose", "Breast", "Body"]
        
        for name in body_part_names:
            existing = BodyPart.query.filter_by(name=name).first()
            if not existing:
                body_part = BodyPart()
                body_part.name = name
                body_part.description = f"{name} procedures and treatments"
                body_part.image_url = f"/static/images/{name.lower()}.jpg"
                body_parts.append(body_part)
                db.session.add(body_part)
        
        db.session.commit()
        logger.info(f"Added {len(body_parts)} body parts")
        
        # Add categories
        categories = []
        # Map category names to body parts
        category_data = [
            {"name": "Facial Rejuvenation", "body_part_name": "Face"},
            {"name": "Rhinoplasty", "body_part_name": "Nose"},
            {"name": "Breast Augmentation", "body_part_name": "Breast"},
            {"name": "Body Contouring", "body_part_name": "Body"}
        ]
        
        for data in category_data:
            existing = Category.query.filter_by(name=data["name"]).first()
            if not existing:
                body_part = BodyPart.query.filter_by(name=data["body_part_name"]).first()
                if body_part:
                    category = Category()
                    category.name = data["name"]
                    category.description = f"{data['name']} procedures"
                    category.body_part_id = body_part.id
                    categories.append(category)
                    db.session.add(category)
        
        db.session.commit()
        logger.info(f"Added {len(categories)} categories")
        
        # Add procedures
        procedures = []
        # Map procedure names to categories
        procedure_data = [
            {"name": "Face Lift", "category_name": "Facial Rejuvenation", "description": "Surgical procedure to reduce facial wrinkles", "price": 8000, "duration": 180, "recovery_time": "2-4 weeks"},
            {"name": "Nose Reshaping", "category_name": "Rhinoplasty", "description": "Surgical procedure to reshape the nose", "price": 5000, "duration": 120, "recovery_time": "1-2 weeks"},
            {"name": "Breast Implants", "category_name": "Breast Augmentation", "description": "Surgical procedure to enhance breast size", "price": 7000, "duration": 90, "recovery_time": "4-6 weeks"},
            {"name": "Liposuction", "category_name": "Body Contouring", "description": "Surgical procedure to remove excess fat", "price": 6000, "duration": 150, "recovery_time": "1-3 weeks"}
        ]
        
        for data in procedure_data:
            existing = Procedure.query.filter_by(name=data["name"]).first()
            if not existing:
                category = Category.query.filter_by(name=data["category_name"]).first()
                if category:
                    procedure = Procedure()
                    procedure.name = data["name"]
                    procedure.description = data["description"]
                    procedure.long_description = data["description"] + " with proven results and high patient satisfaction."
                    procedure.price = data["price"]
                    procedure.duration = data["duration"]
                    procedure.recovery_time = data["recovery_time"]
                    procedure.category_id = category.id
                    procedure.popularity_score = 100
                    procedures.append(procedure)
                    db.session.add(procedure)
        
        db.session.commit()
        logger.info(f"Added {len(procedures)} procedures")
        
        # Add a test doctor if none exists
        if Doctor.query.count() == 0:
            doctor = Doctor()
            doctor.name = "Dr. John Smith"
            doctor.specialty = "Plastic Surgery"
            doctor.experience = 15
            doctor.city = "Mumbai"
            doctor.email = "dr.smith@example.com"
            doctor.phone = "1234567890"
            doctor.about = "Board-certified plastic surgeon with 15 years of experience."
            doctor.created_at = datetime.now()
            db.session.add(doctor)
            db.session.commit()
            logger.info("Added a test doctor")
            
            # Associate doctor with procedures
            for procedure in Procedure.query.all():
                doctor.procedures.append(procedure)
            db.session.commit()
            logger.info("Associated doctor with procedures")
        
        logger.info("Successfully added minimal data to the database")
        return True
        
    except Exception as e:
        logger.error(f"Error adding data: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    add_minimal_data()