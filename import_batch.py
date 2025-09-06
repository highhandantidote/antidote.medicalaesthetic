#!/usr/bin/env python3
"""
Combined database import script with robust error handling.

This script works with both procedures and doctors in small batches with
proper checkpointing and error handling to ensure reliable imports.
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
PROCEDURES_CSV_PATH = "./attached_assets/new_procedure_details - Sheet1.csv"
DOCTORS_CSV_PATH = "./attached_assets/new_doctors_profiles2 - Sheet1.csv"
PROCEDURE_START_ROW = 371  # Start from current progress
DOCTOR_START_ROW = 103  # Start from current progress
BATCH_SIZE = 5  # Very small batches for reliability

# Default values for missing fields
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."
DEFAULT_QUALIFICATION = "MBBS, MS"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

def get_checkpoint(checkpoint_type):
    """Get the current import checkpoint."""
    if checkpoint_type == 'procedure':
        checkpoint_file = "procedure_import_checkpoint.txt"
        default_value = PROCEDURE_START_ROW
    else:  # doctor
        checkpoint_file = "doctor_import_checkpoint.txt"
        default_value = DOCTOR_START_ROW
        
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return default_value
    return default_value

def save_checkpoint(checkpoint_type, row_num):
    """Save the current import checkpoint."""
    if checkpoint_type == 'procedure':
        checkpoint_file = "procedure_import_checkpoint.txt"
    else:  # doctor
        checkpoint_file = "doctor_import_checkpoint.txt"
        
    with open(checkpoint_file, "w") as f:
        f.write(str(row_num))
    logger.info(f"Progress saved: Processed {checkpoint_type} up to row {row_num}")

def clean_integer(value):
    """Clean cost values by removing commas, currency symbols and converting to integer."""
    if not value:
        return None
    # Remove currency symbols and commas
    cleaned = value.replace(",", "").replace("₹", "").replace("$", "").replace("Rs.", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        # If conversion fails, return a default value
        logger.warning(f"Could not convert cost value '{value}' to integer, using default")
        return 10000  # Default value for invalid costs

def get_body_part_id(conn, body_part_name):
    """Get body part ID by name, creating it if it doesn't exist."""
    with conn.cursor() as cursor:
        # Check if body part exists
        cursor.execute(
            "SELECT id FROM body_parts WHERE name = %s",
            (body_part_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new body part if it doesn't exist
        cursor.execute(
            """
            INSERT INTO body_parts (name, created_at, updated_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (body_part_name, datetime.now(), datetime.now())
        )
        body_part_id = cursor.fetchone()[0]
        conn.commit()
        logger.info(f"Created new body part: {body_part_name} (ID: {body_part_id})")
        return body_part_id

def get_category_id(conn, category_name, body_part_id):
    """Get category ID by name and body part, creating it if it doesn't exist."""
    with conn.cursor() as cursor:
        # Check if category exists
        cursor.execute(
            "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
            (category_name, body_part_id)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new category if it doesn't exist
        cursor.execute(
            """
            INSERT INTO categories (name, body_part_id, created_at, description)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (category_name, body_part_id, datetime.now(), f"Category for {category_name} procedures")
        )
        category_id = cursor.fetchone()[0]
        conn.commit()
        logger.info(f"Created new category: {category_name} for body part ID {body_part_id} (ID: {category_id})")
        return category_id

def procedure_exists(conn, procedure_name, category_id):
    """Check if procedure already exists with the same name and category or just the name."""
    with conn.cursor() as cursor:
        # First check by name and category
        cursor.execute(
            "SELECT id FROM procedures WHERE procedure_name = %s AND category_id = %s",
            (procedure_name, category_id)
        )
        if cursor.fetchone() is not None:
            return True
            
        # If not found, check just by name to avoid duplicate key errors
        cursor.execute(
            "SELECT id FROM procedures WHERE procedure_name = %s",
            (procedure_name,)
        )
        return cursor.fetchone() is not None

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

def import_procedures(max_count=20):
    """
    Import procedures from CSV in small batches with error handling.
    
    Args:
        max_count: Maximum number of procedures to import in this run
    """
    start_time = time.time()
    conn = get_db_connection()
    
    try:
        start_row = get_checkpoint('procedure')
        logger.info(f"Starting procedure import from row {start_row}")
        
        with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            # Skip to the starting row
            for _ in range(start_row):
                try:
                    next(csv_reader)
                except StopIteration:
                    logger.warning("Reached end of CSV file while skipping rows")
                    return 0
            
            procedures_added = 0
            current_row = start_row
            batch_count = 0
            
            for row in csv_reader:
                current_row += 1
                batch_count += 1
                
                try:
                    body_part_name = row.get('body_part_name', '').strip()
                    category_name = row.get('category_name', '').strip()
                    procedure_name = row.get('procedure_name', '').strip()
                    
                    if not body_part_name or not category_name or not procedure_name:
                        logger.warning(f"Skipping row {current_row} - missing required fields")
                        continue
                    
                    # Get or create body part and category
                    body_part_id = get_body_part_id(conn, body_part_name)
                    category_id = get_category_id(conn, category_name, body_part_id)
                    
                    # Skip if procedure already exists
                    if procedure_exists(conn, procedure_name, category_id):
                        logger.info(f"Procedure already exists: {procedure_name} (category: {category_name})")
                        continue
                    
                    # Clean cost values
                    min_cost = clean_integer(row.get('min_cost'))
                    max_cost = clean_integer(row.get('max_cost'))
                    
                    # Insert procedure
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO procedures (
                                procedure_name, alternative_names, short_description, overview, 
                                procedure_details, ideal_candidates, recovery_time, 
                                procedure_duration, hospital_stay_required, 
                                min_cost, max_cost, risks, procedure_types, 
                                recovery_process, results_duration, benefits, 
                                benefits_detailed, alternative_procedures, 
                                category_id, created_at, updated_at, tags
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            """,
                            (
                                procedure_name,
                                row.get('alternative_names', ''),
                                row.get('short_description', ''),
                                row.get('overview', ''),
                                row.get('procedure_details', ''),
                                row.get('ideal_candidates', ''),
                                row.get('recovery_time', ''),
                                row.get('procedure_duration', ''),
                                row.get('hospital_stay_required', ''),
                                min_cost,
                                max_cost,
                                row.get('risks', ''),
                                row.get('procedure_types', ''),
                                row.get('recovery_process', ''),
                                row.get('results_duration', ''),
                                row.get('benefits', ''),
                                row.get('benefits_detailed', ''),
                                row.get('alternative_procedures', ''),
                                category_id,
                                datetime.now(),
                                datetime.now(),
                                None  # Temporarily set tags to NULL to avoid format issues
                            )
                        )
                    
                    procedures_added += 1
                    logger.info(f"Added procedure: {procedure_name} (category: {category_name})")
                    
                except Exception as e:
                    logger.error(f"Error processing row {current_row}: {str(e)}")
                    conn.rollback()
                
                # Commit every batch and save checkpoint
                if batch_count >= BATCH_SIZE:
                    conn.commit()
                    save_checkpoint('procedure', current_row)
                    batch_count = 0
                    logger.info(f"Batch completed. Total procedures added so far: {procedures_added}")
                    
                    # Sleep briefly to avoid timeout
                    time.sleep(0.1)
                
                # Stop after processing max_count procedures
                if procedures_added >= max_count:
                    logger.info(f"Reached maximum count of {max_count} procedures for this run")
                    break
            
            # Commit any remaining items
            if batch_count > 0:
                conn.commit()
                save_checkpoint('procedure', current_row)
            
            elapsed = time.time() - start_time
            logger.info(f"Procedure import completed in {elapsed:.2f} seconds")
            logger.info(f"Added {procedures_added} procedures")
            
            return procedures_added
    
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        conn.rollback()
        return 0
    
    finally:
        conn.close()

def import_doctors(max_count=10):
    """
    Import doctors from CSV in small batches with error handling.
    
    Args:
        max_count: Maximum number of doctors to import in this run
    """
    start_time = time.time()
    conn = get_db_connection()
    
    try:
        start_row = get_checkpoint('doctor')
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
                    
                    # Insert doctor only if we have a valid user_id
                    if user_id:
                        with conn.cursor() as cursor:
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
                    else:
                        logger.error(f"Cannot add doctor without valid user_id: {doctor_name}")
                        
                except Exception as e:
                    logger.error(f"Error processing row {current_row}: {str(e)}")
                    conn.rollback()
                
                # Commit every batch and save checkpoint
                if batch_count >= BATCH_SIZE:
                    conn.commit()
                    save_checkpoint('doctor', current_row)
                    batch_count = 0
                    logger.info(f"Batch completed. Total doctors added so far: {doctors_added}")
                    
                    # Sleep briefly to avoid timeout
                    time.sleep(0.1)
                
                # Stop after processing max_count doctors
                if doctors_added >= max_count:
                    logger.info(f"Reached maximum count of {max_count} doctors for this run")
                    break
            
            # Commit any remaining items
            if batch_count > 0:
                conn.commit()
                save_checkpoint('doctor', current_row)
            
            elapsed = time.time() - start_time
            logger.info(f"Doctor import completed in {elapsed:.2f} seconds")
            logger.info(f"Added {doctors_added} doctors")
            
            return doctors_added
    
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        conn.rollback()
        return 0
    
    finally:
        if conn:
            conn.close()

def check_database_status():
    """Check the current status of the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check body parts
            cursor.execute("SELECT COUNT(*) FROM body_parts")
            result = cursor.fetchone()
            body_part_count = result[0] if result else 0
            
            # Check categories
            cursor.execute("SELECT COUNT(*) FROM categories")
            result = cursor.fetchone()
            category_count = result[0] if result else 0
            
            # Check procedures
            cursor.execute("SELECT COUNT(*) FROM procedures")
            result = cursor.fetchone()
            procedure_count = result[0] if result else 0
            
            # Check doctors
            cursor.execute("SELECT COUNT(*) FROM doctors")
            result = cursor.fetchone()
            doctor_count = result[0] if result else 0
            
            # Print summary
            logger.info("=" * 50)
            logger.info("DATABASE IMPORT STATUS")
            logger.info("=" * 50)
            logger.info(f"Body Parts: {body_part_count}")
            logger.info(f"Categories: {category_count}")
            logger.info(f"Procedures: {procedure_count}")
            logger.info(f"Doctors: {doctor_count}")
            logger.info("=" * 50)
            
            # Return counts for potential use by other scripts
            return {
                "body_parts": body_part_count,
                "categories": category_count,
                "procedures": procedure_count,
                "doctors": doctor_count
            }
            
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def main():
    """Run both import processes with limited counts per run."""
    overall_start_time = time.time()
    
    # Check current database status
    status_before = check_database_status()
    
    # First import procedures - limit to 5 per run
    proc_added = import_procedures(max_count=5)
    logger.info(f"Procedures import complete. Added {proc_added} procedures.")
    
    # Then import doctors - limit to 3 per run
    doc_added = import_doctors(max_count=3)
    logger.info(f"Doctors import complete. Added {doc_added} doctors.")
    
    # Check final database status
    status_after = check_database_status()
    
    overall_elapsed = time.time() - overall_start_time
    logger.info(f"Overall import completed in {overall_elapsed:.2f} seconds")
    
    if status_before and status_after:
        procs_diff = status_after["procedures"] - status_before["procedures"]
        docs_diff = status_after["doctors"] - status_before["doctors"]
        logger.info(f"Net procedures added: {procs_diff}")
        logger.info(f"Net doctors added: {docs_diff}")
    
    logger.info("Run this script again to continue importing more data.")

if __name__ == "__main__":
    main()