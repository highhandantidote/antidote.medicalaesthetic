#!/usr/bin/env python3
"""
Create doctor-procedure associations.

This script creates associations between doctors and procedures
to ensure doctors are linked to relevant procedures in their specialty.
"""

import os
import logging
import psycopg2
import random
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def associate_doctors_with_procedures():
    """Create random associations between doctors and procedures."""
    try:
        # Connect to database
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        with conn.cursor() as cur:
            # Get all doctors
            cur.execute("SELECT id, name, specialty FROM doctors")
            doctors = cur.fetchall()
            
            if not doctors:
                logger.warning("No doctors found to create associations")
                return False
            
            logger.info(f"Found {len(doctors)} doctors")
            
            # First get all categories
            cur.execute("""
                SELECT c.id, c.name, b.name as body_part 
                FROM categories c
                JOIN body_parts b ON c.body_part_id = b.id
            """)
            categories = cur.fetchall()
            
            if not categories:
                logger.warning("No categories found")
                return False
            
            logger.info(f"Found {len(categories)} categories")
            
            # Get all procedures grouped by category
            cur.execute("""
                SELECT p.id, p.procedure_name, c.id as category_id
                FROM procedures p
                JOIN categories c ON p.category_id = c.id
            """)
            
            procedures = cur.fetchall()
            
            if not procedures:
                logger.warning("No procedures found")
                return False
            
            logger.info(f"Found {len(procedures)} procedures")
            
            # Group procedures by category
            procedures_by_category = {}
            for proc in procedures:
                category_id = proc[2]
                if category_id not in procedures_by_category:
                    procedures_by_category[category_id] = []
                
                procedures_by_category[category_id].append((proc[0], proc[1]))
            
            # Associate each doctor with categories and procedures
            associations_created = 0
            
            for doctor_id, doctor_name, specialty in doctors:
                try:
                    # Select 2-4 random categories for this doctor
                    selected_categories = random.sample(categories, min(random.randint(2, 4), len(categories)))
                    
                    # First create doctor-category associations
                    for category_id, category_name, body_part in selected_categories:
                        try:
                            # Check if association already exists
                            cur.execute("""
                                SELECT 1 FROM doctor_categories
                                WHERE doctor_id = %s AND category_id = %s
                            """, (doctor_id, category_id))
                            
                            if not cur.fetchone():
                                # Create doctor-category association
                                cur.execute("""
                                    INSERT INTO doctor_categories (doctor_id, category_id)
                                    VALUES (%s, %s)
                                """, (doctor_id, category_id))
                                
                                logger.info(f"Associated doctor {doctor_name} with category {category_name}")
                                
                                # Now associate doctor with 2-5 procedures from this category
                                if category_id in procedures_by_category:
                                    procs_in_category = procedures_by_category[category_id]
                                    selected_procs = random.sample(procs_in_category, 
                                                               min(random.randint(2, 5), len(procs_in_category)))
                                    
                                    for proc_id, proc_name in selected_procs:
                                        # Check if association already exists
                                        cur.execute("""
                                            SELECT 1 FROM doctor_procedures
                                            WHERE doctor_id = %s AND procedure_id = %s
                                        """, (doctor_id, proc_id))
                                        
                                        if not cur.fetchone():
                                            # Create doctor-procedure association
                                            cur.execute("""
                                                INSERT INTO doctor_procedures (doctor_id, procedure_id)
                                                VALUES (%s, %s)
                                            """, (doctor_id, proc_id))
                                            
                                            associations_created += 1
                                            logger.info(f"Associated doctor {doctor_name} with procedure {proc_name}")
                        
                        except Exception as e:
                            logger.error(f"Error associating doctor {doctor_name} with category {category_name}: {str(e)}")
                            conn.rollback()
                
                except Exception as e:
                    logger.error(f"Error processing doctor {doctor_name}: {str(e)}")
                    conn.rollback()
            
            conn.commit()
            logger.info(f"Created {associations_created} doctor-procedure associations")
            return True
        
    except Exception as e:
        logger.error(f"Error in associate_doctors_with_procedures: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting to create doctor-procedure associations...")
    if associate_doctors_with_procedures():
        logger.info("Successfully created doctor-procedure associations")
    else:
        logger.error("Failed to create doctor-procedure associations")