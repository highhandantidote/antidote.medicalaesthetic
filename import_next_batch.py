"""
Import the next batch of procedures from the CSV file.
This script determines the current progress and imports the next batch.
"""
import os
import logging
import argparse
import psycopg2
from import_all_procedures import import_procedures_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('procedure_import_progress.log')
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg2.connect(database_url)

def get_current_procedure_count():
    """Get the current count of procedures in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM procedures")
        count = cursor.fetchone()[0]
        return count
    finally:
        conn.close()

def main():
    """Main function to import the next batch of procedures."""
    parser = argparse.ArgumentParser(description='Import the next batch of procedures')
    parser.add_argument('--batch', type=int, default=10, help='Batch size')
    parser.add_argument('--start', type=int, help='Starting row (0-indexed). If not provided, will start from current count.')
    parser.add_argument('--csv', type=str, default='attached_assets/procedure_details - Sheet1.csv', help='Path to CSV file')
    args = parser.parse_args()
    
    # Get current progress
    current_count = get_current_procedure_count()
    logger.info(f"Current procedure count in database: {current_count}")
    
    # Import next batch
    csv_path = args.csv
    batch_size = args.batch
    
    # Use specified start if provided, otherwise use current count
    start_row = args.start if args.start is not None else current_count
    
    logger.info(f"Importing next batch of {batch_size} procedures starting from row {start_row}")
    success_count, error_count, done = import_procedures_batch(csv_path, start_row, batch_size)
    
    total_count = current_count + success_count
    logger.info(f"Batch import completed: {success_count} procedures imported, {error_count} errors")
    logger.info(f"Total procedures in database: {total_count}")
    
    if done:
        logger.info("All procedures have been imported successfully!")
        print("\nAll procedures have been imported successfully!")
    else:
        next_row = start_row + batch_size
        next_batch = f"python import_next_batch.py --start {next_row} --batch {batch_size}"
        logger.info(f"To continue importing, run: {next_batch}")
        print(f"\nNext command to run: {next_batch}")

if __name__ == "__main__":
    main()