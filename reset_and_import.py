#!/usr/bin/env python3
"""
Reset categories, body parts, and procedures and import fresh data from CSV.

This script:
1. Removes all existing procedures, categories, and body parts
2. Imports all the body parts from the CSV
3. Creates categories under the appropriate body parts
4. Imports procedures with their appropriate relationships
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
CSV_FILE_PATH = 'attached_assets/new_procedure_details - Sheet1.csv'
BATCH_SIZE = 20  # Higher batch size for efficiency

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

def reset_database(conn):
    """Remove all procedures, categories, and body parts."""
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
        raise
    finally:
        cursor.close()

def extract_unique_data(csv_path):
    """Extract unique body parts and categories from CSV."""
    body_parts = set()
    categories = {}  # body_part -> set of categories
    procedures = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                bp = row.get('body_part_name', '').strip()
                cat = row.get('category_name', '').strip()
                proc = row.get('procedure_name', '').strip()
                
                if bp:
                    body_parts.add(bp)
                    
                    if bp not in categories:
                        categories[bp] = set()
                    
                    if cat:
                        categories[bp].add(cat)
                    
                    if proc:
                        procedures.append(row)
            
        logger.info(f"Found {len(body_parts)} unique body parts in CSV")
        logger.info(f"Found {sum(len(cats) for cats in categories.values())} unique categories in CSV")
        logger.info(f"Found {len(procedures)} procedures in CSV")
        
        return body_parts, categories, procedures
    except Exception as e:
        logger.error(f"Error extracting unique data from CSV: {e}")
        raise

def import_body_parts(conn, body_parts):
    """Import body parts into the database."""
    cursor = conn.cursor()
    body_part_ids = {}
    
    try:
        logger.info("Importing body parts...")
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
        return body_part_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing body parts: {e}")
        raise
    finally:
        cursor.close()

def import_categories(conn, categories, body_part_ids):
    """Import categories into the database."""
    cursor = conn.cursor()
    category_ids = {}
    
    try:
        logger.info("Importing categories...")
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
        return category_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing categories: {e}")
        raise
    finally:
        cursor.close()

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

def import_procedures(conn, procedures, category_ids, batch_size=BATCH_SIZE):
    """Import procedures into the database in batches."""
    total_imported = 0
    total_batches = (len(procedures) + batch_size - 1) // batch_size
    
    try:
        logger.info(f"Importing {len(procedures)} procedures in {total_batches} batches...")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(procedures))
            batch = procedures[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num+1}/{total_batches} ({start_idx+1}-{end_idx} of {len(procedures)})")
            
            cursor = conn.cursor()
            imported_in_batch = 0
            
            for row in batch:
                procedure_name = row.get('procedure_name', '').strip()
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                
                # Skip if missing required fields
                if not procedure_name or not body_part_name or not category_name:
                    logger.warning(f"Skipping procedure: {procedure_name} (missing required fields)")
                    continue
                
                # Get category ID
                category_id = category_ids.get((body_part_name, category_name))
                if not category_id:
                    logger.warning(f"Skipping procedure: {procedure_name} (category '{category_name}' under '{body_part_name}' not found)")
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
                
                procedure_types = row.get('procedure_types', '').strip()
                if not procedure_types:
                    procedure_types = "Standard procedure"
                
                # Extract tags
                tags = row.get('tags', '').strip()
                
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
                if any(term in category_name.lower() for term in ["filler", "injectable", "non-surgical", "botox", "laser"]):
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
                        category_id,
                        body_part,
                        created_at,
                        updated_at,
                        tags,
                        body_area,
                        category_type,
                        popularity_score,
                        avg_rating,
                        review_count
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s, %s, %s, %s
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
                        body_part_name,  # Store original body part name
                        tags,
                        body_area,
                        category_type,
                        5,  # Default popularity score
                        0,  # Default avg_rating
                        0   # Default review_count
                    ))
                    
                    imported_in_batch += 1
                    logger.info(f"Added procedure: {procedure_name}")
                except Exception as e:
                    logger.error(f"Error adding procedure {procedure_name}: {e}")
                    # Continue with next procedure, don't break the batch
            
            conn.commit()
            cursor.close()
            
            total_imported += imported_in_batch
            logger.info(f"Batch {batch_num+1} complete: imported {imported_in_batch} procedures")
        
        return total_imported
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        logger.error(f"Error importing procedures: {e}")
        raise

def main():
    """Main function."""
    try:
        # Verify CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            logger.error(f"CSV file not found: {CSV_FILE_PATH}")
            sys.exit(1)
        
        # Extract unique data from CSV
        body_parts, categories, procedures = extract_unique_data(CSV_FILE_PATH)
        
        # Get database connection
        conn = get_db_connection()
        
        # Reset database
        reset_database(conn)
        
        # Import body parts
        body_part_ids = import_body_parts(conn, body_parts)
        
        # Import categories
        category_ids = import_categories(conn, categories, body_part_ids)
        
        # Import procedures
        total_imported = import_procedures(conn, procedures, category_ids)
        
        # Close connection
        conn.close()
        
        logger.info(f"Import complete: {len(body_part_ids)} body parts, {len(category_ids)} categories, {total_imported} procedures")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()