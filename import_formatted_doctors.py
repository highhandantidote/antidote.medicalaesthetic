#!/usr/bin/env python3
"""
Import doctors from formatted CSV file into the Antidote database.

This script reads a properly formatted CSV file containing doctor information
and imports it into the database, creating both user accounts and doctor profiles.
"""
import os
import csv
import json
import logging
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# CSV file path
CSV_FILE = "attached_assets/formatted_doctors.csv"

def clean_phone_number(phone):
    """Clean phone number to standard format."""
    if not phone:
        return ""
    # Remove non-numeric characters
    phone = re.sub(r'\D', '', phone)
    # Ensure it's a valid length
    if len(phone) > 10:
        phone = phone[-10:]  # Take last 10 digits
    return phone

def parse_json_field(field_str):
    """Parse JSON field from string, handling potential errors."""
    if not field_str or field_str == "[]" or field_str.lower() == "null":
        return []
    
    try:
        # Try to parse the JSON string
        return json.loads(field_str)
    except json.JSONDecodeError:
        # If it fails, try to clean up the string
        cleaned_str = field_str.replace("'", '"')
        try:
            return json.loads(cleaned_str)
        except:
            logger.warning(f"Could not parse JSON field: {field_str}")
            return []

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def create_user(conn, doctor_data):
    """Create a user account for the doctor."""
    name = doctor_data['Doctor Name'].strip()
    phone = clean_phone_number(doctor_data['Phone'])
    email = doctor_data['Email'].strip() if doctor_data.get('Email') else f"{name.lower().replace(' ', '.')}@example.com"
    
    # Generate username from name (lowercase, no spaces)
    username = name.lower().replace("dr. ", "").replace(" ", "")
    
    # Generate a default password (doctor12345)
    password_hash = generate_password_hash("doctor12345")
    
    try:
        with conn.cursor() as cursor:
            # Check if user already exists with this email or phone
            cursor.execute(
                "SELECT id FROM users WHERE email = %s OR phone_number = %s",
                (email, phone)
            )
            existing_user = cursor.fetchone()
            if existing_user:
                logger.info(f"User already exists for {name}, ID: {existing_user[0]}")
                return existing_user[0]
            
            # Create new user
            cursor.execute(
                """
                INSERT INTO users (
                    name, phone_number, email, role, username, password_hash, 
                    role_type, is_verified
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
                """,
                (
                    name, 
                    phone,
                    email,
                    "DOCTOR",  # Role
                    username,
                    password_hash,
                    "MEDICAL",  # Role type
                    True  # Is verified
                )
            )
            user_id = cursor.fetchone()[0]
            logger.info(f"Created user account for {name}, ID: {user_id}")
            return user_id
    except Exception as e:
        logger.error(f"Error creating user for {name}: {e}")
        return None

def create_doctor_profile(conn, doctor_data, user_id):
    """Create a doctor profile in the database."""
    if not user_id:
        return None
    
    name = doctor_data['Doctor Name'].strip()
    specialty = doctor_data['Specialization'].strip() if doctor_data.get('Specialization') else "Plastic Surgeon"
    
    # Clean experience value
    experience_str = str(doctor_data.get('Experience', '0')).strip()
    experience_str = re.sub(r'[^0-9]', '', experience_str)  # Remove non-numeric chars
    experience = int(experience_str) if experience_str else 0
    
    city = doctor_data.get('City', '').strip()
    state = doctor_data.get('State', '').strip()
    hospital = doctor_data.get('Hospital Name', '').strip()
    
    # Clean consultation fee value
    fee_str = str(doctor_data.get('Consultation Fee', '0')).strip()
    fee_str = re.sub(r'[^0-9]', '', fee_str)  # Remove non-numeric chars
    consultation_fee = int(fee_str) if fee_str else 0
    
    bio = doctor_data.get('Description', '').strip()
    license_number = doctor_data.get('License Number', '').strip()
    qualification = doctor_data.get('Qualifications', '').strip()
    practice_location = doctor_data.get('Address', '').strip()
    
    # Parse education and certifications (JSON fields)
    education_str = doctor_data.get('Education History', '[]')
    education = parse_json_field(education_str)
    
    certifications_str = doctor_data.get('Certifications', '[]')
    certifications = parse_json_field(certifications_str)
    
    # If parsing failed, create simple objects
    if not education:
        education = [
            {"institution": "Medical School", "degree": qualification, "year": 2010}
        ]
    
    if not certifications:
        certifications = [
            {"name": "Board Certified", "organization": "Medical Board", "year": 2012}
        ]
    
    # Convert to JSON strings for database
    education_json = json.dumps(education)
    certifications_json = json.dumps(certifications)
    
    try:
        with conn.cursor() as cursor:
            # Check if doctor profile already exists
            cursor.execute(
                "SELECT id FROM doctors WHERE user_id = %s",
                (user_id,)
            )
            existing_doctor = cursor.fetchone()
            if existing_doctor:
                logger.info(f"Doctor profile already exists for {name}, ID: {existing_doctor[0]}")
                return existing_doctor[0]
            
            # Create doctor profile
            cursor.execute(
                """
                INSERT INTO doctors (
                    user_id, name, specialty, experience, city, state, hospital,
                    consultation_fee, bio, medical_license_number, qualification,
                    practice_location, education, certifications, is_verified
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                ) RETURNING id
                """,
                (
                    user_id,
                    name,
                    specialty,
                    experience,
                    city,
                    state,
                    hospital,
                    consultation_fee,
                    bio,
                    license_number,
                    qualification,
                    practice_location,
                    education_json,
                    certifications_json,
                    True  # is_verified
                )
            )
            doctor_id = cursor.fetchone()[0]
            logger.info(f"Created doctor profile for {name}, ID: {doctor_id}")
            return doctor_id
    except Exception as e:
        logger.error(f"Error creating doctor profile for {name}: {e}")
        return None

def link_doctor_to_procedures(conn, doctor_id, doctor_data):
    """Link doctor to procedures they offer."""
    if not doctor_id:
        return 0
    
    name = doctor_data['Doctor Name'].strip()
    procedures_str = doctor_data.get('Procedures Offered', '')
    
    if not procedures_str:
        # Default procedures for plastic surgeons
        procedures_str = "Rhinoplasty,Liposuction,Breast Augmentation"
    
    # Split into individual procedure names
    procedure_names = [p.strip() for p in procedures_str.split(',')]
    added_count = 0
    
    for procedure_name in procedure_names:
        try:
            with conn.cursor() as cursor:
                # Find procedure ID
                cursor.execute(
                    "SELECT id FROM procedures WHERE procedure_name = %s",
                    (procedure_name,)
                )
                procedure_result = cursor.fetchone()
                if not procedure_result:
                    logger.warning(f"Procedure not found: {procedure_name}")
                    continue
                
                procedure_id = procedure_result[0]
                
                # Check if link already exists
                cursor.execute(
                    "SELECT id FROM doctor_procedures WHERE doctor_id = %s AND procedure_id = %s",
                    (doctor_id, procedure_id)
                )
                if cursor.fetchone():
                    logger.debug(f"Doctor {name} already linked to procedure {procedure_name}")
                    continue
                
                # Create link
                cursor.execute(
                    """
                    INSERT INTO doctor_procedures (
                        doctor_id, procedure_id
                    ) VALUES (
                        %s, %s
                    )
                    """,
                    (doctor_id, procedure_id)
                )
                added_count += 1
                logger.debug(f"Linked doctor {name} to procedure {procedure_name}")
        except Exception as e:
            logger.error(f"Error linking doctor {name} to procedure {procedure_name}: {e}")
    
    logger.info(f"Linked doctor {name} to {added_count} procedures")
    return added_count

def link_doctor_to_categories(conn, doctor_id, doctor_data):
    """Link doctor to relevant categories based on procedures."""
    if not doctor_id:
        return 0
    
    name = doctor_data['Doctor Name'].strip()
    special_interests = doctor_data.get('Special Interests', '')
    
    if not special_interests:
        # Use default categories for plastic surgeons
        special_interests = "Body Contouring,Facial Aesthetics,Reconstructive Surgery"
    
    # Split into individual category names
    category_names = [c.strip() for c in special_interests.split(',')]
    added_count = 0
    
    for category_name in category_names:
        try:
            with conn.cursor() as cursor:
                # Find category IDs that match this name pattern
                cursor.execute(
                    "SELECT id FROM categories WHERE name ILIKE %s OR name ILIKE %s",
                    (category_name, f"%{category_name}%")
                )
                category_results = cursor.fetchall()
                
                if not category_results:
                    logger.warning(f"Category not found: {category_name}")
                    continue
                
                # Link to each matching category
                for category_row in category_results:
                    category_id = category_row[0]
                    
                    # Check if link already exists
                    cursor.execute(
                        "SELECT id FROM doctor_categories WHERE doctor_id = %s AND category_id = %s",
                        (doctor_id, category_id)
                    )
                    if cursor.fetchone():
                        logger.debug(f"Doctor {name} already linked to category ID {category_id}")
                        continue
                    
                    # Create link
                    cursor.execute(
                        """
                        INSERT INTO doctor_categories (
                            doctor_id, category_id, is_verified
                        ) VALUES (
                            %s, %s, %s
                        )
                        """,
                        (doctor_id, category_id, True)
                    )
                    added_count += 1
                    logger.debug(f"Linked doctor {name} to category ID {category_id}")
        except Exception as e:
            logger.error(f"Error linking doctor {name} to category {category_name}: {e}")
    
    logger.info(f"Linked doctor {name} to {added_count} categories")
    return added_count

def import_doctors():
    """Import doctors from CSV file."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    try:
        # Read the CSV file
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            rows = list(csv_reader)
            
            total_doctors = len(rows)
            imported_doctors = 0
            
            for row in rows:
                # Skip rows without a doctor name
                if not row.get('Doctor Name'):
                    continue
                
                # Create user account
                user_id = create_user(conn, row)
                if not user_id:
                    logger.error(f"Failed to create user for {row.get('Doctor Name', 'Unknown')}")
                    continue
                
                # Create doctor profile
                doctor_id = create_doctor_profile(conn, row, user_id)
                if not doctor_id:
                    logger.error(f"Failed to create doctor profile for {row.get('Doctor Name', 'Unknown')}")
                    continue
                
                # Link to procedures and categories
                link_doctor_to_procedures(conn, doctor_id, row)
                link_doctor_to_categories(conn, doctor_id, row)
                
                imported_doctors += 1
                logger.info(f"Imported doctor {row['Doctor Name']} ({imported_doctors}/{total_doctors})")
            
            logger.info(f"Import complete. Imported {imported_doctors} of {total_doctors} doctors.")
    except Exception as e:
        logger.error(f"Error during import: {e}")
    finally:
        conn.close()

def main():
    """Run the doctor import script."""
    logger.info("Starting doctor import process...")
    import_doctors()
    logger.info("Doctor import process completed.")

if __name__ == "__main__":
    main()