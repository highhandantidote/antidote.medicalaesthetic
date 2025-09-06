#!/usr/bin/env python3
"""
Update doctor profiles with correct data from CSV.

This script properly formats:
- Education as JSON
- Profile images from URLs
- Experience years as integers
"""

import os
import csv
import json
import logging
import psycopg2
import re
from datetime import datetime

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

def get_doctor_data():
    """Get database doctor IDs and names."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM doctors")
            return {name: doctor_id for doctor_id, name in cursor.fetchall()}
    finally:
        conn.close()

def load_csv_doctors():
    """Load and format doctor data from CSV."""
    doctors = {}
    
    try:
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('Doctor Name', '').strip()
                if name:
                    experience_str = row.get('Experience', '')
                    education_str = row.get('education', '')
                    
                    doctors[name] = {
                        'profile_image': row.get('Profile Image', '').strip(),
                        'education_json': format_education_as_json(education_str),
                        'specialty': row.get('specialty', 'Plastic Surgeon').strip(),
                        'experience': extract_years(experience_str),
                        'address': row.get('Address', '').strip(),
                        'city': row.get('city', '').strip(),
                        'state': row.get('state', '').strip()
                    }
        
        return doctors
    except Exception as e:
        logger.error(f"Error loading CSV: {str(e)}")
        return {}

def update_doctor_profiles():
    """Update doctor profiles with properly formatted data."""
    # Get database doctor IDs
    db_doctors = get_doctor_data()
    if not db_doctors:
        logger.error("Failed to retrieve doctor IDs from database")
        return 0
    
    logger.info(f"Found {len(db_doctors)} doctors in database")
    
    # Load doctor data from CSV
    csv_doctors = load_csv_doctors()
    if not csv_doctors:
        logger.error("Failed to load doctor data from CSV")
        return 0
    
    logger.info(f"Loaded {len(csv_doctors)} doctors from CSV")
    
    # Update each doctor
    conn = get_db_connection()
    try:
        conn.autocommit = False
        updated_count = 0
        
        for name, doctor_id in db_doctors.items():
            if name not in csv_doctors:
                logger.warning(f"Doctor not found in CSV: {name}")
                continue
            
            data = csv_doctors[name]
            
            try:
                # Print details for debugging
                logger.info(f"Updating doctor {name} (ID: {doctor_id}):")
                logger.info(f"  Profile Image: {data['profile_image']}")
                logger.info(f"  Education JSON: {data['education_json']}")
                logger.info(f"  Specialty: {data['specialty']}")
                logger.info(f"  Experience: {data['experience']}")
                
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE doctors 
                        SET profile_image = %s,
                            education = %s,
                            specialty = %s, 
                            experience = %s
                        WHERE id = %s
                    """, (
                        data['profile_image'],
                        data['education_json'],
                        data['specialty'],
                        data['experience'],
                        doctor_id
                    ))
                
                updated_count += 1
                conn.commit()  # Commit each update
                logger.info(f"Updated doctor: {name}")
                
            except Exception as e:
                logger.error(f"Error updating doctor {name}: {str(e)}")
                conn.rollback()
        
        logger.info(f"Successfully updated {updated_count} doctor profiles")
        return updated_count
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting doctor profile update")
    count = update_doctor_profiles()
    if count > 0:
        logger.info(f"Successfully updated {count} doctor profiles")
    else:
        logger.error("Failed to update doctor profiles")