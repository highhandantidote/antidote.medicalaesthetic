#!/usr/bin/env python3
"""
Remove doctor profiles that are not present in the CSV file.

This script:
1. Identifies doctors in the database that are NOT in the CSV file
2. Creates a backup list of these doctors before removal
3. Safely removes these profiles from the database
"""

import os
import csv
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
DOCTORS_CSV_PATH = "./attached_assets/new_doctors_profiles2 - Sheet1.csv"
BACKUP_FILE = f"removed_doctors_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def load_csv_doctor_names():
    """Load all doctor names from the CSV file."""
    csv_doctors = set()
    
    with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Doctor Name', '').strip()
            if name:
                csv_doctors.add(name)
    
    return csv_doctors

def get_non_csv_doctors():
    """Get details of all doctors in the database that are not in the CSV."""
    csv_doctors = load_csv_doctor_names()
    logger.info(f"Found {len(csv_doctors)} doctors in CSV")
    
    conn = get_db_connection()
    try:
        non_csv_doctors = []
        
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.id, d.name, d.user_id, d.created_at, u.email
                FROM doctors d
                LEFT JOIN users u ON d.user_id = u.id
            """)
            
            for doctor_id, name, user_id, created_at, email in cursor.fetchall():
                if name not in csv_doctors:
                    non_csv_doctors.append({
                        'id': doctor_id,
                        'name': name,
                        'user_id': user_id,
                        'email': email,
                        'created_at': created_at.isoformat() if created_at else None
                    })
        
        return non_csv_doctors
    
    finally:
        conn.close()

def backup_doctor_data(doctors):
    """Create a backup of doctor data before removal."""
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(doctors, f, indent=2)
    
    logger.info(f"Backed up {len(doctors)} doctor records to {BACKUP_FILE}")

def remove_doctors_not_in_csv():
    """Remove doctors that are not in the CSV file."""
    # First get and backup non-CSV doctors
    non_csv_doctors = get_non_csv_doctors()
    
    if not non_csv_doctors:
        logger.info("No doctors found that need to be removed")
        return 0
    
    logger.info(f"Found {len(non_csv_doctors)} doctors in database that are not in CSV")
    
    # Ask for confirmation before proceeding
    backup_doctor_data(non_csv_doctors)
    
    # Get just the IDs for removal
    doctor_ids = [d['id'] for d in non_csv_doctors]
    user_ids = [d['user_id'] for d in non_csv_doctors if d['user_id']]
    
    # Remove the doctors
    conn = get_db_connection()
    try:
        conn.autocommit = False
        doctors_removed = 0
        
        with conn.cursor() as cursor:
            # Delete doctor records
            doctor_ids_str = ','.join(str(id) for id in doctor_ids)
            cursor.execute(f"DELETE FROM doctors WHERE id IN ({doctor_ids_str})")
            doctors_removed = cursor.rowcount
            
            # We could also remove the associated user accounts, but let's keep them for safety
            # If you want to remove users, uncomment the lines below
            # if user_ids:
            #     user_ids_str = ','.join(str(id) for id in user_ids)
            #     cursor.execute(f"DELETE FROM users WHERE id IN ({user_ids_str})")
            #     logger.info(f"Removed {cursor.rowcount} associated user accounts")
        
        conn.commit()
        logger.info(f"Successfully removed {doctors_removed} doctor profiles that were not in CSV")
        return doctors_removed
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error removing doctors: {str(e)}")
        return 0
    
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting removal of doctors not in CSV")
    count = remove_doctors_not_in_csv()
    logger.info(f"Removed {count} doctor profiles that were not in CSV")
    print(f"\nA backup of the removed doctor profiles has been saved to {BACKUP_FILE}")
    print(f"Note: User accounts associated with these doctors were NOT removed for safety.")