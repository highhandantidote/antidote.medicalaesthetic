#!/usr/bin/env python3
"""
Find and import missing procedures and doctors.

This script scans the CSV files to identify entries that aren't already in the database,
and imports them in small batches, focusing only on new entries.
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
MAX_PROCEDURES_TO_ADD = 2  # Further reduced to avoid timeouts
MAX_DOCTORS_TO_ADD = 1     # Further reduced to avoid timeouts

# Default values for missing fields
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."
DEFAULT_QUALIFICATION = "MBBS, MS"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

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
        # Check if category exists with this name and body part
        cursor.execute(
            "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
            (category_name, body_part_id)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Check if category exists with just this name (to avoid unique constraint violation)
        cursor.execute(
            "SELECT id, body_part_id FROM categories WHERE name = %s",
            (category_name,)
        )
        result = cursor.fetchone()
        
        if result:
            existing_id, existing_body_part = result
            logger.warning(f"Category '{category_name}' already exists with body_part_id {existing_body_part}, using that instead of creating a new one with body_part_id {body_part_id}")
            return existing_id
        
        # Create new category if it doesn't exist at all
        try:
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
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            conn.rollback()
            # Get the existing category as a fallback
            cursor.execute("SELECT id FROM categories WHERE name = %s LIMIT 1", (category_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            # If that fails, use a default category
            cursor.execute("SELECT id FROM categories LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else None

def procedure_exists(conn, procedure_name):
    """Check if procedure already exists with the same name."""
    with conn.cursor() as cursor:
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

def find_missing_procedures():
    """Find procedures in the CSV that aren't in the database yet."""
    conn = get_db_connection()
    missing_procedures = []
    
    try:
        # Get all existing procedure names
        with conn.cursor() as cursor:
            cursor.execute("SELECT procedure_name FROM procedures")
            existing_procedures = {row[0] for row in cursor.fetchall()}
            
        # Read CSV and find missing procedures
        with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for i, row in enumerate(csv_reader):
                procedure_name = row.get('procedure_name', '').strip()
                if procedure_name and procedure_name not in existing_procedures:
                    missing_procedures.append((i + 1, row))  # i+1 to account for header row
                
                # Stop once we have enough
                if len(missing_procedures) >= MAX_PROCEDURES_TO_ADD * 2:  # Get twice as many as needed in case some fail
                    break
                    
        logger.info(f"Found {len(missing_procedures)} procedures that need to be imported")
        return missing_procedures
        
    except Exception as e:
        logger.error(f"Error finding missing procedures: {str(e)}")
        return []
    finally:
        conn.close()

def find_missing_doctors():
    """Find doctors in the CSV that aren't in the database yet."""
    conn = get_db_connection()
    missing_doctors = []
    
    try:
        # Get all existing doctor names
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM doctors")
            existing_doctors = {row[0] for row in cursor.fetchall()}
            
        # Read CSV and find missing doctors
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for i, row in enumerate(csv_reader):
                doctor_name = row.get('Doctor Name', '').strip()
                if doctor_name and doctor_name not in existing_doctors:
                    missing_doctors.append((i + 1, row))  # i+1 to account for header row
                
                # Stop once we have enough
                if len(missing_doctors) >= MAX_DOCTORS_TO_ADD * 2:  # Get twice as many as needed in case some fail
                    break
                    
        logger.info(f"Found {len(missing_doctors)} doctors that need to be imported")
        return missing_doctors
        
    except Exception as e:
        logger.error(f"Error finding missing doctors: {str(e)}")
        return []
    finally:
        conn.close()

def import_missing_procedures(missing_procedures):
    """Import missing procedures found in the CSV."""
    if not missing_procedures:
        logger.info("No missing procedures to import")
        return 0
        
    procedures_added = 0
    conn = get_db_connection()
    
    try:
        for row_num, row in missing_procedures:
            if procedures_added >= MAX_PROCEDURES_TO_ADD:
                break
                
            try:
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                procedure_name = row.get('procedure_name', '').strip()
                
                if not body_part_name or not category_name or not procedure_name:
                    logger.warning(f"Skipping row {row_num} - missing required fields")
                    continue
                
                # Skip if procedure already exists
                if procedure_exists(conn, procedure_name):
                    logger.info(f"Procedure already exists: {procedure_name}")
                    continue
                
                # Get or create body part and category
                body_part_id = get_body_part_id(conn, body_part_name)
                category_id = get_category_id(conn, category_name, body_part_id)
                
                if not category_id:
                    logger.error(f"Could not get category ID for {category_name}, skipping")
                    continue
                
                # Clean cost values with default fallbacks
                min_cost_val = row.get('min_cost')
                max_cost_val = row.get('max_cost')
                
                min_cost = clean_integer(min_cost_val) if min_cost_val else 10000  # Default minimum cost
                max_cost = clean_integer(max_cost_val) if max_cost_val else 50000  # Default maximum cost
                
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
                            None  # Set tags to NULL to avoid format issues
                        )
                    )
                
                conn.commit()
                procedures_added += 1
                logger.info(f"Added procedure: {procedure_name} (category: {category_name})")
                
                # Brief pause to avoid timeouts
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error importing procedure from row {row_num}: {str(e)}")
                conn.rollback()
        
        return procedures_added
        
    except Exception as e:
        logger.error(f"Error in import_missing_procedures: {str(e)}")
        return procedures_added
    finally:
        conn.close()

def import_missing_doctors(missing_doctors):
    """Import missing doctors found in the CSV."""
    if not missing_doctors:
        logger.info("No missing doctors to import")
        return 0
        
    doctors_added = 0
    conn = get_db_connection()
    
    try:
        for row_num, row in missing_doctors:
            if doctors_added >= MAX_DOCTORS_TO_ADD:
                break
                
            try:
                doctor_name = row.get('Doctor Name', '').strip()
                if not doctor_name:
                    logger.warning(f"Skipping row {row_num} - missing doctor name")
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
                            conn.commit()
                        else:
                            logger.error(f"Failed to add doctor: {doctor_name}")
                            conn.rollback()
                else:
                    logger.error(f"Cannot add doctor without valid user_id: {doctor_name}")
                
                # Brief pause to avoid timeouts
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error importing doctor from row {row_num}: {str(e)}")
                conn.rollback()
        
        return doctors_added
        
    except Exception as e:
        logger.error(f"Error in import_missing_doctors: {str(e)}")
        return doctors_added
    finally:
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
            
            # Count remaining in CSV files
            with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as f:
                procedures_total = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
                
            with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as f:
                doctors_total = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
            
            # Print summary
            logger.info("=" * 50)
            logger.info("DATABASE IMPORT STATUS")
            logger.info("=" * 50)
            logger.info(f"Body Parts: {body_part_count}")
            logger.info(f"Categories: {category_count}")
            logger.info(f"Procedures: {procedure_count} out of {procedures_total} in CSV")
            logger.info(f"Doctors: {doctor_count} out of {doctors_total} in CSV")
            logger.info(f"Procedures remaining to import: {procedures_total - procedure_count}")
            logger.info(f"Doctors remaining to import: {doctors_total - doctor_count}")
            logger.info("=" * 50)
            
            # Return counts for potential use by other scripts
            return {
                "body_parts": body_part_count,
                "categories": category_count,
                "procedures": procedure_count,
                "total_procedures": procedures_total,
                "doctors": doctor_count,
                "total_doctors": doctors_total
            }
            
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def main():
    """Find and import missing procedures and doctors."""
    overall_start_time = time.time()
    
    # Check current database status
    status_before = check_database_status()
    
    # Find missing procedures and import them
    missing_procedures = find_missing_procedures()
    procedures_added = import_missing_procedures(missing_procedures)
    logger.info(f"Procedures import complete. Added {procedures_added} procedures.")
    
    # Find missing doctors and import them
    missing_doctors = find_missing_doctors()
    doctors_added = import_missing_doctors(missing_doctors)
    logger.info(f"Doctors import complete. Added {doctors_added} doctors.")
    
    # Check final database status
    status_after = check_database_status()
    
    overall_elapsed = time.time() - overall_start_time
    logger.info(f"Overall import completed in {overall_elapsed:.2f} seconds")
    
    logger.info("Run this script again to continue importing more data.")

if __name__ == "__main__":
    main()