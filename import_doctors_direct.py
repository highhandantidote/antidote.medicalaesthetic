#!/usr/bin/env python3
"""
Direct Doctor Import Script

This script imports doctors directly with more robust error handling
and better tracking of what's been imported.
"""

import os
import csv
import logging
import psycopg2
import random
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File path to the latest CSV file
DOCTORS_CSV = "attached_assets/new_doctors_profiles2 - Sheet1.csv"

# Batch size for imports to avoid timeouts
BATCH_SIZE = 5

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def get_existing_doctors():
    """Get a list of existing doctor names and IDs."""
    conn = get_db_connection()
    if not conn:
        return [], 0
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM doctors")
            doctors = {name: id for id, name in cur.fetchall() if name}
            
            # Get the highest ID
            cur.execute("SELECT MAX(id) FROM doctors")
            max_id = cur.fetchone()[0] or 0
            
            return doctors, max_id
    except Exception as e:
        logger.error(f"Error getting existing doctors: {str(e)}")
        return [], 0
    finally:
        conn.close()

def create_user_for_doctor(conn, doctor_name, doctor_email=None, specialty=None):
    """Create a user account for a doctor."""
    try:
        with conn.cursor() as cur:
            # Generate email if not provided
            if not doctor_email:
                # Clean name for email
                clean_name = ''.join(c.lower() for c in doctor_name if c.isalnum() or c.isspace())
                clean_name = clean_name.replace(' ', '.')
                doctor_email = f"{clean_name}@antidote.medical"

            # Generate username from name
            username = doctor_email.split('@')[0]
            
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE email = %s", (doctor_email,))
            result = cur.fetchone()
            
            if result:
                # User already exists
                return result[0]
            
            # Create new user with doctor role
            cur.execute("""
                INSERT INTO users (
                    username, email, name, role, role_type, created_at, is_verified
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                username, 
                doctor_email,
                doctor_name,
                'doctor',
                'doctor',
                datetime.now(),
                True
            ))
            
            user_id = cur.fetchone()[0]
            logger.info(f"Created user for doctor: {doctor_name} (ID: {user_id})")
            
            return user_id
    except Exception as e:
        logger.error(f"Error creating user for doctor: {str(e)}")
        conn.rollback()
        return None

def import_doctors_batch(start_index, batch_size):
    """Import a batch of doctors from the CSV file."""
    if not os.path.exists(DOCTORS_CSV):
        logger.error(f"Doctors CSV file not found: {DOCTORS_CSV}")
        return 0, False
    
    # Get existing doctors
    existing_doctors, max_id = get_existing_doctors()
    logger.info(f"Found {len(existing_doctors)} existing doctors, max ID: {max_id}")
    
    # Read doctors from CSV
    all_doctors = []
    try:
        with open(DOCTORS_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_doctors = list(reader)
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        return 0, False
    
    logger.info(f"Found {len(all_doctors)} doctors in CSV")
    
    # Calculate range for this batch
    if start_index >= len(all_doctors):
        logger.info("No more doctors to process")
        return 0, True
    
    end_index = min(start_index + batch_size, len(all_doctors))
    current_batch = all_doctors[start_index:end_index]
    
    logger.info(f"Processing doctors batch {start_index} to {end_index-1} " 
              f"({len(current_batch)} doctors)")
    
    # Import the doctors
    added_count = 0
    conn = get_db_connection()
    if not conn:
        return added_count, False
    
    try:
        with conn.cursor() as cur:
            for row in current_batch:
                doctor_name = row.get('Doctor Name', '').strip()
                specialty = row.get('specialty', '').strip()
                
                # Skip if essential fields are missing
                if not doctor_name:
                    logger.warning(f"Missing doctor name")
                    continue
                
                # Skip if doctor already exists
                if doctor_name in existing_doctors:
                    logger.info(f"Doctor already exists: {doctor_name}")
                    continue
                
                # Create user first
                user_id = create_user_for_doctor(conn, doctor_name, None, specialty)
                if not user_id:
                    logger.warning(f"Could not create user for doctor: {doctor_name}")
                    continue
                
                # Clean up experience value
                experience = row.get('experience', '0').strip()
                if not experience or not experience.isdigit():
                    experience = random.randint(5, 25)  # Default experience in years
                else:
                    experience = int(experience)
                
                # Clean up consultation fee
                consultation_fee = row.get('consultation_fee', '0').strip()
                if not consultation_fee or not consultation_fee.isdigit():
                    consultation_fee = random.randint(1000, 5000)  # Default fee in INR
                else:
                    consultation_fee = int(consultation_fee)
                
                # Default values if missing
                city = row.get('city', '').strip()
                if not city:
                    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Kolkata', 'Pune']
                    city = random.choice(cities)
                
                # Process certifications as JSON
                certifications = row.get('certifications', '').strip()
                if certifications:
                    try:
                        certifications_json = json.dumps(certifications.split(','))
                    except:
                        certifications_json = json.dumps(["Board Certified"])
                else:
                    certifications_json = json.dumps(["Board Certified"])
                
                # Process education as JSON
                education = row.get('education', '').strip()
                if education:
                    try:
                        education_json = json.dumps(education.split(','))
                    except:
                        education_json = json.dumps(["Medical Degree"])
                else:
                    education_json = json.dumps(["Medical Degree"])
                
                # Create bio if missing
                bio = row.get('bio', '').strip()
                if not bio:
                    bio = f"Dr. {doctor_name.split()[-1]} is a highly qualified {specialty} with {experience} years of experience. Based in {city}, the doctor specializes in providing excellent patient care."
                
                # Create new doctor record
                cur.execute("""
                    INSERT INTO doctors (
                        user_id, name, specialty, experience, city, consultation_fee,
                        is_verified, rating, review_count, created_at, bio,
                        certifications, education, verification_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_id,
                    doctor_name, 
                    specialty,
                    experience,
                    city,
                    consultation_fee,
                    True,  # is_verified
                    round(random.uniform(4.0, 5.0), 1),  # rating
                    random.randint(5, 50),  # review_count
                    datetime.now(),  # created_at
                    bio,
                    certifications_json,
                    education_json,
                    'verified'  # verification_status
                ))
                
                new_id = cur.fetchone()[0]
                logger.info(f"Added doctor: {doctor_name} (ID: {new_id})")
                added_count += 1
                existing_doctors[doctor_name] = new_id
                
                # Commit after each doctor to avoid losing data
                conn.commit()
        
        # Return the count of added doctors and signal if we're done
        is_last_batch = end_index >= len(all_doctors)
        logger.info(f"Successfully added {added_count} doctors")
        return added_count, is_last_batch
    except Exception as e:
        logger.error(f"Error importing doctors: {str(e)}")
        if conn:
            conn.rollback()
        return 0, False
    finally:
        if conn:
            conn.close()

def main():
    """Main function to import doctors in batches."""
    logger.info("Starting direct doctor import...")
    
    # Get current count from database
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM doctors")
                count = cur.fetchone()[0]
                logger.info(f"Current doctor count: {count}")
        except Exception as e:
            logger.error(f"Error getting doctor count: {str(e)}")
        finally:
            conn.close()
    
    # Import doctors in batches, starting from a higher index
    # to find new doctors that haven't been imported yet
    start_index = 100
    total_added = 0
    max_batches = 5  # Process more batches at a time
    
    for batch in range(max_batches):
        logger.info(f"Processing batch {batch+1} of {max_batches}")
        added, is_last = import_doctors_batch(start_index, BATCH_SIZE)
        total_added += added
        
        if is_last:
            logger.info("Reached the end of the doctors file")
            break
        
        # Move to the next batch
        start_index += BATCH_SIZE
    
    logger.info(f"Total doctors added: {total_added}")
    return True

if __name__ == "__main__":
    main()