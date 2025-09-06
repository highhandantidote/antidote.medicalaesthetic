#!/usr/bin/env python3
"""
Import procedures using direct SQL commands.

This script uses a simpler approach with direct SQL to import procedures from CSV.
"""

import os
import csv
import logging
import psycopg2
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to CSV file
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"
START_ROW = 25  # Skip rows that are already imported
MAX_ROWS = 25   # How many rows to import in this run

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

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

def import_procedures():
    """Import procedures from CSV using direct SQL."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return False
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to connect to database")
            return False
        
        # Read CSV file
        procedures = []
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader):
                if i < START_ROW:
                    continue
                if i >= START_ROW + MAX_ROWS:
                    break
                procedures.append(row)
        
        logger.info(f"Found {len(procedures)} procedures to import")
        
        # Import each procedure
        procedures_added = 0
        
        with conn.cursor() as cur:
            for procedure in procedures:
                body_part_name = procedure.get('body_part_name', '').strip()
                category_name = procedure.get('category_name', '').strip()
                procedure_name = procedure.get('procedure_name', '').strip()
                
                if not body_part_name or not category_name or not procedure_name:
                    logger.warning(f"Skipping procedure with missing data: {procedure_name}")
                    continue
                
                # Check if procedure already exists
                cur.execute("SELECT id FROM procedures WHERE procedure_name = %s", (procedure_name,))
                if cur.fetchone():
                    logger.info(f"Procedure already exists: {procedure_name}")
                    continue
                
                # Handle body part
                cur.execute("SELECT id FROM body_parts WHERE name = %s", (body_part_name,))
                body_part = cur.fetchone()
                
                if not body_part:
                    # Create body part
                    cur.execute("""
                        INSERT INTO body_parts (name, description, icon_url, created_at)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        body_part_name,
                        f"Procedures related to the {body_part_name.lower()}",
                        f"/static/images/body_parts/{body_part_name.lower().replace(' ', '_')}.svg",
                        datetime.utcnow()
                    ))
                    body_part_id = cur.fetchone()[0]
                    logger.info(f"Created body part: {body_part_name} (ID: {body_part_id})")
                else:
                    body_part_id = body_part[0]
                
                # Handle category
                cur.execute("""
                    SELECT id FROM categories 
                    WHERE name = %s AND body_part_id = %s
                """, (category_name, body_part_id))
                category = cur.fetchone()
                
                if not category:
                    # Check if category exists with another body part
                    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
                    existing_category = cur.fetchone()
                    
                    if existing_category:
                        category_id = existing_category[0]
                        logger.info(f"Using existing category: {category_name} (ID: {category_id})")
                    else:
                        # Create category
                        cur.execute("""
                            INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            category_name,
                            f"{category_name} procedures for {body_part_name}",
                            body_part_id,
                            0,
                            datetime.utcnow()
                        ))
                        category_id = cur.fetchone()[0]
                        logger.info(f"Created category: {category_name} under {body_part_name} (ID: {category_id})")
                else:
                    category_id = category[0]
                
                # Clean cost values
                min_cost = clean_integer(procedure.get('min_cost', '0'))
                max_cost = clean_integer(procedure.get('max_cost', '0'))
                
                # Create procedure
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
                    procedure.get('alternative_names', ''),
                    procedure.get('short_description', ''), 
                    procedure.get('overview', ''),
                    procedure.get('procedure_details', ''), 
                    procedure.get('ideal_candidates', ''),
                    procedure.get('recovery_process', ''), 
                    procedure.get('recovery_time', ''),
                    procedure.get('procedure_duration', ''), 
                    procedure.get('hospital_stay_required', 'No'),
                    procedure.get('results_duration', ''),
                    min_cost, 
                    max_cost,
                    procedure.get('benefits', ''), 
                    procedure.get('benefits_detailed', ''),
                    procedure.get('risks', ''), 
                    procedure.get('procedure_types', ''),
                    procedure.get('alternative_procedures', ''), 
                    category_id,
                    50,  # popularity_score
                    0.0,  # avg_rating
                    0,    # review_count
                    body_part_name
                ))
                procedure_id = cur.fetchone()[0]
                logger.info(f"Created procedure: {procedure_name} (ID: {procedure_id})")
                procedures_added += 1
            
            conn.commit()
            logger.info(f"Successfully imported {procedures_added} procedures")
            
            # Return starting row for next run
            return START_ROW + MAX_ROWS
        
    except Exception as e:
        logger.error(f"Error importing procedures: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting procedure import")
    result = import_procedures()
    if result:
        logger.info(f"Import complete. Next start row: {result}")
    else:
        logger.error("Import failed")