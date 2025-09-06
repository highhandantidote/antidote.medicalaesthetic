#!/usr/bin/env python3
"""
Remove duplicate doctor records from the database - Direct approach.

This script directly removes duplicate doctor records by keeping only the highest ID
for each doctor name, as the more recent records likely have more complete information.
"""

import os
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

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

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

def get_duplicates_info():
    """Get information about duplicate doctor records."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT name, COUNT(*) 
                FROM doctors 
                GROUP BY name 
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
            return cursor.fetchall()
    finally:
        conn.close()

def remove_duplicates():
    """Remove duplicate doctor records, keeping only the record with highest ID for each name."""
    # Get initial count
    initial_count = count_doctors()
    logger.info(f"Initial doctor count: {initial_count}")
    
    # Get duplicate info
    duplicates = get_duplicates_info()
    logger.info(f"Found {len(duplicates)} doctor names with duplicates")
    
    if not duplicates:
        logger.info("No duplicates found, nothing to do")
        return
    
    # For each duplicate name, keep only the record with the highest ID
    conn = get_db_connection()
    try:
        conn.autocommit = False
        removed_count = 0
        
        for name, count in duplicates:
            with conn.cursor() as cursor:
                # Get the highest ID for this doctor name
                cursor.execute("""
                    SELECT MAX(id) FROM doctors WHERE name = %s
                """, (name,))
                max_id = cursor.fetchone()[0]
                
                # Delete all other records for this doctor
                cursor.execute("""
                    DELETE FROM doctors 
                    WHERE name = %s AND id != %s
                """, (name, max_id))
                
                deleted = cursor.rowcount
                removed_count += deleted
                logger.info(f"For doctor '{name}': kept ID {max_id}, removed {deleted} duplicate(s)")
            
            # Commit after each doctor name to prevent long transactions
            conn.commit()
        
        # Get final count
        final_count = count_doctors()
        logger.info(f"Final doctor count: {final_count}")
        logger.info(f"Successfully removed {removed_count} duplicate doctor records")
        
        # Verify no duplicates remain
        remaining_duplicates = get_duplicates_info()
        if remaining_duplicates:
            logger.warning(f"Warning: {len(remaining_duplicates)} doctor names still have duplicates")
            return False
        else:
            logger.info("Success: No duplicate doctor names remain in the database")
            return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error removing duplicates: {str(e)}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting direct duplicate doctor removal process")
    success = remove_duplicates()
    
    if success:
        print("\nSuccessfully removed all duplicate doctor records!")
        print("The database now contains only unique doctor profiles.")
    else:
        print("\nWarning: Not all duplicate doctor records were removed.")
        print("Please check the logs for details.")