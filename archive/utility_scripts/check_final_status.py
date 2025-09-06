#!/usr/bin/env python3
"""
Check the final status of our database import.

This script shows the current database counts and summarizes
our progress with the import process.
"""

import os
import csv
import logging
import psycopg2

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
PROCEDURES_CSV_PATH = "./attached_assets/new_procedure_details - Sheet1.csv"
DOCTORS_CSV_PATH = "./attached_assets/new_doctors_profiles2 - Sheet1.csv"

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
            
            # Count total rows in CSV files
            with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as f:
                procedures_total = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
                
            with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as f:
                doctors_total = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
            
            # Get sample of recent procedures
            cursor.execute("""
                SELECT procedure_name, short_description, created_at
                FROM procedures
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_procedures = cursor.fetchall()
            
            # Get sample of recent doctors
            cursor.execute("""
                SELECT name, specialty, city, created_at
                FROM doctors
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_doctors = cursor.fetchall()
            
            # Print summary
            logger.info("=" * 80)
            logger.info("DATABASE IMPORT STATUS")
            logger.info("=" * 80)
            logger.info(f"Body Parts: {body_part_count}")
            logger.info(f"Categories: {category_count}")
            logger.info(f"Procedures: {procedure_count} out of {procedures_total} in CSV ({procedure_count/procedures_total:.1%})")
            logger.info(f"Doctors: {doctor_count} out of {doctors_total} in CSV ({doctor_count/doctors_total:.1%})")
            logger.info("=" * 80)
            
            logger.info("RECENTLY ADDED PROCEDURES:")
            for proc in recent_procedures:
                logger.info(f"  {proc[0]} - {proc[1]}")
            
            logger.info("\nRECENTLY ADDED DOCTORS:")
            for doc in recent_doctors:
                logger.info(f"  {doc[0]} - {doc[1]} in {doc[2]}")
            
            logger.info("=" * 80)
            
            # Return counts for potential use by other scripts
            return {
                "body_parts": body_part_count,
                "categories": category_count,
                "procedures": procedure_count,
                "total_procedures": procedures_total,
                "doctors": doctor_count,
                "total_doctors": doctors_total
            }
            
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database_status()