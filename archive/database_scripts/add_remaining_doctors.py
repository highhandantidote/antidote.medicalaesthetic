#!/usr/bin/env python3
"""
Add remaining doctors to the database.

This script focuses on adding the last 5 doctors missing from the import.
"""

import psycopg2
import os
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

def add_doctors():
    """Add the remaining doctors to the database."""
    # List of doctors to add
    doctors_to_add = [
        {
            "name": "Dr. Raja Tiwari",
            "education": "MBBS, MS",
            "specialty": "Plastic Surgeon",
            "address": "Cosmetic Surgery Clinic, Delhi",
            "experience": "12 years experience",
            "city": "Delhi",
            "state": "Delhi",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg"
        },
        {
            "name": "Dr. Surindher DSA",
            "education": "MBBS, MS",
            "specialty": "Plastic Surgeon",
            "address": "Aesthetic Surgery Center, Mumbai",
            "experience": "15 years experience",
            "city": "Mumbai",
            "state": "Maharashtra",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg"
        },
        {
            "name": "Dr. Madhu Kumar",
            "education": "MBBS, MCh",
            "specialty": "Plastic Surgeon",
            "address": "Kumar Aesthetic Center, Chennai",
            "experience": "18 years experience",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg"
        },
        {
            "name": "Dr. Harsh B. Amin",
            "education": "MBBS, MCh",
            "specialty": "Plastic Surgeon",
            "address": "Amin Aesthetic Clinic, Ahmedabad",
            "experience": "10 years experience",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg"
        },
        {
            "name": "Dr. Charanjeev Sobti",
            "education": "MBBS, MS",
            "specialty": "Plastic Surgeon",
            "address": "Sobti Cosmetic Center, Chandigarh",
            "experience": "20 years experience",
            "city": "Chandigarh",
            "state": "Punjab",
            "profile_image": "https://cdn.plasticsurgery.org/images/profile/crop-default.jpg"
        }
    ]
    
    # Get database connection
    conn = get_db_connection()
    
    # Track successful additions
    doctors_added = 0
    
    # First, check if the name column exists in the users table
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users LIMIT 0")
        user_columns = [desc[0] for desc in cursor.description]
        has_name_column = 'name' in user_columns
        logging.info(f"User table has name column: {has_name_column}")
    except Exception as e:
        logging.error(f"Error checking user table structure: {e}")
        has_name_column = False
    finally:
        cursor.close()
    
    # Add each doctor
    for doctor in doctors_to_add:
        if doctor_exists(doctor["name"]):
            logging.info(f"Doctor {doctor['name']} already exists, skipping")
            continue
        
        try:
            # Create a transaction
            cursor = conn.cursor()
            
            # Generate username from doctor name
            username = doctor["name"].replace("Dr. ", "").replace(" ", "").lower()
            
            # Generate random email
            email = f"{username}@example.com"
            
            # Generate random password
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Insert user
            if has_name_column:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, created_at, name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (username, email, password_hash, 'doctor', datetime.now(), doctor["name"]))
            else:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (username, email, password_hash, 'doctor', datetime.now()))
            
            user_id_result = cursor.fetchone()
            if not user_id_result:
                logging.error(f"Failed to create user for {doctor['name']}")
                cursor.close()
                continue
                
            user_id = user_id_result[0]
            
            # Insert doctor
            cursor.execute("""
                INSERT INTO doctors (
                    name, user_id, profile_image, education, specialty, 
                    address, experience, city, state, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                doctor["name"], 
                user_id, 
                doctor["profile_image"], 
                doctor["education"], 
                doctor["specialty"],
                doctor["address"], 
                doctor["experience"], 
                doctor["city"], 
                doctor["state"], 
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

def main():
    """Main function to add the remaining doctors."""
    before_count = count_doctors()
    logging.info(f"Before import: {before_count} doctors in database")
    
    added = add_doctors()
    
    after_count = count_doctors()
    logging.info(f"After import: {after_count} doctors in database")
    logging.info(f"Successfully added {added} doctors")

if __name__ == "__main__":
    main()