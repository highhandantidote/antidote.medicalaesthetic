#!/usr/bin/env python3
"""
Script to create a doctor for verification testing.
"""
import logging
import os
from datetime import datetime
from app import create_app, db
from models import User, Doctor

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_credentials():
    """Create sample credential files for verification testing."""
    cred_dir = os.path.join('static', 'doctor_credentials')
    os.makedirs(cred_dir, exist_ok=True)
    
    # Create a sample credential file if it doesn't exist
    cred_file_path = os.path.join(cred_dir, 'test_credential.pdf')
    if not os.path.exists(cred_file_path):
        with open(cred_file_path, 'w') as f:
            f.write("This is a sample credential file for testing purposes")
        logger.info(f"Created sample credential file at {cred_file_path}")
    else:
        logger.info(f"Sample credential file already exists at {cred_file_path}")

def create_doctor(username, name, city="Mumbai", state="Maharashtra"):
    """Create a doctor user and profile for testing."""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Create user
            user = User(
                username=username,
                name=name,
                email=f"{username}@example.com",
                phone_number="9876543210",
                role="doctor",
                role_type="doctor",
                is_verified=True,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created doctor user: {username}")
        else:
            logger.info(f"Doctor user {username} already exists, using existing record")
        
        # Check if doctor profile exists
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        
        if not doctor:
            # Create doctor profile
            doctor = Doctor(
                user_id=user.id,
                name=name,
                specialty="Plastic Surgery",
                experience=5,
                city=city,
                state=state,
                hospital="City General Hospital",
                consultation_fee=2000,
                is_verified=False,
                bio="Experienced plastic surgeon specializing in facial procedures.",
                medical_license_number=f"MCI-{username}-2025",
                qualification="MBBS, MS, MCh Plastic Surgery",
                practice_location=f"{city}, {state}",
                verification_status="pending",
                credentials_url="test_credential.pdf",
                aadhaar_number=f"5678-1234-{user.id}",
                created_at=datetime.utcnow()
            )
            db.session.add(doctor)
            db.session.commit()
            logger.info(f"Created doctor profile for {username} with ID: {doctor.id}")
            return doctor.id
        else:
            logger.info(f"Doctor profile for {username} already exists with ID: {doctor.id}")
            return doctor.id

def main():
    """Create a doctor for verification testing."""
    logger.info("Creating test doctor for verification workflow testing...")
    
    # Create sample credential files
    create_sample_credentials()
    
    # Create a test doctor
    doctor_id = create_doctor("doctor_test2", "Doctor Test 2")
    
    logger.info(f"\nTest doctor created successfully with ID: {doctor_id}")
    logger.info("\nTo test the verification workflow:")
    logger.info("1. Log in as administrator")
    logger.info("2. Navigate to /dashboard/admin/doctor-verifications")
    logger.info(f"3. Approve or reject the doctor with ID: {doctor_id}")
    logger.info(f"4. Check the updated status with: SELECT id, name, verification_status FROM doctors WHERE id = {doctor_id};")

if __name__ == "__main__":
    main()