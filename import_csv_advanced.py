#!/usr/bin/env python3
"""
Advanced import script for procedures from CSV file with dynamic category mapping.

This script analyzes the CSV file, creates a mapping between CSV categories
and existing database categories, and imports procedures in batches.
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
BATCH_SIZE = 10  # Increased batch size for efficiency

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
        # Get body parts
        cursor.execute("SELECT id, name FROM body_parts")
        body_parts = {row[1].lower(): row[0] for row in cursor.fetchall()}
        
        # Get categories
        cursor.execute("""
            SELECT c.id, c.name, bp.name 
            FROM categories c
            JOIN body_parts bp ON c.body_part_id = bp.id
        """)
        categories = {}
        for row in cursor.fetchall():
            cat_id, cat_name, bp_name = row
            key = f"{cat_name.lower()}|{bp_name.lower()}"
            categories[key] = cat_id
        
        # Get existing procedures
        cursor.execute("SELECT procedure_name FROM procedures")
        procedures = set(row[0].lower() for row in cursor.fetchall())
        
        return body_parts, categories, procedures
    except Exception as e:
        logger.error(f"Error getting existing data: {e}")
        raise
    finally:
        cursor.close()

def create_mapping_tables(conn, csv_file_path):
    """Create mappings between CSV data and database."""
    body_parts_map = {}
    categories_map = {}
    
    # Get existing data
    db_body_parts, db_categories, _ = get_existing_data(conn)
    
    try:
        # Analysis phase - collect unique values
        csv_body_parts = set()
        csv_categories = {}  # body_part -> set of categories
        
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                bp = row.get('body_part_name', '').strip().lower()
                cat = row.get('category_name', '').strip().lower()
                
                if bp:
                    csv_body_parts.add(bp)
                    
                    if bp not in csv_categories:
                        csv_categories[bp] = set()
                    
                    if cat:
                        csv_categories[bp].add(cat)
        
        # Map body parts (case-insensitive)
        for csv_bp in csv_body_parts:
            # Try exact match
            if csv_bp in db_body_parts:
                body_parts_map[csv_bp] = db_body_parts[csv_bp]
            else:
                # Try normalized match (remove spaces, underscores)
                normalized_csv_bp = csv_bp.replace(' ', '').replace('_', '')
                for db_bp, db_bp_id in db_body_parts.items():
                    normalized_db_bp = db_bp.replace(' ', '').replace('_', '')
                    if normalized_csv_bp == normalized_db_bp:
                        body_parts_map[csv_bp] = db_bp_id
                        break
        
        # Map categories
        for csv_bp, cats in csv_categories.items():
            if csv_bp not in body_parts_map:
                continue
                
            bp_id = body_parts_map[csv_bp]
            
            for csv_cat in cats:
                matched = False
                
                # Try various matching strategies
                for db_key, db_cat_id in db_categories.items():
                    db_cat, db_bp = db_key.split('|')
                    
                    # Strategy 1: Direct match
                    if csv_cat == db_cat and csv_bp == db_bp:
                        categories_map[(csv_bp, csv_cat)] = db_cat_id
                        matched = True
                        break
                    
                    # Strategy 2: Contains match
                    if (csv_bp == db_bp and 
                        (csv_cat in db_cat or db_cat in csv_cat)):
                        categories_map[(csv_bp, csv_cat)] = db_cat_id
                        matched = True
                        break
                    
                    # Strategy 3: Normalized match
                    norm_csv_cat = csv_cat.replace(' ', '').replace('&', 'and').lower()
                    norm_db_cat = db_cat.replace(' ', '').replace('&', 'and').lower()
                    if csv_bp == db_bp and (norm_csv_cat in norm_db_cat or norm_db_cat in norm_csv_cat):
                        categories_map[(csv_bp, csv_cat)] = db_cat_id
                        matched = True
                        break
                
                # Custom mappings based on knowledge of the data
                if not matched:
                    # Define custom mappings for specific categories
                    custom_mappings = {
                        ('butt', 'hip & butt enhancement'): ('butt', 'butt_enhancement'),
                        ('eyes', 'eyelid enhancement'): ('eyes', 'eyelid_surgery'),
                        ('stomach', 'body contouring'): ('body', 'body_contouring'),
                        ('breast', 'gender confirmation surgery'): ('breast', 'breast_surgery'),
                        ('face', 'fillers and other injectables'): ('face', 'fillers_and_injectables')
                    }
                    
                    for (c_bp, c_cat), (d_bp, d_cat) in custom_mappings.items():
                        if csv_bp == c_bp and csv_cat == c_cat:
                            # Look up the database ID for this mapping
                            key = f"{d_cat}|{d_bp}"
                            if key in db_categories:
                                categories_map[(csv_bp, csv_cat)] = db_categories[key]
                                matched = True
                                break
        
        logger.info(f"Mapped {len(body_parts_map)}/{len(csv_body_parts)} body parts")
        logger.info(f"Mapped {len(categories_map)}/{sum(len(cats) for cats in csv_categories.values())} categories")
        
        return body_parts_map, categories_map
    except Exception as e:
        logger.error(f"Error creating mapping tables: {e}")
        raise

def clean_numeric_value(value_str):
    """Clean and convert numeric values from the CSV."""
    if not value_str:
        return None
    
    # Remove commas, currency symbols, and other non-numeric characters
    digits_only = ''.join(c for c in value_str if c.isdigit())
    
    if digits_only:
        return int(digits_only)
    
    return None

def import_procedures_batch(conn, start_index, csv_file_path):
    """Import a batch of procedures from the CSV file."""
    imported_count = 0
    updated_count = 0
    
    try:
        # Create mappings
        body_parts_map, categories_map = create_mapping_tables(conn, csv_file_path)
        
        # Get existing procedures for deduplication
        _, _, existing_procedures = get_existing_data(conn)
        
        # Read the CSV file
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            
            # Check if we've reached the end
            if start_index >= len(rows):
                logger.info("Reached the end of the CSV file")
                return 0, 0
            
            # Process a batch of rows
            end_index = min(start_index + BATCH_SIZE, len(rows))
            batch = rows[start_index:end_index]
            
            logger.info(f"Processing procedures {start_index+1} to {end_index} of {len(rows)}")
            
            cursor = conn.cursor()
            
            for i, row in enumerate(batch):
                procedure_name = row.get('procedure_name', '').strip()
                body_part_name = row.get('body_part_name', '').strip().lower()
                category_name = row.get('category_name', '').strip().lower()
                
                # Skip if missing required fields
                if not procedure_name:
                    logger.info(f"Skipping row {start_index+i+1}: Missing procedure name")
                    continue
                
                # Skip if procedure exists
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
                    
                    conn.commit()
                    
                    imported_count += 1
                    existing_procedures.add(procedure_name.lower())
                    logger.info(f"Added procedure: {procedure_name}")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Error adding procedure {procedure_name}: {e}")
            
            cursor.close()
            
            return imported_count, updated_count
    except Exception as e:
        logger.error(f"Error importing procedures batch: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return 0, 0

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
        imported, updated = import_procedures_batch(conn, last_index, CSV_FILE_PATH)
        
        # Update the state file if we imported any
        if imported > 0:
            with open(state_file, 'w') as f:
                f.write(str(last_index + BATCH_SIZE))
        
        # Close connection
        conn.close()
        
        # Get current total
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM procedures")
        total = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully imported {imported} procedures")
        logger.info(f"Current total procedures: {total}")
        logger.info(f"Next import will start from index {last_index + BATCH_SIZE}")
        
        if imported == 0 and last_index > 0:
            logger.info("Import may be complete. Check logs for details.")
        else:
            logger.info("Run this script again to import the next batch")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()