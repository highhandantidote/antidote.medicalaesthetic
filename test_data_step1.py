#!/usr/bin/env python3
"""
Step 1: Create users and basic categories
"""
import os
import random
import string
import logging
from datetime import datetime, timedelta
from app import create_app, db
from models import User, Doctor, BodyPart, Category

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_user(username, name, role, is_verified=False):
    """Generate a user with the specified role."""
    return User(
        username=username,
        name=name,
        email=f"{username}@example.com",
        phone_number=f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        role=role,
        role_type=role,
        is_verified=is_verified,
        created_at=datetime.utcnow()
    )

def generate_doctor(user_id):
    """Generate a doctor profile for verification testing."""
    return Doctor(
        user_id=user_id,
        name="Doctor Test",
        medical_license_number="MCI-12345-2025",
        qualification="MBBS 2015",
        practice_location="Delhi, India",
        verification_status="pending",
        credentials_url="test_credentials.pdf",
        aadhaar_number="1234-5678-9012",
        specialty="General Surgery",
        experience=10,
        city="Delhi",
        state="Delhi",
        created_at=datetime.utcnow(),
        is_verified=False
    )

def create_sample_files():
    """Create sample credential files for testing."""
    # Create credentials directory
    credentials_dir = os.path.join('static', 'doctor_credentials')
    os.makedirs(credentials_dir, exist_ok=True)
    
    # Create a sample credential file
    sample_file_path = os.path.join(credentials_dir, 'test_credentials.pdf')
    with open(sample_file_path, 'w') as f:
        f.write("This is a sample credential document for testing purposes.")
    
    logger.info(f"Created sample credential file at {sample_file_path}")

def main():
    """Create basic user and category data."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Starting Step 1: Creating users and categories...")
            
            # Create sample files
            create_sample_files()
            
            # Create body part and categories if they don't exist
            body_part = BodyPart.query.filter_by(name="Face").first()
            if not body_part:
                body_part = BodyPart(
                    name="Face",
                    description="Facial procedures and treatments",
                    created_at=datetime.utcnow()
                )
                db.session.add(body_part)
                db.session.commit()
                logger.info("Created body part: Face")
            
            # Create categories
            categories = []
            for cat_name in ["Surgical", "Non-Surgical"]:
                category = Category.query.filter_by(name=cat_name).first()
                if not category:
                    category = Category(
                        name=cat_name,
                        description=f"{cat_name} procedures for face",
                        body_part_id=body_part.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(category)
                    db.session.commit()
                    logger.info(f"Created category: {cat_name}")
                categories.append(category)
            
            # Create admin user if it doesn't exist
            admin = User.query.filter_by(username="admin_test").first()
            if not admin:
                admin = generate_user("admin_test", "Admin Test", "admin", True)
                db.session.add(admin)
                db.session.commit()
                logger.info("Created admin user: admin_test")
            
            # Create doctor user if it doesn't exist
            doctor_user = User.query.filter_by(username="doctor_test").first()
            if not doctor_user:
                doctor_user = generate_user("doctor_test", "Doctor Test", "doctor", True)
                db.session.add(doctor_user)
                db.session.commit()
                logger.info("Created doctor user: doctor_test")
            
            # Create doctor profile if it doesn't exist
            doctor = Doctor.query.filter_by(user_id=doctor_user.id).first()
            if not doctor:
                doctor = generate_doctor(doctor_user.id)
                db.session.add(doctor)
                db.session.commit()
                logger.info("Created doctor profile with pending verification status")
            
            logger.info("\nStep 1 completed successfully!")
            logger.info("Created:")
            logger.info("- 1 body part: Face")
            logger.info("- 2 categories: Surgical, Non-Surgical")
            logger.info("- 1 admin user: admin_test")
            logger.info("- 1 doctor user: doctor_test with pending verification")
            
        except Exception as e:
            logger.error(f"Error in Step 1: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()