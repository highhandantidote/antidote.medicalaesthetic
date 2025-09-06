#!/usr/bin/env python
"""
Final import to complete all remaining procedures.
This script identifies and imports procedures that aren't yet in the database.
"""
import csv
import os
import logging
import time
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Batch size for imports
BATCH_SIZE = 10
# Maximum procedures to import in a single run
MAX_PROCEDURES = 30

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    return conn

def get_procedures_in_db():
    """Get all procedure names that are already in the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT procedure_name FROM procedures")
            procedures = {row[0].lower() for row in cursor.fetchall()}
            logger.info(f"Found {len(procedures)} procedures already in the database")
            return procedures

def read_procedure_data():
    """Read procedure data from CSV."""
    procedures_data = []
    
    with open("attached_assets/new_procedure_details - Sheet1.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            procedure_name = row.get("procedure_name", "").strip()
            if procedure_name and procedure_name not in ["", "procedure_name"]:
                procedures_data.append(row)
    
    logger.info(f"Read {len(procedures_data)} procedures from CSV")
    return procedures_data

def get_body_part_id(cursor, body_part_name):
    """Get body part ID by name."""
    cursor.execute(
        "SELECT id FROM body_parts WHERE name = %s",
        (body_part_name,)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    return None

def get_category_id(cursor, category_name, body_part_name, body_part_id):
    """Get category ID by display name and body part ID."""
    # First try exact match on combined name
    combined_name = f"{body_part_name}_{category_name}"
    cursor.execute(
        "SELECT id FROM categories WHERE name = %s",
        (combined_name,)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # Then try with display_name
    cursor.execute(
        "SELECT id FROM categories WHERE display_name = %s AND body_part_id = %s",
        (category_name, body_part_id)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # If still not found, log the available categories for this body part
    cursor.execute(
        "SELECT name, display_name FROM categories WHERE body_part_id = %s",
        (body_part_id,)
    )
    available_categories = cursor.fetchall()
    logger.warning(f"Available categories for body part {body_part_name} (id={body_part_id}):")
    for cat in available_categories:
        logger.warning(f"  - {cat[0]} (display: {cat[1]})")
    
    return None

def clean_numeric_value(value_str):
    """Clean and convert numeric values from the CSV."""
    if not value_str or value_str.strip() == "":
        return None
    
    # Remove $ and commas, then convert to float
    value_str = value_str.replace("$", "").replace(",", "").strip()
    try:
        return float(value_str)
    except ValueError:
        return None

def import_procedure(cursor, procedure_data):
    """Import a single procedure into the database."""
    procedure_name = procedure_data.get("procedure_name", "").strip()
    body_part_name = procedure_data.get("body_part_name", "").strip()
    category_name = procedure_data.get("category_name", "").strip()
    
    if not procedure_name or not body_part_name or not category_name:
        logger.warning(f"Missing required fields for procedure: {procedure_data}")
        return False
    
    # Skip procedures that are body part names
    if procedure_name.lower() in ["body", "breasts", "butt", "chest", "chin", "ears", 
                                "eyebrows", "eyes", "face", "feet", "female genitals", 
                                "hair", "hands", "hips", "jawline", "legs", "lips", 
                                "male genitals", "neck", "nose", "skin", "stomach", 
                                "teeth & gums"]:
        logger.info(f"Skipping procedure that is a body part name: {procedure_name}")
        return False
    
    # Get body part ID
    body_part_id = get_body_part_id(cursor, body_part_name)
    if not body_part_id:
        logger.warning(f"Body part not found: {body_part_name}")
        return False
    
    # Get category ID
    category_id = get_category_id(cursor, category_name, body_part_name, body_part_id)
    if not category_id:
        logger.warning(f"Category not found: {category_name} for body part {body_part_name}")
        return False
    
    # Get numeric fields
    min_cost = clean_numeric_value(procedure_data.get("min_cost", ""))
    max_cost = clean_numeric_value(procedure_data.get("max_cost", ""))
    
    # Parse tags
    tags_str = procedure_data.get("tags", "").strip()
    if tags_str:
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        # Limit tag length to 20 characters
        tags = [tag[:20] for tag in tags]
    else:
        tags = []
    
    # Prepare procedure data
    procedure_data_dict = {
        "procedure_name": procedure_name,
        "short_description": procedure_data.get("short_description", "").strip(),
        "body_part": body_part_name,
        "category_id": category_id,
        "min_cost": min_cost,
        "max_cost": max_cost,
        "recovery_time": procedure_data.get("recovery_time", "").strip(),
        "benefits": procedure_data.get("benefits", "").strip(),
        "risks": procedure_data.get("risks", "").strip(),
        "procedure_duration": procedure_data.get("procedure_duration", "").strip(),
        "hospital_stay_required": procedure_data.get("hospital_stay_required", "").strip(),
        "alternative_names": procedure_data.get("alternative_names", "").strip(),
        "body_area": body_part_name,
        "category_type": category_name,
    }
    
    # Convert empty strings to None
    for key, value in procedure_data_dict.items():
        if value == "":
            procedure_data_dict[key] = None
    
    # Insert procedure
    try:
        cursor.execute(
            """
            INSERT INTO procedures (
                procedure_name, short_description, body_part, category_id, 
                min_cost, max_cost, recovery_time, 
                benefits, risks, tags,
                procedure_duration, hospital_stay_required, alternative_names,
                body_area, category_type
            ) VALUES (
                %s, %s, %s, %s, 
                %s, %s, %s, 
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
            """,
            (
                procedure_data_dict["procedure_name"],
                procedure_data_dict["short_description"],
                procedure_data_dict["body_part"],
                procedure_data_dict["category_id"],
                procedure_data_dict["min_cost"],
                procedure_data_dict["max_cost"],
                procedure_data_dict["recovery_time"],
                procedure_data_dict["benefits"],
                procedure_data_dict["risks"],
                tags,
                procedure_data_dict["procedure_duration"],
                procedure_data_dict["hospital_stay_required"],
                procedure_data_dict["alternative_names"],
                procedure_data_dict["body_area"],
                procedure_data_dict["category_type"],
            )
        )
        logger.info(f"Added procedure: {procedure_name}")
        return True
    except psycopg2.Error as e:
        logger.error(f"Error adding procedure {procedure_name}: {e}")
        return False

def import_procedures():
    """Import procedures that aren't yet in the database."""
    logger.info("Starting final import of procedures...")
    
    # Get existing procedures
    existing_procedures = get_procedures_in_db()
    
    # Read procedure data from CSV
    all_procedures = read_procedure_data()
    
    # Filter out procedures that are already in the database
    missing_procedures = [
        p for p in all_procedures 
        if p.get("Name", "").strip().lower() not in existing_procedures
    ]
    
    # Skip procedures that are body part names
    filtered_procedures = [
        p for p in missing_procedures
        if p.get("Name", "").strip().lower() not in [
            "body", "breasts", "butt", "chest", "chin", "ears", 
            "eyebrows", "eyes", "face", "feet", "female genitals", 
            "hair", "hands", "hips", "jawline", "legs", "lips", 
            "male genitals", "neck", "nose", "skin", "stomach", 
            "teeth & gums"
        ]
    ]
    
    logger.info(f"Found {len(filtered_procedures)} procedures to import")
    
    if not filtered_procedures:
        logger.info("No procedures to import. Import complete!")
        return
    
    # Limit to MAX_PROCEDURES
    procedures_to_import = filtered_procedures[:MAX_PROCEDURES]
    logger.info(f"Will import up to {len(procedures_to_import)} procedures in this run")
    
    # Import in batches
    imported_count = 0
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for i in range(0, len(procedures_to_import), BATCH_SIZE):
                batch = procedures_to_import[i:i + BATCH_SIZE]
                logger.info(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch)} procedures)")
                
                batch_success = 0
                for procedure in batch:
                    if import_procedure(cursor, procedure):
                        batch_success += 1
                        imported_count += 1
                    
                    # Small delay to avoid database contention
                    time.sleep(0.2)
                
                logger.info(f"Batch {i//BATCH_SIZE + 1} complete: {batch_success}/{len(batch)} imported")
                logger.info(f"Overall progress: {imported_count}/{len(filtered_procedures)}")
                
                # Delay between batches
                time.sleep(1)
    
    logger.info(f"Import complete. Added {imported_count} procedures.")

if __name__ == "__main__":
    import_procedures()