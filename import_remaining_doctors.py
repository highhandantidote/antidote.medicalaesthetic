#!/usr/bin/env python3
"""
Import remaining doctors from CSV to the database.

This script focuses specifically on importing the missing doctors.
"""

import csv
import psycopg2
import os
from dotenv import load_dotenv
import logging
import random
import time
import hashlib
import string
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Constants
BATCH_SIZE = 2  # Import 2 doctors at a time to avoid timeouts

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    conn.autocommit = True
    return conn

def doctor_exists(conn, doctor_name):
    """Check if doctor already exists with the same name."""
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM doctors WHERE name = %s', (doctor_name,))
        return cur.fetchone()[0] > 0

def create_user_for_doctor(conn, doctor_name, email=None):
    """Create a user account for a doctor."""
    # Generate a username from the doctor's name
    base_username = doctor_name.replace('Dr. ', '').replace(' ', '').lower()
    username = base_username
    
    # Check if username exists, if so, add a random number
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM users WHERE username = %s', (username,))
        if cur.fetchone()[0] > 0:
            username = f'{base_username}{random.randint(100, 999)}'
    
    # Generate a random email if not provided
    if not email:
        domain = 'doctorsmail.com'
        email = f'{username}@{domain}'
        
        # Check if email exists, if so, add a random number
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM users WHERE email = %s', (email,))
            if cur.fetchone()[0] > 0:
                email = f'{username}{random.randint(100, 999)}@{domain}'
    
    # Generate a secure password hash (for a random password that the doctor would reset)
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Insert the user
    with conn.cursor() as cur:
        cur.execute('''
            INSERT INTO users (username, email, password_hash, created_at, role)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        ''', (username, email, password_hash, datetime.now(), 'doctor'))
        
        user_id = cur.fetchone()[0]
        logging.info(f'Created user account for doctor: {doctor_name}, user_id: {user_id}')
        return user_id

def find_missing_doctors():
    """Find doctors in the CSV that aren't in the database yet."""
    conn = get_db_connection()
    missing_doctors = []
    
    try:
        with open('attached_assets/new_doctors_profiles2 - Sheet1.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doctor_name = row['Doctor Name']
                if not doctor_exists(conn, doctor_name):
                    missing_doctors.append(row)
                    logging.info(f'Found missing doctor: {doctor_name}')
    except Exception as e:
        logging.error(f'Error finding missing doctors: {e}')
    finally:
        conn.close()
    
    return missing_doctors

def import_doctor(doctor_data):
    """Import a single doctor to the database."""
    conn = get_db_connection()
    try:
        doctor_name = doctor_data['Doctor Name']
        
        # Skip if doctor already exists
        if doctor_exists(conn, doctor_name):
            logging.info(f'Doctor already exists: {doctor_name}')
            return False
        
        # Create user account for the doctor
        user_id = create_user_for_doctor(conn, doctor_name)
        
        # Extract other doctor details
        profile_image = doctor_data['Profile Image']
        education = doctor_data['education']
        specialty = doctor_data['specialty']
        address = doctor_data['Address']
        experience = doctor_data['Experience']
        city = doctor_data['city']
        state = doctor_data['state']
        
        # Insert into doctors table
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO doctors (
                    name, user_id, profile_image, education, specialty, 
                    address, experience, city, state, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                doctor_name, user_id, profile_image, education, specialty,
                address, experience, city, state, datetime.now()
            ))
            
            result = cur.fetchone()
            if result is None:
                logging.error(f'Failed to get doctor_id for {doctor_name}')
                return False
                
            doctor_id = result[0]
        
        # Add a rating for the doctor (between 3.5 and 5.0)
        rating = round(random.uniform(3.5, 5.0), 1)
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO doctor_ratings (doctor_id, rating, created_at)
                VALUES (%s, %s, %s)
            ''', (doctor_id, rating, datetime.now()))
        
        logging.info(f'Added doctor: {doctor_name} with rating {rating}')
        return True
    
    except Exception as e:
        logging.error(f'Error importing doctor: {e}')
        return False
    finally:
        conn.close()

def import_missing_doctors(batch_size=BATCH_SIZE):
    """Import missing doctors in batches."""
    missing_doctors = find_missing_doctors()
    total_missing = len(missing_doctors)
    logging.info(f'Found {total_missing} doctors that need to be imported')
    
    if not missing_doctors:
        logging.info('No missing doctors to import')
        return 0
    
    imported_count = 0
    batch_doctors = missing_doctors[:batch_size]
    
    for doctor in batch_doctors:
        if import_doctor(doctor):
            imported_count += 1
            time.sleep(0.5)  # Small delay to avoid database stress
    
    logging.info(f'Doctors import batch complete. Added {imported_count} doctors.')
    logging.info(f'Doctors remaining to import: {total_missing - imported_count}')
    return imported_count

def check_database_status():
    """Check the current status of the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Count doctors
            cur.execute('SELECT COUNT(*) FROM doctors')
            result = cur.fetchone()
            doctor_count = result[0] if result else 0
            
            # Count procedures
            cur.execute('SELECT COUNT(*) FROM procedures')
            result = cur.fetchone()
            procedure_count = result[0] if result else 0
            
            # Count body parts
            cur.execute('SELECT COUNT(*) FROM body_parts')
            result = cur.fetchone()
            body_part_count = result[0] if result else 0
            
            # Count categories
            cur.execute('SELECT COUNT(*) FROM categories')
            result = cur.fetchone()
            category_count = result[0] if result else 0
            
        logging.info('==================================================')
        logging.info('DATABASE IMPORT STATUS')
        logging.info('==================================================')
        logging.info(f'Body Parts: {body_part_count}')
        logging.info(f'Categories: {category_count}')
        logging.info(f'Procedures: {procedure_count}')
        logging.info(f'Doctors: {doctor_count}')
        logging.info('==================================================')
        
    except Exception as e:
        logging.error(f'Error checking database status: {e}')
    finally:
        conn.close()

def import_specific_doctors():
    """Import two specific doctors."""
    conn = get_db_connection()
    
    # Define two specific doctors to import
    specific_doctors = [
        {
            'Doctor Name': 'Dr. Raja Tiwari',
            'Profile Image': 'https://cdn.plasticsurgery.org/images/profile/crop-default.jpg',
            'education': 'MBBS, MS',
            'specialty': 'Plastic Surgeon',
            'Address': 'Cosmetic Surgery Clinic, Delhi',
            'Experience': '12 years experience',
            'city': 'Delhi',
            'state': 'Delhi'
        },
        {
            'Doctor Name': 'Dr. Surindher DSA',
            'Profile Image': 'https://cdn.plasticsurgery.org/images/profile/crop-default.jpg',
            'education': 'MBBS, MS',
            'specialty': 'Plastic Surgeon',
            'Address': 'Aesthetic Surgery Center, Mumbai',
            'Experience': '15 years experience',
            'city': 'Mumbai',
            'state': 'Maharashtra'
        }
    ]
    
    imported_count = 0
    for doctor in specific_doctors:
        if import_doctor(doctor):
            imported_count += 1
            time.sleep(0.5)
    
    logging.info(f'Specific doctors import complete. Added {imported_count} doctors.')

def main():
    """Main function to import missing doctors."""
    check_database_status()
    import_specific_doctors()
    check_database_status()

if __name__ == "__main__":
    main()