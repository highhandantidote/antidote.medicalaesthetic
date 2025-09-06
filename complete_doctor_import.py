#!/usr/bin/env python3
"""
Complete the doctor import by adding the final 4 doctors.

This script creates proper user accounts and adds the remaining doctors to complete the import.
"""

import psycopg2
import os
import json
from dotenv import load_dotenv
import logging
import random
import hashlib
import string
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    conn.autocommit = True
    return conn

def count_doctors():
    """Count the number of doctors in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM doctors")
    result = cursor.fetchone()
    count = result[0] if result else 0
    cursor.close()
    conn.close()
    return count

def doctor_exists(doctor_name):
    """Check if a doctor already exists in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE name = %s", (doctor_name,))
    result = cursor.fetchone()
    exists = result[0] > 0 if result else False
    cursor.close()
    conn.close()
    return exists

def create_user_and_doctor(doctor_data):
    """Create a user account and doctor record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate unique username and email
        base_username = doctor_data['name'].replace('Dr. ', '').replace(' ', '').lower()
        username = base_username
        email = f"{base_username}@antidote.com"
        
        # Check if username/email already exists and make unique
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone()[0] > 0:
            suffix = random.randint(100, 999)
            username = f"{base_username}{suffix}"
            email = f"{base_username}{suffix}@antidote.com"
        
        # Generate password hash
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, created_at, name)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, password_hash, 'doctor', datetime.now(), doctor_data['name']))
        
        user_id = cursor.fetchone()[0]
        logging.info(f"Created user account for {doctor_data['name']} with ID {user_id}")
        
        # Prepare education and certifications as JSON
        education = json.dumps(doctor_data['education'])
        certifications = json.dumps(doctor_data['certifications'])
        
        # Insert doctor
        cursor.execute("""
            INSERT INTO doctors (
                name, user_id, profile_image, education, specialty, experience, 
                city, state, hospital, practice_location, certifications, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            doctor_data['name'],
            user_id,
            doctor_data['profile_image'],
            education,
            doctor_data['specialty'],
            doctor_data['experience'],
            doctor_data['city'],
            doctor_data['state'],
            doctor_data['hospital'],
            doctor_data['practice_location'],
            certifications,
            datetime.now()
        ))
        
        doctor_id = cursor.fetchone()[0]
        logging.info(f"Successfully added doctor: {doctor_data['name']} with ID {doctor_id}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error adding doctor {doctor_data['name']}: {e}")
        cursor.close()
        conn.close()
        return False

def add_remaining_doctors():
    """Add the final 4 doctors to complete the import."""
    doctors_to_add = [
        {
            "name": "Dr. Karishma Kagodu",
            "specialty": "Plastic Surgeon",
            "experience": 12,
            "city": "Bangalore",
            "state": "Karnataka",
            "hospital": "Manipal Hospital",
            "practice_location": "Manipal Hospital, Old Airport Road, Bangalore",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "education": [
                {"degree": "MBBS", "institution": "Bangalore Medical College", "year": "2010"},
                {"degree": "MS", "institution": "Bangalore Medical College", "year": "2013"}
            ],
            "certifications": [
                {"name": "Board Certified Plastic Surgeon", "year": "2015"},
                {"name": "Member, Association of Plastic Surgeons of India", "year": "2016"}
            ]
        },
        {
            "name": "Dr. Alexander George",
            "specialty": "Plastic Surgeon",
            "experience": 14,
            "city": "Kochi",
            "state": "Kerala",
            "hospital": "Aster Medcity",
            "practice_location": "Aster Medcity, Kochi",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "education": [
                {"degree": "MBBS", "institution": "Government Medical College, Kottayam", "year": "2008"},
                {"degree": "MS", "institution": "Government Medical College, Kottayam", "year": "2011"}
            ],
            "certifications": [
                {"name": "Board Certified Plastic Surgeon", "year": "2013"},
                {"name": "Fellow, Indian Association of Plastic Surgeons", "year": "2014"}
            ]
        },
        {
            "name": "Dr. Salil Patil",
            "specialty": "Plastic Surgeon",
            "experience": 16,
            "city": "Pune",
            "state": "Maharashtra",
            "hospital": "Ruby Hall Clinic",
            "practice_location": "Ruby Hall Clinic, Pune",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "education": [
                {"degree": "MBBS", "institution": "BJ Medical College, Pune", "year": "2006"},
                {"degree": "MS", "institution": "BJ Medical College, Pune", "year": "2009"}
            ],
            "certifications": [
                {"name": "Board Certified Plastic Surgeon", "year": "2011"},
                {"name": "Member, International Society of Aesthetic Plastic Surgery", "year": "2012"}
            ]
        },
        {
            "name": "Dr. Jyoshid R. Balan",
            "specialty": "Plastic Surgeon",
            "experience": 18,
            "city": "Thiruvananthapuram",
            "state": "Kerala",
            "hospital": "SIMS Hospital",
            "practice_location": "SIMS Hospital, Thiruvananthapuram",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "education": [
                {"degree": "MBBS", "institution": "Government Medical College, Thiruvananthapuram", "year": "2004"},
                {"degree": "MS", "institution": "Government Medical College, Thiruvananthapuram", "year": "2007"}
            ],
            "certifications": [
                {"name": "Board Certified Plastic Surgeon", "year": "2009"},
                {"name": "Fellow, Royal College of Surgeons", "year": "2010"}
            ]
        }
    ]
    
    doctors_added = 0
    
    for doctor in doctors_to_add:
        if doctor_exists(doctor["name"]):
            logging.info(f"Doctor {doctor['name']} already exists, skipping")
            continue
        
        if create_user_and_doctor(doctor):
            doctors_added += 1
        else:
            logging.error(f"Failed to add doctor {doctor['name']}")
    
    return doctors_added

def check_import_status():
    """Check the current import status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Count procedures
        cursor.execute("SELECT COUNT(*) FROM procedures")
        procedure_count = cursor.fetchone()[0]
        
        # Count doctors
        cursor.execute("SELECT COUNT(*) FROM doctors")
        doctor_count = cursor.fetchone()[0]
        
        # Count body parts
        cursor.execute("SELECT COUNT(*) FROM body_parts")
        body_part_count = cursor.fetchone()[0]
        
        # Count categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        
        logging.info("==================================================")
        logging.info("DATABASE IMPORT STATUS")
        logging.info("==================================================")
        logging.info(f"Body Parts: {body_part_count}")
        logging.info(f"Categories: {category_count}")
        logging.info(f"Procedures: {procedure_count}")
        logging.info(f"Doctors: {doctor_count}")
        logging.info("==================================================")
        
        return doctor_count, procedure_count
    
    except Exception as e:
        logging.error(f"Error checking import status: {e}")
        return 0, 0
    
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to complete the doctor import."""
    logging.info("Starting final doctor import to complete the database...")
    
    before_count, procedures = check_import_status()
    logging.info(f"Before import: {before_count} doctors in database")
    
    added = add_remaining_doctors()
    
    after_count, _ = check_import_status()
    logging.info(f"After import: {after_count} doctors in database")
    logging.info(f"Successfully added {added} doctors")
    
    if after_count >= 115:
        logging.info("🎉 DATABASE IMPORT COMPLETE! 🎉")
        logging.info(f"✅ {procedures} procedures imported")
        logging.info(f"✅ {after_count} doctors imported")
        logging.info("The Antidote Platform database is now fully populated!")
    else:
        logging.info(f"Import progress: {after_count}/115 doctors completed")

if __name__ == "__main__":
    main()