"""
Add multiple procedures from the CSV file to the database.

This script reads procedures from the CSV file and adds them to the database in batches.
"""
import os
import csv
import logging
import psycopg2
import psycopg2.extras
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_body_part(conn, name):
    """Create a body part entry if it doesn't exist."""
    cursor = conn.cursor()
    
    # Check if body part exists
    check_query = "SELECT id FROM body_parts WHERE name = %s"
    cursor.execute(check_query, (name,))
    result = cursor.fetchone()
    
    if result:
        logger.info(f"Body part already exists: {name}")
        return result[0]
    
    # Create new body part
    insert_query = """
    INSERT INTO body_parts (name, description, created_at) 
    VALUES (%s, %s, %s) RETURNING id
    """
    cursor.execute(insert_query, (name, f"Body part: {name}", datetime.utcnow()))
    body_part_id = cursor.fetchone()[0]
    logger.info(f"Created new body part: {name} with ID: {body_part_id}")
    
    return body_part_id

def create_category(conn, name, body_part_id):
    """Create a category entry if it doesn't exist."""
    cursor = conn.cursor()
    
    # Check if category exists
    check_query = "SELECT id FROM categories WHERE name = %s"
    cursor.execute(check_query, (name,))
    result = cursor.fetchone()
    
    if result:
        logger.info(f"Category already exists: {name}")
        return result[0]
    
    # Create new category
    insert_query = """
    INSERT INTO categories (name, body_part_id, description, created_at) 
    VALUES (%s, %s, %s, %s) RETURNING id
    """
    cursor.execute(insert_query, (name, body_part_id, f"Category: {name}", datetime.utcnow()))
    category_id = cursor.fetchone()[0]
    logger.info(f"Created new category: {name} with ID: {category_id}")
    
    return category_id

def add_procedure(conn, procedure_data):
    """Add a procedure to the database."""
    cursor = conn.cursor()
    
    # Create body part and category first
    body_part_id = create_body_part(conn, procedure_data['body_part_name'])
    category_id = create_category(conn, procedure_data['category_name'], body_part_id)
    
    # Check if procedure exists
    check_query = "SELECT id FROM procedures WHERE procedure_name = %s"
    cursor.execute(check_query, (procedure_data['procedure_name'],))
    result = cursor.fetchone()
    
    if result:
        logger.info(f"Procedure already exists: {procedure_data['procedure_name']}")
        procedure_id = result[0]
        
        # Update existing procedure
        update_query = """
        UPDATE procedures SET 
            alternative_names = %s,
            short_description = %s, 
            overview = %s,
            procedure_details = %s,
            ideal_candidates = %s,
            recovery_process = %s,
            recovery_time = %s,
            procedure_duration = %s,
            hospital_stay_required = %s,
            results_duration = %s,
            min_cost = %s,
            max_cost = %s,
            benefits = %s,
            benefits_detailed = %s,
            risks = %s,
            procedure_types = %s,
            alternative_procedures = %s,
            category_id = %s,
            body_part = %s,
            updated_at = %s
        WHERE id = %s
        """
        cursor.execute(update_query, (
            procedure_data['alternative_names'],
            procedure_data['short_description'],
            procedure_data['overview'],
            procedure_data['procedure_details'],
            procedure_data['ideal_candidates'],
            procedure_data.get('recovery_process', ''),
            procedure_data['recovery_time'],
            procedure_data['procedure_duration'],
            procedure_data['hospital_stay_required'],
            procedure_data.get('results_duration', ''),
            int(procedure_data['min_cost'].replace(',', '')) if procedure_data['min_cost'] else 0,
            int(procedure_data['max_cost'].replace(',', '')) if procedure_data['max_cost'] else 0,
            procedure_data.get('benefits', ''),
            procedure_data.get('benefits_detailed', ''),
            procedure_data['risks'],
            procedure_data['procedure_types'],
            procedure_data.get('alternative_procedures', ''),
            category_id,
            procedure_data['body_part_name'],
            datetime.utcnow(),
            procedure_id
        ))
        logger.info(f"Updated procedure: {procedure_data['procedure_name']}")
    else:
        # Insert new procedure
        insert_query = """
        INSERT INTO procedures (
            procedure_name, alternative_names, short_description, overview, 
            procedure_details, ideal_candidates, recovery_process, recovery_time,
            procedure_duration, hospital_stay_required, results_duration,
            min_cost, max_cost, benefits, benefits_detailed, risks, procedure_types,
            alternative_procedures, category_id, body_part, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """
        cursor.execute(insert_query, (
            procedure_data['procedure_name'],
            procedure_data['alternative_names'],
            procedure_data['short_description'],
            procedure_data['overview'],
            procedure_data['procedure_details'],
            procedure_data['ideal_candidates'],
            procedure_data.get('recovery_process', ''),
            procedure_data['recovery_time'],
            procedure_data['procedure_duration'],
            procedure_data['hospital_stay_required'],
            procedure_data.get('results_duration', ''),
            int(procedure_data['min_cost'].replace(',', '')) if procedure_data['min_cost'] else 0,
            int(procedure_data['max_cost'].replace(',', '')) if procedure_data['max_cost'] else 0,
            procedure_data.get('benefits', ''),
            procedure_data.get('benefits_detailed', ''),
            procedure_data['risks'],
            procedure_data['procedure_types'],
            procedure_data.get('alternative_procedures', ''),
            category_id,
            procedure_data['body_part_name'],
            datetime.utcnow(),
            datetime.utcnow()
        ))
        procedure_id = cursor.fetchone()[0]
        logger.info(f"Added new procedure: {procedure_data['procedure_name']} with ID: {procedure_id}")
    
    # Commit the changes
    conn.commit()
    return procedure_id

def main():
    """Main function to add multiple procedures."""
    parser = argparse.ArgumentParser(description='Add multiple procedures from CSV')
    parser.add_argument('--start', type=int, default=0, help='Starting row index (0-based)')
    parser.add_argument('--count', type=int, default=5, help='Number of procedures to add')
    args = parser.parse_args()
    
    # Get database connection string from environment variable
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment variables")
        return False
    
    csv_path = 'attached_assets/procedure_details - Sheet1.csv'
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    try:
        # Connect to the database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        
        # Read procedures from the CSV file
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            all_procedures = list(csv_reader)
            
            # Validate start and count
            if args.start >= len(all_procedures):
                logger.error(f"Start index {args.start} exceeds the number of procedures {len(all_procedures)}")
                return False
            
            end_index = min(args.start + args.count, len(all_procedures))
            procedures_to_add = all_procedures[args.start:end_index]
            
            logger.info(f"Adding {len(procedures_to_add)} procedures starting from index {args.start}...")
            
            for i, procedure_data in enumerate(procedures_to_add):
                logger.info(f"Processing procedure {i+1}/{len(procedures_to_add)}: {procedure_data['procedure_name']}")
                procedure_id = add_procedure(conn, procedure_data)
                logger.info(f"Successfully added/updated procedure with ID: {procedure_id}")
            
            logger.info(f"Successfully added {len(procedures_to_add)} procedures")
            
            # Provide info for the next batch
            if end_index < len(all_procedures):
                logger.info(f"To add the next batch, run: python add_multiple_procedures.py --start {end_index} --count {args.count}")
            else:
                logger.info("All procedures from the CSV have been processed")
            
        # Close the connection
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error adding procedures: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting to add multiple procedures...")
    success = main()
    
    if success:
        logger.info("Procedures added successfully!")
    else:
        logger.error("Failed to add procedures.")