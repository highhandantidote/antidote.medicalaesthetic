"""
Continue importing categories that were missed during the initial import.
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

def continue_category_import():
    """Import specific categories that were missed."""
    connection = None
    try:
        # Connect to the database
        connection = get_db_connection()
        connection.autocommit = True
        cursor = connection.cursor()
        
        # Get existing categories
        cursor.execute("SELECT display_name FROM categories")
        existing_categories = set(row[0] for row in cursor.fetchall())
        
        # Get body parts from database
        cursor.execute("SELECT id, name FROM body_parts")
        body_parts = {row[1]: row[0] for row in cursor.fetchall()}
        
        logging.info(f"Found {len(existing_categories)} existing categories")
        logging.info(f"Found {len(body_parts)} body parts")
        
        # Specific categories to add that were mentioned in the logs
        missing_categories = [
            ('Teeth & Gums', 'Cosmetic Dentistry'),
            ('Eyebrows', 'Eyebrow And Lash Enhancement'),
            ('Chest', 'Gender Confirmation Surgery'),
            ('Skin', 'Medical Dermatology'),
            ('Face', 'Gender Confirmation Surgery'),
            ('Chin', 'Cheek, Chin And Jawline Enhancement'),
            ('Jawline', 'Cheek, Chin And Jawline Enhancement'),
            ('Face', 'Skin Rejuvenation And Resurfacing'),
            ('Female Genitals', 'Vaginal Rejuvenation'),
            ('Ears', 'Ear Surgery'),
            ('Hair', 'Hair Restoration'),
            ('Lips', 'Lip Enhancement'),
            ('Skin', 'Scar Treatments'),
            ('Skin', 'Skin Rejuvenation And Resurfacing')
        ]
        
        # Get existing category names to avoid duplicates
        cursor.execute("SELECT display_name FROM categories")
        existing_display_names = set(row[0] for row in cursor.fetchall())
        
        # Insert categories
        categories_added = 0
        for body_part, category in missing_categories:
            # Skip if category already exists
            if category in existing_display_names:
                logging.info(f"Category '{category}' already exists. Skipping.")
                continue
            
            # Get body part ID
            body_part_id = body_parts.get(body_part)
            if not body_part_id:
                logging.warning(f"Body part '{body_part}' not found in database, skipping its category {category}")
                continue
            
            # Create a unique internal name
            internal_name = f"{body_part}_{category}"
            description = f"Procedures related to {category} for the {body_part}"
            
            try:
                # Insert category
                cursor.execute(
                    """INSERT INTO categories (name, display_name, body_part_id, description, created_at, popularity_score) 
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, 0) 
                    ON CONFLICT (name) DO NOTHING""",
                    (internal_name, category, body_part_id, description)
                )
                
                logging.info(f"Added category: {category} for body part {body_part}")
                categories_added += 1
                existing_display_names.add(category)
            except Exception as e:
                logging.error(f"Error adding category {category} for {body_part}: {e}")
                continue
        
        # Count categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        logging.info(f"Total categories in database: {count}")
        
        return categories_added
    except Exception as e:
        logging.error(f"Error importing categories: {e}")
        if connection:
            connection.rollback()
        return 0
    finally:
        if connection:
            connection.close()

def main():
    """Run the category import."""
    categories_added = continue_category_import()
    logging.info(f"Added {categories_added} new categories")

if __name__ == "__main__":
    main()