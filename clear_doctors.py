#!/usr/bin/env python3
"""
Clear existing doctor data from the database.

This script removes all doctor records and associated data from the database
to prepare for a fresh import.
"""

import os
import logging
import psycopg2

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

def clear_doctor_data():
    """Clear all doctor-related data from the database."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        with conn.cursor() as cur:
            # First, check if there are any doctors
            cur.execute("SELECT COUNT(*) FROM doctors")
            count = cur.fetchone()[0]
            
            if count == 0:
                logger.info("No doctor records found to clear")
                return True
            
            # Clear doctor-procedure associations
            logger.info("Clearing doctor-procedure associations...")
            cur.execute("DELETE FROM doctor_procedures")
            
            # Clear doctor-category associations
            logger.info("Clearing doctor-category associations...")
            cur.execute("DELETE FROM doctor_categories")
            
            # Clear doctor availability if the table exists
            try:
                logger.info("Checking if doctor_availabilities table exists...")
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'doctor_availabilities'
                    )
                """)
                if cur.fetchone()[0]:
                    logger.info("Clearing doctor availabilities...")
                    cur.execute("DELETE FROM doctor_availabilities")
                else:
                    logger.info("doctor_availabilities table does not exist, skipping")
            except Exception as e:
                logger.warning(f"Error checking/clearing doctor availabilities: {str(e)}")
                # Continue with the process
            
            # Clear doctor photos if the table exists
            try:
                logger.info("Checking if doctor_photos table exists...")
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'doctor_photos'
                    )
                """)
                if cur.fetchone()[0]:
                    logger.info("Clearing doctor photos...")
                    cur.execute("DELETE FROM doctor_photos")
                else:
                    logger.info("doctor_photos table does not exist, skipping")
            except Exception as e:
                logger.warning(f"Error checking/clearing doctor photos: {str(e)}")
                # Continue with the process
            
            # Get user IDs associated with doctors for later deletion
            cur.execute("SELECT user_id FROM doctors")
            doctor_user_ids = [row[0] for row in cur.fetchall() if row[0] is not None]
            
            # Clear doctor records
            logger.info("Clearing doctor records...")
            cur.execute("DELETE FROM doctors")
            
            # Remove user accounts associated with doctors (if any)
            if doctor_user_ids:
                logger.info(f"Removing {len(doctor_user_ids)} user accounts associated with doctors...")
                placeholders = ', '.join(['%s'] * len(doctor_user_ids))
                cur.execute(f"DELETE FROM users WHERE id IN ({placeholders})", doctor_user_ids)
            
            # Commit all changes
            conn.commit()
            
            logger.info("Successfully cleared all doctor data")
            return True
    except Exception as e:
        logger.error(f"Error clearing doctor data: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting cleanup of doctor data...")
    success = clear_doctor_data()
    
    if success:
        logger.info("Doctor data cleanup completed successfully")
    else:
        logger.error("Doctor data cleanup failed")