#!/usr/bin/env python3
"""
Check database status and display a summary of imported items.

This script checks the current status of imported data in the database
and displays counts and sample entries from key tables.
"""

import os
import logging
import psycopg2
from pprint import pformat

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

def check_database_status():
    """Check the current status of the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check body parts
            cursor.execute("SELECT COUNT(*) FROM body_parts")
            result = cursor.fetchone()
            body_part_count = result[0] if result else 0
            
            # Check categories
            cursor.execute("SELECT COUNT(*) FROM categories")
            result = cursor.fetchone()
            category_count = result[0] if result else 0
            
            # Check procedures
            cursor.execute("SELECT COUNT(*) FROM procedures")
            result = cursor.fetchone()
            procedure_count = result[0] if result else 0
            
            # Check doctors
            cursor.execute("SELECT COUNT(*) FROM doctors")
            result = cursor.fetchone()
            doctor_count = result[0] if result else 0
            
            # Get sample body parts
            cursor.execute("SELECT id, name FROM body_parts ORDER BY id LIMIT 5")
            body_part_samples = cursor.fetchall()
            
            # Get sample categories
            cursor.execute("""
                SELECT c.id, c.name, bp.name 
                FROM categories c
                JOIN body_parts bp ON c.body_part_id = bp.id
                ORDER BY c.id LIMIT 5
            """)
            category_samples = cursor.fetchall()
            
            # Get sample procedures
            cursor.execute("""
                SELECT p.id, p.procedure_name, c.name, bp.name
                FROM procedures p
                JOIN categories c ON p.category_id = c.id
                JOIN body_parts bp ON c.body_part_id = bp.id
                ORDER BY p.id LIMIT 5
            """)
            procedure_samples = cursor.fetchall()
            
            # Get sample doctors
            cursor.execute("""
                SELECT d.id, d.name, d.specialty, d.city, d.state
                FROM doctors d
                ORDER BY d.id LIMIT 5
            """)
            doctor_samples = cursor.fetchall()
            
            # Print summary
            logger.info("=" * 50)
            logger.info("DATABASE IMPORT STATUS")
            logger.info("=" * 50)
            logger.info(f"Body Parts: {body_part_count}")
            logger.info(f"Categories: {category_count}")
            logger.info(f"Procedures: {procedure_count}")
            logger.info(f"Doctors: {doctor_count}")
            logger.info("=" * 50)
            
            # Print samples
            logger.info("SAMPLE BODY PARTS:")
            for bp in body_part_samples:
                logger.info(f"  ID: {bp[0]}, Name: {bp[1]}")
            
            logger.info("\nSAMPLE CATEGORIES:")
            for cat in category_samples:
                logger.info(f"  ID: {cat[0]}, Name: {cat[1]}, Body Part: {cat[2]}")
            
            logger.info("\nSAMPLE PROCEDURES:")
            for proc in procedure_samples:
                logger.info(f"  ID: {proc[0]}, Name: {proc[1]}, Category: {proc[2]}, Body Part: {proc[3]}")
            
            logger.info("\nSAMPLE DOCTORS:")
            for doc in doctor_samples:
                logger.info(f"  ID: {doc[0]}, Name: {doc[1]}, Specialty: {doc[2]}, Location: {doc[3]}, {doc[4]}")
            
            logger.info("=" * 50)
            
            # Return counts for potential use by other scripts
            return {
                "body_parts": body_part_count,
                "categories": category_count,
                "procedures": procedure_count,
                "doctors": doctor_count
            }
            
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database_status()