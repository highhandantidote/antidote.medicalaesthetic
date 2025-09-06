#!/usr/bin/env python3
"""
Import all remaining doctors in batches with separate transactions.

This script focuses only on doctor imports with larger batch sizes for faster processing.
"""
import os
import csv
import time
import json
import logging
import psycopg2
import random
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DOCTORS_CSV_PATH = "./attached_assets/new_doctors_profiles2 - Sheet1.csv"
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."
BATCH_SIZE = 20  # Process data in larger batches for doctors

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def extract_experience_years(experience_text):
    """Extract years of experience from text like '20 years experience'."""
    if not experience_text:
        return random.randint(5, 15)  # Default value
    
    try:
        # Extract the number from text like "20 years experience"
        return int(experience_text.split()[0])
    except (ValueError, IndexError, AttributeError):
        return random.randint(5, 15)  # Fallback value

def format_education_json(education_text):
    """Format education text into JSON structure."""
    if not education_text:
        return json.dumps([{"degree": "MBBS", "institution": "Medical College", "year": ""}])
    
    # Split by comma and create JSON structure
    degrees = [degree.strip() for degree in education_text.split(',')]
    education_list = [{"degree": degree, "institution": "", "year": ""} for degree in degrees]
    return json.dumps(education_list)

def import_all_doctors():
    """Import all remaining doctors in batches with separate transactions."""
    logger.info("Starting bulk doctor import...")
    
    conn = get_db_connection()
    try:
        # Get existing doctor names
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM doctors")
            existing_doctor_names = {row[0].lower() for row in cursor.fetchall() if row[0]}
        
        logger.info(f"Found {len(existing_doctor_names)} existing doctors")
        
        # Import all remaining doctors
        import_count = 0
        duplicate_count = 0
        error_count = 0
        
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            all_doctors = list(reader)
            
        # Process in batches
        total_doctors = len(all_doctors)
        logger.info(f"Found {total_doctors} doctors in CSV")
        
        for batch_start in range(0, total_doctors, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_doctors)
            batch = all_doctors[batch_start:batch_end]
            
            logger.info(f"Processing doctor batch {batch_start+1}-{batch_end} of {total_doctors}")
            
            # Process each doctor in the batch with its own transaction
            for doctor in batch:
                doctor_name = doctor.get('Doctor Name', '')
                if not doctor_name:
                    logger.warning("Skipping doctor with no name")
                    continue
                
                # Skip duplicates
                if doctor_name.lower() in existing_doctor_names:
                    duplicate_count += 1
                    logger.info(f"Skipping duplicate doctor: {doctor_name}")
                    continue
                
                # New connection and transaction for each doctor
                doctor_conn = get_db_connection()
                try:
                    # Start a transaction
                    with doctor_conn:
                        with doctor_conn.cursor() as cursor:
                            # Generate a username from the doctor's name
                            username = doctor_name.lower().replace(' ', '_').replace('.', '')
                            email = f"{username}@example.com"
                            phone_number = f"+91{random.randint(7000000000, 9999999999)}"
                            
                            # Check if phone number exists
                            cursor.execute("SELECT id FROM users WHERE phone_number = %s", (phone_number,))
                            result = cursor.fetchone()
                            if result and result[0]:
                                # If phone exists, generate a new one
                                phone_number = f"+91{random.randint(7000000000, 9999999999)}"
                            
                            # Create a new user
                            cursor.execute("""
                                INSERT INTO users (
                                    username, email, name, role, role_type, phone_number,
                                    created_at, is_verified, password_hash
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                            """, (
                                username, 
                                email,
                                doctor_name,
                                'doctor',  # role
                                'doctor',  # role_type
                                phone_number,
                                datetime.utcnow(),
                                True,   # is_verified
                                "pbkdf2:sha256:600000$default_password_hash"  # placeholder hash
                            ))
                            
                            result = cursor.fetchone()
                            if not result:
                                raise Exception("Failed to create user, no ID returned")
                            
                            user_id = result[0]
                            
                            # Extract experience years
                            experience = extract_experience_years(doctor.get('Experience', ''))
                            
                            # Format education as JSON
                            education_json = format_education_json(doctor.get('education', ''))
                            
                            # Default certifications as empty JSON array
                            certifications_json = json.dumps([])
                            
                            # Extract hospital from address field
                            address = doctor.get('Address', '')
                            hospital = address.split(',')[0] if address else 'Unknown Hospital'
                            
                            # Insert the doctor
                            cursor.execute("""
                                INSERT INTO doctors (
                                    user_id, name, specialty, experience, city, state, hospital,
                                    consultation_fee, is_verified, rating, review_count, created_at,
                                    bio, certifications, education, profile_image, image_url, qualification,
                                    practice_location, verification_status
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """, (
                                user_id,
                                doctor_name,
                                doctor.get('specialty', 'Plastic Surgery'),
                                experience,
                                doctor.get('city', 'Delhi'),
                                doctor.get('state', ''),
                                hospital,
                                DEFAULT_CONSULTATION_FEE,  # consultation_fee
                                False,  # is_verified
                                random.uniform(4.0, 5.0),  # rating
                                random.randint(10, 100),  # review_count
                                datetime.utcnow(),
                                DEFAULT_BIO,  # bio
                                certifications_json,  # certifications
                                education_json,  # education
                                doctor.get('Profile Image', ''),  # profile_image
                                doctor.get('Profile Image', ''),  # image_url
                                doctor.get('education', ''),      # qualification
                                address,        # practice_location
                                'pending'                 # verification_status
                            ))
                    
                    # If we get here, the transaction was successful
                    import_count += 1
                    # Add to our list of processed doctors to avoid duplicates in the same run
                    existing_doctor_names.add(doctor_name.lower())
                    
                    # Log progress for each successful import
                    logger.info(f"Successfully imported doctor {import_count}: {doctor_name}")
                        
                except Exception as e:
                    logger.error(f"Error importing doctor {doctor_name}: {str(e)}")
                    error_count += 1
                finally:
                    doctor_conn.close()
            
            # Log batch progress
            logger.info(f"Completed batch {batch_start+1}-{batch_end}: {import_count} doctors imported so far")
        
        logger.info(f"Successfully imported {import_count} doctors")
        logger.info(f"Skipped {duplicate_count} duplicates")
        logger.info(f"Encountered {error_count} errors")
        
    except Exception as e:
        logger.error(f"Bulk doctor import failed: {str(e)}")
        import_count = 0
    finally:
        conn.close()
    
    return import_count

def verify_doctor_count():
    """Verify the final count of doctors."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cursor.fetchone()[0]
            
            logger.info(f"Final doctor count: {doctor_count}")
    finally:
        conn.close()

def main():
    """Run the bulk doctor import."""
    start_time = time.time()
    
    # Import doctors
    doctor_count = import_all_doctors()
    
    # Verify final count
    verify_doctor_count()
    
    total_time = time.time() - start_time
    logger.info(f"Bulk doctor import completed in {total_time:.2f} seconds")
    logger.info(f"Added {doctor_count} doctors")

if __name__ == "__main__":
    main()