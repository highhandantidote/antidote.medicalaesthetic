#!/usr/bin/env python3
"""
Add procedures directly to the database in batches.

This script imports procedure data from CSV in small batches to avoid timeout issues.
"""

import os
import csv
import logging
import psycopg2
import psycopg2.extensions
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to CSV file
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"
BATCH_SIZE = 50  # Process procedures in larger batches

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if value is None or value == "":
        return 0
    
    # Remove commas, spaces, and non-numeric characters except for the first minus sign
    value = str(value)
    clean_value = ''.join(c for c in value if c.isdigit() or (c == '-' and value.index(c) == 0))
    
    try:
        return int(clean_value or 0)
    except ValueError:
        return 0

def add_procedures_batch(start_index=0, batch_size=BATCH_SIZE):
    """Add a batch of procedures to the database."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return False
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
            
        # Set isolation level to ensure proper transaction behavior
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
        
        # Read all rows from CSV
        all_rows = []
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_rows = list(reader)
        
        # Get only the batch we want to process
        end_index = min(start_index + batch_size, len(all_rows))
        batch_rows = all_rows[start_index:end_index]
        
        if not batch_rows:
            logger.info(f"No more procedures to process starting from index {start_index}")
            return False
        
        # Get all body parts and categories for reference
        body_part_ids = {}
        category_ids = {}
        
        with conn.cursor() as cur:
            # Get all body parts
            cur.execute("SELECT id, name FROM body_parts")
            for bp_id, bp_name in cur.fetchall():
                body_part_ids[bp_name] = bp_id
            
            # Get all categories
            cur.execute("SELECT id, name, body_part_id FROM categories")
            for cat_id, cat_name, bp_id in cur.fetchall():
                # Find the body part name for this category
                bp_name = None
                for name, id in body_part_ids.items():
                    if id == bp_id:
                        bp_name = name
                        break
                
                if bp_name:
                    category_ids[(bp_name, cat_name)] = cat_id
        
        # Process the batch
        procedures_added = 0
        skipped = 0
        
        for row in batch_rows:
            # Get essential fields
            body_part_name = row.get('body_part_name', '').strip()
            category_name = row.get('category_name', '').strip()
            procedure_name = row.get('procedure_name', '').strip()
            
            # Skip if essential fields are missing
            if not procedure_name or not body_part_name or not category_name:
                skipped += 1
                continue
            
            # Check if body part exists
            if body_part_name not in body_part_ids:
                # Check if the body part exists but wasn't found in our initial query
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM body_parts WHERE name = %s", (body_part_name,))
                    existing_body_part = cur.fetchone()
                    
                    if existing_body_part:
                        # Body part exists, use existing ID
                        bp_id = existing_body_part[0]
                        body_part_ids[body_part_name] = bp_id
                        logger.info(f"Using existing body part: {body_part_name} (ID: {bp_id})")
                    else:
                        # Create body part since it doesn't exist
                        try:
                            cur.execute("""
                                INSERT INTO body_parts (name, description, icon_url, created_at)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id
                            """, (
                                body_part_name,
                                f"Procedures related to the {body_part_name.lower()}",
                                f"/static/images/body_parts/{body_part_name.lower().replace(' ', '_')}.svg",
                                datetime.utcnow()
                            ))
                            
                            result = cur.fetchone()
                            if result:
                                bp_id = result[0]
                            else:
                                logger.error("Failed to get ID after body part insertion")
                                raise Exception("Failed to get ID after body part insertion")
                            body_part_ids[body_part_name] = bp_id
                            logger.info(f"Created missing body part: {body_part_name} (ID: {bp_id})")
                        except Exception as e:
                            # If insertion fails, try fetching again
                            conn.rollback()
                            cur.execute("SELECT id FROM body_parts WHERE name = %s", (body_part_name,))
                            result = cur.fetchone()
                            if result:
                                bp_id = result[0]
                                body_part_ids[body_part_name] = bp_id
                                logger.info(f"Using existing body part after insertion error: {body_part_name} (ID: {bp_id})")
                            else:
                                # Re-raise if we still can't find the body part
                                logger.error(f"Failed to create or find body part: {body_part_name}")
                                raise
            
            # Get body part ID
            body_part_id = body_part_ids[body_part_name]
            
            # Check if category exists
            category_key = (body_part_name, category_name)
            if category_key not in category_ids:
                # Check if the category exists but with a different body part
                with conn.cursor() as cur:
                    cur.execute("SELECT id, body_part_id FROM categories WHERE name = %s", (category_name,))
                    existing_category = cur.fetchone()
                    
                    if existing_category:
                        # Category exists but might be under a different body part
                        # Let's use the existing category ID
                        cat_id = existing_category[0]
                        category_ids[category_key] = cat_id
                        logger.info(f"Using existing category: {category_name} (ID: {cat_id}) for body part {body_part_name}")
                    else:
                        # Create category since it doesn't exist at all
                        try:
                            cur.execute("""
                                INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                                VALUES (%s, %s, %s, %s, %s)
                                RETURNING id
                            """, (
                                category_name,
                                f"{category_name} procedures for {body_part_name}",
                                body_part_id,
                                0,
                                datetime.utcnow()
                            ))
                            
                            result = cur.fetchone()
                            if result:
                                cat_id = result[0]
                            else:
                                logger.error("Failed to get ID after category insertion")
                                raise Exception("Failed to get ID after category insertion")
                            category_ids[category_key] = cat_id
                            logger.info(f"Created missing category: {category_name} under {body_part_name} (ID: {cat_id})")
                        except Exception as e:
                            # If insertion fails (maybe due to race condition), try fetching again
                            conn.rollback()
                            cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
                            result = cur.fetchone()
                            if result:
                                cat_id = result[0]
                                category_ids[category_key] = cat_id
                                logger.info(f"Using existing category after insertion error: {category_name} (ID: {cat_id})")
                            else:
                                # Re-raise if we still can't find the category
                                logger.error(f"Failed to create or find category: {category_name} for {body_part_name}")
                                raise
            
            # Get category ID
            category_id = category_ids[category_key]
            
            # Check if procedure already exists
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM procedures WHERE procedure_name = %s", (procedure_name,))
                result = cur.fetchone()
                
                if result:
                    # Procedure already exists
                    logger.info(f"Procedure already exists: {procedure_name} (ID: {result[0]})")
                    skipped += 1
                    continue
                
                # Clean cost values
                min_cost = clean_integer(row.get('min_cost', '0'))
                max_cost = clean_integer(row.get('max_cost', '0'))
                
                # Create new procedure
                cur.execute("""
                    INSERT INTO procedures (
                        procedure_name, alternative_names, short_description, overview,
                        procedure_details, ideal_candidates, recovery_process, recovery_time,
                        procedure_duration, hospital_stay_required, results_duration,
                        min_cost, max_cost, benefits, benefits_detailed, risks,
                        procedure_types, alternative_procedures, category_id, popularity_score,
                        avg_rating, review_count, body_part
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    procedure_name, 
                    row.get('alternative_names', ''),
                    row.get('short_description', ''), 
                    row.get('overview', ''),
                    row.get('procedure_details', ''), 
                    row.get('ideal_candidates', ''),
                    row.get('recovery_process', ''), 
                    row.get('recovery_time', ''),
                    row.get('procedure_duration', ''), 
                    row.get('hospital_stay_required', 'No'),
                    row.get('results_duration', ''),
                    min_cost, 
                    max_cost,
                    row.get('benefits', ''), 
                    row.get('benefits_detailed', ''),
                    row.get('risks', ''), 
                    row.get('procedure_types', ''),
                    row.get('alternative_procedures', ''), 
                    category_id,
                    50,  # popularity_score
                    0.0,  # avg_rating
                    0,    # review_count
                    body_part_name
                ))
                
                result = cur.fetchone()
                if result:
                    procedure_id = result[0]
                else:
                    logger.error("Failed to get ID after procedure insertion")
                    raise Exception("Failed to get ID after procedure insertion")
                logger.info(f"Added procedure: {procedure_name} (ID: {procedure_id})")
                procedures_added += 1
        
        conn.commit()
        logger.info(f"Batch processed: Added {procedures_added} procedures (skipped {skipped})")
        
        # Return the next start index for the next batch
        return end_index
    except Exception as e:
        logger.error(f"Error adding procedures batch: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def process_all_procedures(max_runs=5):
    """Process all procedures in batches, with a limit on total runs.
    
    Args:
        max_runs: Maximum number of batch runs to perform
    """
    logger.info(f"Starting procedure import in batches (max {max_runs} batches)...")
    
    start_index = 0
    run_count = 0
    
    while run_count < max_runs:
        run_count += 1
        logger.info(f"Processing batch {run_count} of {max_runs} (starting at index {start_index})")
        
        result = add_procedures_batch(start_index, BATCH_SIZE)
        if result is False:
            logger.error("Procedure import failed or completed")
            break
        if result == start_index:
            logger.info("All procedures processed")
            break
        start_index = result
    
    logger.info(f"Procedure import completed after {run_count} batches")
    return True

if __name__ == "__main__":
    # Process 5 batches of 50 procedures each = 250 procedures total
    process_all_procedures(max_runs=5)