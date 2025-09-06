"""
Add remaining categories and fix mapping issues for proper procedure import.
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

def add_remaining_categories():
    """Add remaining categories needed for procedure import."""
    connection = None
    try:
        # Connect to the database
        connection = get_db_connection()
        connection.autocommit = True
        cursor = connection.cursor()
        
        # Get body parts
        cursor.execute("SELECT id, name FROM body_parts")
        body_parts = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Get existing categories
        cursor.execute("SELECT id, display_name, body_part_id FROM categories")
        existing_categories = {}
        for row in cursor.fetchall():
            display_name = row[1]
            body_part_id = row[2]
            if display_name not in existing_categories:
                existing_categories[display_name] = set()
            existing_categories[display_name].add(body_part_id)
        
        logging.info(f"Found {len(body_parts)} body parts and {len(existing_categories)} category display names")
        
        # Add categories that we know are still missing from the logs
        missing_categories = [
            ('Face', 'Gender Confirmation Surgery'),  # For Transgender Facial Feminization Surgery
            ('Skin', 'Skin Rejuvenation And Resurfacing')  # For BroadBand Light (BBL)
        ]
        
        # Extract all unique category and body part combinations from CSV
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                body_part = row['body_part_name'].strip()
                category = row['category_name'].strip()
                if body_part and category:
                    missing_categories.append((body_part, category))
        
        # Insert missing categories
        categories_added = 0
        for body_part, category in missing_categories:
            # Skip if body part doesn't exist
            body_part_id = body_parts.get(body_part)
            if not body_part_id:
                logging.warning(f"Body part '{body_part}' not found, skipping category '{category}'")
                continue
                
            # Skip if category already exists for this body part
            if category in existing_categories and body_part_id in existing_categories[category]:
                logging.info(f"Category '{category}' already exists for body part '{body_part}'. Skipping.")
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
                
                if category not in existing_categories:
                    existing_categories[category] = set()
                existing_categories[category].add(body_part_id)
                    
                logging.info(f"Added category: {category} for body part {body_part}")
                categories_added += 1
            except Exception as e:
                logging.error(f"Error adding category {category} for {body_part}: {e}")
                continue
        
        # Count categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        logging.info(f"Total categories in database: {count}")
        
        return categories_added
    except Exception as e:
        logging.error(f"Error adding categories: {e}")
        if connection:
            connection.rollback()
        return 0
    finally:
        if connection:
            connection.close()

def main():
    """Run the category import."""
    categories_added = add_remaining_categories()
    logging.info(f"Added {categories_added} new categories")

if __name__ == "__main__":
    main()