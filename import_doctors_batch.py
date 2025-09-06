#!/usr/bin/env python3
"""
Import doctors from CSV in smaller batches to avoid timeouts.

This script imports doctors from the CSV file in batches of 10,
with proper image handling to ensure they display correctly.
"""

import os
import csv
import json
import logging
import requests
import random
import shutil
import time
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
from urllib.parse import urlparse
from pathlib import Path
import psycopg2

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to CSV file
DOCTORS_CSV = "attached_assets/new_doctors_profiles2 - Sheet1.csv"
IMAGE_DOWNLOAD_DIR = "static/images/doctors"
DEFAULT_AVATAR = "/static/images/default-doctor-avatar.png"
BATCH_SIZE = 10  # Process 10 doctors at a time

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def extract_experience_years(experience_text):
    """Extract numeric years of experience from text."""
    if not experience_text:
        return 10  # Default value
    
    try:
        # Look for digits at the beginning of the experience string
        digits = ''.join(c for c in experience_text.split()[0] if c.isdigit())
        if digits:
            return int(digits)
        else:
            return 10  # Default value
    except (ValueError, IndexError):
        return 10  # Default value

def format_education_data(education_text):
    """Format education credentials as structured data."""
    if not education_text:
        return json.dumps([])
    
    # Split by comma and create a list of degree objects
    degrees = []
    for degree in education_text.split(','):
        degree = degree.strip()
        if degree:
            degrees.append({"degree": degree})
    
    return json.dumps(degrees)

def download_image(image_url, doctor_id, doctor_name):
    """Download and save doctor profile image with retries."""
    if not image_url or "avatar" in image_url.lower() or not image_url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid image URL for doctor {doctor_name}: {image_url}")
        return DEFAULT_AVATAR
    
    # Create image directory if it doesn't exist
    os.makedirs(IMAGE_DOWNLOAD_DIR, exist_ok=True)
    
    # Generate filename from doctor ID and name
    parsed_url = urlparse(image_url)
    file_ext = os.path.splitext(parsed_url.path)[1]
    if not file_ext or len(file_ext) <= 1:
        file_ext = ".jpg"  # Default extension
    
    safe_name = ''.join(c if c.isalnum() else '_' for c in doctor_name)
    filename = f"doctor_{doctor_id}_{safe_name}{file_ext}"
    filepath = os.path.join(IMAGE_DOWNLOAD_DIR, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        logger.info(f"Image already exists for Doctor ID {doctor_id}: {filepath}")
        return f"/{filepath}"
    
    # Download with retries
    for attempt in range(3):  # Fewer retries to save time
        try:
            # Add random query param to bypass caching
            bypass_cache_url = f"{image_url}?nocache={random.randint(1, 100000)}"
            response = requests.get(bypass_cache_url, timeout=5, stream=True)  # Shorter timeout
            
            if response.status_code == 200:
                # Save the image
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
                # Verify file was created and has content
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    logger.info(f"Downloaded image for Doctor ID {doctor_id}: {filepath}")
                    return f"/{filepath}"
                else:
                    logger.warning(f"Failed to create image file for Doctor ID {doctor_id}")
            else:
                logger.warning(f"Failed to download image for Doctor ID {doctor_id}, status code: {response.status_code}")
            
            # Wait before retry, but much shorter
            if attempt < 2:
                time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error downloading image for Doctor ID {doctor_id}: {str(e)}")
            if attempt < 2:
                time.sleep(0.5)
    
    # If all retries failed, use default
    logger.warning(f"Using default avatar for Doctor ID {doctor_id} after failed download attempts")
    return DEFAULT_AVATAR

def import_doctors_batch(start_index, batch_size):
    """Import a batch of doctors from CSV."""
    if not os.path.exists(DOCTORS_CSV):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV}")
        return False, 0
    
    try:
        conn = get_db_connection()
        if not conn:
            return False, 0
        
        # Read all doctors from CSV
        all_doctors = []
        with open(DOCTORS_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_doctors = list(reader)
        
        total_doctors = len(all_doctors)
        logger.info(f"Found {total_doctors} doctors in CSV")
        
        if start_index >= total_doctors:
            logger.info(f"Start index {start_index} is beyond the total number of doctors {total_doctors}")
            return True, 0
        
        # Limit to the specified batch
        end_index = min(start_index + batch_size, total_doctors)
        batch_doctors = all_doctors[start_index:end_index]
        
        logger.info(f"Processing batch of {len(batch_doctors)} doctors (indices {start_index}-{end_index-1})")
        
        # Import each doctor in the batch
        doctors_added = 0
        
        for i, row in enumerate(batch_doctors):
            # Get essential fields
            doctor_name = row.get('Doctor Name', '').strip()
            profile_image = row.get('Profile Image', '').strip()
            
            # Skip if essential fields are missing
            if not doctor_name:
                logger.warning(f"Skipping row {start_index + i + 1}: Missing doctor name")
                continue
            
            # Generate username from doctor name
            username = doctor_name.lower().replace(' ', '_').replace('.', '').replace(',', '')
            email = f"{username}@example.com"
            
            try:
                # Create user
                with conn.cursor() as cur:
                    # Check if email already exists
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    result = cur.fetchone()
                    
                    if result:
                        # Email exists, use a different email
                        email = f"{username}_{random.randint(100, 999)}@example.com"
                    
                    # Generate a default phone number
                    phone_number = f"999{random.randint(1000000, 9999999)}"
                    
                    # Create user
                    cur.execute("""
                        INSERT INTO users (name, email, username, phone_number, role, role_type, is_verified, password_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        doctor_name,
                        email,
                        username,
                        phone_number,
                        'doctor',
                        'doctor',
                        True,
                        generate_password_hash("Doctor1234")  # Default password
                    ))
                    
                    user_id = cur.fetchone()[0]
                    
                    # Extract experience years
                    experience_text = row.get('Experience', '')
                    experience_years = extract_experience_years(experience_text)
                    
                    # Format education data
                    education_text = row.get('education', '')
                    education_json = format_education_data(education_text)
                    
                    # Create doctor profile with default avatar first
                    cur.execute("""
                        INSERT INTO doctors (
                            user_id, name, specialty, experience, city, state, hospital,
                            consultation_fee, is_verified, rating, review_count, bio,
                            education, verification_status, verification_date, profile_image
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        user_id,
                        doctor_name,
                        row.get('specialty', 'Plastic Surgeon'),
                        experience_years,
                        row.get('city', ''),
                        row.get('state', ''),
                        row.get('Address', ''),
                        1000,  # Default fee
                        True,
                        4.0,   # Default rating
                        0,     # review_count
                        f"Dr. {doctor_name.split()[-1]} is a {row.get('specialty', 'Plastic Surgeon')} with {experience_years} years of experience.",
                        education_json,
                        'approved',
                        datetime.utcnow(),
                        DEFAULT_AVATAR  # Temporary, will update after download
                    ))
                    
                    doctor_id = cur.fetchone()[0]
                    
                    # Download and save profile image, then update the record
                    image_path = download_image(profile_image, doctor_id, doctor_name)
                    
                    cur.execute("""
                        UPDATE doctors
                        SET profile_image = %s
                        WHERE id = %s
                    """, (image_path, doctor_id))
                    
                    # Associate with procedures - simple approach to avoid ON CONFLICT issues
                    try:
                        # Get up to 5 procedure IDs
                        cur.execute("SELECT id FROM procedures LIMIT 5")
                        procedure_ids = [row[0] for row in cur.fetchall()]
                        
                        if procedure_ids:
                            for procedure_id in procedure_ids:
                                try:
                                    # Check if association exists
                                    cur.execute("""
                                        SELECT 1 FROM doctor_procedures 
                                        WHERE doctor_id = %s AND procedure_id = %s
                                    """, (doctor_id, procedure_id))
                                    
                                    if cur.fetchone() is None:
                                        # Insert only if not exists
                                        cur.execute("""
                                            INSERT INTO doctor_procedures (doctor_id, procedure_id)
                                            VALUES (%s, %s)
                                        """, (doctor_id, procedure_id))
                                except Exception as e2:
                                    logger.warning(f"Error associating procedure {procedure_id} with doctor {doctor_id}: {str(e2)}")
                    except Exception as e1:
                        logger.warning(f"Error with procedures for doctor {doctor_id}: {str(e1)}")
                    
                    # Commit after each doctor
                    conn.commit()
                    doctors_added += 1
                    logger.info(f"Added doctor {start_index + i + 1}/{total_doctors}: {doctor_name} (ID: {doctor_id})")
            
            except Exception as e:
                logger.error(f"Error adding doctor {doctor_name}: {str(e)}")
                conn.rollback()
        
        return True, doctors_added
    except Exception as e:
        logger.error(f"Error in batch import: {str(e)}")
        if conn:
            conn.rollback()
        return False, 0
    finally:
        if conn:
            conn.close()

def main():
    """Run the batch import process."""
    # Initialize image directories
    if not os.path.exists(IMAGE_DOWNLOAD_DIR):
        os.makedirs(IMAGE_DOWNLOAD_DIR, exist_ok=True)
    
    # Get start index from command line if provided
    start_index = 0
    if len(sys.argv) > 1:
        try:
            start_index = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid start index: {sys.argv[1]}, using 0")
    
    success, count = import_doctors_batch(start_index, BATCH_SIZE)
    next_index = start_index + BATCH_SIZE
    
    if success:
        logger.info(f"Successfully imported {count} doctors from index {start_index}")
        logger.info(f"Next batch should start at index {next_index}")
        print(f"NEXT_INDEX={next_index}")  # For shell script to capture
    else:
        logger.error(f"Failed to import doctors batch starting at index {start_index}")

if __name__ == "__main__":
    main()