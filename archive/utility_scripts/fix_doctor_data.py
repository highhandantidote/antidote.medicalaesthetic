#!/usr/bin/env python3
"""
Fix doctor data by updating profiles with complete information from the CSV.

This script addresses issues with doctor profiles:
- Updates missing profile images
- Corrects experience values (extracts numeric values)
- Updates missing education/qualifications
"""

import os
import csv
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
        return 0
    
    # Look for numbers in the string
    years_match = re.search(r'(\d+)', experience_string)
    if years_match:
        return int(years_match.group(1))
    return 0

def load_csv_data():
    """Load doctor data from CSV file."""
    csv_doctors = {}
    
    try:
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('Doctor Name', '').strip()
                if name:
                    # Extract experience years
                    experience_text = row.get('Experience', '')
                    experience_years = extract_years(experience_text)
                    
                    csv_doctors[name] = {
                        'profile_image': row.get('Profile Image', '').strip(),
                        'education': row.get('education', '').strip(),
                        'specialty': row.get('specialty', '').strip(),
                        'experience': experience_years,
                        'address': row.get('Address', '').strip(),
                        'city': row.get('city', '').strip(),
                        'state': row.get('state', '').strip()
                    }
        
        logger.info(f"Loaded {len(csv_doctors)} doctors from CSV")
        return csv_doctors
    
    except Exception as e:
        logger.error(f"Error loading CSV data: {str(e)}")
        return {}

def fix_doctor_data():
    """Update doctor profiles with complete data from CSV."""
    # Load CSV data
    csv_doctors = load_csv_data()
    if not csv_doctors:
        logger.error("Failed to load CSV data")
        return 0
    
    conn = get_db_connection()
    try:
        # Get all doctor IDs and names from database
        doctors_db = {}
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM doctors")
            for doctor_id, name in cursor.fetchall():
                doctors_db[name] = doctor_id
        
        logger.info(f"Found {len(doctors_db)} doctors in database")
        
        # Start updating doctors
        updated_count = 0
        
        for doctor_name, doctor_id in doctors_db.items():
            if doctor_name not in csv_doctors:
                logger.warning(f"Doctor {doctor_name} not found in CSV")
                continue
            
            # Get CSV data for this doctor
            csv_data = csv_doctors[doctor_name]
            
            try:
                # Update doctor profile with complete data
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE doctors 
                        SET profile_image = %s,
                            education = %s,
                            specialty = %s,
                            experience = %s,
                            address = %s,
                            city = %s,
                            state = %s,
                            updated_at = %s
                        WHERE id = %s
                    """, (
                        csv_data['profile_image'],
                        csv_data['education'],
                        csv_data['specialty'],
                        csv_data['experience'],
                        csv_data['address'],
                        csv_data['city'],
                        csv_data['state'],
                        datetime.now(),
                        doctor_id
                    ))
                
                updated_count += 1
                logger.info(f"Updated doctor: {doctor_name}")
                
                # Commit after each update to avoid losing progress
                conn.commit()
                
            except Exception as e:
                logger.error(f"Error updating doctor {doctor_name}: {str(e)}")
                conn.rollback()
        
        logger.info(f"Successfully updated {updated_count} doctor profiles")
        return updated_count
    
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return 0
    
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting doctor data fix")
    fix_count = fix_doctor_data()
    logger.info(f"Fixed {fix_count} doctor profiles")