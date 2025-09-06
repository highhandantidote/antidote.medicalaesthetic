#!/usr/bin/env python3
"""
Add essential procedures directly to the database.

This script creates the most essential body parts, categories, and procedures directly in the database.
"""

import os
import csv
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import required models and db
from app import db
from models import BodyPart, Category, Procedure

# Path to CSV file
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    import os
    import psycopg2
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def reset_database():
    """Reset the database by removing all existing entries."""
    try:
        # Use SQLAlchemy models for resetting
        Procedure.query.delete()
        Category.query.delete()
        BodyPart.query.delete()
        db.session.commit()
        logger.info("Database reset successful")
        return True
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        db.session.rollback()
        return False

def add_body_parts():
    """Add essential body parts to the database."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return {}
    
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        # Get unique body parts from CSV
        unique_body_parts = set()
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                body_part_name = row.get('body_part_name', '').strip()
                if body_part_name:
                    unique_body_parts.add(body_part_name)
        
        # Add body parts to database using direct SQL
        body_part_ids = {}
        with conn.cursor() as cur:
            for body_part_name in unique_body_parts:
                # Check if body part already exists
                cur.execute("SELECT id FROM body_parts WHERE name = %s", (body_part_name,))
                result = cur.fetchone()
                
                if result:
                    # Body part already exists
                    body_part_ids[body_part_name] = result[0]
                    logger.info(f"Body part already exists: {body_part_name} (ID: {result[0]})")
                else:
                    # Create new body part
                    description = f"Procedures related to the {body_part_name.lower()}"
                    icon_url = f"/static/images/body_parts/{body_part_name.lower().replace(' ', '_')}.svg"
                    
                    cur.execute("""
                        INSERT INTO body_parts (name, description, icon_url, created_at)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (body_part_name, description, icon_url, datetime.utcnow()))
                    
                    body_part_id = cur.fetchone()[0]
                    body_part_ids[body_part_name] = body_part_id
                    logger.info(f"Added body part: {body_part_name} (ID: {body_part_id})")
        
        conn.commit()
        logger.info(f"Successfully added {len(body_part_ids)} body parts")
        return body_part_ids
    except Exception as e:
        logger.error(f"Error adding body parts: {str(e)}")
        if conn:
            conn.rollback()
        return {}
    finally:
        if conn:
            conn.close()

def add_categories(body_part_ids):
    """Add essential categories to the database."""
    if not os.path.exists(PROCEDURES_CSV) or not body_part_ids:
        logger.error(f"Procedures CSV file not found or no body parts added")
        return {}
    
    try:
        conn = get_db_connection()
        if not conn:
            return {}
        
        # Get unique categories per body part from CSV
        unique_categories = {}  # {(body_part_name, category_name): None}
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                
                if body_part_name and category_name:
                    unique_categories[(body_part_name, category_name)] = None
        
        # Add categories to database using direct SQL
        category_ids = {}
        with conn.cursor() as cur:
            for (body_part_name, category_name) in unique_categories:
                # Skip if body part doesn't exist
                if body_part_name not in body_part_ids:
                    logger.warning(f"Body part not found for category: {body_part_name} - {category_name}")
                    continue
                
                body_part_id = body_part_ids[body_part_name]
                
                # Check if category already exists
                cur.execute(
                    "SELECT id FROM categories WHERE name = %s AND body_part_id = %s",
                    (category_name, body_part_id)
                )
                result = cur.fetchone()
                
                if result:
                    # Category already exists
                    category_ids[(body_part_name, category_name)] = result[0]
                    logger.info(f"Category already exists: {category_name} under {body_part_name} (ID: {result[0]})")
                else:
                    # Create new category
                    description = f"{category_name} procedures for {body_part_name}"
                    
                    cur.execute("""
                        INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (category_name, description, body_part_id, 0, datetime.utcnow()))
                    
                    category_id = cur.fetchone()[0]
                    category_ids[(body_part_name, category_name)] = category_id
                    logger.info(f"Added category: {category_name} under {body_part_name} (ID: {category_id})")
        
        conn.commit()
        logger.info(f"Successfully added {len(category_ids)} categories")
        return category_ids
    except Exception as e:
        logger.error(f"Error adding categories: {str(e)}")
        if conn:
            conn.rollback()
        return {}
    finally:
        if conn:
            conn.close()

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if value is None or value == "":
        return 0
    
    # Remove commas, spaces, and non-numeric characters except for the first minus sign
    value = str(value)
    clean_value = ''.join(c for c in value if c.isdigit() or (c == '-' and value.index(c) == 0))
    
    try:
        return int(clean_value or 0)
    except ValueError:
        return 0

def add_procedures(category_ids):
    """Add essential procedures to the database."""
    if not os.path.exists(PROCEDURES_CSV) or not category_ids:
        logger.error(f"Procedures CSV file not found or no categories added")
        return False
    
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # Add procedures from CSV
        procedures_added = 0
        skipped = 0
        
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Get essential fields
                body_part_name = row.get('body_part_name', '').strip()
                category_name = row.get('category_name', '').strip()
                procedure_name = row.get('procedure_name', '').strip()
                
                # Skip if essential fields are missing
                if not procedure_name or not body_part_name or not category_name:
                    skipped += 1
                    continue
                
                # Get category ID
                category_key = (body_part_name, category_name)
                if category_key not in category_ids:
                    logger.warning(f"Category not found for procedure: {category_name} under {body_part_name}")
                    skipped += 1
                    continue
                
                category_id = category_ids[category_key]
                
                with conn.cursor() as cur:
                    # Check if procedure already exists
                    cur.execute("SELECT id FROM procedures WHERE procedure_name = %s", (procedure_name,))
                    result = cur.fetchone()
                    
                    if result:
                        # Procedure already exists
                        logger.info(f"Procedure already exists: {procedure_name} (ID: {result[0]})")
                        skipped += 1
                        continue
                    
                    # Clean cost values
                    min_cost = clean_integer(row.get('min_cost', '0'))
                    max_cost = clean_integer(row.get('max_cost', '0'))
                    
                    # Create new procedure
                    cur.execute("""
                        INSERT INTO procedures (
                            procedure_name, alternative_names, short_description, overview,
                            procedure_details, ideal_candidates, recovery_process, recovery_time,
                            procedure_duration, hospital_stay_required, results_duration,
                            min_cost, max_cost, benefits, benefits_detailed, risks,
                            procedure_types, alternative_procedures, category_id, popularity_score,
                            avg_rating, review_count, body_part
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        procedure_name, 
                        row.get('alternative_names', ''),
                        row.get('short_description', ''), 
                        row.get('overview', ''),
                        row.get('procedure_details', ''), 
                        row.get('ideal_candidates', ''),
                        row.get('recovery_process', ''), 
                        row.get('recovery_time', ''),
                        row.get('procedure_duration', ''), 
                        row.get('hospital_stay_required', 'No'),
                        row.get('results_duration', ''),
                        min_cost, 
                        max_cost,
                        row.get('benefits', ''), 
                        row.get('benefits_detailed', ''),
                        row.get('risks', ''), 
                        row.get('procedure_types', ''),
                        row.get('alternative_procedures', ''), 
                        category_id,
                        50,  # popularity_score
                        0.0,  # avg_rating
                        0,    # review_count
                        body_part_name
                    ))
                    
                    procedure_id = cur.fetchone()[0]
                    logger.info(f"Added procedure: {procedure_name} (ID: {procedure_id})")
                    procedures_added += 1
                    
                    # Commit every 10 procedures to avoid timeouts
                    if procedures_added % 10 == 0:
                        conn.commit()
                        logger.info(f"Imported {procedures_added} procedures so far (skipped {skipped})")
        
        conn.commit()
        logger.info(f"Successfully added {procedures_added} procedures (skipped {skipped})")
        return True
    except Exception as e:
        logger.error(f"Error adding procedures: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function to add essential procedures."""
    logger.info("Starting essential procedures import...")
    
    # Add body parts
    logger.info("Step 1: Adding body parts...")
    body_part_ids = add_body_parts()
    if not body_part_ids:
        logger.error("Failed to add body parts")
        return False
    
    # Add categories
    logger.info("Step 2: Adding categories...")
    category_ids = add_categories(body_part_ids)
    if not category_ids:
        logger.error("Failed to add categories")
        return False
    
    # Add procedures
    logger.info("Step 3: Adding procedures...")
    success = add_procedures(category_ids)
    if not success:
        logger.error("Failed to add procedures")
        return False
    
    logger.info("Essential procedures import completed successfully")
    return True

if __name__ == "__main__":
    main()