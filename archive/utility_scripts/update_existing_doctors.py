#!/usr/bin/env python3
"""
Update existing doctors with complete profile data from CSV.

This script:
1. Fixes missing profile images
2. Updates education JSON data
3. Corrects experience values
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

def get_doctors_for_update():
    """Get all doctors from the database that need updates, with matching CSV entries."""
    conn = get_db_connection()
    doctors_to_update = {}
    
    try:
        # Load CSV data
        csv_doctors = {}
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('Doctor Name', '').strip()
                if name:
                    csv_doctors[name] = row
        
        # Get all doctors from database
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, profile_image, education, experience
                FROM doctors
            """)
            
            for doctor_id, name, profile_image, education, experience in cursor.fetchall():
                # Only include doctors that exist in CSV
                if name in csv_doctors:
                    doctors_to_update[name] = {
                        'id': doctor_id,
                        'db_profile_image': profile_image,
                        'db_education': education,
                        'db_experience': experience,
                        'csv_data': csv_doctors[name]
                    }
        
        return doctors_to_update
    
    finally:
        conn.close()

def update_existing_doctors():
    """Update existing doctors with complete information from CSV."""
    doctors = get_doctors_for_update()
    logger.info(f"Found {len(doctors)} existing doctors that match CSV entries")
    
    conn = get_db_connection()
    try:
        conn.autocommit = False
        updated_count = 0
        
        for name, data in doctors.items():
            doctor_id = data['id']
            csv_data = data['csv_data']
            
            # Check what needs to be updated
            update_fields = []
            update_values = []
            
            # Update profile image if missing
            if not data['db_profile_image'] and csv_data.get('Profile Image'):
                profile_image = csv_data.get('Profile Image', '').strip()
                if profile_image:
                    update_fields.append("profile_image = %s")
                    update_values.append(profile_image)
                    logger.info(f"Will update profile image for {name}")
            
            # Update education if missing or empty
            if not data['db_education'] or data['db_education'] == '[]' or data['db_education'] == 'null':
                education_str = csv_data.get('education', '').strip()
                if education_str:
                    education_json = format_education_as_json(education_str)
                    update_fields.append("education = %s")
                    update_values.append(education_json)
                    logger.info(f"Will update education for {name} to {education_json}")
            
            # Update experience if zero or very low
            experience = data['db_experience'] if data['db_experience'] is not None else 0
            if experience < 2:  # Probably incorrect if less than 2 years
                experience_str = csv_data.get('Experience', '')
                if experience_str:
                    new_experience = extract_years(experience_str)
                    if new_experience > experience:
                        update_fields.append("experience = %s")
                        update_values.append(new_experience)
                        logger.info(f"Will update experience for {name} from {experience} to {new_experience}")
            
            # If any updates needed, apply them
            if update_fields:
                try:
                    query = f"""
                        UPDATE doctors 
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                    """
                    
                    with conn.cursor() as cursor:
                        cursor.execute(query, update_values + [doctor_id])
                    
                    conn.commit()
                    updated_count += 1
                    logger.info(f"Updated doctor: {name}")
                
                except Exception as e:
                    logger.error(f"Error updating doctor {name}: {str(e)}")
                    conn.rollback()
        
        logger.info(f"Successfully updated {updated_count} doctor profiles with complete information")
        return updated_count
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting update of existing doctor profiles")
    count = update_existing_doctors()
    logger.info(f"Updated {count} doctor profiles with complete information")