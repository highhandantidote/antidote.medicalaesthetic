#!/usr/bin/env python3
"""
Import all procedures from attached CSV file.

This script reads the CSV file and imports all procedures, creating necessary
body parts and categories as needed.
"""

import os
import csv
import logging
import psycopg2
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CSV_FILE_PATH = 'attached_assets/new_procedure_details - Sheet1.csv'
BATCH_SIZE = 20  # Process 20 procedures at a time to avoid timeouts

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def reset_database():
    """Reset the database by removing all existing entries."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if there are any dependencies on procedures
        cursor.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE column_name = 'procedure_id'
            AND table_schema = 'public';
        """)
        dependencies = cursor.fetchall()
        
        # Delete from dependent tables first to avoid FK constraint errors
        for table, column in dependencies:
            logger.info(f"Clearing dependent table: {table}")
            cursor.execute(f"DELETE FROM {table}")
        
        # Delete all procedures
        logger.info("Deleting all procedures...")
        cursor.execute("DELETE FROM procedures")
        
        # Delete all categories
        logger.info("Deleting all categories...")
        cursor.execute("DELETE FROM categories")
        
        # Delete all body parts
        logger.info("Deleting all body parts...")
        cursor.execute("DELETE FROM body_parts")
        
        # Reset sequences
        cursor.execute("ALTER SEQUENCE procedures_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE categories_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE body_parts_id_seq RESTART WITH 1")
        
        conn.commit()
        logger.info("Database reset successful")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error resetting database: {e}")
    finally:
        cursor.close()
        conn.close()

def extract_unique_data():
    """Extract unique body parts and categories from CSV."""
    body_parts = set()
    categories = {}  # body_part -> set of categories
    
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                bp = row.get('body_part_name', '').strip()
                cat = row.get('category_name', '').strip()
                
                if bp:
                    body_parts.add(bp)
                    
                    if bp not in categories:
                        categories[bp] = set()
                    
                    if cat:
                        categories[bp].add(cat)
        
        logger.info(f"Found {len(body_parts)} unique body parts in CSV")
        logger.info(f"Found {sum(len(cats) for cats in categories.values())} unique categories in CSV")
        
        return body_parts, categories
    except Exception as e:
        logger.error(f"Error extracting unique data from CSV: {e}")
        raise

def add_body_parts(body_parts):
    """Add body parts to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    body_part_ids = {}
    
    try:
        logger.info("Adding body parts...")
        for bp in sorted(body_parts):
            cursor.execute("""
                INSERT INTO body_parts (name, description, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id
            """, (bp, f"Body part: {bp}"))
            
            bp_id = cursor.fetchone()[0]
            body_part_ids[bp] = bp_id
            logger.info(f"Added body part: {bp} (ID: {bp_id})")
        
        conn.commit()
        logger.info(f"Added {len(body_part_ids)} body parts")
        return body_part_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding body parts: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def add_categories(categories, body_part_ids):
    """Add categories to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    category_ids = {}
    
    try:
        logger.info("Adding categories...")
        for bp, cats in categories.items():
            bp_id = body_part_ids.get(bp)
            if not bp_id:
                logger.warning(f"Body part '{bp}' not found in database")
                continue
            
            for cat in sorted(cats):
                cursor.execute("""
                    INSERT INTO categories (name, body_part_id, description, popularity_score, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id
                """, (cat, bp_id, f"Category for {cat} procedures", 5))
                
                cat_id = cursor.fetchone()[0]
                category_ids[(bp, cat)] = cat_id
                logger.info(f"Added category: {cat} under {bp} (ID: {cat_id})")
        
        conn.commit()
        logger.info(f"Added {len(category_ids)} categories")
        return category_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding categories: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def clean_numeric_value(value_str):
    """Clean and convert numeric values from the CSV."""
    if not value_str:
        return None
    
    # Remove commas, currency symbols, and other non-numeric characters
    value_str = str(value_str)
    digits_only = ''.join(c for c in value_str if c.isdigit())
    
    if digits_only:
        return int(digits_only)
    
    return None

def add_procedures_batch(start_idx, body_part_ids, category_ids):
    """Add a batch of procedures to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    
    try:
        # Read CSV and extract procedures
        procedures = []
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            procedures = list(reader)
        
        # Check if we've reached the end
        if start_idx >= len(procedures):
            logger.info("All procedures have been imported")
            return 0, True
        
        # Get batch
        end_idx = min(start_idx + BATCH_SIZE, len(procedures))
        batch = procedures[start_idx:end_idx]
        
        logger.info(f"Processing procedures {start_idx+1} to {end_idx} of {len(procedures)}")
        
        # Process each procedure
        for row in batch:
            procedure_name = row.get('procedure_name', '').strip()
            body_part_name = row.get('body_part_name', '').strip()
            category_name = row.get('category_name', '').strip()
            
            # Skip if missing required fields
            if not procedure_name or not body_part_name or not category_name:
                logger.warning(f"Skipping row: Missing required fields")
                continue
            
            # Get IDs
            body_part_id = body_part_ids.get(body_part_name)
            if not body_part_id:
                logger.warning(f"Body part '{body_part_name}' not found. Skipping {procedure_name}")
                continue
            
            category_id = category_ids.get((body_part_name, category_name))
            if not category_id:
                logger.warning(f"Category '{category_name}' not found for body part '{body_part_name}'. Skipping {procedure_name}")
                continue
            
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
            
            # Extract tags
            tags = row.get('tags', '').strip()
            
            # Set procedure types
            procedure_types = row.get('procedure_types', '').strip()
            if not procedure_types:
                procedure_types = "Standard procedure"
            
            # Determine body area
            body_area = body_part_name.lower()
            if body_area in ["face", "neck", "eyes", "nose", "lips", "chin", "jawline", "eyebrows", "ears"]:
                body_area = "Face"
            elif body_area in ["breasts", "chest"]:
                body_area = "Breasts"
            elif body_area in ["stomach", "abdomen", "butt", "hips", "waist", "back"]:
                body_area = "Body"
            elif body_area in ["arms", "legs", "hands", "feet"]:
                body_area = "Extremities"
            elif "genital" in body_area:
                body_area = "Intimate Areas"
            else:
                body_area = "Other"
            
            # Determine category type
            category_type = "Surgical"
            if any(term in category_name.lower() or term in procedure_name.lower() 
                   for term in ["filler", "injectable", "non-surgical", "botox", "laser"]):
                category_type = "Non-Surgical"
            
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
                    body_part,
                    body_area,
                    category_type,
                    category_id,
                    created_at,
                    updated_at,
                    popularity_score,
                    avg_rating,
                    review_count,
                    tags
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s, %s
                )
                """, (
                    procedure_name,
                    row.get('alternative_names', ''),
                    short_description,
                    overview,
                    procedure_details,
                    ideal_candidates,
                    row.get('recovery_process', 'Standard recovery process'),
                    recovery_time,
                    row.get('procedure_duration', '1-2 hours'),
                    row.get('hospital_stay_required', 'No'),
                    row.get('results_duration', 'Results vary by individual'),
                    min_cost,
                    max_cost,
                    row.get('benefits', 'Improved appearance and confidence'),
                    row.get('benefits_detailed', 'Enhanced aesthetics and self-image'),
                    risks,
                    procedure_types,
                    row.get('alternative_procedures', 'Various alternatives available'),
                    body_part_name, 
                    body_area,
                    category_type,
                    category_id,
                    5,  # popularity_score
                    0,  # avg_rating
                    0,   # review_count
                    tags
                ))
                
                count += 1
                logger.info(f"Added procedure: {procedure_name}")
            except Exception as e:
                logger.error(f"Error adding procedure {procedure_name}: {e}")
                # Continue with next procedure
        
        conn.commit()
        logger.info(f"Added {count} procedures in this batch")
        
        # Check if we've reached the end
        is_complete = end_idx >= len(procedures)
        
        return count, is_complete
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in batch processing: {e}")
        return 0, False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to execute the import process."""
    try:
        logger.info("Starting CSV import process")
        
        # Extract unique data
        body_parts, categories = extract_unique_data()
        
        # Reset database
        reset_database()
        
        # Add body parts
        body_part_ids = add_body_parts(body_parts)
        
        # Add categories
        category_ids = add_categories(categories, body_part_ids)
        
        # Add procedures in batches
        start_idx = 0
        total_imported = 0
        is_complete = False
        
        while not is_complete:
            count, is_complete = add_procedures_batch(start_idx, body_part_ids, category_ids)
            total_imported += count
            start_idx += BATCH_SIZE
            logger.info(f"Total procedures imported so far: {total_imported}")
        
        logger.info(f"Import complete: {len(body_part_ids)} body parts, {len(category_ids)} categories, {total_imported} procedures")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()