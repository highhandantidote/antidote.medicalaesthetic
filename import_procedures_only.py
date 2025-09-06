#!/usr/bin/env python3
"""
Import procedures only from CSV file to the database.

This script focuses only on importing procedures and skips any that are already in the database.
It uses proper checkpointing to continue from where it left off.
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
PROCEDURE_START_ROW = 395  # Start from current progress (395 procedures already in DB)
BATCH_SIZE = 10  # Process in small batches to avoid timeouts

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

def get_checkpoint():
    """Get the current import checkpoint."""
    checkpoint_file = "procedure_import_checkpoint.txt"
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return PROCEDURE_START_ROW
    return PROCEDURE_START_ROW

def save_checkpoint(row_num):
    """Save the current import checkpoint."""
    checkpoint_file = "procedure_import_checkpoint.txt"
    with open(checkpoint_file, "w") as f:
        f.write(str(row_num))
    logger.info(f"Progress saved: Processed up to row {row_num}")

def clean_integer(value):
    """Clean cost values by removing commas, currency symbols and converting to integer."""
    if not value:
        return None
    # Remove currency symbols and commas
    cleaned = value.replace(",", "").replace("₹", "").replace("$", "").replace("Rs.", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        # If conversion fails, return a default value
        logger.warning(f"Could not convert cost value '{value}' to integer, using default")
        return 10000  # Default value for invalid costs

def get_body_part_id(conn, body_part_name):
    """Get body part ID by name, creating it if it doesn't exist."""
    with conn.cursor() as cursor:
        # Check if body part exists
        cursor.execute(
            "SELECT id FROM body_parts WHERE name = %s",
            (body_part_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new body part if it doesn't exist
        cursor.execute(
            """
            INSERT INTO body_parts (name, created_at, updated_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (body_part_name, datetime.now(), datetime.now())
        )
        body_part_id = cursor.fetchone()[0]
        conn.commit()
        logger.info(f"Created new body part: {body_part_name} (ID: {body_part_id})")
        return body_part_id

def get_category_id(conn, category_name, body_part_id):
    """Get category ID by name and body part, creating it if it doesn't exist."""
    with conn.cursor() as cursor:
        # Check if category exists
        cursor.execute(
            "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
            (category_name, body_part_id)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new category if it doesn't exist
        cursor.execute(
            """
            INSERT INTO categories (name, body_part_id, created_at, description)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (category_name, body_part_id, datetime.now(), f"Category for {category_name} procedures")
        )
        category_id = cursor.fetchone()[0]
        conn.commit()
        logger.info(f"Created new category: {category_name} for body part ID {body_part_id} (ID: {category_id})")
        return category_id

def procedure_exists(conn, procedure_name, category_id):
    """Check if procedure already exists with the same name and category or just the name."""
    with conn.cursor() as cursor:
        # First check by name and category
        cursor.execute(
            "SELECT id FROM procedures WHERE procedure_name = %s AND category_id = %s",
            (procedure_name, category_id)
        )
        if cursor.fetchone() is not None:
            return True
            
        # If not found, check just by name to avoid duplicate key errors
        cursor.execute(
            "SELECT id FROM procedures WHERE procedure_name = %s",
            (procedure_name,)
        )
        return cursor.fetchone() is not None

def import_procedures():
    """Import procedures from CSV in batches with error handling."""
    start_time = time.time()
    conn = get_db_connection()
    
    try:
        start_row = get_checkpoint()
        logger.info(f"Starting procedure import from row {start_row}")
        
        with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            # Skip to the starting row
            for _ in range(start_row):
                try:
                    next(csv_reader)
                except StopIteration:
                    logger.warning("Reached end of CSV file while skipping rows")
                    return 0
            
            procedures_added = 0
            current_row = start_row
            batch_count = 0
            
            for row in csv_reader:
                current_row += 1
                batch_count += 1
                
                try:
                    body_part_name = row.get('body_part_name', '').strip()
                    category_name = row.get('category_name', '').strip()
                    procedure_name = row.get('procedure_name', '').strip()
                    
                    if not body_part_name or not category_name or not procedure_name:
                        logger.warning(f"Skipping row {current_row} - missing required fields")
                        continue
                    
                    # Get or create body part and category
                    body_part_id = get_body_part_id(conn, body_part_name)
                    category_id = get_category_id(conn, category_name, body_part_id)
                    
                    # Skip if procedure already exists
                    if procedure_exists(conn, procedure_name, category_id):
                        logger.info(f"Procedure already exists: {procedure_name} (category: {category_name})")
                        continue
                    
                    # Clean cost values
                    min_cost = clean_integer(row.get('min_cost'))
                    max_cost = clean_integer(row.get('max_cost'))
                    
                    # Insert procedure
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO procedures (
                                procedure_name, alternative_names, short_description, overview, 
                                procedure_details, ideal_candidates, recovery_time, 
                                procedure_duration, hospital_stay_required, 
                                min_cost, max_cost, risks, procedure_types, 
                                recovery_process, results_duration, benefits, 
                                benefits_detailed, alternative_procedures, 
                                category_id, created_at, updated_at, tags
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            """,
                            (
                                procedure_name,
                                row.get('alternative_names', ''),
                                row.get('short_description', ''),
                                row.get('overview', ''),
                                row.get('procedure_details', ''),
                                row.get('ideal_candidates', ''),
                                row.get('recovery_time', ''),
                                row.get('procedure_duration', ''),
                                row.get('hospital_stay_required', ''),
                                min_cost,
                                max_cost,
                                row.get('risks', ''),
                                row.get('procedure_types', ''),
                                row.get('recovery_process', ''),
                                row.get('results_duration', ''),
                                row.get('benefits', ''),
                                row.get('benefits_detailed', ''),
                                row.get('alternative_procedures', ''),
                                category_id,
                                datetime.now(),
                                datetime.now(),
                                None  # Temporarily set tags to NULL to avoid format issues
                            )
                        )
                    
                    procedures_added += 1
                    logger.info(f"Added procedure: {procedure_name} (ID: {category_id})")
                    
                except Exception as e:
                    logger.error(f"Error processing row {current_row}: {str(e)}")
                    conn.rollback()
                
                # Commit every batch and save checkpoint
                if batch_count >= BATCH_SIZE:
                    conn.commit()
                    save_checkpoint(current_row)
                    batch_count = 0
                    logger.info(f"Batch completed. Total procedures added so far: {procedures_added}")
                    
                    # Sleep briefly to avoid timeout
                    time.sleep(0.1)
            
            # Commit any remaining items
            if batch_count > 0:
                conn.commit()
                save_checkpoint(current_row)
            
            elapsed = time.time() - start_time
            logger.info(f"Procedure import completed in {elapsed:.2f} seconds")
            logger.info(f"Added {procedures_added} procedures")
            
            return procedures_added
    
    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        conn.rollback()
        return 0
    
    finally:
        conn.close()

if __name__ == "__main__":
    import_procedures()