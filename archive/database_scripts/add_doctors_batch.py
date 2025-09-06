#!/usr/bin/env python3
"""
Add doctors directly to the database in batches.

This script imports doctor data from CSV in small batches to avoid timeout issues.
"""

import os
import csv
import logging
import json
import random
from datetime import datetime
from werkzeug.security import generate_password_hash

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to CSV file
DOCTORS_CSV = "attached_assets/new_doctors_profiles - Sheet1.csv"
BATCH_SIZE = 5  # Process doctors in small batches

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    import os
    import psycopg2
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def add_doctors_batch(start_index=0, batch_size=BATCH_SIZE):
    """Add a batch of doctors to the database."""
    if not os.path.exists(DOCTORS_CSV):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV}")
        return False
    
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # Read all rows from CSV
        all_rows = []
        with open(DOCTORS_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_rows = list(reader)
        
        # Get only the batch we want to process
        end_index = min(start_index + batch_size, len(all_rows))
        batch_rows = all_rows[start_index:end_index]
        
        if not batch_rows:
            logger.info(f"No more doctors to process starting from index {start_index}")
            return False
        
        # Process the batch
        doctors_added = 0
        users_added = 0
        skipped = 0
        
        for row in batch_rows:
            # Get essential fields
            doctor_name = row.get('Doctor Name', '').strip()
            
            # Skip if essential fields are missing
            if not doctor_name:
                skipped += 1
                continue
            
            # Check if doctor already exists
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM doctors WHERE name = %s", (doctor_name,))
                result = cur.fetchone()
                
                if result:
                    # Doctor already exists
                    logger.info(f"Doctor already exists: {doctor_name} (ID: {result[0]})")
                    skipped += 1
                    continue
                
                # Create username and email
                username = doctor_name.lower().replace(' ', '_').replace('.', '').replace(',', '')
                email = f"{username}@example.com"
                
                # Check if user already exists with this email
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                result = cur.fetchone()
                
                if result:
                    # Try with a different email
                    email = f"{username}_{random.randint(100, 999)}@example.com"
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    result = cur.fetchone()
                    
                    if result:
                        logger.warning(f"User already exists with email: {email}")
                        skipped += 1
                        continue
                
                # Generate a phone number (since we don't have this in CSV)
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
                users_added += 1
                
                # Extract years from experience
                experience_text = row.get('Experience', '')
                experience_years = 0
                if experience_text:
                    # Try to extract the years
                    try:
                        # Look for digits at the beginning of the experience string
                        digits = ''.join(c for c in experience_text.split()[0] if c.isdigit())
                        if digits:
                            experience_years = int(digits)
                        else:
                            experience_years = 10  # Default value
                    except (ValueError, IndexError):
                        experience_years = 10  # Default value
                else:
                    experience_years = 10  # Default value
                
                # Store education as JSON
                education = row.get('education', '')
                education_json = "[]"
                if education:
                    education_json = json.dumps([{"degree": degree.strip()} for degree in education.split(',')])
                
                # Create doctor profile
                cur.execute("""
                    INSERT INTO doctors (
                        user_id, name, specialty, experience, city, state, hospital,
                        consultation_fee, is_verified, rating, review_count, bio,
                        education, verification_status, verification_date
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    datetime.utcnow()
                ))
                
                doctor_id = cur.fetchone()[0]
                doctors_added += 1
                logger.info(f"Added doctor: {doctor_name} (ID: {doctor_id})")
        
        conn.commit()
        logger.info(f"Batch processed: Added {doctors_added} doctors and {users_added} users (skipped {skipped})")
        
        # Return the next start index for the next batch
        return end_index
    except Exception as e:
        logger.error(f"Error adding doctors batch: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def associate_doctors_with_procedures_batch(start_index=0, batch_size=BATCH_SIZE):
    """Associate a batch of doctors with procedures."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # Get all doctors
        with conn.cursor() as cur:
            cur.execute("SELECT id, specialty FROM doctors ORDER BY id")
            all_doctors = cur.fetchall()
        
        if not all_doctors:
            logger.warning("No doctors found to associate with procedures.")
            return False
        
        # Get only the batch we want to process
        end_index = min(start_index + batch_size, len(all_doctors))
        batch_doctors = all_doctors[start_index:end_index]
        
        if not batch_doctors:
            logger.info(f"No more doctors to process starting from index {start_index}")
            return False
        
        # Get all procedures
        with conn.cursor() as cur:
            cur.execute("SELECT id, procedure_name FROM procedures ORDER BY id")
            all_procedures = cur.fetchall()
        
        if not all_procedures:
            logger.warning("No procedures found to associate with doctors.")
            return False
        
        # Process the batch
        associations_added = 0
        doctors_processed = 0
        
        for doctor_id, specialty in batch_doctors:
            matched_procedures = []
            specialty = specialty.lower() if specialty else "plastic surgeon"
            
            # For plastic surgeons, assign a broader range of procedures
            if "plastic" in specialty or "cosmetic" in specialty or "aesthetic" in specialty:
                # Get a random selection of procedures (10-15)
                count = min(len(all_procedures), random.randint(10, 15))
                matched_procedures = random.sample(all_procedures, count)
            else:
                # For specific specialists, try to match procedures by keywords
                specialty_keywords = specialty.split()
                matched_by_keyword = []
                
                for proc_id, proc_name in all_procedures:
                    for keyword in specialty_keywords:
                        if len(keyword) > 3 and keyword.lower() in proc_name.lower():
                            matched_by_keyword.append((proc_id, proc_name))
                            break
                
                # If we found matches by keyword, use those
                if matched_by_keyword:
                    matched_procedures = matched_by_keyword[:min(len(matched_by_keyword), 15)]
                else:
                    # Otherwise, assign a small random selection
                    count = min(len(all_procedures), random.randint(5, 10))
                    matched_procedures = random.sample(all_procedures, count)
            
            # Create doctor-procedure associations
            for proc_id, proc_name in matched_procedures:
                with conn.cursor() as cur:
                    # Check if association already exists
                    cur.execute(
                        "SELECT id FROM doctor_procedures WHERE doctor_id = %s AND procedure_id = %s",
                        (doctor_id, proc_id)
                    )
                    result = cur.fetchone()
                    
                    if not result:
                        # Create new association
                        cur.execute("""
                            INSERT INTO doctor_procedures (doctor_id, procedure_id)
                            VALUES (%s, %s)
                        """, (doctor_id, proc_id))
                        
                        associations_added += 1
                        logger.info(f"Associated doctor (ID: {doctor_id}) with procedure: {proc_name} (ID: {proc_id})")
            
            doctors_processed += 1
        
        conn.commit()
        logger.info(f"Batch processed: Associated {doctors_processed} doctors with {associations_added} procedures")
        
        # Return the next start index for the next batch
        return end_index
    except Exception as e:
        logger.error(f"Error associating doctors with procedures: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def process_all_doctors():
    """Process all doctors in batches."""
    logger.info("Starting doctor import in batches...")
    
    start_index = 0
    while True:
        result = add_doctors_batch(start_index, BATCH_SIZE)
        if result is False:
            logger.error("Doctor import failed")
            return False
        if result == start_index:
            logger.info("All doctors processed")
            break
        start_index = result
    
    logger.info("Starting doctor-procedure association in batches...")
    
    start_index = 0
    while True:
        result = associate_doctors_with_procedures_batch(start_index, BATCH_SIZE)
        if result is False:
            logger.error("Doctor-procedure association failed")
            return False
        if result == start_index:
            logger.info("All doctor-procedure associations processed")
            break
        start_index = result
    
    logger.info("Doctor import and association completed successfully")
    return True

if __name__ == "__main__":
    process_all_doctors()