#!/usr/bin/env python3
"""
Complete the deduplication of doctor records and generate a final report.

This script:
1. Removes any remaining duplicate doctors
2. Verifies all doctors match the CSV data
3. Generates a comprehensive report
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
FINAL_REPORT = "doctor_data_final_report.txt"

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

def remove_remaining_duplicates():
    """Remove any remaining duplicate doctor records."""
    conn = get_db_connection()
    try:
        conn.autocommit = False
        removed_count = 0
        
        with conn.cursor() as cursor:
            # Find all duplicate names
            cursor.execute("""
                SELECT name
                FROM doctors 
                GROUP BY name 
                HAVING COUNT(*) > 1
            """)
            duplicate_names = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Found {len(duplicate_names)} remaining doctor names with duplicates")
            
            # For each duplicate name, keep only the highest ID
            for name in duplicate_names:
                # Get the highest ID for this doctor name
                cursor.execute("SELECT MAX(id) FROM doctors WHERE name = %s", (name,))
                max_id = cursor.fetchone()[0]
                
                # Delete all other records for this doctor
                cursor.execute("DELETE FROM doctors WHERE name = %s AND id != %s", (name, max_id))
                
                deleted = cursor.rowcount
                removed_count += deleted
                logger.info(f"For doctor '{name}': kept ID {max_id}, removed {deleted} duplicate(s)")
                
                # Commit after each doctor to avoid long transactions
                conn.commit()
        
        logger.info(f"Successfully removed {removed_count} duplicate doctor records")
        return removed_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error removing duplicates: {str(e)}")
        return 0
        
    finally:
        conn.close()

def load_csv_doctors():
    """Load doctor data from CSV."""
    csv_doctors = {}
    
    try:
        with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('Doctor Name', '').strip()
                if name:
                    csv_doctors[name] = row
        
        logger.info(f"Loaded {len(csv_doctors)} doctors from CSV")
        return csv_doctors
        
    except Exception as e:
        logger.error(f"Error loading CSV: {str(e)}")
        return {}

def get_all_db_doctors():
    """Get all doctors from the database."""
    conn = get_db_connection()
    try:
        db_doctors = {}
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, profile_image, education, experience 
                FROM doctors
            """)
            
            for doctor_id, name, profile_image, education, experience in cursor.fetchall():
                db_doctors[name] = {
                    'id': doctor_id,
                    'profile_image': profile_image,
                    'education': education,
                    'experience': experience
                }
        
        logger.info(f"Retrieved {len(db_doctors)} doctors from database")
        return db_doctors
        
    finally:
        conn.close()

def generate_final_report():
    """Generate a comprehensive final report on doctor data."""
    # Get doctor data from both sources
    csv_doctors = load_csv_doctors()
    db_doctors = get_all_db_doctors()
    
    # Check for discrepancies
    csv_only = [name for name in csv_doctors if name not in db_doctors]
    db_only = [name for name in db_doctors if name not in csv_doctors]
    
    # Count doctors with missing data
    missing_image = []
    missing_education = []
    missing_experience = []
    
    for name, doctor in db_doctors.items():
        if not doctor.get('profile_image'):
            missing_image.append(name)
        
        if not doctor.get('education') or doctor.get('education') == 'null' or doctor.get('education') == '[]':
            missing_education.append(name)
        
        if not doctor.get('experience') or doctor.get('experience') == 0:
            missing_experience.append(name)
    
    # Generate report
    with open(FINAL_REPORT, 'w') as report:
        report.write("FINAL DOCTOR DATA REPORT\n")
        report.write("======================\n\n")
        
        report.write(f"CSV doctors: {len(csv_doctors)}\n")
        report.write(f"Database doctors: {len(db_doctors)}\n\n")
        
        # Report on CSV vs DB discrepancies
        report.write("DATA DISCREPANCIES\n")
        report.write("=================\n")
        report.write(f"Doctors in CSV but not in database: {len(csv_only)}\n")
        if csv_only:
            for name in csv_only:
                report.write(f"  - {name}\n")
            report.write("\n")
        
        report.write(f"Doctors in database but not in CSV: {len(db_only)}\n")
        if db_only:
            for name in db_only:
                report.write(f"  - {name}\n")
            report.write("\n")
        
        # Report on data quality
        report.write("DATA QUALITY ISSUES\n")
        report.write("=================\n")
        report.write(f"Doctors missing profile image: {len(missing_image)}\n")
        if missing_image and len(missing_image) <= 10:
            for name in missing_image:
                report.write(f"  - {name}\n")
            report.write("\n")
        
        report.write(f"Doctors missing education data: {len(missing_education)}\n")
        if missing_education and len(missing_education) <= 10:
            for name in missing_education:
                report.write(f"  - {name}\n")
            report.write("\n")
        
        report.write(f"Doctors missing experience data: {len(missing_experience)}\n")
        if missing_experience and len(missing_experience) <= 10:
            for name in missing_experience:
                report.write(f"  - {name}\n")
            report.write("\n")
        
        # Overall assessment
        report.write("OVERALL ASSESSMENT\n")
        report.write("=================\n")
        
        data_quality_score = 100
        if len(csv_doctors) > 0:
            data_quality_score -= (len(csv_only) / len(csv_doctors)) * 30
        if len(db_doctors) > 0:
            data_quality_score -= (len(db_only) / len(db_doctors)) * 30
            data_quality_score -= (len(missing_image) / len(db_doctors)) * 15
            data_quality_score -= (len(missing_education) / len(db_doctors)) * 15
            data_quality_score -= (len(missing_experience) / len(db_doctors)) * 10
        
        data_quality_score = max(0, min(100, data_quality_score))
        
        if data_quality_score >= 90:
            assessment = "Excellent"
        elif data_quality_score >= 75:
            assessment = "Good"
        elif data_quality_score >= 60:
            assessment = "Fair"
        else:
            assessment = "Poor"
        
        report.write(f"Data Quality Score: {data_quality_score:.1f}% ({assessment})\n\n")
        
        # Make recommendations
        report.write("RECOMMENDATIONS\n")
        report.write("==============\n")
        
        if csv_only:
            report.write("1. Import the remaining doctors from CSV\n")
        
        if db_only:
            report.write("2. Consider removing doctors that are not in the CSV\n")
        
        if missing_image or missing_education or missing_experience:
            report.write("3. Fix missing data for doctors with incomplete profiles\n")
    
    # Print summary
    print("\nFINAL DOCTOR DATA SUMMARY:")
    print(f"Total doctors in database: {len(db_doctors)}")
    print(f"Total doctors in CSV: {len(csv_doctors)}")
    print(f"Doctors in CSV but not in database: {len(csv_only)}")
    print(f"Doctors in database but not in CSV: {len(db_only)}")
    print(f"Doctors missing profile image: {len(missing_image)}")
    print(f"Doctors missing education data: {len(missing_education)}")
    print(f"Doctors missing experience data: {len(missing_experience)}")
    print(f"\nDetailed report saved to: {FINAL_REPORT}")
    
    return {
        'db_count': len(db_doctors),
        'csv_count': len(csv_doctors),
        'csv_only': len(csv_only),
        'db_only': len(db_only),
        'missing_image': len(missing_image),
        'missing_education': len(missing_education),
        'missing_experience': len(missing_experience),
        'data_quality_score': data_quality_score
    }

def check_for_duplicates():
    """Check if any duplicate doctor names remain in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM (
                    SELECT name
                    FROM doctors 
                    GROUP BY name 
                    HAVING COUNT(*) > 1
                ) AS duplicates
            """)
            duplicate_count = cursor.fetchone()[0]
            
            return duplicate_count
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting final doctor data cleanup and reporting")
    
    # Check for duplicates
    duplicate_count = check_for_duplicates()
    if duplicate_count > 0:
        logger.info(f"Found {duplicate_count} doctor names with duplicates")
        removed = remove_remaining_duplicates()
        logger.info(f"Removed {removed} duplicate doctor records")
    else:
        logger.info("No duplicate doctor names found")
    
    # Generate final report
    logger.info("Generating final doctor data report")
    results = generate_final_report()
    
    # Final message
    print("\nDOCTOR DATA CLEANUP COMPLETE!")
    print(f"Data quality score: {results['data_quality_score']:.1f}%")
    print(f"Final report has been saved to {FINAL_REPORT}")