#!/usr/bin/env python3
"""
Add more doctors to the Antidote platform database.

This script focuses only on adding more doctors to reach our target count.
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
BATCH_SIZE = 5  # Process this many doctors at once to avoid timeouts

# Default values
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

def read_doctors_from_csv(offset=0, limit=BATCH_SIZE):
    """Read a batch of doctors from the CSV file."""
    doctors = []
    try:
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Skip to the offset
            for _ in range(offset):
                next(reader, None)
            
            # Read up to the limit
            count = 0
            for row in reader:
                if count >= limit:
                    break
                doctors.append(row)
                count += 1
                
        return doctors
    except Exception as e:
        logger.error(f"Error reading doctors from CSV: {str(e)}")
        return []

def count_total_doctors_in_csv():
    """Count total doctors in CSV."""
    try:
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as f:
            return sum(1 for _ in csv.reader(f)) - 1  # Subtract header row
    except Exception as e:
        logger.error(f"Error counting doctors in CSV: {str(e)}")
        return 0

def count_existing_doctors():
    """Count existing doctors in the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error counting existing doctors: {str(e)}")
        return 0
    finally:
        if conn:
            conn.close()

def doctor_exists(conn, name):
    """Check if a doctor with the given name already exists."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM doctors WHERE name = %s",
            (name,)
        )
        return cursor.fetchone() is not None

def create_user_for_doctor(conn, doctor_name, email=None):
    """Create a user account for a doctor."""
    # Generate email and username from doctor name
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
        try:
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
        except Exception as e:
            logger.error(f"Error creating user for doctor {doctor_name}: {str(e)}")
            conn.rollback()
            return None

def import_doctors(start_index=0, batch_size=BATCH_SIZE):
    """Import a batch of doctors from CSV."""
    conn = get_db_connection()
    doctors_added = 0
    
    try:
        # Read a batch of doctors from CSV
        doctors_batch = read_doctors_from_csv(start_index, batch_size)
        
        if not doctors_batch:
            logger.info(f"No more doctors to import starting at index {start_index}")
            return 0
            
        logger.info(f"Processing {len(doctors_batch)} doctors starting at index {start_index}")
        
        # Process each doctor
        for doctor_data in doctors_batch:
            try:
                # Basic data validation
                doctor_name = doctor_data.get('name', '').strip()
                if not doctor_name:
                    logger.warning("Skipping doctor with missing name")
                    continue
                
                # Check if doctor already exists
                if doctor_exists(conn, doctor_name):
                    logger.info(f"Doctor already exists: {doctor_name}")
                    continue
                
                # Create user account for doctor
                user_id = create_user_for_doctor(conn, doctor_name)
                
                if not user_id:
                    logger.error(f"Cannot add doctor without valid user_id: {doctor_name}")
                    continue
                
                # Map CSV fields to database fields
                specialty = doctor_data.get('specialty', 'Cosmetic Surgery').strip()
                education = doctor_data.get('education', 'MBBS, MS').strip()
                experience = doctor_data.get('experience', '10+ years experience').strip()
                bio = doctor_data.get('bio', DEFAULT_BIO).strip()
                address = doctor_data.get('address', '').strip()
                city = doctor_data.get('city', 'Mumbai').strip()
                state = doctor_data.get('state', 'Maharashtra').strip()
                
                # Parse consultation fee
                try:
                    consultation_fee = int(doctor_data.get('consultation_fee', DEFAULT_CONSULTATION_FEE))
                except (ValueError, TypeError):
                    consultation_fee = DEFAULT_CONSULTATION_FEE
                
                # Insert doctor
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO doctors (
                            name, user_id, specialty, education,
                            experience, bio, address, city, state,
                            consultation_fee, is_verified,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            doctor_name,
                            user_id,
                            specialty,
                            education,
                            experience,
                            bio,
                            address,
                            city,
                            state,
                            consultation_fee,
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
                        
                        # Commit each doctor individually
                        conn.commit()
                        
                        # Brief pause to avoid timeouts
                        time.sleep(0.2)
                    else:
                        logger.error(f"Failed to add doctor: {doctor_name}")
                        conn.rollback()
                    
            except Exception as e:
                logger.error(f"Error adding doctor {doctor_name}: {str(e)}")
                conn.rollback()
        
        return doctors_added
        
    except Exception as e:
        logger.error(f"Error in import_doctors: {str(e)}")
        return doctors_added
    finally:
        conn.close()

def check_database_status():
    """Check the current status of the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check doctors
            cursor.execute("SELECT COUNT(*) FROM doctors")
            result = cursor.fetchone()
            doctor_count = result[0] if result else 0
            
            # Get total doctors in CSV
            total_doctors = count_total_doctors_in_csv()
            
            # Print summary
            logger.info("=" * 80)
            logger.info("DOCTOR IMPORT STATUS")
            logger.info("=" * 80)
            logger.info(f"Doctors: {doctor_count} out of {total_doctors} in CSV ({doctor_count/total_doctors:.1%})")
            logger.info("=" * 80)
            
            # Return counts for potential use by other scripts
            return {
                "doctors": doctor_count,
                "total_doctors": total_doctors
            }
            
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def main():
    """Main function to import doctors in batches."""
    start_time = time.time()
    
    # Check current database status
    status_before = check_database_status()
    
    # Determine where to start
    existing_doctors = count_existing_doctors()
    logger.info(f"Found {existing_doctors} existing doctors in database")
    
    # Import doctors in batches
    total_imported = 0
    current_index = existing_doctors
    batch_size = BATCH_SIZE
    
    # Import up to 3 batches at a time to avoid timeouts
    max_batches = 3
    batch_count = 0
    
    while batch_count < max_batches:
        doctors_added = import_doctors(current_index, batch_size)
        
        if doctors_added == 0:
            logger.info("No more doctors to import")
            break
            
        total_imported += doctors_added
        current_index += batch_size
        batch_count += 1
        
        logger.info(f"Imported batch {batch_count}: {doctors_added} doctors")
    
    # Check final database status
    status_after = check_database_status()
    
    elapsed = time.time() - start_time
    logger.info(f"Doctor import completed in {elapsed:.2f} seconds")
    logger.info(f"Total doctors added in this run: {total_imported}")
    
    if status_before and status_after:
        docs_diff = status_after["doctors"] - status_before["doctors"]
        logger.info(f"Net doctors added: {docs_diff}")
    
    logger.info("Doctor import complete!")

if __name__ == "__main__":
    main()