#!/usr/bin/env python3
"""
Skip to the next batch of records that need to be imported.

This script reads the CSV files and updates the checkpoint files
to skip over entries that are already in the database.
"""

import os
import csv
import logging
import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROCEDURES_CSV_PATH = "./attached_assets/new_procedure_details - Sheet1.csv"
DOCTORS_CSV_PATH = "./attached_assets/new_doctors_profiles2 - Sheet1.csv"
PROCEDURE_START_ROW = 420  # Skip ahead to find more unique entries
DOCTOR_START_ROW = 112  # Skip ahead for doctors too

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def save_checkpoint(checkpoint_type, row_num):
    """Save the current import checkpoint."""
    if checkpoint_type == 'procedure':
        checkpoint_file = "procedure_import_checkpoint.txt"
    else:  # doctor
        checkpoint_file = "doctor_import_checkpoint.txt"
        
    with open(checkpoint_file, "w") as f:
        f.write(str(row_num))
    logger.info(f"Progress saved: Set {checkpoint_type} checkpoint to row {row_num}")

def main():
    """Update checkpoints to skip already processed entries."""
    # Update procedure checkpoint
    save_checkpoint('procedure', PROCEDURE_START_ROW)
    logger.info(f"Updated procedure checkpoint to row {PROCEDURE_START_ROW}")
    
    # Update doctor checkpoint
    save_checkpoint('doctor', DOCTOR_START_ROW)
    logger.info(f"Updated doctor checkpoint to row {DOCTOR_START_ROW}")
    
    # Get current database counts
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            procedure_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cursor.fetchone()[0]
            
            # Count total rows in CSV files
            with open(PROCEDURES_CSV_PATH, 'r', encoding='utf-8') as f:
                procedures_total = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
                
            with open(DOCTORS_CSV_PATH, 'r', encoding='utf-8') as f:
                doctors_total = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
            
            logger.info("=" * 50)
            logger.info("DATABASE IMPORT STATUS")
            logger.info("=" * 50)
            logger.info(f"Procedures in database: {procedure_count} out of {procedures_total} in CSV")
            logger.info(f"Doctors in database: {doctor_count} out of {doctors_total} in CSV")
            logger.info(f"Procedures remaining: {procedures_total - PROCEDURE_START_ROW}")
            logger.info(f"Doctors remaining: {doctors_total - DOCTOR_START_ROW}")
            logger.info("=" * 50)
    finally:
        conn.close()

if __name__ == "__main__":
    main()