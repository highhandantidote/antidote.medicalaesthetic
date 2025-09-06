#!/usr/bin/env python3
"""
Chunked procedure import script.

This script imports procedures in extremely small chunks to avoid timeouts.
It allows resuming from the last imported procedure.
"""

import os
import sys
import csv
import time
import logging
import json
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
CSV_FILE_PATH = 'uploads/procedures.csv'
STATE_FILE = 'import_state.json'
CHUNK_SIZE = 5  # Number of procedures to process in a single run

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False  # We'll manage transactions manually
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def load_state():
    """Load the current import state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'started': False,
        'body_parts_imported': False,
        'categories_imported': False,
        'procedures_imported': 0,
        'body_part_ids': {},
        'category_ids': {}
    }

def save_state(state):
    """Save the current import state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)
    logger.info("Import state saved")

def read_csv_and_get_unique_items():
    """Read the CSV file and extract unique body parts and categories."""
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            
            body_parts = set()
            categories = set()
            for row in rows:
                if row['body_part_name']:
                    body_parts.add(row['body_part_name'])
                if row['body_part_name'] and row['category_name']:
                    categories.add((row['body_part_name'], row['category_name']))
            
            logger.info(f"Found {len(body_parts)} unique body parts")
            logger.info(f"Found {len(categories)} unique categories")
            logger.info(f"Found {len(rows)} procedures to import")
            
            return list(body_parts), list(categories), rows
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise

def clear_tables_if_needed(conn, state):
    """Clear tables if this is the first run."""
    if state['started']:
        logger.info("Resuming previous import, skipping table clearing")
        return
    
    logger.info("First run, clearing existing tables")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM procedures")
        cursor.execute("DELETE FROM categories")
        cursor.execute("DELETE FROM body_parts")
        conn.commit()
        logger.info("Tables cleared successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error clearing tables: {e}")
        raise
    finally:
        cursor.close()

def import_body_parts(conn, body_parts, state):
    """Import body parts if needed."""
    if state['body_parts_imported']:
        logger.info("Body parts already imported, skipping")
        return state['body_part_ids']
    
    logger.info("Importing body parts")
    cursor = conn.cursor()
    body_part_ids = {}
    
    try:
        for body_part in body_parts:
            # Check if body part already exists
            cursor.execute(
                "SELECT id FROM body_parts WHERE name = %s",
                (body_part,)
            )
            result = cursor.fetchone()
            
            if result:
                # Use existing body part
                body_part_id = result[0]
                logger.info(f"Using existing body part: {body_part} with ID {body_part_id}")
            else:
                # Create new body part
                cursor.execute(
                    "INSERT INTO body_parts (name, created_at) VALUES (%s, %s) RETURNING id",
                    (body_part, datetime.utcnow())
                )
                body_part_id = cursor.fetchone()[0]
                logger.info(f"Added new body part: {body_part} with ID {body_part_id}")
            
            body_part_ids[body_part] = body_part_id
        
        conn.commit()
        logger.info(f"Successfully imported {len(body_part_ids)} body parts")
        
        # Update state
        state['body_parts_imported'] = True
        state['body_part_ids'] = body_part_ids
        save_state(state)
        
        return body_part_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing body parts: {e}")
        raise
    finally:
        cursor.close()

def import_categories(conn, categories, body_part_ids, state):
    """Import categories if needed."""
    if state['categories_imported']:
        logger.info("Categories already imported, skipping")
        return state['category_ids']
    
    logger.info("Importing categories")
    cursor = conn.cursor()
    category_ids = {}
    
    try:
        for body_part_name, category_name in categories:
            body_part_id = body_part_ids.get(body_part_name)
            if not body_part_id:
                logger.warning(f"Body part not found for category: {category_name}")
                continue
            
            # Make a unique category name
            safe_name = f"{category_name.replace(' ', '_').replace('&', 'and')}_{body_part_id}"
            
            # Check if category already exists
            cursor.execute(
                "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
                (safe_name, body_part_id)
            )
            result = cursor.fetchone()
            
            if result:
                # Use existing category
                category_id = result[0]
                logger.info(f"Using existing category: {safe_name} with ID {category_id}")
            else:
                # Create new category
                try:
                    cursor.execute(
                        """
                        INSERT INTO categories (
                            name, body_part_id, created_at, description
                        ) VALUES (%s, %s, %s, %s) RETURNING id
                        """,
                        (
                            safe_name,
                            body_part_id,
                            datetime.utcnow(),
                            f"Category for {category_name} procedures in the {body_part_name} area"
                        )
                    )
                    category_id = cursor.fetchone()[0]
                    logger.info(f"Added new category: {safe_name} with ID {category_id}")
                except Exception as e:
                    logger.warning(f"Error creating category {safe_name}: {e}")
                    conn.rollback()
                    # Try with timestamp for uniqueness
                    safe_name = f"{safe_name}_{int(time.time())}"
                    cursor.execute(
                        """
                        INSERT INTO categories (
                            name, body_part_id, created_at, description
                        ) VALUES (%s, %s, %s, %s) RETURNING id
                        """,
                        (
                            safe_name,
                            body_part_id,
                            datetime.utcnow(),
                            f"Category for {category_name} procedures in the {body_part_name} area"
                        )
                    )
                    category_id = cursor.fetchone()[0]
                    logger.info(f"Added category with timestamp: {safe_name} with ID {category_id}")
            
            category_ids[(body_part_name, category_name)] = category_id
        
        conn.commit()
        logger.info(f"Successfully imported {len(category_ids)} categories")
        
        # Update state
        state['categories_imported'] = True
        state['category_ids'] = category_ids
        save_state(state)
        
        return category_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing categories: {e}")
        raise
    finally:
        cursor.close()

def import_procedures_chunk(conn, procedure_rows, category_ids, state):
    """Import a small chunk of procedures."""
    start_index = state['procedures_imported']
    end_index = min(start_index + CHUNK_SIZE, len(procedure_rows))
    
    if start_index >= len(procedure_rows):
        logger.info("All procedures already imported")
        return 0
    
    logger.info(f"Importing procedures {start_index+1} to {end_index} (of {len(procedure_rows)})")
    cursor = conn.cursor()
    imported_count = 0
    
    try:
        for i in range(start_index, end_index):
            row = procedure_rows[i]
            body_part_name = row['body_part_name']
            category_name = row['category_name']
            procedure_name = row.get('procedure_name', '')
            
            if not all([body_part_name, category_name, procedure_name]):
                logger.warning(f"Skipping procedure {i+1}: Missing required fields")
                continue
            
            category_id = category_ids.get((body_part_name, category_name))
            if not category_id:
                logger.warning(f"Skipping procedure {i+1}: Category not found")
                continue
            
            # Parse cost values
            min_cost = None
            if row.get('min_cost'):
                try:
                    min_cost_str = ''.join(c for c in row['min_cost'] if c.isdigit())
                    min_cost = int(min_cost_str) if min_cost_str else None
                except (ValueError, TypeError):
                    min_cost = None
            
            max_cost = None
            if row.get('max_cost'):
                try:
                    max_cost_str = ''.join(c for c in row['max_cost'] if c.isdigit())
                    max_cost = int(max_cost_str) if max_cost_str else None
                except (ValueError, TypeError):
                    max_cost = None
            
            # Parse tags
            tags = []
            if row.get('tags'):
                tags = [tag.strip() for tag in row['tags'].split(',') if tag.strip()]
            
            try:
                # Insert procedure
                cursor.execute(
                    """
                    INSERT INTO procedures (
                        procedure_name, alternative_names, short_description, 
                        overview, procedure_details, ideal_candidates, 
                        recovery_process, recovery_time, procedure_duration,
                        hospital_stay_required, results_duration, min_cost, max_cost,
                        benefits, benefits_detailed, risks, procedure_types,
                        alternative_procedures, body_part, tags, category_id,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        procedure_name,
                        row.get('alternative_names', ''),
                        row.get('short_description', ''),
                        row.get('overview', ''),
                        row.get('procedure_details', ''),
                        row.get('ideal_candidates', ''),
                        row.get('recovery_process', ''),
                        row.get('recovery_time', ''),
                        row.get('procedure_duration', ''),
                        row.get('hospital_stay_required', ''),
                        row.get('results_duration', ''),
                        min_cost,
                        max_cost,
                        row.get('benefits', ''),
                        row.get('benefits_detailed', ''),
                        row.get('risks', ''),
                        row.get('procedure_types', ''),
                        row.get('alternative_procedures', ''),
                        body_part_name,
                        tags,
                        category_id,
                        datetime.utcnow(),
                        datetime.utcnow()
                    )
                )
                imported_count += 1
                logger.info(f"Added procedure {i+1}: {procedure_name}")
            except Exception as e:
                logger.error(f"Error adding procedure {i+1} ({procedure_name}): {e}")
                # Skip this procedure but continue with others
        
        conn.commit()
        logger.info(f"Successfully imported {imported_count} procedures in this chunk")
        
        # Update state
        state['procedures_imported'] = end_index
        save_state(state)
        
        return imported_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing procedures chunk: {e}")
        raise
    finally:
        cursor.close()

def verify_import(conn):
    """Verify the import counts."""
    cursor = conn.cursor()
    try:
        # Count body parts
        cursor.execute("SELECT COUNT(*) FROM body_parts")
        body_part_count = cursor.fetchone()[0]
        
        # Count categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        
        # Count procedures
        cursor.execute("SELECT COUNT(*) FROM procedures")
        procedure_count = cursor.fetchone()[0]
        
        logger.info(f"Current database state: {body_part_count} body parts, {category_count} categories, {procedure_count} procedures")
        return {
            'body_parts': body_part_count,
            'categories': category_count,
            'procedures': procedure_count
        }
    except Exception as e:
        logger.error(f"Error verifying import: {e}")
        raise
    finally:
        cursor.close()

def main():
    """Main function to import procedures in small chunks."""
    start_time = time.time()
    logger.info("Starting chunked procedure import")
    
    # Load state
    state = load_state()
    state['started'] = True
    save_state(state)
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Get information about what needs to be imported
        body_parts, categories, procedure_rows = read_csv_and_get_unique_items()
        
        # Clear tables if this is the first run
        clear_tables_if_needed(conn, state)
        
        # Import body parts
        body_part_ids = import_body_parts(conn, body_parts, state)
        
        # Import categories
        category_ids = import_categories(conn, categories, body_part_ids, state)
        
        # Import a chunk of procedures
        imported_count = import_procedures_chunk(conn, procedure_rows, category_ids, state)
        
        # Verify the current state
        counts = verify_import(conn)
        
        # Calculate elapsed time and completion percentage
        elapsed_time = time.time() - start_time
        if len(procedure_rows) > 0:
            completion_pct = (state['procedures_imported'] / len(procedure_rows)) * 100
        else:
            completion_pct = 100
            
        logger.info(f"Chunk processed in {elapsed_time:.2f} seconds")
        logger.info(f"Overall progress: {state['procedures_imported']} of {len(procedure_rows)} procedures ({completion_pct:.1f}%)")
        
        # Close connection
        conn.close()
        
        # Check if we've completed all procedures
        if state['procedures_imported'] >= len(procedure_rows):
            logger.info("Import complete! All procedures have been imported.")
            # Clean up state file
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
                logger.info("State file removed")
        else:
            logger.info("To continue importing procedures, run this script again.")
        
        return counts
    except Exception as e:
        logger.error(f"Import chunk failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()