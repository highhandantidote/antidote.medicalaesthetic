#!/usr/bin/env python3
"""
Add categories from the CSV file in batches.

This script adds categories in smaller batches to avoid timeouts.
"""

import os
import csv
import logging
import psycopg2
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CSV_FILE_PATH = "attached_assets/new_procedure_details - Sheet1.csv"
BATCH_SIZE = 10  # Process 10 categories at a time

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def extract_unique_categories():
    """Extract unique categories from CSV grouped by body part."""
    categories = {}  # body_part -> set of categories
    
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                bp = row.get('body_part_name', '').strip()
                cat = row.get('category_name', '').strip()
                
                if bp and cat:
                    if bp not in categories:
                        categories[bp] = set()
                    categories[bp].add(cat)
        
        total_categories = sum(len(cats) for cats in categories.values())
        logger.info(f"Found {len(categories)} body parts with {total_categories} unique categories in CSV")
        
        return categories
    except Exception as e:
        logger.error(f"Error extracting unique categories from CSV: {e}")
        raise

def get_category_progress():
    """Get the current category import progress."""
    try:
        with open('category_progress.txt', 'r') as f:
            bp_name = f.readline().strip()
            cat_name = f.readline().strip()
            return bp_name, cat_name
    except:
        return None, None  # Start from the beginning

def save_category_progress(bp_name, cat_name):
    """Save the current category import progress."""
    with open('category_progress.txt', 'w') as f:
        f.write(f"{bp_name}\n{cat_name}\n")

def add_categories_batch():
    """Add a batch of categories to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all body parts
        cursor.execute("SELECT id, name FROM body_parts")
        body_part_ids = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Get existing categories
        cursor.execute("""
            SELECT c.name, bp.name, c.id
            FROM categories c
            JOIN body_parts bp ON c.body_part_id = bp.id
        """)
        existing_categories = {(cat_name, bp_name): cat_id for cat_name, bp_name, cat_id in cursor.fetchall()}
        
        logger.info(f"Found {len(body_part_ids)} body parts and {len(existing_categories)} existing categories in database")
        
        # Get categories from CSV
        all_categories = extract_unique_categories()
        
        # Get current progress
        progress_bp, progress_cat = get_category_progress()
        
        # Flatten categories for batch processing
        flat_categories = []
        for bp, cats in all_categories.items():
            for cat in sorted(cats):
                flat_categories.append((bp, cat))
        
        # Find starting index
        start_idx = 0
        if progress_bp and progress_cat:
            for i, (bp, cat) in enumerate(flat_categories):
                if bp == progress_bp and cat == progress_cat:
                    start_idx = i + 1  # Start from the next one
                    break
        
        logger.info(f"Starting from index {start_idx} of {len(flat_categories)}")
        
        # Process batch
        end_idx = min(start_idx + BATCH_SIZE, len(flat_categories))
        batch = flat_categories[start_idx:end_idx]
        
        logger.info(f"Processing categories {start_idx+1} to {end_idx} of {len(flat_categories)}")
        
        added_count = 0
        for bp, cat in batch:
            bp_id = body_part_ids.get(bp)
            if not bp_id:
                logger.warning(f"Body part '{bp}' not found in database")
                continue
            
            # Skip if category already exists
            if (cat, bp) in existing_categories:
                logger.info(f"Category '{cat}' under '{bp}' already exists. Skipping.")
                continue
            
            # Create a unique internal name
            unique_name = f"{bp}_{cat}"
            
            try:
                cursor.execute("""
                    INSERT INTO categories (name, display_name, body_part_id, description, popularity_score, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    RETURNING id
                """, (unique_name, cat, bp_id, f"Category for {cat} procedures", 5))
                
                cat_id = cursor.fetchone()[0]
                added_count += 1
                logger.info(f"Added category: {cat} under {bp} (ID: {cat_id})")
            except Exception as e:
                logger.error(f"Error adding category '{cat}' under '{bp}': {e}")
                # Try with an even more unique name
                try:
                    more_unique_name = f"{bp}_{cat}_{added_count}"
                    cursor.execute("""
                        INSERT INTO categories (name, display_name, body_part_id, description, popularity_score, created_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        RETURNING id
                    """, (more_unique_name, cat, bp_id, f"Category for {cat} procedures", 5))
                    
                    cat_id = cursor.fetchone()[0]
                    added_count += 1
                    logger.info(f"Added category with alternate name: {cat} under {bp} (ID: {cat_id})")
                except Exception as e2:
                    logger.error(f"Failed to add category '{cat}' under '{bp}' even with alternate name: {e2}")
                    # Continue with next category
        
        conn.commit()
        logger.info(f"Added {added_count} new categories in this batch")
        
        # Save progress
        if end_idx < len(flat_categories):
            next_bp, next_cat = flat_categories[end_idx]
            save_category_progress(next_bp, next_cat)
            logger.info(f"Saved progress: {next_bp}, {next_cat}")
            return False  # Not complete
        else:
            logger.info("All categories processed!")
            return True  # Complete
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding categories: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function."""
    try:
        logger.info("Starting category import batch")
        is_complete = add_categories_batch()
        
        if is_complete:
            logger.info("Category import complete")
        else:
            logger.info("Run this script again to continue importing categories")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()