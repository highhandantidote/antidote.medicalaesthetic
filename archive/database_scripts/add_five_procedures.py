#!/usr/bin/env python3
"""
Add exactly five procedures to the database using the RealSelf hierarchy schema.
Designed to avoid timeouts by adding minimal data in each run.
"""

import os
import csv
import logging
import psycopg2
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to CSV file
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"
START_ROW = 454  # Skip rows that are already imported (already imported rows 0-453)

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not set")
        return None
    return psycopg2.connect(db_url)

def add_procedures():
    """
    Add exactly five procedures to the database.
    
    Returns:
        Number of procedures added
    """
    count = 0
    conn = None
    
    try:
        # Connect to the database
        conn = get_db_connection()
        if not conn:
            return 0
            
        procedures = []
        
        # Read only the data we need
        with open(PROCEDURES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i < START_ROW:
                    continue
                if i >= START_ROW + 5:  # Only process 5 procedures
                    break
                procedures.append(row)
        
        logger.info(f"Found {len(procedures)} procedures to add")
        
        # Process each procedure
        with conn.cursor() as cur:
            for p in procedures:
                # Check if procedure already exists
                procedure_name = p.get('procedure_name', '').strip()
                if not procedure_name:
                    continue
                    
                cur.execute("SELECT id FROM procedures WHERE procedure_name = %s", (procedure_name,))
                if cur.fetchone():
                    logger.info(f"Procedure already exists: {procedure_name}")
                    continue
                
                # Get/create body part
                body_part_name = p.get('body_part_name', '').strip()
                if not body_part_name:
                    continue
                    
                cur.execute("SELECT id FROM body_parts WHERE name = %s", (body_part_name,))
                body_part = cur.fetchone()
                
                if not body_part:
                    # Create new body part
                    cur.execute("""
                        INSERT INTO body_parts (name, description, icon_url, created_at)
                        VALUES (%s, %s, %s, %s) RETURNING id
                    """, (
                        body_part_name,
                        f"Procedures for the {body_part_name.lower()}",
                        f"/static/images/body_parts/{body_part_name.lower().replace(' ', '_')}.svg",
                        datetime.utcnow()
                    ))
                    body_part_id = cur.fetchone()[0]
                    conn.commit()  # Commit immediately after creating the body part
                    logger.info(f"Created body part: {body_part_name} (ID: {body_part_id})")
                else:
                    body_part_id = body_part[0]
                
                # Get/create category
                category_name = p.get('category_name', '').strip()
                if not category_name:
                    continue
                    
                cur.execute("""
                    SELECT id FROM categories 
                    WHERE name = %s AND body_part_id = %s
                """, (category_name, body_part_id))
                category = cur.fetchone()
                
                if not category:
                    # Check if category exists with any body part
                    cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
                    existing_category = cur.fetchone()
                    
                    if existing_category:
                        # Use existing category
                        category_id = existing_category[0]
                        logger.info(f"Using existing category: {category_name} (ID: {category_id})")
                    else:
                        # Create new category
                        cur.execute("""
                            INSERT INTO categories (name, description, body_part_id, popularity_score, created_at)
                            VALUES (%s, %s, %s, %s, %s) RETURNING id
                        """, (
                            category_name,
                            f"{category_name} procedures for {body_part_name}",
                            body_part_id,
                            0,
                            datetime.utcnow()
                        ))
                        category_id = cur.fetchone()[0]
                        conn.commit()  # Commit immediately after creating the category
                        logger.info(f"Created category: {category_name} (ID: {category_id})")
                else:
                    category_id = category[0]
                
                # Parse costs
                try:
                    min_cost = int(p.get('min_cost', '0').replace(',', '').strip() or 0)
                except (ValueError, TypeError):
                    min_cost = 0
                    
                try:
                    max_cost = int(p.get('max_cost', '0').replace(',', '').strip() or 0)
                except (ValueError, TypeError):
                    max_cost = 0
                
                # Insert procedure
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
                    p.get('alternative_names', ''),
                    p.get('short_description', ''),
                    p.get('overview', ''),
                    p.get('procedure_details', ''),
                    p.get('ideal_candidates', ''),
                    p.get('recovery_process', ''),
                    p.get('recovery_time', ''),
                    p.get('procedure_duration', ''),
                    p.get('hospital_stay_required', 'No'),
                    p.get('results_duration', ''),
                    min_cost,
                    max_cost,
                    p.get('benefits', ''),
                    p.get('benefits_detailed', ''),
                    p.get('risks', ''),
                    p.get('procedure_types', ''),
                    p.get('alternative_procedures', ''),
                    category_id,
                    50,  # Default popularity
                    0.0,  # Default rating
                    0,    # Default review count
                    body_part_name
                ))
                
                procedure_id = cur.fetchone()[0]
                conn.commit()  # Commit immediately after creating the procedure
                logger.info(f"Added procedure: {procedure_name} (ID: {procedure_id})")
                count += 1
                
        # Return the number of procedures added
        return count
        
    except Exception as e:
        logger.error(f"Error adding procedures: {str(e)}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()

def main():
    """Run the procedure addition script."""
    logger.info("Starting procedure import")
    count = add_procedures()
    logger.info(f"Added {count} procedures")
    logger.info(f"Next starting row: {START_ROW + 5}")

if __name__ == "__main__":
    main()