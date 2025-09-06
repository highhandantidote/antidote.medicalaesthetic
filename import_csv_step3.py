#!/usr/bin/env python3
"""
Step 3: Import procedures from CSV in batches.

This script reads category mappings from step 2 and imports
procedures in batches to avoid timeouts.
"""

import os
import csv
import logging
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CSV_FILE_PATH = "attached_assets/new_procedure_details - Sheet1.csv"
BATCH_SIZE = 10  # Process 10 procedures at a time to avoid timeouts

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def load_category_mappings():
    """Load category mappings from CSV file."""
    category_ids = {}
    
    try:
        with open('category_mappings.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bp = row['body_part']
                cat = row['category']
                cat_id = int(row['category_id'])
                category_ids[(bp, cat)] = cat_id
        
        logger.info(f"Loaded {len(category_ids)} category mappings")
        return category_ids
    except Exception as e:
        logger.error(f"Error loading category mappings: {e}")
        return {}

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

def get_import_progress():
    """Get the current import progress from file."""
    try:
        with open('import_progress.txt', 'r') as f:
            return int(f.read().strip())
    except:
        return 0

def save_import_progress(index):
    """Save the current import progress to file."""
    with open('import_progress.txt', 'w') as f:
        f.write(str(index))

def add_procedures_batch(category_ids):
    """Add a batch of procedures to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    
    try:
        # Get existing procedures
        cursor.execute("SELECT procedure_name FROM procedures")
        existing_procedures = set(row[0].lower() for row in cursor.fetchall())
        logger.info(f"Found {len(existing_procedures)} existing procedures")
        
        # Read CSV and extract procedures
        procedures = []
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            procedures = list(reader)
        
        # Get current progress
        start_idx = get_import_progress()
        
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
            
            # Skip if procedure already exists
            if procedure_name.lower() in existing_procedures:
                logger.info(f"Procedure '{procedure_name}' already exists. Skipping.")
                continue
            
            # Get category ID
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
                existing_procedures.add(procedure_name.lower())
                logger.info(f"Added procedure: {procedure_name}")
            except Exception as e:
                logger.error(f"Error adding procedure {procedure_name}: {e}")
                # Continue with next procedure
        
        conn.commit()
        logger.info(f"Added {count} procedures in this batch")
        
        # Save progress
        save_import_progress(end_idx)
        
        # Check if we've reached the end
        is_complete = end_idx >= len(procedures)
        if is_complete:
            logger.info("All procedures processed!")
        
        return count, is_complete
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in batch processing: {e}")
        return 0, False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to execute the procedure import."""
    try:
        logger.info("Starting procedure import (Step 3)")
        
        # Load category mappings
        category_ids = load_category_mappings()
        if not category_ids:
            logger.error("No category mappings found. Run Step 2 first.")
            return
        
        # Add procedures in batch
        count, is_complete = add_procedures_batch(category_ids)
        
        # Get total count
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM procedures")
        total_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        logger.info(f"Added {count} procedures (total in database: {total_count})")
        
        if is_complete:
            logger.info("Import process completed!")
        else:
            progress = get_import_progress()
            logger.info(f"Run this script again to continue from index {progress}")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()