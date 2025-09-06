#!/usr/bin/env python3
"""
Step 2: Continue importing categories from the CSV file.

This script picks up where the previous one left off,
adding the categories after the body parts were already created.
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

def add_categories(categories):
    """Add categories to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    category_ids = {}
    
    try:
        # Get body part IDs
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
        
        logger.info("Adding categories...")
        added_count = 0
        
        for bp, cats in categories.items():
            bp_id = body_part_ids.get(bp)
            if not bp_id:
                logger.warning(f"Body part '{bp}' not found in database")
                continue
            
            for cat in sorted(cats):
                # Skip if category already exists
                if (cat, bp) in existing_categories:
                    logger.info(f"Category '{cat}' under '{bp}' already exists. Skipping.")
                    category_ids[(bp, cat)] = existing_categories[(cat, bp)]
                    continue
                
                cursor.execute("""
                    INSERT INTO categories (name, body_part_id, description, popularity_score, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id
                """, (cat, bp_id, f"Category for {cat} procedures", 5))
                
                cat_id = cursor.fetchone()[0]
                category_ids[(bp, cat)] = cat_id
                added_count += 1
                logger.info(f"Added category: {cat} under {bp} (ID: {cat_id})")
        
        conn.commit()
        logger.info(f"Added {added_count} new categories, total categories mapped: {len(category_ids)}")
        
        # Save category mappings for next step
        with open('category_mappings.csv', 'w', encoding='utf-8') as f:
            f.write("body_part,category,category_id\n")
            for (bp, cat), cat_id in category_ids.items():
                f.write(f'"{bp}","{cat}",{cat_id}\n')
        
        logger.info(f"Saved category mappings to category_mappings.csv")
        
        return category_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding categories: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to execute the category import."""
    try:
        logger.info("Starting category import (Step 2)")
        
        # Extract unique categories
        categories = extract_unique_categories()
        
        # Add categories
        category_ids = add_categories(categories)
        
        logger.info(f"Category import complete: {len(category_ids)} categories mapped")
        logger.info("Run step 3 to import procedures")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()