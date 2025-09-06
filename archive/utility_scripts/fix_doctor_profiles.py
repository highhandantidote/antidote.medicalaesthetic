#!/usr/bin/env python3
"""
Fix doctor profiles by updating missing fields from the CSV data.

This script updates existing doctor profiles with correct data from the CSV:
- Fixes missing profile images
- Corrects experience values (converts to integers)
- Updates missing education/qualifications
"""

import os
import csv
import logging
import psycopg2
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
DEFAULT_QUALIFICATION = "MBBS, MS"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

def get_all_doctors():
    """Get all doctors from the database with their current values."""
    conn = get_db_connection()
    doctors = {}
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, profile_image, experience, education 
                FROM doctors
                """
            )
            for doctor_id, name, profile_image, experience, education in cursor.fetchall():
                # Convert experience to int if it's not None, otherwise keep as None
                exp_value = int(experience) if experience is not None else None
                
                doctors[name] = {
                    'id': doctor_id,
                    'profile_image': profile_image,
                    'experience': exp_value,
                    'education': education
                }
                
                # Log current doctor data
                logger.info(f"Doctor in DB: {name}, ID: {doctor_id}, Image: {'Yes' if profile_image else 'No'}, Exp: {exp_value}, Edu: {'Yes' if education else 'No'}")
                
        logger.info(f"Found {len(doctors)} doctors in database")
        return doctors
    
    except Exception as e:
        logger.error(f"Error fetching doctors: {str(e)}")
        return {}
    
    finally:
        conn.close()

def parse_experience(exp_str):
    """Parse experience string to integer years."""
    if not exp_str or exp_str.strip() == '':
        return 5  # Default experience if missing
    
    # Try to extract numeric value
    try:
        # Extract digits from string like "10 years"
        digits = ''.join(c for c in exp_str if c.isdigit())
        if digits:
            return int(digits)
        return 5  # Default if no digits found
    except:
        return 5  # Default on error

def fix_doctor_profiles():
    """Update doctor profiles with correct data from CSV."""
    # Get all doctors currently in the database
    existing_doctors = get_all_doctors()
    if not existing_doctors:
        logger.error("Failed to retrieve doctors from database")
        return 0
    
    # Load CSV data
    csv_doctors = {}
    try:
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                doctor_name = row.get('Doctor Name', '').strip()
                if doctor_name:
                    csv_doctors[doctor_name] = {
                        'profile_image': row.get('Profile Image', '').strip(),
                        'experience': row.get('Experience', '').strip(),
                        'education': row.get('education', '').strip()
                    }
        logger.info(f"Loaded {len(csv_doctors)} doctors from CSV")
    except Exception as e:
        logger.error(f"Error loading CSV: {str(e)}")
        return 0
    
    # Update doctor profiles
    conn = get_db_connection()
    try:
        updated_count = 0
        batch_count = 0
        
        for doctor_name, db_data in existing_doctors.items():
            # Skip if doctor not in CSV
            if doctor_name not in csv_doctors:
                logger.warning(f"Doctor not found in CSV: {doctor_name}")
                continue
            
            # Get CSV data for this doctor
            csv_data = csv_doctors[doctor_name]
            doctor_id = db_data['id']
            
            # Determine what needs updating
            updates_needed = False
            update_fields = []
            update_values = []
            
            # Check profile image
            if (not db_data['profile_image'] or db_data['profile_image'] == '') and csv_data['profile_image']:
                updates_needed = True
                update_fields.append("profile_image = %s")
                update_values.append(csv_data['profile_image'])
                logger.info(f"Will update missing profile image for {doctor_name}")
            
            # Check experience
            csv_experience = parse_experience(csv_data['experience'])
            db_experience = db_data['experience'] if db_data['experience'] else 0
            
            if not db_experience and csv_experience:
                updates_needed = True
                update_fields.append("experience = %s")
                update_values.append(str(csv_experience))
                logger.info(f"Will update experience for {doctor_name} to {csv_experience}")
            
            # Check education/qualifications
            if (not db_data['education'] or db_data['education'] == '') and csv_data['education']:
                education = csv_data['education'] if csv_data['education'] else DEFAULT_QUALIFICATION
                updates_needed = True
                update_fields.append("education = %s")
                update_values.append(education)
                logger.info(f"Will update education for {doctor_name}")
            
            # If updates needed, update the doctor profile
            if updates_needed:
                try:
                    # Add updated_at value to update values
                    update_values.append(datetime.now())
                    # Add doctor_id as the WHERE clause parameter
                    update_values.append(doctor_id)
                    
                    with conn.cursor() as cursor:
                        update_sql = f"""
                            UPDATE doctors 
                            SET {', '.join(update_fields)}, updated_at = %s
                            WHERE id = %s
                        """
                        cursor.execute(update_sql, update_values)
                    
                    updated_count += 1
                    batch_count += 1
                    
                    # Commit every 10 updates
                    if batch_count >= 10:
                        conn.commit()
                        batch_count = 0
                        logger.info(f"Committed batch. Total updated: {updated_count}")
                
                except Exception as e:
                    logger.error(f"Error updating doctor {doctor_name}: {str(e)}")
                    conn.rollback()
        
        # Commit any remaining updates
        if batch_count > 0:
            conn.commit()
        
        logger.info(f"Updated {updated_count} doctor profiles with corrected data")
        return updated_count
    
    except Exception as e:
        logger.error(f"Error during profile update: {str(e)}")
        conn.rollback()
        return 0
    
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting doctor profile fix...")
    fixed_count = fix_doctor_profiles()
    if fixed_count > 0:
        logger.info(f"Successfully fixed {fixed_count} doctor profiles")
    else:
        logger.error("Failed to fix any doctor profiles")