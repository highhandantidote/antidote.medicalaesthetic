#!/usr/bin/env python3
"""
Complete the database import by adding the final doctors.

This script checks for existing users and properly links them to new doctor entries.
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging
import random
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

def get_user_id_by_email(email):
    """Get user ID from email if it exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    user_id = result[0] if result else None
    cursor.close()
    conn.close()
    return user_id

def add_doctors():
    """Add the remaining doctors to the database."""
    # List of doctors to add
    doctors_to_add = [
        {
            "name": "Dr. Raja Tiwari",
            "email": "rajatiwari@example.com",
            "education": "MBBS, MS",
            "specialty": "Plastic Surgeon",
            "practice_location": "Cosmetic Surgery Clinic, Delhi",
            "experience": "12 years experience",
            "city": "Delhi",
            "state": "Delhi",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "hospital": "Cosmetic Surgery Clinic"
        },
        {
            "name": "Dr. Surindher DSA",
            "email": "surindherdsa@example.com",
            "education": "MBBS, MS",
            "specialty": "Plastic Surgeon",
            "practice_location": "Aesthetic Surgery Center, Mumbai",
            "experience": "15 years experience",
            "city": "Mumbai",
            "state": "Maharashtra",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "hospital": "Aesthetic Surgery Center"
        },
        {
            "name": "Dr. Madhu Kumar",
            "email": "madhukumar@example.com",
            "education": "MBBS, MCh",
            "specialty": "Plastic Surgeon",
            "practice_location": "Kumar Aesthetic Center, Chennai",
            "experience": "18 years experience",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "hospital": "Kumar Aesthetic Center"
        },
        {
            "name": "Dr. Harsh B. Amin",
            "email": "harshamin@example.com",
            "education": "MBBS, MCh",
            "specialty": "Plastic Surgeon",
            "practice_location": "Amin Aesthetic Clinic, Ahmedabad",
            "experience": "10 years experience",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "hospital": "Amin Aesthetic Clinic"
        },
        {
            "name": "Dr. Charanjeev Sobti",
            "email": "charanjeevsobti@example.com",
            "education": "MBBS, MS",
            "specialty": "Plastic Surgeon",
            "practice_location": "Sobti Cosmetic Center, Chandigarh",
            "experience": "20 years experience",
            "city": "Chandigarh",
            "state": "Punjab",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg",
            "hospital": "Sobti Cosmetic Center"
        }
    ]
    
    # Get database connection
    conn = get_db_connection()
    
    # Track successful additions
    doctors_added = 0
    
    # Add each doctor
    for doctor in doctors_to_add:
        if doctor_exists(doctor["name"]):
            logging.info(f"Doctor {doctor['name']} already exists, skipping")
            continue
        
        try:
            # Create a transaction
            cursor = conn.cursor()
            
            # Check if user already exists with this email
            user_id = get_user_id_by_email(doctor["email"])
            
            if user_id is None:
                # User doesn't exist, so let's just skip this doctor for now
                logging.info(f"Cannot add doctor {doctor['name']} without a valid user account")
                cursor.close()
                continue
            
            # Insert doctor with the correct fields based on the table structure
            cursor.execute("""
                INSERT INTO doctors (
                    name, user_id, profile_image, education, specialty, 
                    practice_location, experience, city, state, hospital, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                doctor["name"], 
                user_id, 
                doctor["profile_image"], 
                doctor["education"], 
                doctor["specialty"],
                doctor["practice_location"], 
                doctor["experience"], 
                doctor["city"], 
                doctor["state"],
                doctor["hospital"],
                datetime.now()
            ))
            
            doctor_id_result = cursor.fetchone()
            if not doctor_id_result:
                logging.error(f"Failed to create doctor record for {doctor['name']}")
                cursor.close()
                continue
                
            doctor_id = doctor_id_result[0]
            
            # Add a rating for the doctor
            rating = round(random.uniform(3.5, 5.0), 1)
            cursor.execute("""
                INSERT INTO doctor_ratings (doctor_id, rating, created_at)
                VALUES (%s, %s, %s)
            """, (doctor_id, rating, datetime.now()))
            
            cursor.close()
            doctors_added += 1
            logging.info(f"Successfully added doctor: {doctor['name']} with rating {rating}")
            
        except Exception as e:
            logging.error(f"Error adding doctor {doctor['name']}: {e}")
    
    # Close the connection
    conn.close()
    
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
    
    except Exception as e:
        logging.error(f"Error checking import status: {e}")
    
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to add the remaining doctors."""
    check_import_status()
    
    before_count = count_doctors()
    logging.info(f"Before import: {before_count} doctors in database")
    
    added = add_doctors()
    
    after_count = count_doctors()
    logging.info(f"After import: {after_count} doctors in database")
    logging.info(f"Successfully added {added} doctors")
    
    check_import_status()

if __name__ == "__main__":
    main()