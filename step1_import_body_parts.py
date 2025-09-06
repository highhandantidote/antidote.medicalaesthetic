"""
Step 1: Import all body parts from the CSV file.
"""

import os
import csv
import logging
import psycopg2
from psycopg2 import sql

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
    connection = psycopg2.connect(db_url)
    return connection

def clean_text(text):
    """Clean text for database insertion."""
    if text is None:
        return None
    return text.strip()

def import_body_parts():
    """Import all unique body parts from the CSV file."""
    connection = None
    body_parts = {}
    
    try:
        # Connect to the database
        connection = get_db_connection()
        connection.autocommit = False
        
        # Read unique body parts from CSV
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Collect unique body parts
            unique_body_parts = set()
            for row in reader:
                body_part = clean_text(row['body_part_name'])
                if body_part and body_part not in unique_body_parts:
                    unique_body_parts.add(body_part)
            
            logging.info(f"Found {len(unique_body_parts)} unique body parts")
            
            # Insert body parts
            cursor = connection.cursor()
            for body_part in unique_body_parts:
                # Check if body part already exists
                cursor.execute(
                    "SELECT id FROM body_parts WHERE name = %s",
                    (body_part,)
                )
                result = cursor.fetchone()
                
                if result:
                    body_parts[body_part] = result[0]
                    logging.info(f"Body part '{body_part}' already exists with ID {result[0]}")
                else:
                    # Insert the body part
                    description = f"{body_part} structure and appearance"
                    cursor.execute(
                        """
                        INSERT INTO body_parts (name, description, created_at) 
                        VALUES (%s, %s, CURRENT_TIMESTAMP) 
                        RETURNING id
                        """,
                        (body_part, description)
                    )
                    body_part_id = cursor.fetchone()[0]
                    body_parts[body_part] = body_part_id
                    logging.info(f"Added body part: {body_part} with ID {body_part_id}")
            
            # Commit the transaction
            connection.commit()
            
            # Write body part ids to file
            with open('body_parts_ids.py', 'w') as f:
                f.write('body_parts = {\n')
                for body_part, body_part_id in body_parts.items():
                    f.write(f'    "{body_part}": {body_part_id},\n')
                f.write('}\n')
            
            logging.info(f"Successfully imported {len(body_parts)} body parts")
            logging.info("Body parts IDs stored in body_parts_ids.py")
            
            return True
            
    except Exception as e:
        logging.error(f"Error importing body parts: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            connection.close()

def main():
    """Run the body parts import."""
    if import_body_parts():
        logging.info("Successfully completed Step 1: Body parts import")
    else:
        logging.error("Failed to complete Step 1: Body parts import")

if __name__ == "__main__":
    main()