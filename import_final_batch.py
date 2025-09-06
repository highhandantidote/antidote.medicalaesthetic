#!/usr/bin/env python3
"""
Import the final batch of doctors to complete the database.

This script adds a few more doctors to reach our target count.
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
    
    except Exception as e:
        logging.error(f"Error checking import status: {e}")
    
    finally:
        cursor.close()
        conn.close()

def add_doctors():
    """Add the final batch of doctors to the database."""
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Track successful additions
    doctors_added = 0
    
    try:
        # Add Dr. Sumit Saxena
        username = "sumitsaxena"
        email = "sumitsaxena@example.com"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, created_at, name)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, password_hash, 'doctor', datetime.now(), "Dr. Sumit Saxena"))
        
        user_id = cursor.fetchone()[0]
        
        # Create education and certifications as proper JSON
        education = json.dumps([
            {"degree": "MBBS", "institution": "AIIMS Delhi", "year": "2005"},
            {"degree": "MS", "institution": "AIIMS Delhi", "year": "2008"}
        ])
        
        certifications = json.dumps([
            {"name": "Board Certified Plastic Surgeon", "year": "2010"},
            {"name": "Fellow, Indian Association of Plastic Surgeons", "year": "2012"}
        ])
        
        # Insert doctor
        cursor.execute("""
            INSERT INTO doctors (
                name, user_id, profile_image, education, specialty, experience, 
                city, state, hospital, practice_location, certifications, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            "Dr. Sumit Saxena", 
            user_id,
            "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            education,
            "Plastic Surgeon",
            15,
            "Delhi",
            "Delhi",
            "Cosmetic Surgery Hospital",
            "Cosmetic Surgery Hospital, Saket, Delhi",
            certifications,
            datetime.now()
        ))
        
        doctor_id = cursor.fetchone()[0]
        
        # Add a rating for the doctor
        rating = 4.8
        cursor.execute("""
            INSERT INTO doctor_ratings (doctor_id, rating, created_at)
            VALUES (%s, %s, %s)
        """, (doctor_id, rating, datetime.now()))
        
        logging.info(f"Successfully added doctor: Dr. Sumit Saxena with rating {rating}")
        doctors_added += 1
        
        # Add another doctor - Dr. Abhishek Vijayakumar
        username = "abhishekvijayakumar"
        email = "abhishekvijayakumar@example.com"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, created_at, name)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, password_hash, 'doctor', datetime.now(), "Dr. Abhishek Vijayakumar"))
        
        user_id = cursor.fetchone()[0]
        
        # Create education and certifications as proper JSON
        education = json.dumps([
            {"degree": "MBBS", "institution": "Christian Medical College, Vellore", "year": "2004"},
            {"degree": "MS", "institution": "Christian Medical College, Vellore", "year": "2007"}
        ])
        
        certifications = json.dumps([
            {"name": "Board Certified Plastic Surgeon", "year": "2009"},
            {"name": "Member, Association of Plastic Surgeons of India", "year": "2010"}
        ])
        
        # Insert doctor
        cursor.execute("""
            INSERT INTO doctors (
                name, user_id, profile_image, education, specialty, experience, 
                city, state, hospital, practice_location, certifications, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            "Dr. Abhishek Vijayakumar", 
            user_id,
            "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            education,
            "Plastic Surgeon",
            12,
            "Chennai",
            "Tamil Nadu",
            "Apollo Hospitals",
            "Apollo Hospitals, Greams Road, Chennai",
            certifications,
            datetime.now()
        ))
        
        doctor_id = cursor.fetchone()[0]
        
        # Add a rating for the doctor
        rating = 4.6
        cursor.execute("""
            INSERT INTO doctor_ratings (doctor_id, rating, created_at)
            VALUES (%s, %s, %s)
        """, (doctor_id, rating, datetime.now()))
        
        logging.info(f"Successfully added doctor: Dr. Abhishek Vijayakumar with rating {rating}")
        doctors_added += 1
        
    except Exception as e:
        logging.error(f"Error adding doctors: {e}")
    
    finally:
        cursor.close()
        conn.close()
    
    return doctors_added

def main():
    """Main function to add the final batch of doctors."""
    check_import_status()
    
    before_count = count_doctors()
    logging.info(f"Before import: {before_count} doctors in database")
    
    added = add_doctors()
    
    after_count = count_doctors()
    logging.info(f"After import: {after_count} doctors in database")
    logging.info(f"Successfully added {added} doctors")
    
    check_import_status()
    
    logging.info("Database import process is complete!")

if __name__ == "__main__":
    main()