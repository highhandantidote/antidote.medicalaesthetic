#!/usr/bin/env python3
"""
Import doctors from CSV file to the database.

This script focuses only on importing doctors and skips any that are already in the database.
It uses proper checkpointing to continue from where it left off.
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
DOCTOR_START_ROW = 110  # Start from current progress (110 doctors already in DB)
BATCH_SIZE = 5  # Process in small batches to avoid timeouts

# Default values for missing fields
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."
DEFAULT_QUALIFICATION = "MBBS, MS"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

def get_checkpoint():
    """Get the current import checkpoint."""
    checkpoint_file = "doctor_import_checkpoint.txt"
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return DOCTOR_START_ROW
    return DOCTOR_START_ROW

def save_checkpoint(row_num):
    """Save the current import checkpoint."""
    checkpoint_file = "doctor_import_checkpoint.txt"
    with open(checkpoint_file, "w") as f:
        f.write(str(row_num))
    logger.info(f"Progress saved: Processed up to row {row_num}")

def doctor_exists(conn, doctor_name):
    """Check if doctor already exists with the same name."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM doctors WHERE name = %s",
            (doctor_name,)
        )
        return cursor.fetchone() is not None

def create_user_for_doctor(conn, doctor_name, email=None):
    """Create a user account for a doctor."""
    # Generate email and username
    # Create a clean username from doctor name
    username = doctor_name.lower().replace("dr. ", "").replace("dr.", "").strip()
    username = ''.join(c for c in username if c.isalnum() or c.isspace()).replace(" ", ".")
    
    # Generate email if not provided
    if not email:
        email = f"{username}@example.com"
    
    # Generate a random password
    password = f"Doctor{random.randint(10000, 99999)}"
    
    # Check if user already exists with this email
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            return existing_user[0]
        
        # Create new user
        cursor.execute(
            """
            INSERT INTO users (
                username, email, password_hash, is_active, 
                is_doctor, created_at, updated_at, email_verified
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """,
            (
                username,
                email,
                generate_password_hash(password),
                True,
                True,
                datetime.now(),
                datetime.now(),
                True
            )
        )
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            logger.info(f"Created user account for doctor: {doctor_name} (ID: {user_id}, Email: {email})")
            return user_id
        else:
            logger.error(f"Failed to create user for doctor: {doctor_name}")
            return None

def import_doctors():
    """Import doctors from CSV in batches with error handling."""
    start_time = time.time()
    conn = get_db_connection()
    
    try:
        start_row = get_checkpoint()
        logger.info(f"Starting doctor import from row {start_row}")
        
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            # Skip to the starting row
            for _ in range(start_row):
                try:
                    next(csv_reader)
                except StopIteration:
                    logger.warning("Reached end of CSV file while skipping rows")
                    return 0
            
            doctors_added = 0
            current_row = start_row
            batch_count = 0
            
            for row in csv_reader:
                current_row += 1
                batch_count += 1
                
                try:
                    doctor_name = row.get('Doctor Name', '').strip()
                    if not doctor_name:
                        logger.warning(f"Skipping row {current_row} - missing doctor name")
                        continue
                    
                    # Skip if doctor already exists
                    if doctor_exists(conn, doctor_name):
                        logger.info(f"Doctor already exists: {doctor_name}")
                        continue
                    
                    # Create user account for doctor
                    user_id = create_user_for_doctor(conn, doctor_name)
                    
                    # Extract specialty or use default
                    specialty = row.get('specialty', '').strip()
                    if not specialty:
                        specialty = "Plastic Surgeon"  # Default specialty
                    
                    # Extract education or use default
                    education = row.get('education', '').strip()
                    if not education:
                        education = DEFAULT_QUALIFICATION
                    
                    # Get experience as string
                    experience = row.get('Experience', '').strip()
                    
                    # Extract address and location
                    address = row.get('Address', '').strip()
                    city = row.get('city', '').strip()
                    state = row.get('state', '').strip()
                    
                    # Process profile image
                    profile_image = row.get('Profile Image', '').strip()
                    
                    # Insert doctor
                    with conn.cursor() as cursor:
                        if user_id:
                            cursor.execute(
                                """
                                INSERT INTO doctors (
                                    name, user_id, specialty, education,
                                    experience, bio, address, city, state,
                                    profile_image, consultation_fee, is_verified,
                                    created_at, updated_at
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                ) RETURNING id
                                """,
                                (
                                    doctor_name,
                                    user_id,
                                    specialty,
                                    education,
                                    experience,
                                    DEFAULT_BIO,
                                    address,
                                    city,
                                    state,
                                    profile_image,
                                    DEFAULT_CONSULTATION_FEE,
                                    True,  # Set verified to true by default
                                    datetime.now(),
                                    datetime.now()
                                )
                            )
                            result = cursor.fetchone()
                            if result:
                                doctor_id = result[0]
                                logger.info(f"Added doctor: {doctor_name} (ID: {doctor_id})")
                                doctors_added += 1
                            else:
                                logger.error(f"Failed to add doctor: {doctor_name}")
                                continue
                        else:
                            logger.error(f"Cannot add doctor without valid user_id: {doctor_name}")
                            continue
                    # Doctor has been added successfully in the above code
                    
                except Exception as e:
                    logger.error(f"Error processing row {current_row}: {str(e)}")
                    conn.rollback()
                
                # Commit every batch and save checkpoint
                if batch_count >= BATCH_SIZE:
                    conn.commit()
                    save_checkpoint(current_row)
                    batch_count = 0
                    logger.info(f"Batch completed. Total doctors added so far: {doctors_added}")
                    
                    # Sleep briefly to avoid timeout
                    time.sleep(0.1)
            
            # Commit any remaining items
            if batch_count > 0:
                conn.commit()
                save_checkpoint(current_row)
            
            elapsed = time.time() - start_time
            logger.info(f"Doctor import completed in {elapsed:.2f} seconds")
            logger.info(f"Added {doctors_added} doctors")
            
            return doctors_added
    
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        conn.rollback()
        return 0
    
    finally:
        conn.close()

if __name__ == "__main__":
    import_doctors()