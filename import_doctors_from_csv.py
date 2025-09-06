#!/usr/bin/env python3
"""
Import doctors from CSV file with proper schema mapping.

This script imports doctors from the CSV file and handles all required schema fields.
"""

import os
import csv
import re
import psycopg2
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL not found in environment variables")
        return None
    
    try:
        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def extract_experience_years(experience_text):
    """Extract years from experience text like '20 years experience'."""
    if not experience_text:
        return 0
    
    # Look for number followed by 'years' or 'year'
    match = re.search(r'(\d+)\s*years?', experience_text.lower())
    if match:
        return int(match.group(1))
    
    # Look for just a number
    match = re.search(r'(\d+)', experience_text)
    if match:
        return int(match.group(1))
    
    return 0

def create_user_for_doctor(conn, doctor_name, email=None):
    """Create a user account for a doctor and return user_id."""
    cursor = conn.cursor()
    
    try:
        # Generate email if not provided
        if not email:
            # Create email from doctor name
            name_parts = doctor_name.lower().replace('dr. ', '').replace(' ', '.')
            email = f"{name_parts}@antidote-doctors.com"
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            logger.info(f"User already exists for {doctor_name}")
            return existing_user[0]
        
        # Create new user (using available columns)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, is_verified, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            doctor_name,
            email,
            'hashed_password_placeholder',  # Will be updated when doctor sets password
            'doctor',
            True
        ))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        logger.info(f"Created user account for {doctor_name} with ID {user_id}")
        return user_id
        
    except Exception as e:
        logger.error(f"Error creating user for {doctor_name}: {str(e)}")
        conn.rollback()
        return None
    finally:
        cursor.close()

def doctor_exists(conn, name):
    """Check if a doctor with the given name already exists."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM doctors WHERE name = %s", (name,))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking if doctor exists: {str(e)}")
        return False
    finally:
        cursor.close()

def import_doctors_from_csv():
    """Import doctors from the CSV file."""
    conn = get_db_connection()
    if not conn:
        return False
    
    csv_file_path = "attached_assets/new_doctors_profiles2 - Sheet1.csv"
    
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return False
    
    cursor = conn.cursor()
    success_count = 0
    skip_count = 0
    error_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    doctor_name = row['Doctor Name'].strip()
                    
                    # Skip if doctor already exists
                    if doctor_exists(conn, doctor_name):
                        logger.info(f"Skipping {doctor_name} - already exists")
                        skip_count += 1
                        continue
                    
                    # Create user account first
                    user_id = create_user_for_doctor(conn, doctor_name)
                    if not user_id:
                        logger.error(f"Could not create user for {doctor_name}")
                        error_count += 1
                        continue
                    
                    # Extract and clean data
                    profile_image = row['Profile Image'].strip() if row['Profile Image'] else None
                    education = row['education'].strip() if row['education'] else None
                    specialty = row['specialty'].strip() if row['specialty'] else 'Plastic Surgeon'
                    address = row['Address'].strip() if row['Address'] else None
                    experience_years = extract_experience_years(row['Experience'])
                    city = row['city'].strip() if row['city'] else None
                    state = row['state'].strip() if row['state'] else None
                    
                    # Insert doctor record
                    cursor.execute("""
                        INSERT INTO doctors (
                            user_id, name, specialty, experience, city, state,
                            hospital, profile_image, education, qualification,
                            is_verified, rating, review_count, consultation_fee,
                            created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                        )
                    """, (
                        user_id,
                        doctor_name,
                        specialty,
                        experience_years,
                        city,
                        state,
                        address,  # hospital field
                        profile_image,
                        education,  # education JSON field - will store as text for now
                        education,  # qualification field
                        True,  # is_verified
                        4.5,   # default rating
                        0,     # review_count
                        5000   # default consultation_fee
                    ))
                    
                    conn.commit()
                    success_count += 1
                    logger.info(f"Successfully imported {doctor_name}")
                    
                except Exception as e:
                    logger.error(f"Error importing doctor on row {row_num}: {str(e)}")
                    error_count += 1
                    conn.rollback()
                    continue
        
        logger.info(f"Import completed: {success_count} successful, {skip_count} skipped, {error_count} errors")
        return True
        
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function."""
    logger.info("Starting doctor import from CSV...")
    
    if import_doctors_from_csv():
        logger.info("Doctor import completed successfully")
    else:
        logger.error("Doctor import failed")

if __name__ == "__main__":
    main()