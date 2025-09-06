"""
Check the progress of data import.
"""

import os
import csv
import logging
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# CSV file path
CSV_FILE = "attached_assets/new_procedure_details - Sheet1.csv"

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    logging.info("Connecting to database...")
    return psycopg2.connect(db_url)

def check_progress():
    """Check the progress of data import."""
    connection = None
    try:
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check counts
        cursor.execute("SELECT COUNT(*) FROM body_parts")
        body_parts_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        categories_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM procedures")
        procedures_count = cursor.fetchone()[0]
        
        # Get total expected counts from CSV
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            
            unique_body_parts = set()
            unique_categories = set()
            unique_procedures = set()
            
            for row in rows:
                body_part = row['body_part_name'].strip()
                category = row['category_name'].strip()
                procedure = row['procedure_name'].strip()
                
                if body_part:
                    unique_body_parts.add(body_part)
                if category:
                    unique_categories.add(category)
                if procedure:
                    unique_procedures.add(procedure)
        
        # Calculate progress
        body_parts_expected = len(unique_body_parts)
        body_parts_progress = (body_parts_count / body_parts_expected) * 100 if body_parts_expected > 0 else 0
        
        categories_expected = len(unique_categories)
        categories_progress = (categories_count / categories_expected) * 100 if categories_expected > 0 else 0
        
        procedures_expected = len(unique_procedures)
        procedures_progress = (procedures_count / procedures_expected) * 100 if procedures_expected > 0 else 0
        
        # Print summary
        logging.info(f"Body Parts: {body_parts_count}/{body_parts_expected} ({body_parts_progress:.2f}%)")
        logging.info(f"Categories: {categories_count}/{categories_expected} ({categories_progress:.2f}%)")
        logging.info(f"Procedures: {procedures_count}/{procedures_expected} ({procedures_progress:.2f}%)")
        
        # Explain the category count difference
        if categories_count > categories_expected:
            logging.info(f"Note: We have more categories ({categories_count}) than unique category names in the CSV ({categories_expected})")
            logging.info(f"      This is because some categories appear in multiple body parts and need unique database entries.")
        
        return body_parts_count, categories_count, procedures_count
    except Exception as e:
        logging.error(f"Error checking progress: {e}")
        return 0, 0, 0
    finally:
        if connection:
            connection.close()

def main():
    """Run the progress check."""
    check_progress()

if __name__ == "__main__":
    main()