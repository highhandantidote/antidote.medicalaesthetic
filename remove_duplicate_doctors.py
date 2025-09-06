#!/usr/bin/env python3
"""
Remove duplicate doctor records from the database.

This script:
1. Identifies all duplicate doctor records
2. Analyzes which record is more complete for each doctor
3. Keeps the most complete record and removes duplicates
4. Creates a backup of removed records
"""

import os
import json
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
BACKUP_FILE = f"removed_duplicate_doctors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def get_duplicate_doctors():
    """Get all doctors with duplicate names."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get all doctor names that appear more than once
            cursor.execute("""
                SELECT name, COUNT(*) 
                FROM doctors 
                GROUP BY name 
                HAVING COUNT(*) > 1
                ORDER BY name
            """)
            duplicate_names = [(name, count) for name, count in cursor.fetchall()]
            
            # For each duplicate name, get all the records
            duplicate_doctors = {}
            for name, count in duplicate_names:
                cursor.execute("""
                    SELECT id, user_id, profile_image, education, experience, 
                           specialty, bio, consultation_fee, created_at
                    FROM doctors 
                    WHERE name = %s
                    ORDER BY id
                """, (name,))
                
                duplicate_doctors[name] = []
                for row in cursor.fetchall():
                    (doctor_id, user_id, profile_image, education, experience, 
                     specialty, bio, consultation_fee, created_at) = row
                    
                    duplicate_doctors[name].append({
                        'id': doctor_id,
                        'user_id': user_id,
                        'profile_image': profile_image,
                        'education': education,
                        'experience': experience,
                        'specialty': specialty,
                        'bio': bio,
                        'consultation_fee': consultation_fee,
                        'created_at': created_at.isoformat() if created_at else None,
                        'completeness_score': 0  # Will calculate this next
                    })
            
            return duplicate_doctors
    
    finally:
        conn.close()

def calculate_completeness_score(doctor):
    """Calculate a completeness score for a doctor record based on available data."""
    score = 0
    
    # Profile image is very important
    if doctor['profile_image']:
        score += 10
    
    # Education is important
    if doctor['education'] and doctor['education'] not in ('null', '[]'):
        score += 5
    
    # Experience is important
    if doctor['experience'] and doctor['experience'] > 0:
        score += 5
    
    # Specialty
    if doctor['specialty']:
        score += 3
    
    # Bio
    if doctor['bio']:
        score += 2
    
    # Consultation fee
    if doctor['consultation_fee'] and doctor['consultation_fee'] > 0:
        score += 1
    
    # Newer record gets a small bonus
    if doctor['created_at']:
        score += 0.5
    
    return score

def determine_records_to_keep():
    """Determine which doctor records to keep and which to remove."""
    duplicate_doctors = get_duplicate_doctors()
    logger.info(f"Found {len(duplicate_doctors)} doctor names with duplicates")
    
    records_to_keep = {}
    records_to_remove = {}
    
    for name, duplicates in duplicate_doctors.items():
        # Calculate completeness score for each duplicate
        for doctor in duplicates:
            doctor['completeness_score'] = calculate_completeness_score(doctor)
        
        # Sort by completeness score (descending)
        sorted_duplicates = sorted(duplicates, key=lambda x: x['completeness_score'], reverse=True)
        
        # Keep the most complete record
        keep_record = sorted_duplicates[0]
        records_to_keep[name] = keep_record
        
        # Mark the rest for removal
        remove_records = sorted_duplicates[1:]
        records_to_remove[name] = remove_records
        
        logger.info(f"For {name}: keeping ID {keep_record['id']} (score: {keep_record['completeness_score']}), " + 
                   f"removing {len(remove_records)} duplicate(s)")
    
    return records_to_keep, records_to_remove

def backup_duplicate_records(records_to_remove):
    """Create a backup of the records to be removed."""
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(records_to_remove, f, indent=2)
    
    # Count total records to be removed
    total_records = sum(len(records) for records in records_to_remove.values())
    logger.info(f"Backed up {total_records} duplicate doctor records to {BACKUP_FILE}")

def remove_duplicate_records(records_to_remove):
    """Remove duplicate doctor records from the database."""
    conn = get_db_connection()
    try:
        conn.autocommit = False
        removed_count = 0
        
        with conn.cursor() as cursor:
            # For each doctor name
            for name, remove_records in records_to_remove.items():
                # Remove each duplicate record
                for record in remove_records:
                    doctor_id = record['id']
                    try:
                        cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
                        removed_count += 1
                        logger.info(f"Removed duplicate doctor ID {doctor_id} ({name})")
                    except Exception as e:
                        logger.error(f"Error removing doctor ID {doctor_id}: {str(e)}")
                        conn.rollback()
                
                # Commit after processing each doctor name
                conn.commit()
        
        return removed_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error removing duplicate doctors: {str(e)}")
        return 0
    
    finally:
        conn.close()

def verify_no_duplicates():
    """Verify that no duplicate doctor names remain in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT name, COUNT(*) 
                FROM doctors 
                GROUP BY name 
                HAVING COUNT(*) > 1
            """)
            remaining_duplicates = cursor.fetchall()
            
            if remaining_duplicates:
                logger.warning(f"Found {len(remaining_duplicates)} doctor names that still have duplicates")
                for name, count in remaining_duplicates:
                    logger.warning(f"Doctor {name} still has {count} records")
                return False
            else:
                logger.info("No duplicate doctor names remain in the database")
                return True
    
    finally:
        conn.close()

def count_doctors():
    """Get the total count of doctors in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            count = cursor.fetchone()[0]
            return count
    finally:
        conn.close()

def remove_duplicate_doctors():
    """Main function to remove duplicate doctors from the database."""
    # Get initial doctor count
    initial_count = count_doctors()
    logger.info(f"Initial doctor count: {initial_count}")
    
    # Determine which records to keep and which to remove
    records_to_keep, records_to_remove = determine_records_to_keep()
    
    # Create a backup of records to be removed
    backup_duplicate_records(records_to_remove)
    
    # Remove duplicate records
    removed_count = remove_duplicate_records(records_to_remove)
    logger.info(f"Removed {removed_count} duplicate doctor records")
    
    # Verify no duplicates remain
    if verify_no_duplicates():
        # Get final doctor count
        final_count = count_doctors()
        logger.info(f"Final doctor count: {final_count}")
        logger.info(f"Successfully removed {initial_count - final_count} duplicate doctor records")
        return True
    else:
        logger.error("Failed to remove all duplicate doctor records")
        return False

if __name__ == "__main__":
    logger.info("Starting duplicate doctor removal process")
    success = remove_duplicate_doctors()
    
    if success:
        print(f"\nSuccessfully removed duplicate doctor records!")
        print(f"A backup of the removed records has been saved to {BACKUP_FILE}")
    else:
        print(f"\nWarning: Not all duplicate doctor records were removed.")
        print(f"Please check the logs for details.")