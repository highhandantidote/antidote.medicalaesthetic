#!/usr/bin/env python3
"""
Verify doctors in database against CSV and generate a report.

This script:
1. Creates a report of all doctors in database that are NOT in the CSV file
2. Creates a report of all doctors in CSV that are NOT in the database
3. Updates all CSV doctors with proper information
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
REPORT_FILE = "doctor_verification_report.txt"

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

def get_all_db_doctors():
    """Get all doctors from database with their details."""
    conn = get_db_connection()
    doctors = {}
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, user_id, profile_image, education, experience
                FROM doctors
            """)
            for row in cursor.fetchall():
                doctor_id, name, user_id, profile_image, education, experience = row
                doctors[name] = {
                    'id': doctor_id,
                    'user_id': user_id,
                    'profile_image': profile_image,
                    'education': education,
                    'experience': experience
                }
        
        return doctors
    
    finally:
        conn.close()

def load_all_csv_doctors():
    """Load all doctors from CSV file."""
    csv_doctors = {}
    
    with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Doctor Name', '').strip()
            if name:
                csv_doctors[name] = row
    
    return csv_doctors

def generate_verification_report():
    """Generate report of doctor verification between database and CSV."""
    # Get all doctors from database and CSV
    db_doctors = get_all_db_doctors()
    csv_doctors = load_all_csv_doctors()
    
    logger.info(f"Found {len(db_doctors)} doctors in database")
    logger.info(f"Found {len(csv_doctors)} doctors in CSV")
    
    # Find doctors in DB but not in CSV
    db_only_doctors = [name for name in db_doctors.keys() if name not in csv_doctors]
    
    # Find doctors in CSV but not in DB
    csv_only_doctors = [name for name in csv_doctors.keys() if name not in db_doctors]
    
    # Generate detailed report
    with open(REPORT_FILE, 'w') as report:
        report.write("DOCTOR VERIFICATION REPORT\n")
        report.write("=========================\n\n")
        
        report.write(f"Database doctors: {len(db_doctors)}\n")
        report.write(f"CSV doctors: {len(csv_doctors)}\n\n")
        
        # DB-only doctors (potential issues)
        report.write("DOCTORS IN DATABASE BUT NOT IN CSV\n")
        report.write("=================================\n")
        for i, name in enumerate(db_only_doctors, 1):
            doctor = db_doctors[name]
            report.write(f"{i}. {name} (ID: {doctor['id']}, User ID: {doctor['user_id']})\n")
            report.write(f"   Profile Image: {'Yes' if doctor['profile_image'] else 'No'}\n")
            report.write(f"   Education: {'Yes' if doctor['education'] else 'No'}\n")
            report.write(f"   Experience: {doctor['experience']}\n\n")
        
        # CSV-only doctors (not imported)
        report.write("\nDOCTORS IN CSV BUT NOT IN DATABASE\n")
        report.write("=================================\n")
        for i, name in enumerate(csv_only_doctors, 1):
            doctor = csv_doctors[name]
            report.write(f"{i}. {name}\n")
            report.write(f"   Profile Image: {'Yes' if doctor.get('Profile Image') else 'No'}\n")
            report.write(f"   Education: {'Yes' if doctor.get('education') else 'No'}\n")
            report.write(f"   Experience: {doctor.get('Experience', 'Not specified')}\n\n")
    
    logger.info(f"Found {len(db_only_doctors)} doctors in database but not in CSV")
    logger.info(f"Found {len(csv_only_doctors)} doctors in CSV but not in database")
    logger.info(f"Report saved to {REPORT_FILE}")
    
    # Print summary to console
    print("\nSUMMARY OF POTENTIAL ISSUES:")
    print("==========================")
    print(f"Doctors in database but not in CSV: {len(db_only_doctors)}")
    for name in db_only_doctors:
        print(f" - {name}")
    
    print(f"\nDoctors in CSV but not in database: {len(csv_only_doctors)}")
    if len(csv_only_doctors) > 10:
        print(f" - First 10 of {len(csv_only_doctors)}: {', '.join(csv_only_doctors[:10])}...")
    else:
        print(f" - {', '.join(csv_only_doctors)}")
    
    return db_only_doctors, csv_only_doctors

def update_csv_doctors():
    """Update all doctors from CSV with proper data."""
    # Get database doctor IDs
    db_doctors = get_all_db_doctors()
    
    # Load doctor data from CSV
    csv_doctors = load_all_csv_doctors()
    
    # Update each doctor
    conn = get_db_connection()
    try:
        conn.autocommit = False
        updated_count = 0
        
        for name, data in csv_doctors.items():
            if name not in db_doctors:
                logger.warning(f"Doctor not in database: {name}")
                continue
            
            doctor_id = db_doctors[name]['id']
            
            # Extract and format data
            profile_image = data.get('Profile Image', '').strip()
            education_str = data.get('education', '').strip()
            education_json = format_education_as_json(education_str)
            specialty = data.get('specialty', 'Plastic Surgeon').strip()
            experience = extract_years(data.get('Experience', ''))
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE doctors 
                        SET profile_image = %s,
                            education = %s,
                            specialty = %s, 
                            experience = %s
                        WHERE id = %s
                    """, (
                        profile_image,
                        education_json,
                        specialty,
                        experience,
                        doctor_id
                    ))
                
                updated_count += 1
                conn.commit()  # Commit each update
                
            except Exception as e:
                logger.error(f"Error updating doctor {name}: {str(e)}")
                conn.rollback()
        
        logger.info(f"Successfully updated {updated_count} doctor profiles from CSV")
        return updated_count
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting doctor verification process")
    
    # Generate verification report
    db_only, csv_only = generate_verification_report()
    
    # Update all CSV doctors
    logger.info("Updating all doctors from CSV with proper data")
    updated = update_csv_doctors()
    
    logger.info("Doctor verification and update complete:")
    logger.info(f"- {len(db_only)} doctors in database but not in CSV")
    logger.info(f"- {len(csv_only)} doctors in CSV but not in database")
    logger.info(f"- {updated} doctors successfully updated from CSV")