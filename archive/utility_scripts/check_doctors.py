#!/usr/bin/env python3
"""
Check the status of doctors in the database.

This script checks how many doctors have been imported
and displays information about them.
"""

import os
import json
import logging
import psycopg2
from pprint import pformat

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def check_doctors():
    """Check doctors in the database and display information."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        with conn.cursor() as cur:
            # Count total doctors
            cur.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cur.fetchone()[0]
            
            logger.info(f"Total doctors in database: {doctor_count}")
            
            # Get a sample of doctors with their profile images
            cur.execute("""
                SELECT id, name, specialty, profile_image, is_verified
                FROM doctors
                ORDER BY id
                LIMIT 10
            """)
            
            doctors = cur.fetchall()
            
            logger.info("Sample of doctors:")
            for doctor in doctors:
                logger.info(f"ID: {doctor[0]}, Name: {doctor[1]}, Specialty: {doctor[2]}, Image: {doctor[3]}, Verified: {doctor[4]}")
            
            # Check doctor-procedure associations
            cur.execute("""
                SELECT d.id, d.name, COUNT(dp.procedure_id) as proc_count
                FROM doctors d
                LEFT JOIN doctor_procedures dp ON d.id = dp.doctor_id
                GROUP BY d.id, d.name
                ORDER BY d.id
                LIMIT 10
            """)
            
            associations = cur.fetchall()
            
            logger.info("Doctor-Procedure associations:")
            for assoc in associations:
                logger.info(f"Doctor ID: {assoc[0]}, Name: {assoc[1]}, Procedure Count: {assoc[2]}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking doctors: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Checking doctor information...")
    check_doctors()