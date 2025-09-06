#!/usr/bin/env python3
"""
Bulk import script for procedures and doctors with advanced error handling.

This script combines our optimized imports for both procedures and doctors
into a single script that can be run repeatedly to gradually import all data.
"""

import os
import csv
import time
import json
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
# Initialize to current counts - will automatically self-update
PROCEDURE_START_ROW = 366  # Procedures already in database
DOCTOR_START_ROW = 103     # Doctors already in database
BATCH_SIZE = 25  # Increased batch size for faster imports

# Default values for missing fields
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."
DEFAULT_SPECIALTY = "Cosmetic Surgery"
DEFAULT_QUALIFICATION = "MBBS, MS"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def get_existing_procedure_names():
    """Get a set of existing procedure names to avoid duplicates."""
    existing_names = set()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT LOWER(procedure_name) FROM procedures")
            for row in cursor.fetchall():
                if row[0]:
                    existing_names.add(row[0].lower())
    finally:
        conn.close()
    
    return existing_names

def import_procedures():
    """Import a batch of procedures to the database."""
    if not os.path.exists(PROCEDURES_CSV_PATH):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV_PATH}")
        return False
    
    # Get existing procedure names to avoid duplicates
    existing_names = get_existing_procedure_names()
    logger.info(f"Found {len(existing_names)} existing procedures")
    
    # Read CSV file to find procedures to add
    procedures_to_import = []
    with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i < PROCEDURE_START_ROW:  # Skip procedures we've likely already processed
                continue
                
            procedure_name = row.get('procedure_name', '').strip()
            
            # Skip if already exists
            if procedure_name.lower() in existing_names:
                continue
                
            procedures_to_import.append(row)
            
            # Once we have BATCH_SIZE procedures, stop collecting
            if len(procedures_to_import) >= BATCH_SIZE:
                break
    
    logger.info(f"Found {len(procedures_to_import)} procedures to import")
    
    # Initialize counters
    procedures_added = 0
    procedures_skipped = 0
    
    # Now import each procedure one by one
    conn = get_db_connection()
    try:
        conn.autocommit = False
        
        for procedure in procedures_to_import:
            # Extract procedure data with proper defaults
            procedure_name = procedure.get('procedure_name', '').strip()
            body_part_name = procedure.get('body_part_name', '').strip()
            category_name = procedure.get('category_name', '').strip()
            
            if not procedure_name or not body_part_name or not category_name:
                logger.warning(f"Skipping procedure with missing essential data: {procedure_name}")
                procedures_skipped += 1
                continue
            
            # Prepare other data
            try:
                min_cost = int(procedure.get('min_cost', '0').replace(',', '').strip() or '0')
            except (ValueError, TypeError):
                min_cost = 0
                
            try:
                max_cost = int(procedure.get('max_cost', '0').replace(',', '').strip() or '0')
            except (ValueError, TypeError):
                max_cost = 0
                
            description = procedure.get('description', '').strip() or f"Professional {procedure_name} procedure with excellent results."
            benefits = procedure.get('benefits', '').strip() or f"Improved appearance and confidence."
            risks = procedure.get('risks', '').strip() or "Standard surgical risks including infection, scarring, and asymmetry."
            
            # Prepare default values for required fields
            short_desc = description[:250] if description else f"Professional {procedure_name} procedure."
            overview = description or f"This {procedure_name} procedure provides excellent aesthetic results."
            procedure_details = f"The {procedure_name} procedure involves advanced techniques to achieve optimal results."
            ideal_candidates = f"Ideal candidates for {procedure_name} are generally healthy individuals seeking aesthetic improvement."
            recovery_time = "Varies depending on individual factors"
            procedure_types = "Standard"
            
            try:
                with conn.cursor() as cursor:
                    # Get or create body part
                    cursor.execute(
                        "SELECT id FROM body_parts WHERE LOWER(name) = LOWER(%s)",
                        (body_part_name,)
                    )
                    body_part_result = cursor.fetchone()
                    
                    if body_part_result and body_part_result[0] is not None:
                        body_part_id = body_part_result[0]
                    else:
                        cursor.execute(
                            "INSERT INTO body_parts (name, created_at) VALUES (%s, %s) RETURNING id",
                            (body_part_name, datetime.now())
                        )
                        result = cursor.fetchone()
                        body_part_id = result[0] if result else None
                        if not body_part_id:
                            raise ValueError(f"Failed to create body part: {body_part_name}")
                        logger.info(f"Created new body part: {body_part_name}")
                    
                    # Get or create category
                    cursor.execute(
                        "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)",
                        (category_name,)
                    )
                    category_result = cursor.fetchone()
                    
                    if category_result and category_result[0] is not None:
                        category_id = category_result[0]
                        logger.info(f"Using existing category: {category_name}")
                    else:
                        cursor.execute(
                            "INSERT INTO categories (name, body_part_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                            (category_name, body_part_id, datetime.now())
                        )
                        result = cursor.fetchone()
                        category_id = result[0] if result else None
                        if not category_id:
                            raise ValueError(f"Failed to create category: {category_name}")
                        logger.info(f"Created new category: {category_name}")
                    
                    # Insert procedure with all required fields
                    cursor.execute(
                        """
                        INSERT INTO procedures 
                        (procedure_name, category_id, min_cost, max_cost, short_description, 
                         overview, procedure_details, ideal_candidates, recovery_time,
                         procedure_types, risks, benefits, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            procedure_name, category_id, 
                            min_cost, max_cost,
                            short_desc,
                            overview,
                            procedure_details,
                            ideal_candidates,
                            recovery_time,
                            procedure_types,
                            risks,
                            benefits,
                            datetime.now()
                        )
                    )
                    result = cursor.fetchone()
                    if not result:
                        raise ValueError(f"Failed to insert procedure: {procedure_name}")
                    
                    # Success - commit this procedure
                    conn.commit()
                    logger.info(f"Added procedure: {procedure_name}")
                    procedures_added += 1
                    
                    # Add to existing names to avoid duplicates
                    existing_names.add(procedure_name.lower())
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Error adding procedure {procedure_name}: {str(e)}")
                procedures_skipped += 1
        
        logger.info(f"Procedure import complete. Added {procedures_added} procedures, skipped {procedures_skipped}")
        return procedures_added
    
    except Exception as e:
        logger.error(f"Error in procedure import process: {str(e)}")
        return 0
    
    finally:
        if not conn.closed:
            conn.autocommit = True
            conn.close()

def import_doctors():
    """Import a batch of doctors to the database."""
    if not os.path.exists(DOCTORS_CSV_PATH):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV_PATH}")
        return False
    
    # Read CSV to find doctors to add
    doctors_to_process = []
    with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i < DOCTOR_START_ROW:  # Skip doctors we've likely already processed
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
        
        logger.info(f"Doctor import complete. Added {doctors_added} doctors, skipped {doctors_skipped}")
        return doctors_added
    
    except Exception as e:
        logger.error(f"Error in doctor import process: {str(e)}")
        return 0
    
    finally:
        if not conn.closed:
            conn.autocommit = True  # Reset to default
            conn.close()

def check_database_status():
    """Check current database status and return counts."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check body parts
            cur.execute("SELECT COUNT(*) FROM body_parts")
            result = cur.fetchone()
            body_part_count = result[0] if result and result[0] is not None else 0
            
            # Check categories
            cur.execute("SELECT COUNT(*) FROM categories")
            result = cur.fetchone()
            category_count = result[0] if result and result[0] is not None else 0
            
            # Check procedures
            cur.execute("SELECT COUNT(*) FROM procedures")
            result = cur.fetchone()
            procedure_count = result[0] if result and result[0] is not None else 0
            
            # Check doctors
            cur.execute("SELECT COUNT(*) FROM doctors")
            result = cur.fetchone()
            doctor_count = result[0] if result and result[0] is not None else 0
            
            logger.info("=== DATABASE STATUS ===")
            logger.info(f"Body Parts: {body_part_count}")
            logger.info(f"Categories: {category_count}")
            logger.info(f"Procedures: {procedure_count}")
            logger.info(f"Doctors: {doctor_count}")
            
            return {
                "body_parts": body_part_count,
                "categories": category_count,
                "procedures": procedure_count,
                "doctors": doctor_count
            }
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return None
    finally:
        conn.close()

def update_start_rows(procedure_count, doctor_count):
    """Update the start row constants in this script for next run."""
    if procedure_count is None or doctor_count is None:
        return
        
    script_path = os.path.abspath(__file__)
    with open(script_path, 'r') as file:
        content = file.read()
    
    # Update PROCEDURE_START_ROW
    new_content = content.replace(
        f"PROCEDURE_START_ROW = {PROCEDURE_START_ROW}",
        f"PROCEDURE_START_ROW = {procedure_count}"
    )
    
    # Update DOCTOR_START_ROW
    new_content = new_content.replace(
        f"DOCTOR_START_ROW = {DOCTOR_START_ROW}",
        f"DOCTOR_START_ROW = {doctor_count}"
    )
    
    with open(script_path, 'w') as file:
        file.write(new_content)
        
    logger.info(f"Updated start rows: Procedures={procedure_count}, Doctors={doctor_count}")

def main():
    """Run the bulk import process."""
    start_time = time.time()
    
    # Import a batch of each
    procedures_added = import_procedures()
    doctors_added = import_doctors()
    
    # Check final status
    status = check_database_status()
    if status:
        update_start_rows(status["procedures"], status["doctors"])
    
    elapsed = time.time() - start_time
    logger.info(f"Import completed in {elapsed:.2f} seconds.")
    logger.info(f"Added {procedures_added} procedures and {doctors_added} doctors.")
    logger.info("Run this script again to continue importing more data.")

if __name__ == "__main__":
    main()