#!/usr/bin/env python3
"""
Update doctor profiles with images and additional data in smaller batches.

This script processes the new doctor profiles CSV in smaller batches to avoid timeouts.
It updates existing doctors with profile images and other enhancements while also
creating new doctors.
"""

import os
import csv
import json
import logging
import requests
import random
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
from urllib.parse import urlparse
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to CSV file
DOCTORS_CSV = "attached_assets/new_doctors_profiles2 - Sheet1.csv"
DEFAULT_AVATAR = "/static/images/default-doctor-avatar.png"
IMAGE_DOWNLOAD_DIR = "static/images/doctors"
BATCH_SIZE = 5  # Process 5 doctors at a time

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    import os
    import psycopg2
    
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
    """Download and save doctor profile image."""
    if not image_url or "avatar" in image_url:
        return DEFAULT_AVATAR
    
    # Create image directory if it doesn't exist
    os.makedirs(IMAGE_DOWNLOAD_DIR, exist_ok=True)
    
    # Generate filename from doctor ID and name
    parsed_url = urlparse(image_url)
    file_ext = os.path.splitext(parsed_url.path)[1]
    if not file_ext:
        file_ext = ".jpg"  # Default extension
    
    safe_name = ''.join(c if c.isalnum() else '_' for c in doctor_name)
    filename = f"doctor_{doctor_id}_{safe_name}{file_ext}"
    filepath = os.path.join(IMAGE_DOWNLOAD_DIR, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        return f"/{filepath}"
    
    try:
        # Download and save the image
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded image for Doctor ID {doctor_id}: {filepath}")
            return f"/{filepath}"
        else:
            logger.warning(f"Failed to download image for Doctor ID {doctor_id}, status code: {response.status_code}")
            return DEFAULT_AVATAR
    except Exception as e:
        logger.error(f"Error downloading image for Doctor ID {doctor_id}: {str(e)}")
        return DEFAULT_AVATAR

def update_doctor_profiles_batch(start_index=0, batch_size=BATCH_SIZE):
    """Update doctor profiles in smaller batches."""
    if not os.path.exists(DOCTORS_CSV):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV}")
        return False, 0, 0, 0, start_index
    
    try:
        conn = get_db_connection()
        if not conn:
            return False, 0, 0, 0, start_index
        
        # Read all doctors from CSV
        all_doctors = []
        with open(DOCTORS_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_doctors = list(reader)
        
        total_doctors = len(all_doctors)
        logger.info(f"Found {total_doctors} doctors in CSV")
        
        # Calculate the end index for this batch
        end_index = min(start_index + batch_size, total_doctors)
        batch_doctors = all_doctors[start_index:end_index]
        
        if not batch_doctors:
            logger.info("No more doctors to process")
            return True, 0, 0, 0, end_index
            
        logger.info(f"Processing batch of {len(batch_doctors)} doctors (indices {start_index} to {end_index-1})")
        
        # Get existing doctors from database
        existing_doctors = {}
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM doctors")
            for doctor_id, doctor_name in cur.fetchall():
                existing_doctors[doctor_name] = doctor_id
        
        # Process each doctor from the batch
        doctors_updated = 0
        doctors_added = 0
        users_added = 0
        
        for i, row in enumerate(batch_doctors):
            # Get essential fields
            doctor_name = row.get('Doctor Name', '').strip()
            profile_image = row.get('Profile Image', '').strip()
            
            # Skip if essential fields are missing
            if not doctor_name:
                logger.warning(f"Skipping row {start_index + i + 1}: Missing doctor name")
                continue
            
            # Check if doctor exists in database
            doctor_id = existing_doctors.get(doctor_name)
            
            if doctor_id:
                # Update existing doctor
                # Download and process profile image
                image_path = download_image(profile_image, doctor_id, doctor_name)
                
                # Extract experience years
                experience_text = row.get('Experience', '')
                experience_years = extract_experience_years(experience_text)
                
                # Format education data
                education_text = row.get('education', '')
                education_json = format_education_data(education_text)
                
                # Update doctor profile
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE doctors
                        SET profile_image = %s,
                            specialty = %s,
                            experience = %s,
                            city = %s,
                            state = %s,
                            hospital = %s,
                            education = %s,
                            bio = %s
                        WHERE id = %s
                    """, (
                        image_path,
                        row.get('specialty', 'Plastic Surgeon'),
                        experience_years,
                        row.get('city', ''),
                        row.get('state', ''),
                        row.get('Address', ''),
                        education_json,
                        f"Dr. {doctor_name.split()[-1]} is a {row.get('specialty', 'Plastic Surgeon')} with {experience_years} years of experience.",
                        doctor_id
                    ))
                    
                    doctors_updated += 1
                    logger.info(f"Updated doctor: {doctor_name} (ID: {doctor_id})")
            else:
                # Create new doctor
                # Create username and email
                username = doctor_name.lower().replace(' ', '_').replace('.', '').replace(',', '')
                email = f"{username}@example.com"
                
                # Check if user already exists with this email
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    result = cur.fetchone()
                    
                    if result:
                        # Try with a different email
                        email = f"{username}_{random.randint(100, 999)}@example.com"
                        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                        result = cur.fetchone()
                        
                        if result:
                            logger.warning(f"User already exists with email: {email}")
                            continue
                
                # Generate a phone number (since we don't have this in CSV)
                phone_number = f"999{random.randint(1000000, 9999999)}"
                
                # Create user
                with conn.cursor() as cur:
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
                    users_added += 1
                    
                    # Extract experience years
                    experience_text = row.get('Experience', '')
                    experience_years = extract_experience_years(experience_text)
                    
                    # Format education data
                    education_text = row.get('education', '')
                    education_json = format_education_data(education_text)
                    
                    # Create doctor profile
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
                        DEFAULT_AVATAR  # Set default first, update after
                    ))
                    
                    doctor_id = cur.fetchone()[0]
                    
                    # Download and save profile image, then update the record
                    image_path = download_image(profile_image, doctor_id, doctor_name)
                    
                    cur.execute("""
                        UPDATE doctors
                        SET profile_image = %s
                        WHERE id = %s
                    """, (image_path, doctor_id))
                    
                    # Add doctor to existing_doctors dict for future reference
                    existing_doctors[doctor_name] = doctor_id
                    
                    doctors_added += 1
                    logger.info(f"Added doctor: {doctor_name} (ID: {doctor_id})")
            
            # Commit after each doctor to avoid losing progress if an error occurs
            conn.commit()
                
        logger.info(f"Successfully updated {doctors_updated} doctors and added {doctors_added} new doctors in this batch")
        logger.info(f"Added {users_added} new user accounts in this batch")
        
        return True, doctors_updated, doctors_added, users_added, end_index
    except Exception as e:
        logger.error(f"Error updating doctor profiles: {str(e)}")
        if conn:
            conn.rollback()
        return False, 0, 0, 0, start_index
    finally:
        if conn:
            conn.close()

def process_all_doctors():
    """Process all doctors in small batches."""
    start_index = 0
    total_updated = 0
    total_added = 0
    total_users = 0
    
    # Check if a starting point was provided as a command-line argument
    if len(sys.argv) > 1:
        try:
            start_index = int(sys.argv[1])
            logger.info(f"Starting from index {start_index}")
        except ValueError:
            logger.warning(f"Invalid start index: {sys.argv[1]}, starting from 0")
    
    while True:
        logger.info(f"Processing batch starting at index {start_index}")
        success, updated, added, users, next_index = update_doctor_profiles_batch(start_index, BATCH_SIZE)
        
        if not success:
            logger.error(f"Failed to process batch starting at index {start_index}")
            print(f"ERROR: Failed to process batch starting at index {start_index}")
            print(f"To resume, run: python {sys.argv[0]} {start_index}")
            break
        
        total_updated += updated
        total_added += added
        total_users += users
        
        if start_index == next_index:
            logger.info("No more doctors to process")
            break
            
        start_index = next_index
        logger.info(f"Next batch will start at index {start_index}")
        
        # Save progress after each batch
        with open("doctor_update_progress.txt", "w") as f:
            f.write(str(start_index))
    
    logger.info(f"Finished processing doctors: {total_updated} updated, {total_added} added, {total_users} users created")
    print(f"Finished processing doctors: {total_updated} updated, {total_added} added, {total_users} users created")

if __name__ == "__main__":
    process_all_doctors()