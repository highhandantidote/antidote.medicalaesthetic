#!/usr/bin/env python3
"""
Find procedures in the CSV that are not yet in the database.
This script identifies which procedures from the CSV file are not yet imported.
"""

import os
import csv
import logging
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
PROCEDURES_CSV = 'attached_assets/new_procedure_details - Sheet1.csv'

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def find_missing_procedures():
    """Find procedures in the CSV that are not yet in the database."""
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database")
        return

    try:
        # Get all existing procedure names from the database
        existing_names = set()
        with conn.cursor() as cur:
            cur.execute("SELECT procedure_name FROM procedures")
            for row in cur.fetchall():
                existing_names.add(row[0].lower())  # Lowercase for case-insensitive comparison
        
        logger.info(f"Found {len(existing_names)} existing procedures in the database")
        
        # Read all procedures from the CSV and find missing ones
        missing_procedures = []
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for index, row in enumerate(reader):
                procedure_name = row['procedure_name'].strip()
                body_part = row['body_part'].strip()
                
                if procedure_name.lower() not in existing_names:
                    missing_procedures.append({
                        'index': index,
                        'name': procedure_name,
                        'body_part': body_part
                    })
        
        # Print missing procedures
        logger.info(f"Found {len(missing_procedures)} procedures in CSV that are not in the database")
        logger.info("First 20 missing procedures:")
        for i, proc in enumerate(missing_procedures[:20]):
            logger.info(f"{i+1}. {proc['name']} (Body Part: {proc['body_part']}, CSV Index: {proc['index']})")

        # Group missing procedures by body part
        by_body_part = {}
        for proc in missing_procedures:
            bp = proc['body_part']
            if bp not in by_body_part:
                by_body_part[bp] = []
            by_body_part[bp].append(proc)
        
        logger.info("\nMissing procedures by body part:")
        for bp, procs in by_body_part.items():
            logger.info(f"{bp}: {len(procs)} procedures")
            
        # Suggest starting positions for imports
        logger.info("\nSuggested starting positions for batch imports:")
        for i in range(0, min(len(missing_procedures), 100), 5):
            start_index = missing_procedures[i]['index']
            logger.info(f"Batch {i//5 + 1}: start_index = {start_index} (Procedure: {missing_procedures[i]['name']})")
            
    except Exception as e:
        logger.error(f"Error finding missing procedures: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    find_missing_procedures()