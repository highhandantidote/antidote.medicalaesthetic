#!/usr/bin/env python
"""
Check import progress against CSV data.
"""
import csv
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    return conn

def count_procedures_in_db():
    """Count procedures in the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            count = cursor.fetchone()[0]
            return count

def count_csv_entries():
    """Count entries in the CSV file."""
    total_rows = 0
    duplicate_names = set()
    procedure_names = set()
    
    with open("attached_assets/new_procedure_details - Sheet1.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            procedure_name = row.get("Name", "").strip()
            if procedure_name:
                total_rows += 1
                if procedure_name in procedure_names:
                    duplicate_names.add(procedure_name)
                procedure_names.add(procedure_name)
    
    unique_procedures = len(procedure_names)
    duplicates = len(duplicate_names)
    
    return {
        "total_rows": total_rows,
        "unique_procedures": unique_procedures,
        "duplicates": duplicates,
        "duplicate_names": sorted(list(duplicate_names))
    }

def main():
    """Check import progress."""
    logger.info("Checking import progress...")
    
    # Get database counts
    db_count = count_procedures_in_db()
    logger.info(f"Total procedures in database: {db_count}")
    
    # Get CSV counts
    csv_info = count_csv_entries()
    logger.info(f"Total rows in CSV: {csv_info['total_rows']}")
    logger.info(f"Unique procedure names in CSV: {csv_info['unique_procedures']}")
    logger.info(f"Duplicate procedure names in CSV: {csv_info['duplicates']}")
    
    # Calculate import percentage
    target_count = csv_info['unique_procedures']
    import_percentage = (db_count / target_count) * 100 if target_count > 0 else 0
    logger.info(f"Import progress: {db_count}/{target_count} procedures ({import_percentage:.1f}%)")
    
    # Display duplicate names
    logger.info("Duplicate procedure names found in CSV:")
    for name in csv_info['duplicate_names']:
        logger.info(f"  - {name}")
    
    logger.info("Check complete.")

if __name__ == "__main__":
    main()