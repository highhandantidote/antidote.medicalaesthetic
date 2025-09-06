#!/usr/bin/env python3
"""
Add more procedures to the Antidote platform database.

This script focuses on importing more procedures from the CSV file to reach our target count.
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
BATCH_SIZE = 5  # Process this many procedures at once to avoid timeouts

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

def read_procedures_from_csv(offset=0, limit=BATCH_SIZE):
    """Read a batch of procedures from the CSV file."""
    procedures = []
    try:
        with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Skip to the offset
            for _ in range(offset):
                next(reader, None)
            
            # Read up to the limit
            count = 0
            for row in reader:
                if count >= limit:
                    break
                procedures.append(row)
                count += 1
                
        return procedures
    except Exception as e:
        logger.error(f"Error reading procedures from CSV: {str(e)}")
        return []

def count_total_procedures_in_csv():
    """Count total procedures in CSV."""
    try:
        with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as f:
            return sum(1 for _ in csv.reader(f)) - 1  # Subtract header row
    except Exception as e:
        logger.error(f"Error counting procedures in CSV: {str(e)}")
        return 0

def count_existing_procedures():
    """Count existing procedures in the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error counting existing procedures: {str(e)}")
        return 0
    finally:
        if conn:
            conn.close()

def procedure_exists(conn, name):
    """Check if a procedure with the given name already exists."""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM procedures WHERE procedure_name = %s",
            (name,)
        )
        return cursor.fetchone() is not None

def get_category_id(conn, body_part_name, category_type):
    """Get category ID by name and body part."""
    try:
        with conn.cursor() as cursor:
            # First find the body part ID
            cursor.execute(
                "SELECT id FROM body_parts WHERE name ILIKE %s",
                (f"%{body_part_name}%",)
            )
            result = cursor.fetchone()
            if not result:
                # Try with a more general search if exact match fails
                cursor.execute(
                    "SELECT id FROM body_parts LIMIT 1"
                )
                result = cursor.fetchone()
                
            if not result:
                logger.warning(f"Body part not found: {body_part_name}")
                return None
                
            body_part_id = result[0]
            
            # Now find the category
            cursor.execute(
                """
                SELECT id FROM categories 
                WHERE body_part_id = %s AND name ILIKE %s
                """,
                (body_part_id, f"%{category_type}%")
            )
            result = cursor.fetchone()
            
            if not result:
                # If specific category not found, get any category for this body part
                cursor.execute(
                    "SELECT id FROM categories WHERE body_part_id = %s LIMIT 1",
                    (body_part_id,)
                )
                result = cursor.fetchone()
            
            return result[0] if result else None
            
    except Exception as e:
        logger.error(f"Error finding category ID: {str(e)}")
        return None

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if not value:
        return None
        
    # Remove any currency symbols, commas, and non-numeric characters
    cleaned = ''.join(c for c in value if c.isdigit() or c == '.')
    
    try:
        if '.' in cleaned:
            # Convert to float first, then integer
            return int(float(cleaned))
        elif cleaned:
            return int(cleaned)
        else:
            return None
    except (ValueError, TypeError):
        return None

def import_procedures(start_index=0, batch_size=BATCH_SIZE):
    """Import a batch of procedures from CSV."""
    conn = get_db_connection()
    procedures_added = 0
    
    try:
        # Read a batch of procedures from CSV
        procedures_batch = read_procedures_from_csv(start_index, batch_size)
        
        if not procedures_batch:
            logger.info(f"No more procedures to import starting at index {start_index}")
            return 0
            
        logger.info(f"Processing {len(procedures_batch)} procedures starting at index {start_index}")
        
        # Process each procedure
        for procedure_data in procedures_batch:
            try:
                # Basic data validation
                procedure_name = procedure_data.get('Name', '').strip()
                if not procedure_name:
                    logger.warning("Skipping procedure with missing name")
                    continue
                
                # Check if procedure already exists
                if procedure_exists(conn, procedure_name):
                    logger.info(f"Procedure already exists: {procedure_name}")
                    continue
                
                # Get category ID
                body_part = procedure_data.get('Body Part', '').strip()
                category_type = procedure_data.get('Category', '').strip()
                
                category_id = get_category_id(conn, body_part, category_type)
                if not category_id:
                    logger.warning(f"Cannot find category for procedure: {procedure_name}")
                    continue
                
                # Clean cost values
                min_cost = clean_integer(procedure_data.get('Min Cost', '0'))
                max_cost = clean_integer(procedure_data.get('Max Cost', '0'))
                
                # Set default values if missing
                if not min_cost:
                    min_cost = 15000
                if not max_cost:
                    max_cost = 50000
                    
                # Ensure max cost is greater than min cost
                if max_cost < min_cost:
                    max_cost = min_cost * 1.5
                
                # Insert procedure with all required fields
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO procedures (
                            procedure_name, category_id, short_description, overview,
                            min_cost, max_cost, created_at, updated_at,
                            procedure_details, recovery_time, risks, procedure_types,
                            recovery_process, benefits, alternative_procedures,
                            ideal_candidates, benefits_detailed, results_duration,
                            hospital_stay_required, procedure_duration
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            procedure_name,
                            category_id,
                            procedure_data.get('Short Description', 'A cosmetic procedure to enhance appearance.'),
                            procedure_data.get('Overview', 'A popular cosmetic procedure designed to improve aesthetic appearance.'),
                            min_cost,
                            max_cost,
                            datetime.now(),
                            datetime.now(),
                            procedure_data.get('Procedure Details', 'Standard procedure involving multiple treatment sessions for optimal results.'),
                            procedure_data.get('Recovery Time', '1-2 weeks for full recovery'),
                            procedure_data.get('Risks', 'Minor redness and swelling may occur but typically resolves quickly'),
                            procedure_data.get('Procedure Types', 'Standard and advanced options available'),
                            procedure_data.get('Recovery Process', 'Rest and follow post-procedure care instructions'),
                            procedure_data.get('Benefits', 'Improved appearance and confidence'),
                            procedure_data.get('Alternative Procedures', 'Alternative treatments are available'),
                            procedure_data.get('Ideal Candidates', 'Adults in good health seeking cosmetic improvement'),
                            procedure_data.get('Benefits Detailed', 'Enhanced confidence, improved appearance, and greater self-esteem'),
                            procedure_data.get('Results Duration', 'Results may last 6-18 months depending on treatment type'),
                            procedure_data.get('Hospital Stay Required', 'No'),
                            procedure_data.get('Procedure Duration', '45-90 minutes')
                        )
                    )
                    result = cursor.fetchone()
                    if result:
                        procedure_id = result[0]
                        logger.info(f"Added procedure: {procedure_name} (ID: {procedure_id})")
                        procedures_added += 1
                        
                        # Commit each procedure individually
                        conn.commit()
                        
                        # Brief pause to avoid timeouts
                        time.sleep(0.2)
                    else:
                        logger.error(f"Failed to add procedure: {procedure_name}")
                        conn.rollback()
                    
            except Exception as e:
                logger.error(f"Error adding procedure {procedure_name}: {str(e)}")
                conn.rollback()
        
        return procedures_added
        
    except Exception as e:
        logger.error(f"Error in import_procedures: {str(e)}")
        return procedures_added
    finally:
        conn.close()

def check_database_status():
    """Check the current status of the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check procedures
            cursor.execute("SELECT COUNT(*) FROM procedures")
            result = cursor.fetchone()
            procedure_count = result[0] if result else 0
            
            # Get total procedures in CSV
            total_procedures = count_total_procedures_in_csv()
            
            # Print summary
            logger.info("=" * 80)
            logger.info("PROCEDURE IMPORT STATUS")
            logger.info("=" * 80)
            logger.info(f"Procedures: {procedure_count} out of {total_procedures} in CSV ({procedure_count/total_procedures:.1%})")
            logger.info("=" * 80)
            
            # Return counts for potential use by other scripts
            return {
                "procedures": procedure_count,
                "total_procedures": total_procedures
            }
            
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def main():
    """Main function to import procedures in batches."""
    start_time = time.time()
    
    # Check current database status
    status_before = check_database_status()
    
    # Determine where to start
    existing_procedures = count_existing_procedures()
    logger.info(f"Found {existing_procedures} existing procedures in database")
    
    # Import procedures in batches
    total_imported = 0
    current_index = existing_procedures
    batch_size = BATCH_SIZE
    
    # Import up to 3 batches at a time to avoid timeouts
    max_batches = 3
    batch_count = 0
    
    while batch_count < max_batches:
        procedures_added = import_procedures(current_index, batch_size)
        
        if procedures_added == 0:
            logger.info("No more procedures to import")
            break
            
        total_imported += procedures_added
        current_index += batch_size
        batch_count += 1
        
        logger.info(f"Imported batch {batch_count}: {procedures_added} procedures")
    
    # Check final database status
    status_after = check_database_status()
    
    elapsed = time.time() - start_time
    logger.info(f"Procedure import completed in {elapsed:.2f} seconds")
    logger.info(f"Total procedures added in this run: {total_imported}")
    
    if status_before and status_after:
        procs_diff = status_after["procedures"] - status_before["procedures"]
        logger.info(f"Net procedures added: {procs_diff}")
    
    logger.info("Procedure import complete!")

if __name__ == "__main__":
    main()