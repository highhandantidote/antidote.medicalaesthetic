#!/usr/bin/env python3
"""
Link imported doctors to common plastic surgery procedures.
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

# Common plastic surgery procedures to link
COMMON_PROCEDURES = [
    "Rhinoplasty",
    "Liposuction",
    "Breast Augmentation",
    "Breast Reduction",
    "Abdominoplasty",
    "Facelift",
    "Blepharoplasty",
    "Botox Injection",
    "Dermal Fillers",
    "Hair Transplant"
]

# Common plastic surgery categories
COMMON_CATEGORIES = [
    "Facial Rejuvenation",
    "Body Contouring",
    "Breast Surgery",
    "Skin Rejuvenation And Resurfacing",
    "Reconstructive Surgery"
]

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

def link_doctors_to_procedures():
    """Link all doctors to common procedures."""
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
            
            # For each doctor, link to procedures
            for doctor_id, doctor_name in doctors:
                procedure_count = 0
                
                # Find procedures
                for procedure_name in COMMON_PROCEDURES:
                    cursor.execute(
                        "SELECT id FROM procedures WHERE procedure_name = %s",
                        (procedure_name,)
                    )
                    procedure_result = cursor.fetchone()
                    
                    if not procedure_result:
                        logger.warning(f"Procedure not found: {procedure_name}")
                        continue
                    
                    procedure_id = procedure_result[0]
                    
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
    except Exception as e:
        logger.error(f"Error linking doctors to procedures: {e}")
    finally:
        conn.close()

def link_doctors_to_categories():
    """Link all doctors to common categories."""
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
            
            # For each doctor, link to categories
            for doctor_id, doctor_name in doctors:
                category_count = 0
                
                # Find categories using LIKE search
                for category_name in COMMON_CATEGORIES:
                    cursor.execute(
                        "SELECT id FROM categories WHERE name ILIKE %s OR name ILIKE %s",
                        (category_name, f"%{category_name}%")
                    )
                    category_results = cursor.fetchall()
                    
                    if not category_results:
                        logger.warning(f"No categories found matching: {category_name}")
                        continue
                    
                    # Link to each matching category
                    for category_row in category_results:
                        category_id = category_row[0]
                        
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
    logger.info("Starting doctor linking process...")
    link_doctors_to_procedures()
    link_doctors_to_categories()
    logger.info("Doctor linking process completed.")

if __name__ == "__main__":
    main()