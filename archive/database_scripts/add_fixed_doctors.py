#!/usr/bin/env python3
"""
Add a specific set of doctors directly to the database.

This script focuses ONLY on adding doctors with minimal SQL commands.
"""
import os
import psycopg2
import json
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """Get a database connection."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def add_doctors():
    """Add a specific set of doctors."""
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
        {"name": "Dr. Jayshree Naidu", "specialty": "Facial Plastic Surgeon", "city": "Lucknow"},
        {"name": "Dr. Kunal Verma", "specialty": "Cosmetic Surgeon", "city": "Chandigarh"},
        {"name": "Dr. Leela Reddy", "specialty": "Plastic Surgeon", "city": "Bhopal"},
        {"name": "Dr. Manish Joshi", "specialty": "Aesthetic Surgeon", "city": "Indore"},
        {"name": "Dr. Neha Malhotra", "specialty": "Cosmetic Dermatologist", "city": "Nagpur"},
        {"name": "Dr. Omkar Kulkarni", "specialty": "Plastic Surgeon", "city": "Surat"}
    ]
    
    # Get existing doctor names
    conn = get_connection()
    existing_doctors = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT LOWER(name) FROM doctors")
            existing_doctors = [row[0] for row in cursor.fetchall() if row[0]]
        logger.info(f"Found {len(existing_doctors)} existing doctors")
    finally:
        conn.close()
        
    added_count = 0
    
    # Process each doctor individually with separate connections
    for doctor in doctors:
        # Skip if doctor already exists
        if doctor["name"].lower() in existing_doctors:
            logger.info(f"Doctor {doctor['name']} already exists. Skipping.")
            continue
            
        conn = get_connection()
        try:
            # Create user
            username = doctor["name"].lower().replace(' ', '_').replace('.', '')
            email = f"{username}@example.com"
            phone_number = f"+91{random.randint(7000000000, 9999999999)}"
            
            with conn.cursor() as cursor:
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
                existing_doctors.append(doctor["name"].lower())
                logger.info(f"Added doctor: {doctor['name']}")
        
        except Exception as e:
            logger.error(f"Error adding doctor {doctor['name']}: {str(e)}")
            conn.rollback()
        finally:
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
    """Run the doctor import process."""
    # Add doctors
    doctor_count = add_doctors()
    logger.info(f"Added {doctor_count} doctors")

if __name__ == "__main__":
    main()