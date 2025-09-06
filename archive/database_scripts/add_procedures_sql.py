#!/usr/bin/env python3
"""
Add procedures to the database using direct SQL statements for better performance.
"""
import os
import sys
import logging
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
LOG_FILE = f"add_procedures_sql_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Database connection info from environment variables
DB_URL = os.environ.get('DATABASE_URL')
if not DB_URL:
    DB_HOST = os.environ.get('PGHOST', 'localhost')
    DB_PORT = os.environ.get('PGPORT', '5432')
    DB_USER = os.environ.get('PGUSER', 'postgres')
    DB_PASS = os.environ.get('PGPASSWORD', 'postgres')
    DB_NAME = os.environ.get('PGDATABASE', 'antidote')
    
    DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Data for procedures to add - add more as needed
PROCEDURES_DATA = [
    # Face procedures - set 10
    {
        "name": "Endoscopic Brow Lift",
        "body_part": "Face",
        "category": "Facelift",
        "tags": ["Surgical", "Minimally Invasive"],
        "min_cost": 4000,
        "max_cost": 8000,
        "is_surgical": True
    },
    {
        "name": "Revision Rhinoplasty",
        "body_part": "Face",
        "category": "Rhinoplasty",
        "tags": ["Surgical", "Reconstructive"],
        "min_cost": 8000,
        "max_cost": 15000,
        "is_surgical": True
    },
    {
        "name": "Submental Liposuction",
        "body_part": "Face",
        "category": "Liposuction",
        "tags": ["Surgical", "Cosmetic"],
        "min_cost": 2500,
        "max_cost": 5000,
        "is_surgical": True
    },
    {
        "name": "PDO Thread Lift",
        "body_part": "Face",
        "category": "Facelift",
        "tags": ["Minimally Invasive", "Cosmetic"],
        "min_cost": 1500,
        "max_cost": 4000,
        "is_surgical": False
    },
    # Body procedures - set 10
    {
        "name": "Neck Liposuction",
        "body_part": "Body",
        "category": "Liposuction",
        "tags": ["Surgical", "Cosmetic"],
        "min_cost": 3500,
        "max_cost": 7000,
        "is_surgical": True
    },
    {
        "name": "Abdominoplasty with Mesh",
        "body_part": "Body",
        "category": "Body Contouring",
        "tags": ["Surgical", "Medical"],
        "min_cost": 10000,
        "max_cost": 15000,
        "is_surgical": True
    },
    # Breast procedures - set 10
    {
        "name": "Male Chest Contouring",
        "body_part": "Breast",
        "category": "Breast Reduction",
        "tags": ["Surgical", "Cosmetic"],
        "min_cost": 6000,
        "max_cost": 10000,
        "is_surgical": True
    },
    # Skin procedures - set 10
    {
        "name": "LED Light Therapy",
        "body_part": "Skin",
        "category": "Skin Treatments",
        "tags": ["Non-Surgical", "Cosmetic"],
        "min_cost": 100,
        "max_cost": 400,
        "is_surgical": False
    },
    {
        "name": "Vampire Facial",
        "body_part": "Face",
        "category": "Skin Treatments",
        "tags": ["Non-Surgical", "Medical"],
        "min_cost": 800,
        "max_cost": 1500,
        "is_surgical": False
    },
    {
        "name": "Hydrofacial",
        "body_part": "Face",
        "category": "Skin Treatments",
        "tags": ["Non-Surgical", "Cosmetic"],
        "min_cost": 150,
        "max_cost": 500,
        "is_surgical": False
    }
]

def connect_to_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def get_existing_data(conn):
    """Get existing data from the database to avoid duplicates."""
    cursor = conn.cursor()
    
    # Get existing procedures
    cursor.execute("SELECT procedure_name FROM procedures")
    existing_procedures = [row[0] for row in cursor.fetchall()]
    
    # Get existing body parts
    cursor.execute("SELECT id, name FROM body_parts")
    body_parts = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Get existing categories
    cursor.execute("SELECT id, name, body_part_id FROM categories")
    categories = {}
    for row in cursor.fetchall():
        categories[row[1]] = {"id": row[0], "body_part_id": row[2]}
    
    cursor.close()
    return existing_procedures, body_parts, categories

def ensure_body_parts_exist(conn, needed_body_parts, existing_body_parts):
    """Ensure all needed body parts exist in the database."""
    cursor = conn.cursor()
    
    for body_part in needed_body_parts:
        if body_part not in existing_body_parts:
            try:
                cursor.execute(
                    "INSERT INTO body_parts (name, description, created_at) VALUES (%s, %s, %s) RETURNING id",
                    (body_part, f"{body_part} procedures and treatments", datetime.utcnow())
                )
                body_part_id = cursor.fetchone()[0]
                existing_body_parts[body_part] = body_part_id
                logger.info(f"Created body part: {body_part} (ID: {body_part_id})")
            except Exception as e:
                logger.error(f"Error creating body part {body_part}: {str(e)}")
                conn.rollback()
                raise
    
    cursor.close()
    return existing_body_parts

def ensure_categories_exist(conn, procedures, existing_body_parts, existing_categories):
    """Ensure all needed categories exist in the database."""
    cursor = conn.cursor()
    
    # Get all categories needed for our procedures
    category_to_body_part = {}
    for proc in procedures:
        category = proc["category"]
        body_part = proc["body_part"]
        category_to_body_part[category] = body_part
    
    for category, body_part in category_to_body_part.items():
        if category not in existing_categories:
            try:
                body_part_id = existing_body_parts.get(body_part)
                if not body_part_id:
                    logger.error(f"Body part '{body_part}' not found for category '{category}'")
                    continue
                
                cursor.execute(
                    "INSERT INTO categories (name, description, body_part_id, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
                    (category, f"{category} procedures", body_part_id, datetime.utcnow())
                )
                category_id = cursor.fetchone()[0]
                existing_categories[category] = {"id": category_id, "body_part_id": body_part_id}
                logger.info(f"Created category: {category} (ID: {category_id}) under body part ID: {body_part_id}")
            except Exception as e:
                logger.error(f"Error creating category {category}: {str(e)}")
                conn.rollback()
                raise
    
    cursor.close()
    return existing_categories

def add_procedures(conn, procedures_data, existing_procedures, existing_categories):
    """Add procedures to the database using SQL."""
    cursor = conn.cursor()
    added_count = 0
    
    for proc in procedures_data:
        name = proc["name"]
        
        # Skip if procedure already exists
        if name in existing_procedures:
            logger.info(f"Procedure '{name}' already exists, skipping")
            continue
        
        try:
            # Get required data
            body_part = proc["body_part"]
            category_name = proc["category"]
            tags = proc["tags"]
            min_cost = proc["min_cost"]
            max_cost = proc["max_cost"]
            is_surgical = proc["is_surgical"]
            
            # Get category ID
            if category_name not in existing_categories:
                logger.error(f"Category '{category_name}' not found, skipping procedure '{name}'")
                continue
            
            category_id = existing_categories[category_name]["id"]
            
            # Generate descriptions
            if is_surgical:
                short_desc = f"A surgical procedure for the {body_part.lower()} area"
                benefits = "Long-lasting results, Significant improvement, Customized to your needs"
                risks = "Temporary swelling and bruising, Recovery time needed, Surgical risks apply"
                recovery_time = "10-14 days"
                results_duration = "Long-lasting"
            else:
                short_desc = f"A non-surgical procedure for the {body_part.lower()} area"
                benefits = "Minimal downtime, Quick results, Natural-looking improvement"
                risks = "Temporary redness, Results may not be permanent, Multiple sessions may be needed"
                recovery_time = "1-3 days"
                results_duration = "6-12 months"
            
            procedure_types = f"{name} Standard, {name} Advanced"
            
            # Insert procedure
            cursor.execute("""
                INSERT INTO procedures (
                    procedure_name, short_description, overview, procedure_details, 
                    ideal_candidates, recovery_process, recovery_time, results_duration,
                    min_cost, max_cost, benefits, risks, procedure_types, category_id,
                    body_part, tags, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                name, 
                short_desc,
                f"This {'surgical' if is_surgical else 'non-surgical'} procedure focuses on enhancing the {body_part.lower()} with {'significant' if is_surgical else 'minimal'} downtime.",
                f"The {name} procedure involves advanced techniques to address common concerns in the {body_part.lower()}.",
                f"Ideal candidates for {name} are individuals who wish to improve the appearance of their {body_part.lower()}.",
                "Follow your doctor's post-procedure instructions carefully for optimal results." if is_surgical else "Minimal recovery time is needed for this procedure.",
                recovery_time,
                results_duration,
                min_cost,
                max_cost,
                benefits,
                risks,
                procedure_types,
                category_id,
                body_part,
                tags,
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            existing_procedures.append(name)
            added_count += 1
            logger.info(f"Added procedure: {name} (category ID: {category_id})")
            
        except Exception as e:
            logger.error(f"Error adding procedure '{name}': {str(e)}")
            conn.rollback()
            raise
    
    # Commit if successful
    conn.commit()
    cursor.close()
    
    return added_count

def main():
    """Run the procedure addition script."""
    logger.info("Starting procedure addition script using SQL...")
    
    try:
        # Connect to the database
        conn = connect_to_db()
        
        # Get existing data
        existing_procedures, body_parts, categories = get_existing_data(conn)
        logger.info(f"Found {len(existing_procedures)} existing procedures")
        logger.info(f"Found {len(body_parts)} existing body parts")
        logger.info(f"Found {len(categories)} existing categories")
        
        # Check current procedure count
        current_count = len(existing_procedures)
        if current_count >= 117:
            logger.info(f"Already have {current_count} procedures. No need to add more.")
            conn.close()
            return 0
        
        # Ensure all needed body parts exist
        needed_body_parts = set(proc["body_part"] for proc in PROCEDURES_DATA)
        body_parts = ensure_body_parts_exist(conn, needed_body_parts, body_parts)
        
        # Ensure all needed categories exist
        categories = ensure_categories_exist(conn, PROCEDURES_DATA, body_parts, categories)
        
        # Add procedures
        count = add_procedures(conn, PROCEDURES_DATA, existing_procedures, categories)
        logger.info(f"Successfully added {count} new procedures")
        
        # Close connection
        conn.close()
        
        # Final log
        logger.info(f"Added {count} procedures to the database")
        logger.info(f"Log saved to: {LOG_FILE}")
        
        return 0 if count > 0 else 1
        
    except Exception as e:
        logger.error(f"Error in main procedure: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())