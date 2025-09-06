#!/usr/bin/env python3
"""
Import remaining procedures from CSV file to the database.

This script imports the missing procedures from the CSV file to the database
while preserving all existing data. It works in small batches to avoid timeouts.
"""
import os
import csv
import time
import logging
import psycopg2
from datetime import datetime
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"import_procedures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
CSV_PATH = "./attached_assets/new_procedure_details - Sheet1.csv"
BATCH_SIZE = 10  # Small batch size to avoid timeouts

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if not value:
        return 10000  # Default cost if no value provided
    # Remove commas and convert to integer
    try:
        return int(value.replace(',', ''))
    except (ValueError, AttributeError):
        return 10000  # Default cost if conversion fails

def get_existing_procedure_names():
    """Get all existing procedure names to avoid duplicates."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT procedure_name FROM procedures")
            return {row[0].lower() for row in cursor.fetchall()}
    finally:
        conn.close()

def ensure_body_part_exists(conn, body_part_name):
    """Ensure body part exists and return its ID."""
    with conn.cursor() as cursor:
        # Check if the body part already exists
        cursor.execute("SELECT id FROM body_parts WHERE LOWER(name) = LOWER(%s)", (body_part_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create the body part if it doesn't exist
        cursor.execute(
            "INSERT INTO body_parts (name, created_at) VALUES (%s, %s) RETURNING id",
            (body_part_name, datetime.utcnow())
        )
        return cursor.fetchone()[0]

def ensure_category_exists(conn, category_name, body_part_id):
    """Ensure category exists and return its ID."""
    with conn.cursor() as cursor:
        # First check if the category already exists with the exact name and body part
        cursor.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s) AND body_part_id = %s",
            (category_name, body_part_id)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # If not found, check if the category exists with the same name but different body part
        cursor.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)",
            (category_name,)
        )
        result = cursor.fetchone()
        if result:
            # If it exists, just use that category ID (avoid duplicate category names)
            return result[0]
        
        # Create the category if it doesn't exist at all
        try:
            cursor.execute(
                "INSERT INTO categories (name, body_part_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                (category_name, body_part_id, datetime.utcnow())
            )
            return cursor.fetchone()[0]
        except psycopg2.errors.UniqueViolation:
            # Handle race condition - if another process created it while we were checking
            conn.rollback()
            cursor.execute(
                "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s)",
                (category_name,)
            )
            return cursor.fetchone()[0]

def parse_tags(tags_str):
    """Parse tags string into an array format with length limits."""
    if not tags_str:
        return []
    # Split by comma, clean whitespace, and limit each tag to 20 characters
    return [tag.strip()[:20] for tag in tags_str.split(',')]

def import_procedures():
    """Import procedures from CSV using small batches."""
    logger.info("Starting procedure import...")
    
    # Get existing procedure names to avoid duplicates
    existing_procedure_names = get_existing_procedure_names()
    logger.info(f"Found {len(existing_procedure_names)} existing procedures")
    
    # Initialize counters
    total_procedures = 0
    imported_procedures = 0
    duplicate_procedures = 0
    error_procedures = 0
    
    # Read CSV file
    with open(CSV_PATH, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        batch = []
        
        for row in reader:
            total_procedures += 1
            
            # Skip duplicates
            if row['procedure_name'].lower() in existing_procedure_names:
                duplicate_procedures += 1
                continue
            
            # Add to batch
            batch.append(row)
            
            # Process batch when it reaches the batch size
            if len(batch) >= BATCH_SIZE:
                imported_count, error_count = process_batch(batch)
                imported_procedures += imported_count
                error_procedures += error_count
                
                # Clear batch for next round
                batch = []
                
                # Log progress
                logger.info(f"Progress: Imported {imported_procedures}, Duplicates {duplicate_procedures}, Errors {error_procedures}")
                
                # Add a small delay to avoid resource exhaustion
                time.sleep(0.5)
        
        # Process any remaining procedures in the batch
        if batch:
            imported_count, error_count = process_batch(batch)
            imported_procedures += imported_count
            error_procedures += error_count
    
    # Log final results
    logger.info("===== Import Summary =====")
    logger.info(f"Total procedures in CSV: {total_procedures}")
    logger.info(f"Successfully imported: {imported_procedures}")
    logger.info(f"Duplicates skipped: {duplicate_procedures}")
    logger.info(f"Errors encountered: {error_procedures}")
    
    # Verify final counts
    verify_final_counts()

def process_batch(batch):
    """Process a batch of procedures."""
    conn = get_db_connection()
    imported_count = 0
    error_count = 0
    
    try:
        for procedure in batch:
            try:
                # Begin transaction
                with conn:
                    with conn.cursor() as cursor:
                        # Ensure body part exists
                        body_part_id = ensure_body_part_exists(conn, procedure['body_part_name'])
                        
                        # Ensure category exists
                        category_id = ensure_category_exists(conn, procedure['category_name'], body_part_id)
                        
                        # Parse tags
                        tags = parse_tags(procedure['tags'])
                        
                        # Ensure required fields have values
                        short_description = procedure.get('short_description') or f"A procedure for {procedure['body_part_name']} treatment"
                        overview = procedure.get('overview') or f"Treatment for {procedure['body_part_name']} using {procedure['procedure_name']}"
                        procedure_details = procedure.get('procedure_details') or f"Details about {procedure['procedure_name']} procedure"
                        ideal_candidates = procedure.get('ideal_candidates') or "Individuals looking for treatment"
                        recovery_time = procedure.get('recovery_time') or "Varies by individual"
                        risks = procedure.get('risks') or "Standard medical procedure risks"
                        procedure_types = procedure.get('procedure_types') or f"Standard {procedure['procedure_name']}"
                        
                        # Insert the procedure
                        cursor.execute("""
                            INSERT INTO procedures (
                                procedure_name, alternative_names, short_description, overview,
                                procedure_details, ideal_candidates, recovery_time, procedure_duration,
                                hospital_stay_required, results_duration, min_cost, max_cost, benefits,
                                benefits_detailed, risks, procedure_types, recovery_process,
                                alternative_procedures, category_id, body_part, tags, body_area,
                                category_type, created_at, updated_at, popularity_score, avg_rating, review_count
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            procedure['procedure_name'],
                            procedure.get('alternative_names', ''),
                            short_description,
                            overview,
                            procedure_details,
                            ideal_candidates,
                            recovery_time,
                            procedure.get('procedure_duration', ''),
                            procedure.get('hospital_stay_required', 'No'),
                            procedure.get('results_duration', ''),
                            clean_integer(procedure.get('min_cost', '10000')),
                            clean_integer(procedure.get('max_cost', '20000')),
                            procedure.get('benefits', ''),
                            procedure.get('benefits_detailed', ''),
                            risks,
                            procedure_types,
                            procedure.get('recovery_process', ''),
                            procedure.get('alternative_procedures', ''),
                            category_id,
                            procedure['body_part_name'],  # Map to body_part column
                            tags,
                            procedure['body_part_name'],  # Map to body_area column
                            procedure['category_name'],   # Map to category_type column
                            datetime.utcnow(),
                            datetime.utcnow(),
                            0,  # default popularity_score
                            4.5,  # default avg_rating
                            0  # default review_count
                        ))
                
                # Count successful import
                imported_count += 1
                
            except Exception as e:
                # Log the error and continue with the next procedure
                logger.error(f"Error importing procedure {procedure['procedure_name']}: {e}")
                error_count += 1
    
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
    finally:
        conn.close()
    
    return imported_count, error_count

def verify_final_counts():
    """Verify the final counts of procedures."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            result = cursor.fetchone()
            # Handle the case where the query doesn't return a valid result
            if result is not None and len(result) > 0:
                final_count = result[0]
            else:
                final_count = 0
            logger.info(f"Final procedure count in database: {final_count}")
    finally:
        conn.close()

def main():
    """Run the procedure import."""
    start_time = time.time()
    try:
        import_procedures()
        logger.info(f"Import completed successfully in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Import failed: {e}")

if __name__ == "__main__":
    main()