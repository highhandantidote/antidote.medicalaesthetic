#!/usr/bin/env python3
"""
Map CSV categories to database categories.

This script analyzes the CSV file and creates a mapping between CSV categories
and existing database categories to improve import success rate.
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

def analyze_csv_categories():
    """Analyze CSV file to extract all unique body parts and categories."""
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Collect unique body parts and categories
            body_parts = set()
            categories = {}  # body_part -> set of categories
            
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
            for bp in sorted(body_parts):
                cat_count = len(categories.get(bp, []))
                logger.info(f"  {bp}: {cat_count} categories")
            
            total_categories = sum(len(cats) for cats in categories.values())
            logger.info(f"Found {total_categories} unique body part/category combinations in CSV")
            
            return body_parts, categories
    except Exception as e:
        logger.error(f"Error analyzing CSV: {e}")
        raise

def get_db_structure(conn):
    """Get existing body parts and categories from the database."""
    cursor = conn.cursor()
    
    try:
        # Get body parts
        cursor.execute("SELECT id, name FROM body_parts")
        db_body_parts = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Get categories
        cursor.execute("""
            SELECT c.id, c.name, bp.id, bp.name
            FROM categories c
            JOIN body_parts bp ON c.body_part_id = bp.id
        """)
        
        db_categories = {}  # body_part_name -> {category_name: id}
        for row in cursor.fetchall():
            cat_id, cat_name, bp_id, bp_name = row
            
            if bp_name not in db_categories:
                db_categories[bp_name] = {}
                
            db_categories[bp_name][cat_name] = cat_id
        
        logger.info(f"Found {len(db_body_parts)} body parts in database")
        logger.info(f"Found {sum(len(cats) for cats in db_categories.values())} categories in database")
        
        return db_body_parts, db_categories
    except Exception as e:
        logger.error(f"Error getting database structure: {e}")
        raise
    finally:
        cursor.close()

def suggest_mapping(csv_body_parts, csv_categories, db_body_parts, db_categories):
    """Suggest mappings between CSV and DB categories."""
    # Map body parts first
    body_part_mapping = {}
    for csv_bp in csv_body_parts:
        # Try exact match
        if csv_bp in db_body_parts:
            body_part_mapping[csv_bp] = csv_bp
        else:
            # Try case-insensitive match
            matches = [db_bp for db_bp in db_body_parts if db_bp.lower() == csv_bp.lower()]
            if matches:
                body_part_mapping[csv_bp] = matches[0]
    
    logger.info(f"Matched {len(body_part_mapping)}/{len(csv_body_parts)} body parts")
    
    # Map categories
    category_mapping = {}  # (csv_bp, csv_cat) -> (db_bp, db_cat)
    
    for csv_bp, csv_cats in csv_categories.items():
        if csv_bp not in body_part_mapping:
            continue
            
        db_bp = body_part_mapping[csv_bp]
        db_cats = db_categories.get(db_bp, {})
        
        for csv_cat in csv_cats:
            # Try exact match
            if csv_cat in db_cats:
                category_mapping[(csv_bp, csv_cat)] = (db_bp, csv_cat)
            else:
                # Try various transformations
                normalizations = [
                    csv_cat.replace(' ', '_'),  # Replace spaces with underscores
                    csv_cat.replace('&', 'and'),  # Replace & with and
                    csv_cat.replace(' ', '_').replace('&', 'and')  # Both replacements
                ]
                
                matched = False
                for norm in normalizations:
                    if norm in db_cats:
                        category_mapping[(csv_bp, csv_cat)] = (db_bp, norm)
                        matched = True
                        break
                
                # If still no match, look for partial matches
                if not matched:
                    for db_cat in db_cats:
                        if (csv_cat.lower() in db_cat.lower() or 
                            db_cat.lower() in csv_cat.lower()):
                            category_mapping[(csv_bp, csv_cat)] = (db_bp, db_cat)
                            matched = True
                            break
    
    total_combos = sum(len(cats) for cats in csv_categories.values())
    matched_count = len(category_mapping)
    
    logger.info(f"Matched {matched_count}/{total_combos} category combinations")
    
    # Print unmatched categories
    logger.info("Unmatched categories:")
    for csv_bp, csv_cats in csv_categories.items():
        if csv_bp not in body_part_mapping:
            logger.info(f"  Body part not matched: {csv_bp}")
            continue
            
        for csv_cat in csv_cats:
            if (csv_bp, csv_cat) not in category_mapping:
                logger.info(f"  {csv_bp} -> {csv_cat}")
    
    return body_part_mapping, category_mapping

def main():
    """Main function."""
    try:
        # Analyze CSV
        csv_body_parts, csv_categories = analyze_csv_categories()
        
        # Get database structure
        conn = get_db_connection()
        db_body_parts, db_categories = get_db_structure(conn)
        
        # Suggest mappings
        body_part_mapping, category_mapping = suggest_mapping(
            csv_body_parts, csv_categories, db_body_parts, db_categories
        )
        
        # Close connection
        conn.close()
        
        logger.info("Category mapping analysis complete")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()