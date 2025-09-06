#!/usr/bin/env python3
"""
Import doctors directly from CSV without user creation complexity.

This script adds doctors directly to the doctors table using a simple approach.
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
        return 5  # default
    
    # Look for number followed by 'years' or 'year'
    match = re.search(r'(\d+)\s*years?', experience_text.lower())
    if match:
        return int(match.group(1))
    
    # Look for just a number
    match = re.search(r'(\d+)', experience_text)
    if match:
        return int(match.group(1))
    
    return 5  # default

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

def import_doctors_simple():
    """Import doctors from CSV using a simple direct approach."""
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
    
    # Use a dummy user_id - we'll create a default user first
    try:
        # Create a default user for all doctors
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, phone_number, role, is_verified, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (
            'default_doctor',
            'doctors@antidote.com',
            'hashed_password_placeholder',
            '+1234567890',  # dummy phone number
            'doctor',
            True
        ))
        
        result = cursor.fetchone()
        if result:
            default_user_id = result[0]
        else:
            # User already exists, get the ID
            cursor.execute("SELECT id FROM users WHERE email = %s", ('doctors@antidote.com',))
            default_user_id = cursor.fetchone()[0]
        
        conn.commit()
        logger.info(f"Using default user_id: {default_user_id}")
        
    except Exception as e:
        logger.error(f"Error creating default user: {str(e)}")
        return False
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    doctor_name = row['Doctor Name'].strip()
                    
                    # Skip if doctor already exists or if it's dummy data
                    if doctor_exists(conn, doctor_name) or 'karthik ram' in doctor_name.lower():
                        logger.info(f"Skipping {doctor_name} - already exists or dummy data")
                        skip_count += 1
                        continue
                    
                    # Extract and clean data
                    profile_image = row['Profile Image'].strip() if row['Profile Image'] else None
                    education = row['education'].strip() if row['education'] else 'Medical Degree'
                    specialty = row['specialty'].strip() if row['specialty'] else 'Plastic Surgeon'
                    address = row['Address'].strip() if row['Address'] else None
                    experience_years = extract_experience_years(row['Experience'])
                    city = row['city'].strip() if row['city'] else 'Mumbai'
                    state = row['state'].strip() if row['state'] else 'Maharashtra'
                    
                    # Generate consultation fee based on experience
                    consultation_fee = max(3000, min(10000, experience_years * 200))
                    
                    # Generate a simple bio
                    bio = f"Experienced {specialty.lower()} with {experience_years} years of practice in {city}."
                    
                    # Insert doctor record
                    cursor.execute("""
                        INSERT INTO doctors (
                            user_id, name, specialty, experience, city, state,
                            hospital, profile_image, education, qualification,
                            is_verified, rating, review_count, consultation_fee,
                            bio, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                        )
                    """, (
                        default_user_id,
                        doctor_name,
                        specialty,
                        experience_years,
                        city,
                        state,
                        address,
                        profile_image,
                        education,
                        education,  # qualification same as education
                        True,       # is_verified
                        4.5,        # default rating
                        0,          # review_count
                        consultation_fee,
                        bio
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
    logger.info("Starting simplified doctor import from CSV...")
    
    if import_doctors_simple():
        logger.info("Doctor import completed successfully")
    else:
        logger.error("Doctor import failed")

if __name__ == "__main__":
    main()