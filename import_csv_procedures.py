#!/usr/bin/env python3
"""
Import procedures from CSV file.

This script imports procedures from the CSV file using existing body parts and categories,
ensuring no new categories or body parts are created.
"""

import os
import sys
import csv
import logging
import psycopg2
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CSV_FILE_PATH = 'uploads/procedures.csv'
BATCH_SIZE = 10  # Number of procedures to process in one run

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def get_existing_data(conn):
    """Get existing body parts, categories, and procedures."""
    cursor = conn.cursor()
    
    try:
        # Get existing body parts
        cursor.execute("SELECT id, name FROM body_parts")
        body_parts = {row[1]: row[0] for row in cursor.fetchall()}
        logger.info(f"Found {len(body_parts)} existing body parts")
        
        # Get existing categories with their body part IDs
        cursor.execute("""
            SELECT c.id, c.name, bp.name 
            FROM categories c
            JOIN body_parts bp ON c.body_part_id = bp.id
        """)
        categories = {}
        for row in cursor.fetchall():
            cat_id, cat_name, body_part_name = row
            categories[(cat_name, body_part_name)] = cat_id
        logger.info(f"Found {len(categories)} existing categories")
        
        # Get existing procedures
        cursor.execute("SELECT procedure_name FROM procedures")
        procedures = set(row[0] for row in cursor.fetchall())
        logger.info(f"Found {len(procedures)} existing procedures")
        
        return body_parts, categories, procedures
    except Exception as e:
        logger.error(f"Error getting existing data: {e}")
        raise
    finally:
        cursor.close()

def find_category_for_procedure(categories, category_name, body_part_name):
    """Find the appropriate category ID based on name and body part."""
    # Try exact match first
    if (category_name, body_part_name) in categories:
        return categories[(category_name, body_part_name)]
    
    # Try matching with underscores instead of spaces
    category_underscore = category_name.replace(' ', '_')
    if (category_underscore, body_part_name) in categories:
        return categories[(category_underscore, body_part_name)]
    
    # Try partial matching
    for (cat_name, bp_name), cat_id in categories.items():
        # Match if category contains the target name and body part matches
        if (category_name.lower() in cat_name.lower() or 
            cat_name.lower() in category_name.lower()) and bp_name == body_part_name:
            return cat_id
    
    return None

def clean_numeric_value(value_str):
    """Clean and convert numeric values from the CSV."""
    if not value_str:
        return None
    
    # Remove commas, currency symbols, and other non-numeric characters
    digits_only = ''.join(c for c in value_str if c.isdigit())
    
    if digits_only:
        return int(digits_only)
    
    return None

def import_procedures_batch(conn, start_index):
    """Import a batch of procedures from the CSV file."""
    imported_count = 0
    
    try:
        # Get existing data
        body_parts, categories, existing_procedures = get_existing_data(conn)
        
        # Read the CSV file
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            
            # Check if we've reached the end
            if start_index >= len(rows):
                logger.info("Reached the end of the CSV file")
                return 0
            
            # Process a batch of rows
            end_index = min(start_index + BATCH_SIZE, len(rows))
            batch = rows[start_index:end_index]
            
            logger.info(f"Processing procedures {start_index+1} to {end_index} of {len(rows)}")
            
            cursor = conn.cursor()
            
            for i, row in enumerate(batch):
                procedure_name = row.get('procedure_name', '').strip()
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                
                # Skip if procedure exists or missing required fields
                if not procedure_name or procedure_name in existing_procedures:
                    logger.info(f"Skipping procedure: {procedure_name or 'unknown'} (exists or invalid name)")
                    continue
                
                # Skip if body part doesn't exist
                if body_part_name not in body_parts:
                    logger.warning(f"Skipping procedure: {procedure_name} (body part '{body_part_name}' not found)")
                    continue
                
                # Find the appropriate category
                category_id = find_category_for_procedure(categories, category_name, body_part_name)
                if not category_id:
                    logger.warning(f"Skipping procedure: {procedure_name} (category '{category_name}' not found for body part '{body_part_name}')")
                    continue
                
                # Process numeric fields
                min_cost = clean_numeric_value(row.get('min_cost', ''))
                max_cost = clean_numeric_value(row.get('max_cost', ''))
                
                # Default values for required fields
                min_cost = min_cost if min_cost is not None else 10000
                max_cost = max_cost if max_cost is not None else 100000
                
                # Process tags
                tags = []
                if row.get('tags'):
                    tags = [tag.strip() for tag in row['tags'].split(',') if tag.strip()]
                
                # Ensure required fields have values
                short_description = row.get('short_description', '').strip()
                if not short_description:
                    short_description = f"{procedure_name} procedure."
                
                overview = row.get('overview', '').strip()
                if not overview:
                    overview = f"{procedure_name} is a cosmetic procedure for the {body_part_name}."
                
                procedure_details = row.get('procedure_details', '').strip()
                if not procedure_details:
                    procedure_details = f"The {procedure_name} procedure involves professional medical techniques."
                
                ideal_candidates = row.get('ideal_candidates', '').strip()
                if not ideal_candidates:
                    ideal_candidates = f"Individuals seeking {body_part_name} enhancement."
                
                recovery_time = row.get('recovery_time', '').strip()
                if not recovery_time:
                    recovery_time = "Varies by individual"
                
                risks = row.get('risks', '').strip()
                if not risks:
                    risks = "All procedures carry risks. Consult with your doctor."
                
                procedure_types = row.get('procedure_types', '').strip()
                if not procedure_types:
                    procedure_types = "Standard procedure"
                
                # Insert the procedure
                try:
                    cursor.execute("""
                    INSERT INTO procedures (
                        procedure_name,
                        alternative_names,
                        short_description,
                        overview,
                        procedure_details,
                        ideal_candidates,
                        recovery_process,
                        recovery_time,
                        procedure_duration,
                        hospital_stay_required,
                        results_duration,
                        min_cost,
                        max_cost,
                        benefits,
                        benefits_detailed,
                        risks,
                        procedure_types,
                        alternative_procedures,
                        category_id,
                        body_part,
                        tags,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                    """, (
                        procedure_name,
                        row.get('alternative_names', ''),
                        short_description,
                        overview,
                        procedure_details,
                        ideal_candidates,
                        row.get('recovery_process', ''),
                        recovery_time,
                        row.get('procedure_duration', ''),
                        row.get('hospital_stay_required', ''),
                        row.get('results_duration', ''),
                        min_cost,
                        max_cost,
                        row.get('benefits', ''),
                        row.get('benefits_detailed', ''),
                        risks,
                        procedure_types,
                        row.get('alternative_procedures', ''),
                        category_id,
                        body_part_name,
                        tags,
                    ))
                    
                    imported_count += 1
                    existing_procedures.add(procedure_name)
                    logger.info(f"Added procedure: {procedure_name}")
                except Exception as e:
                    logger.error(f"Error adding procedure {procedure_name}: {e}")
                    # Continue with the next procedure
            
            # Commit the changes
            conn.commit()
            cursor.close()
            
            # Get the current count
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM procedures")
            total_count = cursor.fetchone()[0]
            cursor.close()
            
            logger.info(f"Current total procedures: {total_count}")
            
            return imported_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing procedures batch: {e}")
        return 0

def main():
    """Main function."""
    try:
        # Get the last imported index from a state file
        last_index = 0
        state_file = "import_state.txt"
        
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                last_index = int(f.read().strip())
        
        # Get database connection
        conn = get_db_connection()
        
        # Import a batch
        imported = import_procedures_batch(conn, last_index)
        
        # Update the state file
        with open(state_file, 'w') as f:
            f.write(str(last_index + imported))
        
        # Close connection
        conn.close()
        
        logger.info(f"Successfully imported {imported} procedures")
        logger.info(f"Next import will start from index {last_index + imported}")
        
        if imported == 0:
            logger.info("Import completed or no procedures to import")
        else:
            logger.info("Run this script again to import the next batch")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()