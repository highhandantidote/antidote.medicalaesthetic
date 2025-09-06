"""
Step 3: Import procedures from the CSV file in batches.
"""

import os
import csv
import logging
import psycopg2
from psycopg2 import sql
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# CSV file path
CSV_FILE = "attached_assets/new_procedure_details - Sheet1.csv"

# Batch size for processing procedures (smaller batches to avoid timeouts)
BATCH_SIZE = 10

# Marker file to track import progress
PROGRESS_FILE = "procedure_progress.txt"

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

def clean_cost(cost_str):
    """Convert cost string to numeric value."""
    if not cost_str or cost_str.strip() == '':
        return None
        
    # Remove any commas, currency symbols, etc.
    cost_str = cost_str.replace(',', '')
    cost_str = ''.join(c for c in cost_str if c.isdigit() or c == '.')
    
    try:
        return float(cost_str)
    except (ValueError, TypeError):
        return None

def prepare_tags(tags_str):
    """Convert comma-separated tags to PostgreSQL array format."""
    if not tags_str or tags_str.strip() == '':
        return None
        
    # Split by comma and clean each tag
    tags = [tag.strip() for tag in tags_str.split(',')]
    # Filter out empty tags and limit to 20 characters
    tags = [tag[:20] for tag in tags if tag]
    
    return tags if tags else None

def get_categories():
    """Get all categories from the database."""
    categories = {}
    
    try:
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get all categories
        cursor.execute("""
            SELECT c.id, c.display_name, bp.name 
            FROM categories c
            JOIN body_parts bp ON c.body_part_id = bp.id
        """)
        
        for row in cursor.fetchall():
            category_id, category_name, body_part_name = row
            categories[(body_part_name, category_name)] = category_id
            
        logging.info(f"Found {len(categories)} categories in the database")
        
        # Log a sample of category mappings to verify
        logging.info("Sample category mappings:")
        i = 0
        for (body_part, category), category_id in categories.items():
            logging.info(f"Body Part: {body_part}, Category: {category}, ID: {category_id}")
            i += 1
            if i >= 5:
                break
        
        return categories
    except Exception as e:
        logging.error(f"Error getting categories: {e}")
        return {}
    finally:
        if connection:
            connection.close()

def get_procedure_progress():
    """Get the current procedure import progress."""
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_procedure_progress(progress):
    """Save the current procedure import progress."""
    with open(PROGRESS_FILE, 'w') as f:
        f.write(str(progress))

def import_procedures_batch():
    """Import a batch of procedures from the CSV file, linked to categories."""
    connection = None
    procedures_added = 0
    
    try:
        # Get categories from database
        categories = get_categories()
        if not categories:
            logging.error("No categories found in the database. Run step2_import_categories.py first.")
            return False
        
        # Get current progress
        start_index = get_procedure_progress()
        
        # Count existing procedures
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM procedures")
        existing_procedures = cursor.fetchone()[0]
        
        # Read all procedures from CSV
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_procedures = list(reader)
            total_procedures = len(all_procedures)
            
            logging.info(f"Found {total_procedures} procedures in CSV")
            
            # Get the batch to process
            end_index = min(start_index + BATCH_SIZE, total_procedures)
            current_batch = all_procedures[start_index:end_index]
            
            logging.info(f"Processing procedures {start_index+1} to {end_index} of {total_procedures}")
            
            # Insert procedures
            connection.autocommit = False
            cursor = connection.cursor()
            
            for row in current_batch:
                body_part = clean_text(row['body_part_name'])
                category = clean_text(row['category_name'])
                procedure_name = clean_text(row['procedure_name'])
                
                if not all([body_part, category, procedure_name]):
                    logging.warning(f"Missing required fields for procedure. Skipping.")
                    continue
                
                # Get category ID
                category_id = categories.get((body_part, category))
                if not category_id:
                    logging.warning(f"Category '{category}' for body part '{body_part}' not found. Skipping procedure: {procedure_name}")
                    continue
                
                # Check if procedure already exists
                cursor.execute(
                    "SELECT id FROM procedures WHERE procedure_name = %s AND category_id = %s",
                    (procedure_name, category_id)
                )
                if cursor.fetchone():
                    logging.info(f"Procedure '{procedure_name}' already exists. Skipping.")
                    continue
                
                # Prepare procedure data
                alternative_names = clean_text(row.get('alternative_names', ''))
                short_description = clean_text(row.get('short_description', ''))
                overview = clean_text(row.get('overview', ''))
                procedure_details = clean_text(row.get('procedure_details', ''))
                ideal_candidates = clean_text(row.get('ideal_candidates', ''))
                recovery_time = clean_text(row.get('recovery_time', ''))
                procedure_duration = clean_text(row.get('procedure_duration', ''))
                hospital_stay_required = clean_text(row.get('hospital_stay_required', ''))
                min_cost = clean_cost(row.get('min_cost', ''))
                max_cost = clean_cost(row.get('max_cost', ''))
                risks = clean_text(row.get('risks', ''))
                procedure_types = clean_text(row.get('procedure_types', ''))
                recovery_process = clean_text(row.get('recovery_process', ''))
                results_duration = clean_text(row.get('results_duration', ''))
                benefits = clean_text(row.get('benefits', ''))
                benefits_detailed = clean_text(row.get('benefits_detailed', ''))
                alternative_procedures = clean_text(row.get('alternative_procedures', ''))
                tags = prepare_tags(row.get('tags', ''))
                
                # Insert the procedure
                cursor.execute(
                    """
                    INSERT INTO procedures (
                        procedure_name, category_id, body_part, body_area, category_type,
                        alternative_names, short_description, overview, 
                        procedure_details, ideal_candidates, recovery_time, 
                        procedure_duration, hospital_stay_required, 
                        min_cost, max_cost, risks, procedure_types, 
                        recovery_process, results_duration, benefits, 
                        benefits_detailed, alternative_procedures, tags,
                        created_at, updated_at, avg_rating, review_count, popularity_score
                    ) 
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0, 0
                    )
                    RETURNING id
                    """,
                    (
                        procedure_name, category_id, body_part, body_part, category,
                        alternative_names, short_description, overview,
                        procedure_details, ideal_candidates, recovery_time,
                        procedure_duration, hospital_stay_required,
                        min_cost, max_cost, risks, procedure_types,
                        recovery_process, results_duration, benefits,
                        benefits_detailed, alternative_procedures, tags
                    )
                )
                
                procedure_id = cursor.fetchone()[0]
                logging.info(f"Added procedure: {procedure_name}")
                procedures_added += 1
                
                # Introduce a small delay to prevent database overload
                time.sleep(0.5)
            
            # Commit the transaction
            connection.commit()
            
            # Save progress
            save_procedure_progress(end_index)
            
            return procedures_added, end_index, total_procedures
            
    except Exception as e:
        logging.error(f"Error importing procedures: {e}")
        if connection and not connection.closed:
            connection.rollback()
        return 0, start_index, 0
    finally:
        if connection and not connection.closed:
            connection.close()

def main():
    """Run the procedures import batch."""
    procedures_added, current_index, total_procedures = import_procedures_batch()
    
    if procedures_added > 0:
        logging.info(f"Successfully imported {procedures_added} procedures in this batch")
        logging.info(f"Progress: {current_index}/{total_procedures} procedures processed")
        
        if current_index >= total_procedures:
            logging.info("All procedures have been imported successfully!")
    else:
        logging.warning("No procedures were imported in this batch")

if __name__ == "__main__":
    main()