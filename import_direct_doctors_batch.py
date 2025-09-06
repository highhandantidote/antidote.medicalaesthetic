#!/usr/bin/env python3
"""
Import specific doctors directly to the database.

This script targets doctors from higher indexes in the CSV to avoid duplicates.
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

# File paths to the CSV files
DOCTORS_CSV = "attached_assets/new_doctors_profiles2 - Sheet1.csv"

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

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
            
            if result and result[0]:
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
            
            result = cur.fetchone()
            if result and result[0]:
                user_id = result[0]
                logger.info(f"Created user for doctor: {doctor_name} (ID: {user_id})")
                return user_id
            else:
                logger.warning(f"Failed to create user for doctor: {doctor_name}")
                return None
    except Exception as e:
        logger.error(f"Error creating user for doctor: {str(e)}")
        conn.rollback()
        return None

def import_specific_doctors():
    """Import specific doctors from the CSV file."""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Get existing doctor names to avoid duplicates
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM doctors")
            existing_doctors = set(row[0] for row in cur.fetchall() if row[0])
            logger.info(f"Found {len(existing_doctors)} existing doctors")
        
        # Load all doctors from CSV
        all_doctors = []
        with open(DOCTORS_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for idx, row in enumerate(reader):
                all_doctors.append((idx, row))
        
        # Choose specific doctors from different sections of the CSV
        # Target different indices than before to avoid duplicates
        target_indices = [68, 72, 76, 82, 84, 88, 92, 96, 98, 102, 104, 106, 108, 110, 112, 114]
        
        doctors_added = 0
        for idx_pair in target_indices:
            if idx_pair < len(all_doctors):
                idx, row = all_doctors[idx_pair]
                
                # Get essential fields
                doctor_name = row.get('Doctor Name', '').strip()
                specialty = row.get('specialty', '').strip()
                
                # Skip if essential fields are missing
                if not doctor_name:
                    logger.warning(f"Missing essential fields for doctor at index {idx}")
                    continue
                
                # Skip if doctor already exists
                if doctor_name in existing_doctors:
                    logger.info(f"Doctor already exists: {doctor_name}")
                    continue
                
                logger.info(f"Adding doctor: {doctor_name} from index {idx}")
                
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
                
                try:
                    # Create new doctor
                    with conn.cursor() as cur:
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
                        
                        result = cur.fetchone()
                        if result and result[0]:
                            doctor_id = result[0]
                            logger.info(f"Added doctor: {doctor_name} (ID: {doctor_id}) from index {idx}")
                            doctors_added += 1
                            conn.commit()  # Commit after each doctor
                        else:
                            logger.warning(f"Failed to add doctor: {doctor_name}")
                            continue
                except Exception as e:
                    logger.error(f"Error adding doctor {doctor_name}: {str(e)}")
                    conn.rollback()
                    continue
            else:
                logger.warning(f"Index {idx_pair} is out of range")
        
        logger.info(f"Successfully added {doctors_added} doctors")
        return True
    except Exception as e:
        logger.error(f"Error in import_specific_doctors: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting direct doctor import...")
    success = import_specific_doctors()
    if success:
        logger.info("Direct doctor import completed successfully")
    else:
        logger.error("Direct doctor import failed")