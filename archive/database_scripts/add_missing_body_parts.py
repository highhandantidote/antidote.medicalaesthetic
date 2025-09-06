#!/usr/bin/env python3
"""
Add missing body parts from the CSV file.

This script adds all the body parts mentioned in the CSV file
that aren't already in the database.
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

def extract_unique_body_parts():
    """Extract unique body parts from CSV."""
    body_parts = set()
    
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                bp = row.get('body_part_name', '').strip()
                
                if bp:
                    body_parts.add(bp)
        
        logger.info(f"Found {len(body_parts)} unique body parts in CSV")
        return body_parts
    except Exception as e:
        logger.error(f"Error extracting unique body parts from CSV: {e}")
        raise

def add_missing_body_parts():
    """Add missing body parts to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get existing body parts
        cursor.execute("SELECT name FROM body_parts")
        existing_body_parts = set(row[0] for row in cursor.fetchall())
        
        # Get body parts from CSV
        all_body_parts = extract_unique_body_parts()
        
        # Find missing body parts
        missing_body_parts = all_body_parts - existing_body_parts
        
        logger.info(f"Found {len(existing_body_parts)} existing body parts")
        logger.info(f"Need to add {len(missing_body_parts)} missing body parts")
        
        # Add missing body parts
        for bp in sorted(missing_body_parts):
            cursor.execute("""
                INSERT INTO body_parts (name, description, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id
            """, (bp, f"Body part for {bp} procedures"))
            
            bp_id = cursor.fetchone()[0]
            logger.info(f"Added body part: {bp} (ID: {bp_id})")
        
        conn.commit()
        logger.info(f"Added {len(missing_body_parts)} missing body parts successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding missing body parts: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function."""
    try:
        logger.info("Starting body parts import")
        add_missing_body_parts()
        logger.info("Body parts import complete")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()