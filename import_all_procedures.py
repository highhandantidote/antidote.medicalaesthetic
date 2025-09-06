"""
Import all procedures from the CSV file in batches.

This script reads all procedures from the provided CSV file and imports them into the database
while properly organizing them by body_part_name and category_name as specified in the CSV.

It processes data in small batches to avoid timeouts, and provides progress tracking.
"""
import os
import csv
import time
import logging
import argparse
import psycopg2
import psycopg2.extras
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('procedure_import.log')
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def count_csv_rows(csv_path):
    """Count the number of rows in the CSV file."""
    with open(csv_path, 'r', encoding='utf-8') as file:
        return sum(1 for _ in csv.reader(file)) - 1  # Subtract 1 for header row

def get_or_create_body_part(conn, name):
    """Get or create a body part record."""
    cursor = conn.cursor()
    
    # Try to find the body part
    cursor.execute(
        "SELECT id FROM body_parts WHERE name = %s",
        (name,)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Create a new body part
    cursor.execute(
        """
        INSERT INTO body_parts (name, description, created_at)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (name, f"Body part: {name}", datetime.utcnow())
    )
    body_part_id = cursor.fetchone()[0]
    logger.info(f"Created new body part: {name} with ID: {body_part_id}")
    
    return body_part_id

def get_or_create_category(conn, name, body_part_id):
    """Get or create a category record."""
    cursor = conn.cursor()
    
    # Try to find the category
    cursor.execute(
        "SELECT id FROM categories WHERE name = %s",
        (name,)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Create a new category
    cursor.execute(
        """
        INSERT INTO categories (name, body_part_id, description, created_at)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (name, body_part_id, f"Category: {name}", datetime.utcnow())
    )
    category_id = cursor.fetchone()[0]
    logger.info(f"Created new category: {name} with ID: {category_id}")
    
    return category_id

def add_procedure(conn, procedure_data):
    """Add a single procedure to the database."""
    cursor = conn.cursor()
    
    # Get or create body part and category
    body_part_id = get_or_create_body_part(conn, procedure_data['body_part_name'])
    category_id = get_or_create_category(conn, procedure_data['category_name'], body_part_id)
    
    # Check if procedure already exists
    cursor.execute(
        "SELECT id FROM procedures WHERE procedure_name = %s",
        (procedure_data['procedure_name'],)
    )
    result = cursor.fetchone()
    
    min_cost = int(procedure_data['min_cost'].replace(',', '')) if procedure_data['min_cost'] else 0
    max_cost = int(procedure_data['max_cost'].replace(',', '')) if procedure_data['max_cost'] else 0
    
    # Handle tags if they exist in the CSV
    tags = None
    if 'tags' in procedure_data and procedure_data['tags']:
        # Split tags and ensure each tag is trimmed to max 20 chars per database constraint
        tags = [tag.strip()[:20] for tag in procedure_data['tags'].split(',')]
        logger.info(f"Processed tags: {tags}")
    
    if result:
        # Update existing procedure
        procedure_id = result[0]
        
        cursor.execute(
            """
            UPDATE procedures SET
                alternative_names = %s,
                short_description = %s,
                overview = %s,
                procedure_details = %s,
                ideal_candidates = %s,
                recovery_process = %s,
                recovery_time = %s,
                procedure_duration = %s,
                hospital_stay_required = %s,
                results_duration = %s,
                min_cost = %s,
                max_cost = %s,
                benefits = %s,
                benefits_detailed = %s,
                risks = %s,
                procedure_types = %s,
                alternative_procedures = %s,
                category_id = %s,
                body_part = %s,
                tags = %s,
                updated_at = %s
            WHERE id = %s
            """,
            (
                procedure_data['alternative_names'],
                procedure_data['short_description'],
                procedure_data['overview'],
                procedure_data['procedure_details'],
                procedure_data['ideal_candidates'],
                procedure_data.get('recovery_process', ''),
                procedure_data['recovery_time'],
                procedure_data['procedure_duration'],
                procedure_data['hospital_stay_required'],
                procedure_data.get('results_duration', ''),
                min_cost,
                max_cost,
                procedure_data.get('benefits', ''),
                procedure_data.get('benefits_detailed', ''),
                procedure_data['risks'],
                procedure_data['procedure_types'],
                procedure_data.get('alternative_procedures', ''),
                category_id,
                procedure_data['body_part_name'],
                tags,
                datetime.utcnow(),
                procedure_id
            )
        )
        logger.info(f"Updated procedure: {procedure_data['procedure_name']}")
    else:
        # Insert new procedure
        cursor.execute(
            """
            INSERT INTO procedures (
                procedure_name, alternative_names, short_description,
                overview, procedure_details, ideal_candidates,
                recovery_process, recovery_time, procedure_duration,
                hospital_stay_required, results_duration,
                min_cost, max_cost, benefits, benefits_detailed,
                risks, procedure_types, alternative_procedures,
                category_id, body_part, tags, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """,
            (
                procedure_data['procedure_name'],
                procedure_data['alternative_names'],
                procedure_data['short_description'],
                procedure_data['overview'],
                procedure_data['procedure_details'],
                procedure_data['ideal_candidates'],
                procedure_data.get('recovery_process', ''),
                procedure_data['recovery_time'],
                procedure_data['procedure_duration'],
                procedure_data['hospital_stay_required'],
                procedure_data.get('results_duration', ''),
                min_cost,
                max_cost,
                procedure_data.get('benefits', ''),
                procedure_data.get('benefits_detailed', ''),
                procedure_data['risks'],
                procedure_data['procedure_types'],
                procedure_data.get('alternative_procedures', ''),
                category_id,
                procedure_data['body_part_name'],
                tags,
                datetime.utcnow(),
                datetime.utcnow()
            )
        )
        procedure_id = cursor.fetchone()[0]
        logger.info(f"Added new procedure: {procedure_data['procedure_name']} with ID: {procedure_id}")
    
    return procedure_id

def import_procedures_batch(csv_path, start_row, batch_size):
    """Import a batch of procedures from the CSV file."""
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return 0, 0, False
    
    total_rows = count_csv_rows(csv_path)
    logger.info(f"CSV file contains {total_rows} procedures (excluding header)")
    
    if start_row >= total_rows:
        logger.info(f"Start row {start_row} exceeds total rows {total_rows}. Import complete.")
        return 0, 0, True  # Done with import
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        # Skip to start_row
        for i in range(start_row):
            next(csv_reader)
        
        conn = get_db_connection()
        
        try:
            success_count = 0
            error_count = 0
            
            # Only process batch_size procedures
            for i in range(batch_size):
                try:
                    row = next(csv_reader)
                except StopIteration:
                    # End of file reached
                    logger.info("Reached end of CSV file")
                    break
                
                try:
                    current_row = start_row + i + 1
                    logger.info(f"Processing procedure {current_row}/{total_rows}: {row['procedure_name']}")
                    
                    add_procedure(conn, row)
                    conn.commit()
                    
                    success_count += 1
                    
                    # Log progress as percentage
                    progress = (current_row / total_rows) * 100
                    logger.info(f"Progress: {progress:.2f}% ({current_row}/{total_rows})")
                    
                except Exception as e:
                    conn.rollback()
                    error_count += 1
                    logger.error(f"Error importing procedure {row.get('procedure_name', 'unknown')}: {str(e)}")
            
            # Check if we've processed all rows
            done = (start_row + success_count + error_count) >= total_rows
            
            # If we had to stop processing due to reaching batch_size, we're not done yet
            if success_count + error_count == batch_size and not done:
                done = False
            
            return success_count, error_count, done
            
        finally:
            conn.close()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Import procedures from CSV in batches')
    parser.add_argument('--start', type=int, default=0, help='Starting row index (0-based)')
    parser.add_argument('--batch', type=int, default=10, help='Batch size')
    parser.add_argument('--csv', type=str, default='attached_assets/procedure_details - Sheet1.csv', help='Path to CSV file')
    args = parser.parse_args()
    
    csv_path = args.csv
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    logger.info(f"Starting import from {csv_path} at row {args.start} with batch size {args.batch}")
    start_time = time.time()
    
    success_count, error_count, done = import_procedures_batch(csv_path, args.start, args.batch)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Batch import completed in {elapsed_time:.2f} seconds: {success_count} procedures imported, {error_count} errors")
    
    next_start = args.start + args.batch
    if not done:
        logger.info(f"To continue importing, run: python import_all_procedures.py --start {next_start} --batch {args.batch}")
        print(f"\nNext command to run: python import_all_procedures.py --start {next_start} --batch {args.batch}")
    else:
        logger.info("All procedures have been imported successfully!")
        print("\nAll procedures have been imported successfully!")

if __name__ == "__main__":
    main()