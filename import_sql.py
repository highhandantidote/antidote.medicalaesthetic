"""
Import data directly using SQL commands to avoid timeout issues.
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

def import_body_parts():
    """Import all body parts from the CSV file."""
    connection = None
    try:
        # Connect to the database
        connection = get_db_connection()
        connection.autocommit = True
        cursor = connection.cursor()
        
        # Read unique body parts from CSV
        unique_body_parts = set()
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                body_part = row['body_part_name'].strip()
                if body_part:
                    unique_body_parts.add(body_part)
        
        logging.info(f"Found {len(unique_body_parts)} unique body parts")
        
        # Insert body parts
        body_parts_data = []
        for body_part in unique_body_parts:
            description = f"{body_part} structure and appearance"
            body_parts_data.append((body_part, description))
        
        # Use COPY for faster bulk insert
        cursor.execute("PREPARE body_part_insert AS INSERT INTO body_parts (name, description, created_at) VALUES ($1, $2, CURRENT_TIMESTAMP) ON CONFLICT (name) DO NOTHING")
        
        for body_part, description in body_parts_data:
            cursor.execute("EXECUTE body_part_insert (%s, %s)", (body_part, description))
            logging.info(f"Added body part: {body_part}")
        
        cursor.execute("DEALLOCATE body_part_insert")
        
        # Count body parts
        cursor.execute("SELECT COUNT(*) FROM body_parts")
        count = cursor.fetchone()[0]
        logging.info(f"Total body parts in database: {count}")
        
        return True
    except Exception as e:
        logging.error(f"Error importing body parts: {e}")
        return False
    finally:
        if connection:
            connection.close()

def import_categories():
    """Import all categories from the CSV file."""
    connection = None
    try:
        # Connect to the database
        connection = get_db_connection()
        connection.autocommit = True
        cursor = connection.cursor()
        
        # Get body parts from database
        cursor.execute("SELECT id, name FROM body_parts")
        body_parts = {row[1]: row[0] for row in cursor.fetchall()}
        
        if not body_parts:
            logging.error("No body parts found in the database. Run import_body_parts first.")
            return False
        
        # Read unique categories from CSV
        unique_categories = {}
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                body_part = row['body_part_name'].strip()
                category = row['category_name'].strip()
                
                if body_part and category:
                    if body_part not in unique_categories:
                        unique_categories[body_part] = set()
                    unique_categories[body_part].add(category)
        
        # Insert categories
        cursor.execute("PREPARE category_insert AS INSERT INTO categories (name, display_name, body_part_id, description, created_at, popularity_score) VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, 0) ON CONFLICT (name) DO NOTHING")
        
        categories_added = 0
        for body_part, categories in unique_categories.items():
            body_part_id = body_parts.get(body_part)
            if not body_part_id:
                logging.warning(f"Body part '{body_part}' not found in database, skipping its categories")
                continue
                
            for category in categories:
                # Create a unique internal name
                internal_name = f"{body_part}_{category}"
                description = f"Procedures related to {category} for the {body_part}"
                
                cursor.execute("EXECUTE category_insert (%s, %s, %s, %s)", 
                              (internal_name, category, body_part_id, description))
                
                logging.info(f"Added category: {category} for body part {body_part}")
                categories_added += 1
        
        cursor.execute("DEALLOCATE category_insert")
        
        # Count categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        logging.info(f"Total categories in database: {count}")
        
        return True
    except Exception as e:
        logging.error(f"Error importing categories: {e}")
        return False
    finally:
        if connection:
            connection.close()

def import_procedures_batch(start_row, batch_size):
    """Import a batch of procedures from the CSV file."""
    connection = None
    try:
        # Connect to the database
        connection = get_db_connection()
        connection.autocommit = True
        cursor = connection.cursor()
        
        # Get categories from database
        cursor.execute("""
            SELECT c.id, c.display_name, bp.name 
            FROM categories c
            JOIN body_parts bp ON c.body_part_id = bp.id
        """)
        categories = {(row[2], row[1]): row[0] for row in cursor.fetchall()}
        
        if not categories:
            logging.error("No categories found in the database. Run import_categories first.")
            return 0, start_row
        
        # Read procedures from CSV
        all_procedures = []
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_procedures = list(reader)
        
        total_procedures = len(all_procedures)
        end_row = min(start_row + batch_size, total_procedures)
        
        logging.info(f"Processing procedures {start_row+1} to {end_row} of {total_procedures}")
        
        # Prepare statement
        cursor.execute("""
            PREPARE procedure_insert AS 
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
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0, 0
            )
            ON CONFLICT (procedure_name, category_id) DO NOTHING
        """)
        
        procedures_added = 0
        for i in range(start_row, end_row):
            row = all_procedures[i]
            
            body_part = row['body_part_name'].strip()
            category = row['category_name'].strip()
            procedure_name = row['procedure_name'].strip()
            
            if not all([body_part, category, procedure_name]):
                logging.warning(f"Missing required fields for procedure. Skipping.")
                continue
            
            # Get category ID
            category_id = categories.get((body_part, category))
            if not category_id:
                logging.warning(f"Category '{category}' for body part '{body_part}' not found. Skipping procedure: {procedure_name}")
                continue
            
            # Clean and prepare data
            def clean(text):
                return text.strip() if text else None
            
            def clean_cost(cost_str):
                if not cost_str or cost_str.strip() == '':
                    return None
                cost_str = cost_str.replace(',', '')
                cost_str = ''.join(c for c in cost_str if c.isdigit() or c == '.')
                try:
                    return float(cost_str)
                except (ValueError, TypeError):
                    return None
            
            def prepare_tags(tags_str):
                if not tags_str or tags_str.strip() == '':
                    return None
                tags = [tag.strip() for tag in tags_str.split(',')]
                tags = [tag[:20] for tag in tags if tag]
                return tags if tags else None
            
            # Prepare procedure data
            alternative_names = clean(row.get('alternative_names', ''))
            short_description = clean(row.get('short_description', ''))
            overview = clean(row.get('overview', ''))
            procedure_details = clean(row.get('procedure_details', ''))
            ideal_candidates = clean(row.get('ideal_candidates', ''))
            recovery_time = clean(row.get('recovery_time', ''))
            procedure_duration = clean(row.get('procedure_duration', ''))
            hospital_stay_required = clean(row.get('hospital_stay_required', ''))
            min_cost = clean_cost(row.get('min_cost', ''))
            max_cost = clean_cost(row.get('max_cost', ''))
            risks = clean(row.get('risks', ''))
            procedure_types = clean(row.get('procedure_types', ''))
            recovery_process = clean(row.get('recovery_process', ''))
            results_duration = clean(row.get('results_duration', ''))
            benefits = clean(row.get('benefits', ''))
            benefits_detailed = clean(row.get('benefits_detailed', ''))
            alternative_procedures = clean(row.get('alternative_procedures', ''))
            tags = prepare_tags(row.get('tags', ''))
            
            # Insert the procedure
            cursor.execute(
                "EXECUTE procedure_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
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
            
            logging.info(f"Added procedure: {procedure_name}")
            procedures_added += 1
        
        cursor.execute("DEALLOCATE procedure_insert")
        
        # Count procedures
        cursor.execute("SELECT COUNT(*) FROM procedures")
        count = cursor.fetchone()[0]
        logging.info(f"Total procedures in database: {count}")
        
        return procedures_added, end_row
    except Exception as e:
        logging.error(f"Error importing procedures: {e}")
        return 0, start_row
    finally:
        if connection:
            connection.close()

def main():
    """Run the import process."""
    # Step 1: Import body parts
    logging.info("Step 1: Importing body parts...")
    if import_body_parts():
        logging.info("Body parts imported successfully")
    else:
        logging.error("Failed to import body parts")
        return
    
    # Step 2: Import categories
    logging.info("Step 2: Importing categories...")
    if import_categories():
        logging.info("Categories imported successfully")
    else:
        logging.error("Failed to import categories")
        return
    
    # Step 3: Import procedures in batches
    logging.info("Step 3: Importing procedures in batches...")
    start_row = 0
    batch_size = 20
    total_imported = 0
    
    while True:
        procedures_added, next_row = import_procedures_batch(start_row, batch_size)
        total_imported += procedures_added
        
        if next_row == start_row or procedures_added == 0:
            # No more procedures to process
            break
        
        start_row = next_row
        logging.info(f"Imported {total_imported} procedures so far")
    
    logging.info(f"Successfully imported {total_imported} procedures")
    logging.info("Import process completed successfully")

if __name__ == "__main__":
    main()