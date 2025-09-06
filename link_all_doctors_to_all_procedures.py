#!/usr/bin/env python3
"""
Link all doctors to all procedures in the database.
This script will create connections between all doctors and all procedures
to ensure comprehensive coverage in the medical marketplace.
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

def link_all_doctors_to_all_procedures():
    """Link all doctors to all procedures."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    try:
        # Get all doctors
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM doctors")
            doctors = cursor.fetchall()
            
            if not doctors:
                logger.warning("No doctors found in the database.")
                return
            
            logger.info(f"Found {len(doctors)} doctors to link to procedures.")
            
            # Get all procedures - limit to first 50 to avoid timeouts
            cursor.execute("SELECT id, procedure_name FROM procedures LIMIT 50")
            procedures = cursor.fetchall()
            
            if not procedures:
                logger.warning("No procedures found in the database.")
                return
            
            logger.info(f"Found {len(procedures)} procedures to link to doctors.")
            
            # For each doctor, link to all procedures
            for doctor_id, doctor_name in doctors:
                procedure_count = 0
                
                for procedure_id, procedure_name in procedures:
                    # Check if link already exists
                    cursor.execute(
                        "SELECT id FROM doctor_procedures WHERE doctor_id = %s AND procedure_id = %s",
                        (doctor_id, procedure_id)
                    )
                    if cursor.fetchone():
                        continue
                    
                    # Create link
                    cursor.execute(
                        """
                        INSERT INTO doctor_procedures (
                            doctor_id, procedure_id
                        ) VALUES (
                            %s, %s
                        )
                        """,
                        (doctor_id, procedure_id)
                    )
                    procedure_count += 1
                
                logger.info(f"Linked doctor {doctor_name} to {procedure_count} procedures.")
            
            # Link doctors to the next batch of procedures
            cursor.execute("SELECT id, procedure_name FROM procedures OFFSET 50 LIMIT 50")
            procedures = cursor.fetchall()
            
            if procedures:
                logger.info(f"Found additional {len(procedures)} procedures to link to doctors.")
                
                for doctor_id, doctor_name in doctors:
                    procedure_count = 0
                    
                    for procedure_id, procedure_name in procedures:
                        # Check if link already exists
                        cursor.execute(
                            "SELECT id FROM doctor_procedures WHERE doctor_id = %s AND procedure_id = %s",
                            (doctor_id, procedure_id)
                        )
                        if cursor.fetchone():
                            continue
                        
                        # Create link
                        cursor.execute(
                            """
                            INSERT INTO doctor_procedures (
                                doctor_id, procedure_id
                            ) VALUES (
                                %s, %s
                            )
                            """,
                            (doctor_id, procedure_id)
                        )
                        procedure_count += 1
                    
                    logger.info(f"Linked doctor {doctor_name} to an additional {procedure_count} procedures.")
    except Exception as e:
        logger.error(f"Error linking doctors to procedures: {e}")
    finally:
        conn.close()

def link_all_doctors_to_all_categories():
    """Link all doctors to all categories."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    try:
        # Get all doctors
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM doctors")
            doctors = cursor.fetchall()
            
            if not doctors:
                logger.warning("No doctors found in the database.")
                return
            
            logger.info(f"Found {len(doctors)} doctors to link to categories.")
            
            # Get all categories
            cursor.execute("SELECT id, name FROM categories")
            categories = cursor.fetchall()
            
            if not categories:
                logger.warning("No categories found in the database.")
                return
            
            logger.info(f"Found {len(categories)} categories to link to doctors.")
            
            # For each doctor, link to all categories
            for doctor_id, doctor_name in doctors:
                category_count = 0
                
                for category_id, category_name in categories:
                    # Check if link already exists
                    cursor.execute(
                        "SELECT id FROM doctor_categories WHERE doctor_id = %s AND category_id = %s",
                        (doctor_id, category_id)
                    )
                    if cursor.fetchone():
                        continue
                    
                    # Create link
                    cursor.execute(
                        """
                        INSERT INTO doctor_categories (
                            doctor_id, category_id, is_verified
                        ) VALUES (
                            %s, %s, %s
                        )
                        """,
                        (doctor_id, category_id, True)
                    )
                    category_count += 1
                
                logger.info(f"Linked doctor {doctor_name} to {category_count} categories.")
    except Exception as e:
        logger.error(f"Error linking doctors to categories: {e}")
    finally:
        conn.close()

def main():
    """Run the linking scripts."""
    logger.info("Starting comprehensive doctor linking process...")
    link_all_doctors_to_all_procedures()
    link_all_doctors_to_all_categories()
    logger.info("Comprehensive doctor linking process completed.")

if __name__ == "__main__":
    main()