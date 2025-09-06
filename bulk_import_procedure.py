#!/usr/bin/env python3
"""
Bulk import procedure script for the medical marketplace platform.

This script automates the direct SQL import of procedures into the database
with proper error handling and validation.
"""
import os
import sys
import csv
import json
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"bulk_import_procedures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BATCH_SIZE = 10
CSV_FILE_PATH = "new_procedures.csv"
REQUIRED_FIELDS = [
    "procedure_name", "category_type", "body_area", "short_description",
    "overview", "procedure_details", "ideal_candidates", "recovery_time", 
    "min_cost", "max_cost", "risks", "procedure_types"
]

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        sys.exit(1)

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if not value:
        return 0
    try:
        return int(str(value).replace(",", "").replace("₹", "").strip())
    except ValueError:
        return 0

def validate_procedure(procedure):
    """Validate that a procedure has all required fields."""
    for field in REQUIRED_FIELDS:
        if field not in procedure or not procedure[field]:
            return False, f"Missing required field: {field}"
    return True, ""

def get_or_create_body_part(conn, body_part_name):
    """Get existing body part ID or create if it doesn't exist."""
    cursor = conn.cursor()
    try:
        # Check if body part exists
        cursor.execute(
            "SELECT id FROM body_parts WHERE name = %s",
            (body_part_name,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new body part
        cursor.execute(
            """
            INSERT INTO body_parts (name, created_at, updated_at)
            VALUES (%s, NOW(), NOW())
            RETURNING id
            """,
            (body_part_name,)
        )
        body_part_id = cursor.fetchone()[0]
        conn.commit()
        return body_part_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in get_or_create_body_part: {e}")
        raise
    finally:
        cursor.close()

def get_or_create_category(conn, category_name, body_part_id):
    """Get existing category ID or create if it doesn't exist."""
    cursor = conn.cursor()
    try:
        # Check if category exists
        cursor.execute(
            "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
            (category_name, body_part_id)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new category
        cursor.execute(
            """
            INSERT INTO categories (
                name, body_part_id, created_at, updated_at
            ) VALUES (%s, %s, NOW(), NOW())
            RETURNING id
            """,
            (category_name, body_part_id)
        )
        category_id = cursor.fetchone()[0]
        conn.commit()
        return category_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in get_or_create_category: {e}")
        raise
    finally:
        cursor.close()

def prepare_procedure_data(procedure, category_id):
    """Prepare procedure data for insertion, handling constraints."""
    # Truncate tags to meet the 20-character limit
    tags = []
    if procedure.get('tags'):
        if isinstance(procedure['tags'], str):
            # Parse tags if they're in string format
            try:
                tag_list = json.loads(procedure['tags'].replace("'", '"'))
                tags = [tag[:20] for tag in tag_list]
            except json.JSONDecodeError:
                tags = [tag.strip()[:20] for tag in procedure['tags'].split(',')]
        elif isinstance(procedure['tags'], list):
            tags = [tag[:20] for tag in procedure['tags']]
    
    # Default values for missing fields
    return {
        "procedure_name": procedure['procedure_name'],
        "short_description": procedure.get('short_description', '')[:255],
        "overview": procedure['overview'],
        "procedure_details": procedure['procedure_details'],
        "ideal_candidates": procedure['ideal_candidates'],
        "recovery_time": procedure['recovery_time'][:50] if procedure.get('recovery_time') else "Varies",
        "min_cost": clean_integer(procedure.get('min_cost', 0)),
        "max_cost": clean_integer(procedure.get('max_cost', 0)),
        "risks": procedure['risks'],
        "procedure_types": procedure['procedure_types'],
        "category_id": category_id,
        "body_part": procedure['body_area'],
        "tags": tags,
        "body_area": procedure['body_area'],
        "category_type": procedure['category_type'],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "procedure_duration": procedure.get('procedure_duration', '1-2 hours'),
        "hospital_stay_required": procedure.get('hospital_stay_required', 'No'),
        "alternative_names": procedure.get('alternative_names', '')
    }

def add_procedures_batch(conn, procedures):
    """Add a batch of procedures to the database."""
    cursor = conn.cursor()
    inserted_count = 0
    error_count = 0
    
    for procedure in procedures:
        try:
            # Validate procedure data
            valid, error_msg = validate_procedure(procedure)
            if not valid:
                logger.warning(f"Skipping invalid procedure '{procedure.get('procedure_name', 'UNKNOWN')}': {error_msg}")
                error_count += 1
                continue
            
            # Check if procedure already exists
            cursor.execute(
                "SELECT id FROM procedures WHERE procedure_name = %s",
                (procedure['procedure_name'],)
            )
            if cursor.fetchone():
                logger.info(f"Procedure '{procedure['procedure_name']}' already exists, skipping")
                continue
                
            # Get or create body part
            body_part_id = get_or_create_body_part(conn, procedure['body_area'])
            
            # Get or create category
            category_id = get_or_create_category(conn, procedure['category_type'], body_part_id)
            
            # Prepare procedure data
            proc_data = prepare_procedure_data(procedure, category_id)
            
            # Insert procedure
            cursor.execute(
                """
                INSERT INTO procedures (
                    procedure_name, short_description, overview, procedure_details, 
                    ideal_candidates, recovery_time, min_cost, max_cost, risks, 
                    procedure_types, category_id, body_part, tags, body_area, 
                    category_type, created_at, updated_at, procedure_duration,
                    hospital_stay_required, alternative_names
                ) VALUES (
                    %(procedure_name)s, %(short_description)s, %(overview)s, %(procedure_details)s,
                    %(ideal_candidates)s, %(recovery_time)s, %(min_cost)s, %(max_cost)s,
                    %(risks)s, %(procedure_types)s, %(category_id)s, %(body_part)s,
                    %(tags)s, %(body_area)s, %(category_type)s, %(created_at)s,
                    %(updated_at)s, %(procedure_duration)s, %(hospital_stay_required)s,
                    %(alternative_names)s
                )
                """,
                proc_data
            )
            conn.commit()
            inserted_count += 1
            logger.info(f"Added procedure: {procedure['procedure_name']}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding procedure '{procedure.get('procedure_name', 'UNKNOWN')}': {e}")
            error_count += 1
    
    cursor.close()
    return inserted_count, error_count

def read_procedures_from_csv(csv_file_path):
    """Read procedures from CSV file."""
    procedures = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                procedures.append(row)
        return procedures
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        sys.exit(1)

def main():
    """Main function to import procedures."""
    logger.info(f"Starting bulk import from {CSV_FILE_PATH}")
    
    # Read procedures from CSV
    procedures = read_procedures_from_csv(CSV_FILE_PATH)
    logger.info(f"Found {len(procedures)} procedures in CSV")
    
    # Get database connection
    conn = get_db_connection()
    
    # Process procedures in batches
    total_inserted = 0
    total_errors = 0
    total_batches = (len(procedures) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(procedures), BATCH_SIZE):
        batch = procedures[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} procedures)")
        
        inserted, errors = add_procedures_batch(conn, batch)
        total_inserted += inserted
        total_errors += errors
    
    conn.close()
    logger.info(f"Import completed: {total_inserted} procedures added, {total_errors} errors")

if __name__ == "__main__":
    main()