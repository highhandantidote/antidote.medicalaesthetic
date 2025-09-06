#!/usr/bin/env python3
"""
Import doctors from the clean CSV file to Supabase database.

This script:
1. Reads doctors from the CSV file
2. Matches them with existing user accounts by name
3. Creates new user accounts if no match is found
4. Inserts doctor profiles into the doctors table
"""
import os
import csv
import psycopg2
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the Supabase database."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return None
        
        conn = psycopg2.connect(database_url)
        logger.info("Connected to Supabase database successfully")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return None

def create_user_email(doctor_name):
    """Create a unique email from doctor name."""
    # Remove special characters and spaces, convert to lowercase
    clean_name = re.sub(r'[^a-zA-Z\s]', '', doctor_name)
    clean_name = clean_name.lower().replace(' ', '.')
    return f"{clean_name}@antidote.com"

def find_or_create_user(conn, doctor_name):
    """Find existing user by name or create a new one."""
    try:
        cursor = conn.cursor()
        
        # First, try to find existing user by name (case-insensitive)
        cursor.execute("""
            SELECT id FROM users 
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) 
            AND role = 'doctor'
            LIMIT 1
        """, (doctor_name,))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"Found existing user for {doctor_name}: user_id {result[0]}")
            return result[0]
        
        # If not found, create new user
        email = create_user_email(doctor_name)
        password_hash = '$2b$12$defaulthashfordemopurposes'  # Default hash
        phone_number = "+91" + str(9000000000 + hash(doctor_name) % 1000000000)[:10]  # Generate unique phone
        
        cursor.execute("""
            INSERT INTO users (name, email, phone_number, password_hash, role, is_verified, created_at)
            VALUES (%s, %s, %s, %s, 'doctor', true, %s)
            RETURNING id
        """, (doctor_name, email, phone_number, password_hash, datetime.utcnow()))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        logger.info(f"Created new user for {doctor_name}: user_id {user_id}")
        return user_id
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error finding/creating user for {doctor_name}: {str(e)}")
        return None

def doctor_exists(conn, doctor_name):
    """Check if doctor already exists in doctors table."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM doctors 
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
            LIMIT 1
        """, (doctor_name,))
        
        result = cursor.fetchone()
        return result is not None
        
    except Exception as e:
        logger.error(f"Error checking if doctor exists: {str(e)}")
        return False

def clean_experience(experience_str):
    """Extract numeric experience from string."""
    if not experience_str or experience_str.strip() == '':
        return 15  # Default experience
    
    # Extract numbers from string
    numbers = re.findall(r'\d+', str(experience_str))
    if numbers:
        return int(numbers[0])
    return 15  # Default if no numbers found

def import_doctors():
    """Import doctors from CSV file."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        csv_file = 'attached_assets/doctors_updated - Sheet2.csv'
        
        if not os.path.exists(csv_file):
            logger.error(f"CSV file not found: {csv_file}")
            return
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    name = row['name'].strip() if row['name'] else f"Doctor_{row_num}"
                    
                    # Skip if doctor already exists
                    if doctor_exists(conn, name):
                        logger.info(f"Doctor {name} already exists, skipping...")
                        skipped_count += 1
                        continue
                    
                    # Get or create user
                    user_id = find_or_create_user(conn, name)
                    if not user_id:
                        logger.error(f"Failed to get/create user for {name}")
                        error_count += 1
                        continue
                    
                    # Prepare doctor data
                    profile_image = row['profile_image'].strip() if row['profile_image'] else None
                    education = row['education'].strip() if row['education'] else 'MBBS'
                    specialty = row['specialty'].strip() if row['specialty'] else 'Plastic Surgeon'
                    hospital = row['hospital'].strip() if row['hospital'] else None
                    experience = clean_experience(row['experience'])
                    city = row['city'].strip() if row['city'] else 'Not specified'
                    state = row['state'].strip() if row['state'] else None
                    
                    # Insert doctor
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO doctors (
                            user_id, name, specialty, qualification, experience, 
                            city, state, hospital, profile_image, image_url,
                            consultation_fee, is_verified, rating, review_count,
                            verification_status, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        user_id, name, specialty, education, experience,
                        city, state, hospital, profile_image, profile_image,
                        5000, True, 4.5, 12, 'approved', datetime.utcnow()
                    ))
                    
                    conn.commit()
                    imported_count += 1
                    logger.info(f"Imported doctor {imported_count}: {name}")
                    
                except Exception as e:
                    conn.rollback()
                    error_count += 1
                    doctor_name = row.get('name', f'Row_{row_num}') if 'row' in locals() else f'Row_{row_num}'
                    logger.error(f"Error importing row {row_num} ({doctor_name}): {str(e)}")
                    continue
        
        # Final summary
        logger.info("=" * 50)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Successfully imported: {imported_count} doctors")
        logger.info(f"Skipped (already exist): {skipped_count} doctors")
        logger.info(f"Errors: {error_count} doctors")
        logger.info(f"Total processed: {imported_count + skipped_count + error_count}")
        
        # Verify final count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM doctors")
        result = cursor.fetchone()
        total_doctors = result[0] if result else 0
        logger.info(f"Total doctors in database: {total_doctors}")
        
    except Exception as e:
        logger.error(f"Import process failed: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting doctor import from CSV...")
    import_doctors()
    logger.info("Doctor import completed.")