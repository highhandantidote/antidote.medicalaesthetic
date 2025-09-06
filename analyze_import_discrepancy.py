"""
Analyze the discrepancy between the CSV file and the database.

This script identifies which procedures from the CSV file are missing in the database
and potential reasons for the discrepancy.
"""

import csv
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# CSV file path (note the quotes in the path since it contains spaces)
CSV_FILE = 'attached_assets/new_procedure_details - Sheet1.csv'

def get_csv_procedure_count():
    """Get the total count of procedures in the CSV file."""
    try:
        output = subprocess.check_output(f"wc -l '{CSV_FILE}'", shell=True).decode('utf-8')
        # Subtract 1 for header
        count = int(output.strip().split()[0]) - 1
        return count
    except Exception as e:
        logging.error(f"Error counting CSV lines: {e}")
        return 0

def get_db_procedure_count():
    """Get the count of procedures in the database."""
    try:
        output = subprocess.check_output(
            f"psql {os.environ.get('DATABASE_URL')} -c 'SELECT COUNT(*) FROM procedures'",
            shell=True
        ).decode('utf-8')
        # Parse the count from output
        count_line = [line for line in output.splitlines() if line.strip().isdigit()]
        if count_line:
            return int(count_line[0].strip())
        return 0
    except Exception as e:
        logging.error(f"Error counting database procedures: {e}")
        return 0

def find_duplicate_csv_names():
    """Find duplicate procedure names in the CSV."""
    try:
        output = subprocess.check_output(
            f"cat '{CSV_FILE}' | cut -d',' -f1 | grep -v 'procedure_name' | sort | uniq -d",
            shell=True
        ).decode('utf-8')
        duplicates = [line.strip() for line in output.splitlines() if line.strip()]
        return duplicates
    except Exception as e:
        logging.error(f"Error finding duplicates: {e}")
        return []

def analyze_discrepancy():
    """Analyze the discrepancy between CSV and database."""
    # Get counts
    csv_count = get_csv_procedure_count()
    db_count = get_db_procedure_count()
    duplicates = find_duplicate_csv_names()
    
    # Report findings
    logging.info(f"Total procedures in CSV: {csv_count}")
    logging.info(f"Total procedures in database: {db_count}")
    logging.info(f"Difference: {csv_count - db_count}")
    
    if duplicates:
        logging.info(f"Found {len(duplicates)} duplicate procedure names in CSV:")
        for dup in duplicates:
            logging.info(f"  - {dup}")
    
    # Add more detailed analysis using direct SQL if needed
    try:
        # Get sample procedure names from database
        output = subprocess.check_output(
            f"psql {os.environ.get('DATABASE_URL')} -c 'SELECT procedure_name FROM procedures LIMIT 5'",
            shell=True
        ).decode('utf-8')
        logging.info("Sample procedures in database:")
        for line in output.splitlines():
            if line.strip() and "procedure_name" not in line and "-" not in line:
                logging.info(f"  - {line.strip()}")
    except Exception as e:
        logging.error(f"Error getting sample procedures: {e}")

def main():
    """Main function."""
    logging.info("Analyzing import discrepancy...")
    analyze_discrepancy()
    logging.info("Analysis complete.")

if __name__ == "__main__":
    main()