"""
Step 2: Import all categories from the CSV file.
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

def get_body_parts():
    """Get all body parts from the database."""
    body_parts = {}
    
    try:
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get all body parts
        cursor.execute("SELECT id, name FROM body_parts")
        for row in cursor.fetchall():
            body_parts[row[1]] = row[0]
        
        logging.info(f"Found {len(body_parts)} body parts in the database")
        
        return body_parts
    except Exception as e:
        logging.error(f"Error getting body parts: {e}")
        return {}
    finally:
        if connection:
            connection.close()

def import_categories():
    """Import all unique categories from the CSV file, linked to body parts."""
    connection = None
    categories = {}
    
    try:
        # Get body parts from database
        body_parts = get_body_parts()
        if not body_parts:
            logging.error("No body parts found in the database. Run step1_import_body_parts.py first.")
            return False
        
        # Connect to the database
        connection = get_db_connection()
        connection.autocommit = False
        
        # Read unique categories from CSV
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Collect unique categories per body part
            unique_categories = {}
            for row in reader:
                body_part = clean_text(row['body_part_name'])
                category = clean_text(row['category_name'])
                
                if body_part and category:
                    if body_part not in unique_categories:
                        unique_categories[body_part] = set()
                    
                    if category not in unique_categories[body_part]:
                        unique_categories[body_part].add(category)
            
            total_categories = sum(len(cats) for cats in unique_categories.values())
            logging.info(f"Found {total_categories} unique categories across all body parts")
            
            # Insert categories
            cursor = connection.cursor()
            for body_part, body_categories in unique_categories.items():
                body_part_id = body_parts.get(body_part)
                
                if not body_part_id:
                    logging.warning(f"Body part '{body_part}' not found in database, skipping its categories")
                    continue
                
                for category in body_categories:
                    # Create a unique internal name (to handle same category name across different body parts)
                    internal_name = f"{body_part}_{category}"
                    
                    # Check if category already exists
                    cursor.execute(
                        "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
                        (internal_name, body_part_id)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        categories[(body_part, category)] = result[0]
                        logging.info(f"Category '{category}' for body part '{body_part}' already exists with ID {result[0]}")
                    else:
                        # Insert the category
                        description = f"Procedures related to {category} for the {body_part}"
                        cursor.execute(
                            """
                            INSERT INTO categories (name, display_name, body_part_id, description, created_at, popularity_score) 
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, 0) 
                            RETURNING id
                            """,
                            (internal_name, category, body_part_id, description)
                        )
                        category_id = cursor.fetchone()[0]
                        categories[(body_part, category)] = category_id
                        logging.info(f"Added category: {category} for body part {body_part} with ID {category_id}")
            
            # Commit the transaction
            connection.commit()
            
            # Write category ids to file
            with open('categories_ids.py', 'w') as f:
                f.write('categories = {\n')
                for (body_part, category), category_id in categories.items():
                    f.write(f'    ("{body_part}", "{category}"): {category_id},\n')
                f.write('}\n')
            
            logging.info(f"Successfully imported {len(categories)} categories")
            logging.info("Categories IDs stored in categories_ids.py")
            
            return True
            
    except Exception as e:
        logging.error(f"Error importing categories: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            connection.close()

def main():
    """Run the categories import."""
    if import_categories():
        logging.info("Successfully completed Step 2: Categories import")
    else:
        logging.error("Failed to complete Step 2: Categories import")

if __name__ == "__main__":
    main()