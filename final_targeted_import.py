#!/usr/bin/env python3
"""
Final targeted import script designed for maximum efficiency and reliability.

This script:
1. Imports only a specific number of procedures and doctors
2. Uses the most direct SQL possible
3. Focuses on speed with minimal error logging
4. Commits each record individually for maximum stability
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
PROCEDURES_CSV_PATH = "./attached_assets/new_procedure_details - Sheet1.csv"
DOCTORS_CSV_PATH = "./attached_assets/new_doctors_profiles2 - Sheet1.csv"
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."

# Target numbers - can be adjusted based on time constraints
TARGET_PROCEDURE_COUNT = 25  # Import up to this many procedures (adjust as needed)
TARGET_DOCTOR_COUNT = 25     # Import up to this many doctors (adjust as needed)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if not value:
        return 10000  # Default cost if no value provided
    try:
        # Remove commas and convert to integer
        return int(value.replace(',', ''))
    except (ValueError, AttributeError):
        return 10000  # Default cost if conversion fails

def parse_tags(tags_str):
    """Parse tags string into an array format with length limits."""
    if not tags_str:
        return []
    # Split by comma, clean whitespace, and limit each tag to 20 characters
    return [tag.strip()[:20] for tag in tags_str.split(',')]

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

def import_procedures():
    """Import a target number of procedures."""
    logger.info(f"Starting targeted procedure import (target: {TARGET_PROCEDURE_COUNT})...")
    
    # Count existing procedures
    conn = get_db_connection()
    initial_count = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            initial_count = cursor.fetchone()[0]
            
            # Also get existing procedure names to avoid duplicates
            cursor.execute("SELECT LOWER(procedure_name) FROM procedures")
            existing_procedures = {row[0] for row in cursor.fetchall() if row[0]}
    finally:
        conn.close()
    
    logger.info(f"Found {initial_count} existing procedures")
    
    # Read procedures from CSV
    with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_procedures = list(reader)
    
    logger.info(f"Found {len(all_procedures)} procedures in CSV")
    
    # Filter out procedures that already exist
    new_procedures = [p for p in all_procedures 
                     if p.get('procedure_name', '').lower() not in existing_procedures]
    logger.info(f"Found {len(new_procedures)} new procedures to import")
    
    # Limit to target count
    procedures_to_import = new_procedures[:TARGET_PROCEDURE_COUNT]
    logger.info(f"Will import up to {len(procedures_to_import)} procedures")
    
    # Start importing
    success_count = 0
    error_count = 0
    body_part_cache = {}
    category_cache = {}
    
    for i, procedure in enumerate(procedures_to_import):
        procedure_name = procedure.get('procedure_name', '')
        if not procedure_name:
            continue
            
        conn = get_db_connection()
        try:
            # Get body part info
            body_part_name = procedure.get('body_part_name', 'General')
            body_part_id = None
            
            # Check cache first
            if body_part_name.lower() in body_part_cache:
                body_part_id = body_part_cache[body_part_name.lower()]
            else:
                # Try to get from database
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM body_parts WHERE LOWER(name) = LOWER(%s)",
                        (body_part_name,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        body_part_id = result[0]
                        body_part_cache[body_part_name.lower()] = body_part_id
                    else:
                        # Create new body part
                        cursor.execute(
                            "INSERT INTO body_parts (name, created_at) VALUES (%s, %s) RETURNING id",
                            (body_part_name, datetime.utcnow())
                        )
                        body_part_id = cursor.fetchone()[0]
                        body_part_cache[body_part_name.lower()] = body_part_id
                        conn.commit()
            
            # Get category info
            category_name = procedure.get('category_name', 'General Procedures')
            category_id = None
            
            # Check cache first
            cache_key = f"{category_name.lower()}_{body_part_id}"
            if cache_key in category_cache:
                category_id = category_cache[cache_key]
            else:
                # Try to get from database
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)",
                        (category_name,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        category_id = result[0]
                        category_cache[cache_key] = category_id
                    else:
                        # Create new category
                        cursor.execute(
                            "INSERT INTO categories (name, body_part_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                            (category_name, body_part_id, datetime.utcnow())
                        )
                        category_id = cursor.fetchone()[0]
                        category_cache[cache_key] = category_id
                        conn.commit()
            
            # Prepare procedure data
            tags = parse_tags(procedure.get('tags', ''))
            short_description = procedure.get('short_description') or f"A procedure for {body_part_name} treatment"
            overview = procedure.get('overview') or f"Treatment for {body_part_name} using {procedure_name}"
            procedure_details = procedure.get('procedure_details') or f"Details about {procedure_name} procedure"
            ideal_candidates = procedure.get('ideal_candidates') or "Individuals looking for treatment"
            recovery_time = procedure.get('recovery_time') or "Varies by individual"
            risks = procedure.get('risks') or "Standard medical procedure risks"
            procedure_types = procedure.get('procedure_types') or f"Standard {procedure_name}"
            
            # Insert the procedure
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO procedures (
                        procedure_name, alternative_names, short_description, overview,
                        procedure_details, ideal_candidates, recovery_time, procedure_duration,
                        hospital_stay_required, results_duration, min_cost, max_cost, benefits,
                        benefits_detailed, risks, procedure_types, recovery_process,
                        alternative_procedures, category_id, body_part, tags, body_area,
                        category_type, created_at, updated_at, popularity_score, avg_rating, review_count
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    procedure_name,
                    procedure.get('alternative_names', ''),
                    short_description,
                    overview,
                    procedure_details,
                    ideal_candidates,
                    recovery_time,
                    procedure.get('procedure_duration', ''),
                    procedure.get('hospital_stay_required', 'No'),
                    procedure.get('results_duration', ''),
                    clean_integer(procedure.get('min_cost', '10000')),
                    clean_integer(procedure.get('max_cost', '20000')),
                    procedure.get('benefits', ''),
                    procedure.get('benefits_detailed', ''),
                    risks,
                    procedure_types,
                    procedure.get('recovery_process', ''),
                    procedure.get('alternative_procedures', ''),
                    category_id,
                    body_part_name,  # Map to body_part column
                    tags,
                    body_part_name,  # Map to body_area column
                    category_name,   # Map to category_type column
                    datetime.utcnow(),
                    datetime.utcnow(),
                    0,  # default popularity_score
                    4.5,  # default avg_rating
                    0  # default review_count
                ))
                conn.commit()
            
            success_count += 1
            logger.info(f"Successfully imported procedure [{success_count}/{len(procedures_to_import)}]: {procedure_name}")
            
            # Add to existing procedures to avoid duplicates
            existing_procedures.add(procedure_name.lower())
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error importing procedure {procedure_name}: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
            
        if success_count >= TARGET_PROCEDURE_COUNT:
            logger.info(f"Reached target procedure count of {TARGET_PROCEDURE_COUNT}")
            break
    
    # Final count
    conn = get_db_connection()
    final_count = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            final_count = cursor.fetchone()[0]
    finally:
        conn.close()
    
    logger.info(f"Procedure import completed")
    logger.info(f"Successfully imported {success_count} procedures")
    logger.info(f"Encountered {error_count} errors")
    logger.info(f"Procedures before: {initial_count}, after: {final_count}, added: {final_count - initial_count}")
    
    return success_count

def import_doctors():
    """Import a target number of doctors."""
    logger.info(f"Starting targeted doctor import (target: {TARGET_DOCTOR_COUNT})...")
    
    # Count existing doctors
    conn = get_db_connection()
    initial_count = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            initial_count = cursor.fetchone()[0]
            
            # Also get existing doctor names to avoid duplicates
            cursor.execute("SELECT LOWER(name) FROM doctors")
            existing_doctors = {row[0] for row in cursor.fetchall() if row[0]}
    finally:
        conn.close()
    
    logger.info(f"Found {initial_count} existing doctors")
    
    # Read doctors from CSV
    with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_doctors = list(reader)
    
    logger.info(f"Found {len(all_doctors)} doctors in CSV")
    
    # Filter out doctors that already exist
    new_doctors = [d for d in all_doctors 
                  if d.get('Doctor Name', '').lower() not in existing_doctors]
    logger.info(f"Found {len(new_doctors)} new doctors to import")
    
    # Limit to target count
    doctors_to_import = new_doctors[:TARGET_DOCTOR_COUNT]
    logger.info(f"Will import up to {len(doctors_to_import)} doctors")
    
    # Start importing
    success_count = 0
    error_count = 0
    
    for i, doctor in enumerate(doctors_to_import):
        doctor_name = doctor.get('Doctor Name', '')
        if not doctor_name:
            continue
            
        conn = get_db_connection()
        try:
            # Generate a username from the doctor's name
            username = doctor_name.lower().replace(' ', '_').replace('.', '')
            email = f"{username}@example.com"
            phone_number = f"+91{random.randint(7000000000, 9999999999)}"
            
            # Create a new user
            with conn.cursor() as cursor:
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
                user_id = cursor.fetchone()[0]
                conn.commit()
            
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
            with conn.cursor() as cursor:
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
                conn.commit()
            
            success_count += 1
            logger.info(f"Successfully imported doctor [{success_count}/{len(doctors_to_import)}]: {doctor_name}")
            
            # Add to existing doctors to avoid duplicates
            existing_doctors.add(doctor_name.lower())
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error importing doctor {doctor_name}: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
            
        if success_count >= TARGET_DOCTOR_COUNT:
            logger.info(f"Reached target doctor count of {TARGET_DOCTOR_COUNT}")
            break
    
    # Final count
    conn = get_db_connection()
    final_count = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            final_count = cursor.fetchone()[0]
    finally:
        conn.close()
    
    logger.info(f"Doctor import completed")
    logger.info(f"Successfully imported {success_count} doctors")
    logger.info(f"Encountered {error_count} errors")
    logger.info(f"Doctors before: {initial_count}, after: {final_count}, added: {final_count - initial_count}")
    
    return success_count

def main():
    """Run the targeted import process."""
    overall_start_time = time.time()
    
    # First import procedures
    procedure_count = import_procedures()
    
    # Then import doctors
    doctor_count = import_doctors()
    
    overall_elapsed = time.time() - overall_start_time
    logger.info(f"Overall import completed in {overall_elapsed:.2f} seconds")
    logger.info(f"Added {procedure_count} procedures and {doctor_count} doctors")
    
    # Final verification of counts
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            procedure_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cursor.fetchone()[0]
            
            logger.info(f"Final procedure count: {procedure_count}")
            logger.info(f"Final doctor count: {doctor_count}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()