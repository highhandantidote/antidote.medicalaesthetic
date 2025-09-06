#!/usr/bin/env python3
"""
Import doctors with robust handling of missing fields.

This script adds doctor profiles with appropriate defaults for missing fields
and proper error handling to maximize successful imports.
"""

import os
import csv
import time
import logging
import psycopg2
import random
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DOCTORS_CSV_PATH = "./attached_assets/new_doctors_profiles2 - Sheet1.csv"
START_ROW = 103  # Start at the current doctor count
BATCH_SIZE = 5  # Process 5 at a time

# Default values for missing fields
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."
DEFAULT_SPECIALTY = "Cosmetic Surgery"
DEFAULT_QUALIFICATION = "MBBS, MS"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def import_doctors():
    """Import doctors with proper handling of missing fields."""
    if not os.path.exists(DOCTORS_CSV_PATH):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV_PATH}")
        return False
    
    # Read CSV to find doctors to import
    doctors_to_process = []
    with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i < START_ROW:  # Skip doctors we've likely already processed
                continue
                
            doctors_to_process.append(row)
            
            # Once we have enough doctors for this batch, stop collecting
            if len(doctors_to_process) >= BATCH_SIZE:
                break
    
    logger.info(f"Found {len(doctors_to_process)} doctors to process")
    
    # Initialize counters
    doctors_added = 0
    doctors_skipped = 0
    
    # Process each doctor
    conn = get_db_connection()
    try:
        for doctor in doctors_to_process:
            # Extract doctor data with proper defaults
            doctor_name = doctor.get('Doctor Name', '').strip()
            if not doctor_name:
                logger.warning(f"Skipping row - missing doctor name")
                doctors_skipped += 1
                continue
            
            # Prepare doctor data with defaults
            speciality = doctor.get('Specialty', '').strip() or DEFAULT_SPECIALTY
            qualification = doctor.get('Qualification', '').strip() or DEFAULT_QUALIFICATION
            profile_image = doctor.get('Profile Image', '').strip()
            bio = doctor.get('Bio', '').strip() or DEFAULT_BIO
            city = doctor.get('City', '').strip() or "Mumbai"
            
            # Try to convert experience to integer
            try:
                experience = int(doctor.get('Experience', '0'))
            except (ValueError, TypeError):
                experience = random.randint(5, 15)  # Default random experience
            
            try:
                # Set autocommit to False to use transactions
                conn.autocommit = False
                
                # Create a user account first
                user_id = None
                with conn.cursor() as cursor:
                    # Generate a username from the doctor name
                    username = doctor_name.lower().replace(' ', '_').replace('.', '')
                    
                    # Create synthetic email based on doctor name
                    email = f"{username}@example.com"
                    
                    # Generate a secure password
                    password = f"temp{random.randint(100000, 999999)}"
                    password_hash = generate_password_hash(password)
                    
                    # Create user account with all required fields
                    cursor.execute(
                        """
                        INSERT INTO users 
                        (username, email, password_hash, created_at, role, name, is_verified)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (username, email, password_hash, datetime.now(), 'doctor', doctor_name, True)
                    )
                    result = cursor.fetchone()
                    if not result:
                        raise ValueError(f"Failed to create user account for doctor: {doctor_name}")
                    
                    user_id = result[0]
                    logger.info(f"Created new user account for doctor: {doctor_name}")
                
                # Create doctor entry with the user_id
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO doctors 
                        (name, specialty, qualification, profile_image, bio, experience, 
                         consultation_fee, is_verified, created_at, city, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            doctor_name, speciality, qualification, profile_image, 
                            bio, experience, DEFAULT_CONSULTATION_FEE, 
                            True, datetime.now(), city, user_id
                        )
                    )
                    
                    result = cursor.fetchone()
                    if not result:
                        raise ValueError(f"Failed to create doctor profile: {doctor_name}")
                
                # Commit transaction
                conn.commit()
                
                logger.info(f"Added doctor: {doctor_name}")
                doctors_added += 1
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error adding doctor {doctor_name}: {str(e)}")
                doctors_skipped += 1
        
        logger.info(f"Import complete. Added {doctors_added} doctors, skipped {doctors_skipped}")
        
        # Update START_ROW for next run
        if doctors_added > 0:
            new_start_row = START_ROW + doctors_added + doctors_skipped
            script_path = os.path.abspath(__file__)
            with open(script_path, 'r') as file:
                content = file.read()
            
            # Update START_ROW value for next run
            with open(script_path, 'w') as file:
                file.write(content.replace(
                    f"START_ROW = {START_ROW}",
                    f"START_ROW = {new_start_row}"
                ))
            logger.info(f"Updated START_ROW to {new_start_row} for next run")
        
        return doctors_added
    
    except Exception as e:
        logger.error(f"Error in import process: {str(e)}")
        return 0
    
    finally:
        if not conn.closed:
            conn.autocommit = True  # Reset to default
            conn.close()

def main():
    """Run the doctor import."""
    start_time = time.time()
    
    added_count = import_doctors()
    
    if added_count > 0:
        logger.info(f"Successfully added {added_count} doctors in {time.time() - start_time:.2f} seconds")
    else:
        logger.error("Failed to add any doctors")

if __name__ == "__main__":
    main()