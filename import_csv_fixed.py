#!/usr/bin/env python3
"""
Import procedures from CSV file with improved matching.

This script imports procedures from the CSV file using existing body parts and categories,
with better category matching and error handling.
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
BATCH_SIZE = 5  # Small batch size for reliability

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

def create_mapping_tables(conn):
    """Create mapping for categories and body parts from CSV to database."""
    cursor = conn.cursor()
    
    # Get all body parts and categories from the database
    cursor.execute("SELECT id, name FROM body_parts")
    db_body_parts = {row[1].lower(): row[0] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT c.id, c.name, bp.name 
        FROM categories c
        JOIN body_parts bp ON c.body_part_id = bp.id
    """)
    db_categories = {}
    for row in cursor.fetchall():
        cat_id, cat_name, bp_name = row
        db_categories[f"{cat_name.lower()}__{bp_name.lower()}"] = cat_id
    
    # Read unique body parts and categories from the CSV
    body_parts_map = {}
    categories_map = {}
    
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # First pass: collect all unique body parts and categories
            csv_body_parts = set()
            csv_categories = set()
            
            for row in reader:
                bp = row.get('body_part_name', '').strip()
                cat = row.get('category_name', '').strip()
                
                if bp:
                    csv_body_parts.add(bp.lower())
                if bp and cat:
                    csv_categories.add((bp.lower(), cat.lower()))
            
            # Create mappings for body parts
            for csv_bp in csv_body_parts:
                # Try exact match
                if csv_bp in db_body_parts:
                    body_parts_map[csv_bp] = db_body_parts[csv_bp]
                    continue
                
                # Try normalized match (remove spaces, underscores)
                normalized_csv_bp = csv_bp.replace(' ', '').replace('_', '')
                for db_bp, db_bp_id in db_body_parts.items():
                    normalized_db_bp = db_bp.replace(' ', '').replace('_', '')
                    if normalized_csv_bp == normalized_db_bp:
                        body_parts_map[csv_bp] = db_bp_id
                        break
            
            # Create mappings for categories
            for csv_bp, csv_cat in csv_categories:
                if csv_bp not in body_parts_map:
                    continue
                
                # Try different combination formats for matching
                found = False
                
                # Format 1: category__bodypart
                key1 = f"{csv_cat}__{csv_bp}"
                if key1 in db_categories:
                    categories_map[(csv_bp, csv_cat)] = db_categories[key1]
                    found = True
                    continue
                
                # Format 2: normalize category name (replace spaces with underscores)
                normalized_cat = csv_cat.replace(' ', '_').replace('&', 'and')
                key2 = f"{normalized_cat}__{csv_bp}"
                if key2 in db_categories:
                    categories_map[(csv_bp, csv_cat)] = db_categories[key2]
                    found = True
                    continue
                
                # Format 3: partial matching
                if not found:
                    for db_key, db_id in db_categories.items():
                        db_cat, db_bp = db_key.split('__')
                        if db_bp == csv_bp and (csv_cat in db_cat or db_cat in csv_cat):
                            categories_map[(csv_bp, csv_cat)] = db_id
                            found = True
                            break
                
                # If still not found, try one more approach with more flexible matching
                if not found:
                    for db_key, db_id in db_categories.items():
                        db_cat, db_bp = db_key.split('__')
                        # Match if the normalized categories have significant overlap
                        norm_csv_cat = csv_cat.replace(' ', '').lower()
                        norm_db_cat = db_cat.replace(' ', '').lower()
                        if db_bp == csv_bp and (norm_csv_cat in norm_db_cat or norm_db_cat in norm_csv_cat):
                            categories_map[(csv_bp, csv_cat)] = db_id
                            break
    
    except Exception as e:
        logger.error(f"Error creating mapping tables: {e}")
        raise
    finally:
        cursor.close()
    
    logger.info(f"Mapped {len(body_parts_map)}/{len(csv_body_parts)} body parts and {len(categories_map)}/{len(csv_categories)} categories")
    
    return body_parts_map, categories_map

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
        # Create mappings for body parts and categories
        body_parts_map, categories_map = create_mapping_tables(conn)
        
        # Get existing procedures
        cursor = conn.cursor()
        cursor.execute("SELECT procedure_name FROM procedures")
        existing_procedures = set(row[0].lower() for row in cursor.fetchall())
        cursor.close()
        
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
                body_part_name = row.get('body_part_name', '').strip().lower()
                category_name = row.get('category_name', '').strip().lower()
                
                # Skip if procedure exists or missing required fields
                if not procedure_name:
                    logger.info(f"Skipping row {start_index+i+1}: Missing procedure name")
                    continue
                
                if procedure_name.lower() in existing_procedures:
                    logger.info(f"Skipping procedure: {procedure_name} (already exists)")
                    continue
                
                # Skip if body part or category mapping not found
                if body_part_name not in body_parts_map:
                    logger.warning(f"Skipping procedure: {procedure_name} (body part '{body_part_name}' not mapped)")
                    continue
                
                if (body_part_name, category_name) not in categories_map:
                    logger.warning(f"Skipping procedure: {procedure_name} (category '{category_name}' not mapped for body part '{body_part_name}')")
                    continue
                
                # Get the mapped IDs
                body_part_id = body_parts_map[body_part_name]
                category_id = categories_map[(body_part_name, category_name)]
                
                # Process numeric fields
                min_cost = clean_numeric_value(row.get('min_cost', ''))
                max_cost = clean_numeric_value(row.get('max_cost', ''))
                
                # Default values for required fields
                min_cost = min_cost if min_cost is not None else 50000
                max_cost = max_cost if max_cost is not None else 200000
                
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
                
                # Insert the procedure with a single transaction per procedure
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
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
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
                        body_part_name.title()  # Convert to title case for consistency
                    ))
                    
                    conn.commit()  # Commit each procedure separately
                    
                    imported_count += 1
                    existing_procedures.add(procedure_name.lower())
                    logger.info(f"Added procedure: {procedure_name}")
                except Exception as e:
                    conn.rollback()  # Rollback only this procedure
                    logger.error(f"Error adding procedure {procedure_name}: {e}")
                    # Continue with the next procedure
            
            cursor.close()
            
            # Get the current count
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM procedures")
            total_count = cursor.fetchone()[0]
            cursor.close()
            
            logger.info(f"Current total procedures: {total_count}")
            
            return imported_count
    except Exception as e:
        if 'conn' in locals() and conn:
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
        
        if imported == 0 and last_index > 0:
            logger.info("Import completed or no procedures to import")
        else:
            logger.info("Run this script again to import the next batch")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()