#!/usr/bin/env python3
"""
Import exactly five new doctors to the database.

This script is a simplified version that focuses on importing just 5 doctors
with proper handling of all required fields.
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
START_ROW = 78  # Start at the current doctor count

# Default values for missing fields
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def get_existing_doctor_emails():
    """Get a set of existing doctor emails to avoid duplicates."""
    existing_emails = set()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get emails from users table only
            cursor.execute("SELECT LOWER(email) FROM users WHERE email IS NOT NULL")
            for row in cursor.fetchall():
                if row[0]:
                    existing_emails.add(row[0].lower())
            
            # Get user_ids from doctors table
            cursor.execute("SELECT user_id FROM doctors WHERE user_id IS NOT NULL")
            user_ids = [row[0] for row in cursor.fetchall() if row[0]]
            
            # If we have user_ids, get their emails
            if user_ids:
                placeholders = ','.join(['%s'] * len(user_ids))
                cursor.execute(f"SELECT LOWER(email) FROM users WHERE id IN ({placeholders})", user_ids)
                for row in cursor.fetchall():
                    if row[0]:
                        existing_emails.add(row[0].lower())
    finally:
        conn.close()
    
    return existing_emails

def import_five_doctors():
    """Import exactly five new doctors to the database."""
    if not os.path.exists(DOCTORS_CSV_PATH):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV_PATH}")
        return False
    
    # Get existing doctor emails to avoid duplicates
    existing_emails = get_existing_doctor_emails()
    logger.info(f"Found {len(existing_emails)} existing emails")
    
    # Read CSV file to find doctors to add
    doctors_to_import = []
    with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i < START_ROW:  # Skip doctors we've likely already processed
                continue
                
            email = row.get('Email', '').strip().lower()
            
            # Skip if email already exists and is not empty
            if email and email in existing_emails:
                continue
                
            doctors_to_import.append(row)
            
            # Once we have 5 doctors, stop collecting
            if len(doctors_to_import) >= 5:
                break
    
    logger.info(f"Found {len(doctors_to_import)} doctors to import")
    
    # Initialize counters
    doctors_added = 0
    doctors_skipped = 0
    
    # Now import each doctor one by one
    conn = get_db_connection()
    try:
        for doctor in doctors_to_import:
            # Extract doctor data with proper defaults
            name = doctor.get('Doctor Name', '').strip()
            email = doctor.get('Email', '').strip().lower()
            specialty = doctor.get('Specialty', '').strip()
            qualification = doctor.get('Qualification', '').strip()
            phone = doctor.get('Phone', '').strip()
            clinic_address = doctor.get('Clinic Address', '').strip()
            city = doctor.get('City', '').strip()
            profile_image = doctor.get('Profile Image', '').strip()
            bio = doctor.get('Bio', DEFAULT_BIO).strip()
            
            # Skip if essential fields are missing
            if not name or not specialty:
                logger.warning(f"Skipping doctor with missing essential data: {name}")
                doctors_skipped += 1
                continue
            
            # Generate username from email or name
            username = email.split('@')[0] if email else name.lower().replace(' ', '_')
            
            try:
                # Set autocommit to False to use transactions
                conn.autocommit = False
                
                # Initialize variables
                user_id = None
                
                # Create user account if email is provided
                if email:
                    with conn.cursor() as cursor:
                        # Check if user already exists
                        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
                        user_result = cursor.fetchone()
                        
                        if user_result and user_result[0] is not None:
                            user_id = user_result[0]
                            logger.info(f"Using existing user for email: {email}")
                        else:
                            # Generate a secure password
                            password = f"temp{random.randint(100000, 999999)}"
                            password_hash = generate_password_hash(password)
                            
                            # Create user
                            cursor.execute(
                                """
                                INSERT INTO users 
                                (username, email, password_hash, created_at, role)
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING id
                                """,
                                (username, email, password_hash, datetime.now(), 'doctor')
                            )
                            result = cursor.fetchone()
                            user_id = result[0] if result else None
                            
                            if not user_id:
                                raise ValueError(f"Failed to create user account for doctor: {name}")
                            
                            logger.info(f"Created new user account for: {name}")
                
                # Try to convert experience years to integer
                try:
                    experience_years = int(doctor.get('Experience', '0'))
                except (ValueError, TypeError):
                    experience_years = 0
                
                # Create doctor entry
                with conn.cursor() as cursor:
                    if user_id:
                        # Create doctor with user_id
                        cursor.execute(
                            """
                            INSERT INTO doctors 
                            (name, specialty, qualification, profile_image, bio, experience, 
                             consultation_fee, user_id, is_verified, created_at, city)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """,
                            (
                                name, specialty, qualification, profile_image, bio, experience_years,
                                DEFAULT_CONSULTATION_FEE, user_id, True, datetime.now(), city
                            )
                        )
                    else:
                        # Create doctor without user_id
                        cursor.execute(
                            """
                            INSERT INTO doctors 
                            (name, specialty, qualification, profile_image, bio, experience, 
                             consultation_fee, is_verified, created_at, city)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """,
                            (
                                name, specialty, qualification, profile_image, bio, experience_years,
                                DEFAULT_CONSULTATION_FEE, True, datetime.now(), city
                            )
                        )
                    
                    result = cursor.fetchone()
                    if not result:
                        raise ValueError(f"Failed to create doctor profile: {name}")
                
                # Commit transaction
                conn.commit()
                
                # Add to existing emails to avoid duplicates
                if email:
                    existing_emails.add(email)
                
                logger.info(f"Added doctor: {name}")
                doctors_added += 1
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error adding doctor {name}: {str(e)}")
                doctors_skipped += 1
        
        logger.info(f"Import complete. Added {doctors_added} doctors, skipped {doctors_skipped}")
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
    
    added_count = import_five_doctors()
    
    if added_count > 0:
        logger.info(f"Successfully added {added_count} doctors in {time.time() - start_time:.2f} seconds")
    else:
        logger.error("Failed to add any doctors")

if __name__ == "__main__":
    main()