#!/usr/bin/env python3
"""
Import exactly five new procedures to the database.

This script is a simplified version that focuses on importing just 5 procedures
with proper handling of all required fields.
"""

import os
import csv
import time
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
PROCEDURES_CSV_PATH = "./attached_assets/new_procedure_details - Sheet1.csv"
START_ROW = 234  # Start at the current procedure count

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if value is None or value == '':
        return 0
    try:
        return int(str(value).replace(',', '').replace(' ', ''))
    except ValueError:
        return 0

def import_five_procedures():
    """Import exactly five new procedures to the database."""
    if not os.path.exists(PROCEDURES_CSV_PATH):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV_PATH}")
        return False
    
    # Get existing procedure names to avoid duplicates
    existing_names = set()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT LOWER(procedure_name) FROM procedures")
            for row in cursor.fetchall():
                if row[0]:
                    existing_names.add(row[0].lower())
    finally:
        conn.close()
    
    logger.info(f"Found {len(existing_names)} existing procedures")
    
    # Initialize counters
    procedures_added = 0
    procedures_skipped = 0
    
    # Read CSV file to find procedures to add
    procedures_to_import = []
    with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader):
            if i < START_ROW:  # Skip procedures we've likely already processed
                continue
                
            procedure_name = row.get('procedure_name', '').strip()
            
            # Skip if already exists
            if procedure_name.lower() in existing_names:
                continue
                
            procedures_to_import.append(row)
            
            # Once we have 5 procedures, stop collecting
            if len(procedures_to_import) >= 5:
                break
    
    logger.info(f"Found {len(procedures_to_import)} procedures to import")
    
    # Now import each procedure one by one
    conn = get_db_connection()
    try:
        conn.autocommit = False
        
        for procedure in procedures_to_import:
            # Extract procedure data with proper defaults
            procedure_name = procedure.get('procedure_name', '').strip()
            body_part_name = procedure.get('body_part_name', '').strip()
            category_name = procedure.get('category_name', '').strip()
            
            if not procedure_name or not body_part_name or not category_name:
                logger.warning(f"Skipping procedure with missing essential data: {procedure_name}")
                procedures_skipped += 1
                continue
            
            # Prepare other data
            min_cost = clean_integer(procedure.get('min_cost', 0))
            max_cost = clean_integer(procedure.get('max_cost', 0))
            description = procedure.get('description', '').strip() or f"Professional {procedure_name} procedure with excellent results."
            benefits = procedure.get('benefits', '').strip() or f"Improved appearance and confidence."
            risks = procedure.get('risks', '').strip() or "Standard surgical risks including infection, scarring, and asymmetry."
            
            # Prepare default values for required fields
            short_desc = description[:250] if description else f"Professional {procedure_name} procedure."
            overview = description or f"This {procedure_name} procedure provides excellent aesthetic results."
            procedure_details = f"The {procedure_name} procedure involves advanced techniques to achieve optimal results."
            ideal_candidates = f"Ideal candidates for {procedure_name} are generally healthy individuals seeking aesthetic improvement."
            recovery_time = "Varies depending on individual factors"
            procedure_types = "Standard"
            
            try:
                with conn.cursor() as cursor:
                    # Get or create body part
                    cursor.execute(
                        "SELECT id FROM body_parts WHERE LOWER(name) = LOWER(%s)",
                        (body_part_name,)
                    )
                    body_part_result = cursor.fetchone()
                    
                    if body_part_result and body_part_result[0] is not None:
                        body_part_id = body_part_result[0]
                    else:
                        cursor.execute(
                            "INSERT INTO body_parts (name, created_at) VALUES (%s, %s) RETURNING id",
                            (body_part_name, datetime.now())
                        )
                        result = cursor.fetchone()
                        body_part_id = result[0] if result else None
                        if not body_part_id:
                            raise ValueError(f"Failed to create body part: {body_part_name}")
                        logger.info(f"Created new body part: {body_part_name}")
                    
                    # Get or create category
                    cursor.execute(
                        "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)",
                        (category_name,)
                    )
                    category_result = cursor.fetchone()
                    
                    if category_result and category_result[0] is not None:
                        category_id = category_result[0]
                        logger.info(f"Using existing category: {category_name}")
                    else:
                        cursor.execute(
                            "INSERT INTO categories (name, body_part_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                            (category_name, body_part_id, datetime.now())
                        )
                        result = cursor.fetchone()
                        category_id = result[0] if result else None
                        if not category_id:
                            raise ValueError(f"Failed to create category: {category_name}")
                        logger.info(f"Created new category: {category_name}")
                    
                    # Insert procedure with all required fields
                    cursor.execute(
                        """
                        INSERT INTO procedures 
                        (procedure_name, category_id, min_cost, max_cost, short_description, 
                         overview, procedure_details, ideal_candidates, recovery_time,
                         procedure_types, risks, benefits, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            procedure_name, category_id, 
                            min_cost, max_cost,
                            short_desc,
                            overview,
                            procedure_details,
                            ideal_candidates,
                            recovery_time,
                            procedure_types,
                            risks,
                            benefits,
                            datetime.now()
                        )
                    )
                    result = cursor.fetchone()
                    if not result:
                        raise ValueError(f"Failed to insert procedure: {procedure_name}")
                    
                    # Success - commit this procedure
                    conn.commit()
                    logger.info(f"Added procedure: {procedure_name}")
                    procedures_added += 1
                    
                    # Add to existing names to avoid duplicates
                    existing_names.add(procedure_name.lower())
                    
            except Exception as e:
                conn.rollback()
                logger.error(f"Error adding procedure {procedure_name}: {str(e)}")
                procedures_skipped += 1
        
        logger.info(f"Import complete. Added {procedures_added} procedures, skipped {procedures_skipped}")
        return procedures_added
    
    except Exception as e:
        logger.error(f"Error in import process: {str(e)}")
        return 0
    
    finally:
        conn.close()

def main():
    """Run the procedure import."""
    start_time = time.time()
    
    added_count = import_five_procedures()
    
    if added_count > 0:
        logger.info(f"Successfully added {added_count} procedures in {time.time() - start_time:.2f} seconds")
    else:
        logger.error("Failed to add any procedures")

if __name__ == "__main__":
    main()