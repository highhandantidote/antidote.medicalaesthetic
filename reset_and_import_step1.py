#!/usr/bin/env python3
"""
Reset and import body parts and categories from CSV file.

Step 1: Reset database and import body parts and categories.
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
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
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
        
        # Write the category mappings to a file for step 2
        with open('category_mappings.txt', 'w') as f:
            for (bp, cat), cat_id in category_ids.items():
                f.write(f"{bp}|{cat}|{cat_id}\n")
        
        logger.info(f"Wrote {len(category_ids)} category mappings to category_mappings.txt")
        
        return category_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing categories: {e}")
        raise
    finally:
        cursor.close()

def main():
    """Main function."""
    try:
        # Verify CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            logger.error(f"CSV file not found: {CSV_FILE_PATH}")
            sys.exit(1)
        
        # Extract unique data from CSV
        body_parts, categories = extract_unique_data(CSV_FILE_PATH)
        
        # Get database connection
        conn = get_db_connection()
        
        # Reset database
        reset_database(conn)
        
        # Import body parts
        body_part_ids = import_body_parts(conn, body_parts)
        
        # Import categories
        category_ids = import_categories(conn, categories, body_part_ids)
        
        # Close connection
        conn.close()
        
        logger.info(f"Step 1 complete: {len(body_part_ids)} body parts, {len(category_ids)} categories")
        logger.info("Run import_procedures.py to import procedures (Step 2)")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()