#!/usr/bin/env python3
"""
Bulk import doctors script for the medical marketplace platform.

This script automates the direct SQL import of doctor profiles into the database
with proper error handling and validation.
"""
import os
import sys
import csv
import json
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"bulk_import_doctors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BATCH_SIZE = 5
CSV_FILE_PATH = "new_doctors.csv"
REQUIRED_FIELDS = ["name", "specialty", "experience", "city"]

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)

def validate_doctor(doctor):
    """Validate that a doctor has all required fields."""
    for field in REQUIRED_FIELDS:
        if field not in doctor or not doctor[field]:
            return False, f"Missing required field: {field}"
    return True, ""

def clean_integer(value, default=0):
    """Convert a string to integer, handling errors."""
    if not value:
        return default
    try:
        # Remove non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', str(value))
        return int(float(cleaned))
    except ValueError:
        return default

def generate_username(name):
    """Generate a username from doctor's name."""
    # Remove non-alphanumeric characters and replace spaces with underscores
    base_username = re.sub(r'[^\w\s]', '', name.lower()).replace(' ', '_')
    return f"dr_{base_username}"

def generate_email(name):
    """Generate an email from doctor's name."""
    # Remove non-alphanumeric characters and replace spaces with dots
    email_name = re.sub(r'[^\w\s]', '', name.lower()).replace(' ', '.')
    return f"{email_name}@example.com"

def create_user_for_doctor(conn, doctor):
    """Create a user account for a doctor."""
    cursor = conn.cursor()
    try:
        username = doctor.get('username', generate_username(doctor['name']))
        email = doctor.get('email', generate_email(doctor['name']))
        
        # Check if user already exists
        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email)
        )
        existing_user = cursor.fetchone()
        if existing_user:
            return existing_user[0]
        
        # Create new user
        cursor.execute(
            """
            INSERT INTO users (
                username, email, name, role, role_type, phone_number,
                created_at, is_verified, password_hash
            ) VALUES (
                %s, %s, %s, 'doctor', 'doctor', %s, NOW(), %s, %s
            ) RETURNING id
            """,
            (
                username,
                email,
                doctor['name'],
                doctor.get('phone_number', '+91' + str(9000000000 + hash(doctor['name']) % 1000000000)),
                doctor.get('is_verified', True),
                'pbkdf2:sha256:600000$default_password_hash'  # Default password hash
            )
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in create_user_for_doctor: {e}")
        raise
    finally:
        cursor.close()

def add_doctor(conn, doctor):
    """Add a single doctor to the database."""
    cursor = conn.cursor()
    try:
        # Check if doctor already exists
        cursor.execute(
            "SELECT id FROM doctors WHERE name = %s",
            (doctor['name'],)
        )
        if cursor.fetchone():
            logger.info(f"Doctor '{doctor['name']}' already exists, skipping")
            return False
            
        # Create user account for the doctor
        user_id = create_user_for_doctor(conn, doctor)
        
        # Prepare education data
        education = doctor.get('education', [])
        if isinstance(education, str):
            try:
                education = json.loads(education.replace("'", '"'))
            except json.JSONDecodeError:
                education = [{"degree": "MBBS", "institution": "Medical College", "year": ""}]
        
        # Prepare certifications data
        certifications = doctor.get('certifications', [])
        if isinstance(certifications, str):
            try:
                certifications = json.loads(certifications.replace("'", '"'))
            except json.JSONDecodeError:
                certifications = []
        
        # Insert doctor
        cursor.execute(
            """
            INSERT INTO doctors (
                user_id, name, specialty, experience, city,
                consultation_fee, is_verified, rating, review_count, created_at,
                bio, certifications, education, verification_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s
            )
            """,
            (
                user_id,
                doctor['name'],
                doctor['specialty'],
                clean_integer(doctor['experience']),
                doctor['city'],
                clean_integer(doctor.get('consultation_fee', 1500)),
                doctor.get('is_verified', False),
                float(doctor.get('rating', 4.5)),
                clean_integer(doctor.get('review_count', 20)),
                doctor.get('bio', 'Experienced healthcare professional specializing in cosmetic procedures.'),
                json.dumps(certifications),
                json.dumps(education),
                doctor.get('verification_status', 'pending')
            )
        )
        conn.commit()
        logger.info(f"Added doctor: {doctor['name']}")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding doctor '{doctor.get('name', 'UNKNOWN')}': {e}")
        raise
    finally:
        cursor.close()

def add_doctors_batch(conn, doctors):
    """Add a batch of doctors to the database."""
    inserted_count = 0
    error_count = 0
    
    for doctor in doctors:
        try:
            # Validate doctor data
            valid, error_msg = validate_doctor(doctor)
            if not valid:
                logger.warning(f"Skipping invalid doctor '{doctor.get('name', 'UNKNOWN')}': {error_msg}")
                error_count += 1
                continue
            
            if add_doctor(conn, doctor):
                inserted_count += 1
                
        except Exception as e:
            logger.error(f"Error processing doctor '{doctor.get('name', 'UNKNOWN')}': {e}")
            error_count += 1
    
    return inserted_count, error_count

def read_doctors_from_csv(csv_file_path):
    """Read doctors from CSV file."""
    doctors = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doctors.append(row)
        return doctors
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        sys.exit(1)

def main():
    """Main function to import doctors."""
    logger.info(f"Starting bulk import from {CSV_FILE_PATH}")
    
    # Read doctors from CSV
    doctors = read_doctors_from_csv(CSV_FILE_PATH)
    logger.info(f"Found {len(doctors)} doctors in CSV")
    
    # Get database connection
    conn = get_db_connection()
    
    # Process doctors in batches
    total_inserted = 0
    total_errors = 0
    total_batches = (len(doctors) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(doctors), BATCH_SIZE):
        batch = doctors[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} doctors)")
        
        inserted, errors = add_doctors_batch(conn, batch)
        total_inserted += inserted
        total_errors += errors
    
    conn.close()
    logger.info(f"Import completed: {total_inserted} doctors added, {total_errors} errors")

if __name__ == "__main__":
    main()