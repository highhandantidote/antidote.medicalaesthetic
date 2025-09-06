#!/usr/bin/env python3
"""
Final attempt to add remaining doctors directly to the database.
This script uses minimal SQL with hardcoded values for maximum reliability.
"""
import os
import psycopg2
import json
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_connection():
    """Get a database connection."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def add_remaining_doctors():
    """Add the remaining doctors one by one."""
    doctors = [
        {"name": "Dr. Anand Sharma", "specialty": "Cosmetic Surgeon", "city": "Mumbai"},
        {"name": "Dr. Bhavna Patel", "specialty": "Plastic Surgeon", "city": "Delhi"},
        {"name": "Dr. Chetan Desai", "specialty": "Facial Plastic Surgeon", "city": "Bengaluru"},
        {"name": "Dr. Divya Agarwal", "specialty": "Aesthetic Surgeon", "city": "Chennai"},
        {"name": "Dr. Eshan Gupta", "specialty": "Plastic Surgeon", "city": "Hyderabad"},
        {"name": "Dr. Falguni Mehta", "specialty": "Cosmetic Dermatologist", "city": "Pune"},
        {"name": "Dr. Gaurav Singh", "specialty": "Plastic Surgeon", "city": "Kolkata"},
        {"name": "Dr. Hina Khan", "specialty": "Aesthetic Surgeon", "city": "Ahmedabad"},
        {"name": "Dr. Imran Ali", "specialty": "Plastic Surgeon", "city": "Jaipur"},
        {"name": "Dr. Jayshree Naidu", "specialty": "Facial Plastic Surgeon", "city": "Lucknow"}
    ]
    
    # Add doctors one by one
    added_count = 0
    
    for doctor in doctors:
        # Skip if doctor already exists
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM doctors WHERE LOWER(name) = LOWER(%s)",
                    (doctor["name"],)
                )
                if cursor.fetchone():
                    logger.info(f"Doctor {doctor['name']} already exists. Skipping.")
                    conn.close()
                    continue
            
            # Add new doctor with separate connection
            conn.close()
            conn = get_connection()
            
            # Create user first
            with conn.cursor() as cursor:
                username = doctor["name"].lower().replace(' ', '_').replace('.', '')
                email = f"{username}@example.com"
                phone_number = f"+91{random.randint(7000000000, 9999999999)}"
                
                cursor.execute("""
                    INSERT INTO users (
                        username, email, name, role, role_type, phone_number,
                        created_at, is_verified, password_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    username,
                    email,
                    doctor["name"],
                    'doctor',
                    'doctor',
                    phone_number,
                    datetime.utcnow(),
                    True,
                    "pbkdf2:sha256:600000$default_password_hash"  # placeholder hash
                ))
                
                user_id = cursor.fetchone()[0]
                conn.commit()
                
                # Create doctor profile
                education = json.dumps([{"degree": "MBBS", "institution": "Medical College", "year": ""}])
                certifications = json.dumps([])
                
                cursor.execute("""
                    INSERT INTO doctors (
                        user_id, name, specialty, experience, city,
                        consultation_fee, is_verified, rating, review_count, created_at,
                        bio, certifications, education, verification_status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    user_id,
                    doctor["name"],
                    doctor["specialty"],
                    random.randint(5, 20),  # experience
                    doctor["city"],
                    1500,  # consultation_fee
                    False,  # is_verified
                    round(random.uniform(4.0, 5.0), 1),  # rating
                    random.randint(10, 50),  # review_count
                    datetime.utcnow(),
                    "Experienced healthcare professional specializing in cosmetic procedures.",  # bio
                    certifications,
                    education,
                    'pending'  # verification_status
                ))
                conn.commit()
                
                added_count += 1
                logger.info(f"Successfully added doctor {added_count}: {doctor['name']}")
        
        except Exception as e:
            logger.error(f"Error adding doctor {doctor['name']}: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    # Get final count
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            final_count = cursor.fetchone()[0]
            logger.info(f"Final doctor count: {final_count}")
    finally:
        conn.close()
    
    return added_count

def main():
    """Run the final doctor import."""
    logger.info("Starting final doctor import")
    start_time = datetime.now()
    
    # Get initial doctor count
    conn = get_connection()
    initial_count = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            initial_count = cursor.fetchone()[0]
            logger.info(f"Initial doctor count: {initial_count}")
    finally:
        conn.close()
    
    # Add remaining doctors
    added_count = add_remaining_doctors()
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Added {added_count} doctors in {elapsed:.2f} seconds")
    logger.info(f"Initial count: {initial_count}, Final count: {initial_count + added_count}")

if __name__ == "__main__":
    main()