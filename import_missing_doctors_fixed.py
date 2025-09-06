#!/usr/bin/env python3
"""
Import missing doctors from CSV to database with correct structure.

This script adds doctors that are in the CSV but not in the database,
using the actual database structure.
"""

import os
import csv
import json
import logging
import psycopg2
import re
import random
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
DOCTORS_CSV_PATH = "./attached_assets/new_doctors_profiles2 - Sheet1.csv"
DEFAULT_CONSULTATION_FEE = 1500
DEFAULT_BIO = "Experienced healthcare professional specializing in cosmetic procedures."

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def extract_years(experience_string):
    """Extract years of experience from string."""
    if not experience_string:
        return 5  # Default experience
    
    # Look for numbers in the string
    years_match = re.search(r'(\d+)', experience_string)
    if years_match:
        return int(years_match.group(1))
    return 5  # Default if no digits found

def format_education_as_json(education_str):
    """Format education string as JSON array."""
    if not education_str:
        return json.dumps(["MBBS"])
    
    # Split by commas and create array
    education_items = [item.strip() for item in education_str.split(',')]
    return json.dumps(education_items)

def get_existing_doctors():
    """Get names of all doctors currently in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM doctors")
            return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

def create_user_for_doctor(conn, doctor_name, email=None):
    """Create a user account for a doctor based on actual database structure."""
    # Generate username from doctor name
    username = doctor_name.lower().replace("dr. ", "").replace("dr.", "").strip()
    username = ''.join(c for c in username if c.isalnum() or c.isspace()).replace(" ", ".")
    
    # Generate email if not provided
    if not email:
        email = f"{username}@example.com"
    
    # Generate a random password
    password = f"Doctor{random.randint(10000, 99999)}"
    
    # Check if user already exists with this email
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            return existing_user[0]
        
        # Create new user based on actual database structure
        cursor.execute(
            """
            INSERT INTO users (
                username, email, password_hash, is_verified, 
                role, created_at, name, bio
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """,
            (
                username,
                email,
                generate_password_hash(password),
                True,
                'doctor',  # Use role field instead of is_doctor
                datetime.now(),
                doctor_name,
                DEFAULT_BIO
            )
        )
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            logger.info(f"Created user account for doctor: {doctor_name} (ID: {user_id}, Email: {email})")
            return user_id
        else:
            logger.error(f"Failed to create user for doctor: {doctor_name}")
            return None

def import_missing_doctors():
    """Import doctors that are in CSV but not in database."""
    # Get existing doctors
    existing_doctors = get_existing_doctors()
    logger.info(f"Found {len(existing_doctors)} doctors in database")
    
    # Load all doctors from CSV
    csv_doctors = []
    with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Doctor Name', '').strip()
            if name and name not in existing_doctors:
                csv_doctors.append(row)
    
    logger.info(f"Found {len(csv_doctors)} doctors in CSV that need to be imported")
    
    # Import missing doctors
    conn = get_db_connection()
    try:
        conn.autocommit = False
        doctors_added = 0
        
        for data in csv_doctors:
            name = data.get('Doctor Name', '').strip()
            if not name:
                continue
                
            try:
                # Create user for doctor
                user_id = create_user_for_doctor(conn, name)
                if not user_id:
                    logger.error(f"Failed to create user for {name}")
                    continue
                
                # Extract and format data
                profile_image = data.get('Profile Image', '').strip()
                education_str = data.get('education', '').strip()
                education_json = format_education_as_json(education_str)
                specialty = data.get('specialty', 'Plastic Surgeon').strip()
                experience = extract_years(data.get('Experience', ''))
                address = data.get('Address', '').strip()
                city = data.get('city', '').strip()
                state = data.get('state', '').strip()
                
                # Insert doctor
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO doctors (
                            name, user_id, specialty, education,
                            experience, bio, address, city, state,
                            profile_image, consultation_fee, is_verified,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            name,
                            user_id,
                            specialty,
                            education_json,
                            experience,
                            DEFAULT_BIO,
                            address,
                            city,
                            state,
                            profile_image,
                            DEFAULT_CONSULTATION_FEE,
                            True,  # Set verified to true by default
                            datetime.now(),
                            datetime.now()
                        )
                    )
                    result = cursor.fetchone()
                    if result:
                        doctor_id = result[0]
                        logger.info(f"Added doctor: {name} (ID: {doctor_id})")
                        doctors_added += 1
                        conn.commit()  # Commit each doctor individually
                    else:
                        logger.error(f"Failed to add doctor: {name}")
                        conn.rollback()
                        continue
                
            except Exception as e:
                logger.error(f"Error adding doctor {name}: {str(e)}")
                conn.rollback()
        
        logger.info(f"Successfully added {doctors_added} doctors from CSV")
        return doctors_added
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting import of missing doctors from CSV")
    count = import_missing_doctors()
    logger.info(f"Imported {count} missing doctors from CSV")