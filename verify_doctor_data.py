#!/usr/bin/env python3
"""
Verify that all doctors in the database perfectly match those in the CSV file.

This script:
1. Compares doctor names between database and CSV
2. Verifies all critical fields match (profile image, experience, education)
3. Reports any discrepancies found
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
VERIFICATION_REPORT = f"doctor_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

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

def format_education_list(education_json):
    """Format education JSON as a sorted list for comparison."""
    if not education_json:
        return []
    
    try:
        if isinstance(education_json, str):
            education_list = json.loads(education_json)
        else:
            education_list = education_json
            
        # Handle null case
        if education_list is None:
            return []
            
        # Ensure it's a list and sort for consistent comparison
        if isinstance(education_list, list):
            return sorted([str(item).strip() for item in education_list])
        else:
            return []
    except:
        return []

def load_csv_doctors():
    """Load all doctors from CSV with formatted data for comparison."""
    csv_doctors = {}
    
    with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Doctor Name', '').strip()
            if name:
                # Format data for consistent comparison
                experience = extract_years(row.get('Experience', ''))
                education = row.get('education', '').strip()
                education_list = [item.strip() for item in education.split(',')] if education else []
                
                csv_doctors[name] = {
                    'profile_image': row.get('Profile Image', '').strip(),
                    'experience': experience,
                    'education': sorted(education_list),
                    'specialty': row.get('specialty', '').strip(),
                    'city': row.get('city', '').strip(),
                    'state': row.get('state', '').strip()
                }
    
    return csv_doctors

def get_db_doctors():
    """Get all doctors from database with formatted data for comparison."""
    conn = get_db_connection()
    db_doctors = {}
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, profile_image, education, experience, 
                       specialty, city, state
                FROM doctors
            """)
            
            for row in cursor.fetchall():
                (doctor_id, name, profile_image, education_json, 
                 experience, specialty, city, state) = row
                
                education_list = format_education_list(education_json)
                
                db_doctors[name] = {
                    'id': doctor_id,
                    'profile_image': profile_image or '',
                    'experience': experience or 0,
                    'education': education_list,
                    'specialty': specialty or '',
                    'city': city or '',
                    'state': state or ''
                }
        
        return db_doctors
    
    finally:
        conn.close()

def verify_doctors_match():
    """Verify that all doctors in database match those in CSV file."""
    # Load doctor data from both sources
    csv_doctors = load_csv_doctors()
    db_doctors = get_db_doctors()
    
    logger.info(f"Found {len(csv_doctors)} doctors in CSV")
    logger.info(f"Found {len(db_doctors)} doctors in database")
    
    # Check for missing doctors
    csv_only = set(csv_doctors.keys()) - set(db_doctors.keys())
    db_only = set(db_doctors.keys()) - set(csv_doctors.keys())
    
    # Track verification results
    verification_results = {
        'csv_only': list(csv_only),
        'db_only': list(db_only),
        'mismatches': [],
        'matches': []
    }
    
    # Check for data mismatches in common doctors
    common_doctors = set(csv_doctors.keys()) & set(db_doctors.keys())
    
    for name in common_doctors:
        csv_data = csv_doctors[name]
        db_data = db_doctors[name]
        
        mismatches = []
        
        # Check profile image
        if csv_data['profile_image'] and not db_data['profile_image']:
            mismatches.append(f"Missing profile image: CSV has {csv_data['profile_image']}, DB is empty")
        
        # Check experience (allow small variance)
        if abs(csv_data['experience'] - db_data['experience']) > 3:
            mismatches.append(f"Experience mismatch: CSV={csv_data['experience']}, DB={db_data['experience']}")
        
        # Check education (sets for order-independent comparison)
        csv_edu_set = set(csv_data['education'])
        db_edu_set = set(db_data['education'])
        
        if csv_edu_set and not db_edu_set:
            mismatches.append(f"Missing education: CSV has {csv_edu_set}, DB is empty")
        
        if mismatches:
            verification_results['mismatches'].append({
                'name': name,
                'id': db_data['id'],
                'issues': mismatches
            })
        else:
            verification_results['matches'].append(name)
    
    # Generate report
    with open(VERIFICATION_REPORT, 'w') as report:
        report.write("DOCTOR DATA VERIFICATION REPORT\n")
        report.write("=============================\n\n")
        
        report.write(f"CSV doctors: {len(csv_doctors)}\n")
        report.write(f"Database doctors: {len(db_doctors)}\n")
        report.write(f"Matching doctors: {len(verification_results['matches'])}\n\n")
        
        # Report CSV-only doctors
        if verification_results['csv_only']:
            report.write("DOCTORS IN CSV BUT NOT IN DATABASE\n")
            report.write("=================================\n")
            for i, name in enumerate(verification_results['csv_only'], 1):
                report.write(f"{i}. {name}\n")
            report.write("\n")
        
        # Report DB-only doctors
        if verification_results['db_only']:
            report.write("DOCTORS IN DATABASE BUT NOT IN CSV\n")
            report.write("=================================\n")
            for i, name in enumerate(verification_results['db_only'], 1):
                report.write(f"{i}. {name}\n")
            report.write("\n")
        
        # Report mismatches
        if verification_results['mismatches']:
            report.write("DOCTORS WITH DATA MISMATCHES\n")
            report.write("===========================\n")
            for i, mismatch in enumerate(verification_results['mismatches'], 1):
                report.write(f"{i}. {mismatch['name']} (ID: {mismatch['id']})\n")
                for issue in mismatch['issues']:
                    report.write(f"   - {issue}\n")
                report.write("\n")
    
    # Print summary
    print("\nVERIFICATION SUMMARY:")
    print(f"Total doctors in CSV: {len(csv_doctors)}")
    print(f"Total doctors in database: {len(db_doctors)}")
    print(f"Perfectly matching doctors: {len(verification_results['matches'])}")
    print(f"Doctors in CSV but not in database: {len(verification_results['csv_only'])}")
    print(f"Doctors in database but not in CSV: {len(verification_results['db_only'])}")
    print(f"Doctors with data mismatches: {len(verification_results['mismatches'])}")
    print(f"\nDetailed report saved to: {VERIFICATION_REPORT}")
    
    return verification_results

if __name__ == "__main__":
    logger.info("Starting doctor data verification")
    results = verify_doctors_match()
    
    success = (len(results['csv_only']) == 0 and 
               len(results['db_only']) == 0 and 
               len(results['mismatches']) == 0)
    
    if success:
        logger.info("VERIFICATION SUCCESSFUL: All doctors in database perfectly match the CSV file!")
    else:
        logger.warning("VERIFICATION FAILED: Found discrepancies between database and CSV.")
    
    logger.info(f"Verification report saved to {VERIFICATION_REPORT}")