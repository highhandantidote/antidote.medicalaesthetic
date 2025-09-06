#!/usr/bin/env python3
"""
Quick link doctors to procedures and categories using direct SQL.
This script uses a more efficient approach to link doctors to procedures and categories.
"""
import os
import logging
import psycopg2

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def quick_link_doctors_to_procedures():
    """Link all doctors to procedures using a single SQL statement."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    try:
        with conn.cursor() as cursor:
            # Get doctor and procedure counts
            cursor.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM procedures")
            procedure_count = cursor.fetchone()[0]
            
            logger.info(f"Found {doctor_count} doctors and {procedure_count} procedures.")
            
            # First clear any existing links to ensure clean data
            logger.info("Clearing existing procedure links...")
            cursor.execute("DELETE FROM doctor_procedures")
            
            # Use a SQL statement that inserts all combinations
            logger.info("Creating new doctor-procedure links...")
            cursor.execute("""
                INSERT INTO doctor_procedures (doctor_id, procedure_id)
                SELECT d.id, p.id
                FROM doctors d
                CROSS JOIN procedures p
                ORDER BY d.id, p.id
            """)
            
            # Get count of new links
            cursor.execute("SELECT COUNT(*) FROM doctor_procedures")
            link_count = cursor.fetchone()[0]
            
            logger.info(f"Successfully linked doctors to procedures. Created {link_count} links.")
    except Exception as e:
        logger.error(f"Error linking doctors to procedures: {e}")
    finally:
        conn.close()

def quick_link_doctors_to_categories():
    """Link all doctors to categories using a single SQL statement."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    try:
        with conn.cursor() as cursor:
            # Get doctor and category counts
            cursor.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categories")
            category_count = cursor.fetchone()[0]
            
            logger.info(f"Found {doctor_count} doctors and {category_count} categories.")
            
            # First clear any existing links to ensure clean data
            logger.info("Clearing existing category links...")
            cursor.execute("DELETE FROM doctor_categories")
            
            # Use a SQL statement that inserts all combinations
            logger.info("Creating new doctor-category links...")
            cursor.execute("""
                INSERT INTO doctor_categories (doctor_id, category_id, is_verified)
                SELECT d.id, c.id, TRUE
                FROM doctors d
                CROSS JOIN categories c
                ORDER BY d.id, c.id
            """)
            
            # Get count of new links
            cursor.execute("SELECT COUNT(*) FROM doctor_categories")
            link_count = cursor.fetchone()[0]
            
            logger.info(f"Successfully linked doctors to categories. Created {link_count} links.")
    except Exception as e:
        logger.error(f"Error linking doctors to categories: {e}")
    finally:
        conn.close()

def main():
    """Run the quick linking scripts."""
    logger.info("Starting quick doctor linking process...")
    quick_link_doctors_to_procedures()
    quick_link_doctors_to_categories()
    logger.info("Quick doctor linking process completed.")

if __name__ == "__main__":
    main()