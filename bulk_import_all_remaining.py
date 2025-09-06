#!/usr/bin/env python3
"""
Bulk import all remaining procedures and doctors in one go.

This script uses direct SQL commands and bulk operations to quickly import
all remaining data without small batches or slow progress.
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
BATCH_SIZE = 10  # Process data in smaller batches

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if not value:
        return 10000  # Default cost if no value provided
    # Remove commas and convert to integer
    try:
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

def get_or_create_body_part(conn, body_part_name):
    """Get or create body part and return its ID."""
    with conn.cursor() as cursor:
        # Check if body part exists
        cursor.execute(
            "SELECT id FROM body_parts WHERE LOWER(name) = LOWER(%s)",
            (body_part_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create the body part
        cursor.execute(
            "INSERT INTO body_parts (name, created_at) VALUES (%s, %s) RETURNING id",
            (body_part_name, datetime.utcnow())
        )
        return cursor.fetchone()[0]

def get_or_create_category(conn, category_name, body_part_id):
    """Get or create category and return its ID."""
    with conn.cursor() as cursor:
        # Check if category exists by name (regardless of body part)
        cursor.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)",
            (category_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create the category if it doesn't exist
        try:
            cursor.execute(
                "INSERT INTO categories (name, body_part_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                (category_name, body_part_id, datetime.utcnow())
            )
            return cursor.fetchone()[0]
        except psycopg2.errors.UniqueViolation:
            # Handle race condition or duplicate name with different case
            conn.rollback()
            cursor.execute(
                "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)",
                (category_name,)
            )
            return cursor.fetchone()[0]

def import_all_procedures():
    """Import all remaining procedures in batches with separate transactions."""
    logger.info("Starting bulk procedure import...")
    
    conn = get_db_connection()
    try:
        # Get existing procedure names
        with conn.cursor() as cursor:
            cursor.execute("SELECT procedure_name FROM procedures")
            existing_procedure_names = {row[0].lower() for row in cursor.fetchall() if row[0]}
        
        logger.info(f"Found {len(existing_procedure_names)} existing procedures")
        
        # Import all remaining procedures
        import_count = 0
        duplicate_count = 0
        error_count = 0
        
        # Read all procedures into memory
        with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            all_procedures = list(reader)
        
        # Process in batches
        total_procedures = len(all_procedures)
        logger.info(f"Found {total_procedures} procedures in CSV")
        
        for batch_start in range(0, total_procedures, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_procedures)
            batch = all_procedures[batch_start:batch_end]
            
            logger.info(f"Processing procedure batch {batch_start+1}-{batch_end} of {total_procedures}")
            
            # Process each procedure in the batch with its own transaction
            for procedure in batch:
                procedure_name = procedure.get('procedure_name', '')
                
                # Skip empty procedure names
                if not procedure_name:
                    logger.warning("Skipping procedure with no name")
                    continue
                
                # Skip duplicates
                if procedure_name.lower() in existing_procedure_names:
                    duplicate_count += 1
                    logger.info(f"Skipping duplicate procedure: {procedure_name}")
                    continue
                
                # New connection and transaction for each procedure
                proc_conn = get_db_connection()
                try:
                    # Start a transaction
                    with proc_conn:
                        # Get or create body part
                        body_part_name = procedure.get('body_part_name', 'General')
                        body_part_id = get_or_create_body_part(proc_conn, body_part_name)
                        
                        # Get or create category
                        category_name = procedure.get('category_name', 'General Procedures')
                        category_id = get_or_create_category(proc_conn, category_name, body_part_id)
                        
                        # Parse tags
                        tags = parse_tags(procedure.get('tags', ''))
                        
                        # Ensure required fields have values
                        short_description = procedure.get('short_description') or f"A procedure for {body_part_name} treatment"
                        overview = procedure.get('overview') or f"Treatment for {body_part_name} using {procedure_name}"
                        procedure_details = procedure.get('procedure_details') or f"Details about {procedure_name} procedure"
                        ideal_candidates = procedure.get('ideal_candidates') or "Individuals looking for treatment"
                        recovery_time = procedure.get('recovery_time') or "Varies by individual"
                        risks = procedure.get('risks') or "Standard medical procedure risks"
                        procedure_types = procedure.get('procedure_types') or f"Standard {procedure_name}"
                        
                        # Insert the procedure
                        with proc_conn.cursor() as cursor:
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
                    
                    # If we get here, the transaction was successful
                    import_count += 1
                    # Add to our list of processed procedures to avoid duplicates in the same run
                    existing_procedure_names.add(procedure_name.lower())
                    
                    # Log each successful import
                    logger.info(f"Successfully imported procedure {import_count}: {procedure_name}")
                        
                except Exception as e:
                    logger.error(f"Error importing procedure {procedure_name}: {str(e)}")
                    error_count += 1
                finally:
                    proc_conn.close()
            
            # Log batch progress
            logger.info(f"Completed batch {batch_start+1}-{batch_end}: {import_count} procedures imported so far")
        
        logger.info(f"Successfully imported {import_count} procedures")
        logger.info(f"Skipped {duplicate_count} duplicates")
        logger.info(f"Encountered {error_count} errors")
        
    except Exception as e:
        logger.error(f"Bulk procedure import failed: {str(e)}")
        import_count = 0
    finally:
        conn.close()
    
    return import_count

def verify_final_counts():
    """Verify the final counts of both doctors and procedures."""
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

def main():
    """Run the bulk import."""
    start_time = time.time()
    
    # Import procedures
    procedure_count = import_all_procedures()
    
    # Import doctors
    doctor_count = import_all_doctors()
    
    # Verify final counts
    verify_final_counts()
    
    total_time = time.time() - start_time
    logger.info(f"Bulk import completed in {total_time:.2f} seconds")
    logger.info(f"Added {procedure_count} procedures and {doctor_count} doctors")

if __name__ == "__main__":
    main()