#!/usr/bin/env python3
"""
Import top procedures manually from CSV.

This script imports the most important procedures from the CSV file.
"""

import os
import sys
import csv
import logging
import psycopg2
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CSV_FILE_PATH = 'attached_assets/new_procedure_details - Sheet1.csv'

# List of top procedures to import
TOP_PROCEDURES = [
    "Breast Augmentation",
    "Tummy Tuck (Abdominoplasty)",
    "Brazilian Butt Lift",
    "Rhinoplasty",
    "Mommy Makeover",
    "Breast Reduction",
    "Breast Implants",
    "Eyelid Surgery",
    "Breast Lift",
    "Breast Revision Surgery",
    "Facelift",
    "Liposuction",
    "Botox",
    "Fillers",
    "Laser Hair Removal",
    "Hair Transplant",
    "CoolSculpting",
    "Chin Augmentation",
    "Jawline Contouring",
    "Non-Surgical Rhinoplasty"
]

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def reset_database(conn):
    """Reset the database to start fresh."""
    cursor = conn.cursor()
    try:
        # Check if there are any dependencies on procedures
        cursor.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE column_name = 'procedure_id'
            AND table_schema = 'public';
        """)
        dependencies = cursor.fetchall()
        
        # Delete from dependent tables first to avoid FK constraint errors
        for table, column in dependencies:
            logger.info(f"Clearing dependent table: {table}")
            cursor.execute(f"DELETE FROM {table}")
        
        # Delete all procedures
        logger.info("Deleting all procedures...")
        cursor.execute("DELETE FROM procedures")
        
        # Delete all categories
        logger.info("Deleting all categories...")
        cursor.execute("DELETE FROM categories")
        
        # Delete all body parts
        logger.info("Deleting all body parts...")
        cursor.execute("DELETE FROM body_parts")
        
        # Reset sequences
        cursor.execute("ALTER SEQUENCE procedures_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE categories_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE body_parts_id_seq RESTART WITH 1")
        
        conn.commit()
        logger.info("Database reset successful")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error resetting database: {e}")
        raise
    finally:
        cursor.close()

def import_body_parts_and_categories(conn):
    """Import essential body parts and categories."""
    cursor = conn.cursor()
    body_part_ids = {}
    category_ids = {}
    
    try:
        # Insert body parts
        body_parts = {
            "Face": "Face and facial features",
            "Nose": "Nasal structure and appearance",
            "Breasts": "Breast size, shape, and appearance",
            "Body": "Overall body contouring and shaping",
            "Butt": "Buttocks enhancement and shaping",
            "Eyes": "Eye and eyelid appearance",
            "Lips": "Lip enhancement and shaping",
            "Hair": "Hair restoration and removal",
            "Skin": "Skin rejuvenation and treatment",
            "Stomach": "Abdominal contouring and flattening"
        }
        
        for bp_name, bp_desc in body_parts.items():
            cursor.execute("""
                INSERT INTO body_parts (name, description, created_at)
                VALUES (%s, %s, NOW())
                RETURNING id
            """, (bp_name, bp_desc))
            
            bp_id = cursor.fetchone()[0]
            body_part_ids[bp_name] = bp_id
            logger.info(f"Added body part: {bp_name} (ID: {bp_id})")
        
        # Insert categories
        categories = [
            ("Face", "Face_And_Neck_Lifts", "Procedures to lift and rejuvenate the face and neck"),
            ("Face", "Fillers_And_Injectables", "Non-surgical enhancement using injectables"),
            ("Nose", "Rhinoplasty", "Procedures to reshape the nose"),
            ("Breasts", "Breast_Surgery", "Surgical procedures for breast enhancement"),
            ("Body", "Body_Contouring", "Procedures to reshape and contour the body"),
            ("Eyes", "Eyelid_Surgery", "Procedures to rejuvenate the eye area"),
            ("Lips", "Lip_Enhancement", "Procedures to enhance lip appearance"),
            ("Stomach", "Abdominoplasty", "Procedures to flatten and contour the abdomen"),
            ("Hair", "Hair_Restoration", "Procedures to restore hair growth"),
            ("Butt", "Butt_Enhancement", "Procedures to enhance the buttocks")
        ]
        
        for bp_name, cat_name, cat_desc in categories:
            bp_id = body_part_ids.get(bp_name)
            if not bp_id:
                logger.warning(f"Body part '{bp_name}' not found")
                continue
                
            cursor.execute("""
                INSERT INTO categories (name, body_part_id, description, popularity_score, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
            """, (cat_name, bp_id, cat_desc, 5))
            
            cat_id = cursor.fetchone()[0]
            category_ids[(bp_name, cat_name)] = cat_id
            logger.info(f"Added category: {cat_name} under {bp_name} (ID: {cat_id})")
        
        conn.commit()
        
        # Get mapping between category names and IDs
        category_map = {}
        for (bp_name, cat_name), cat_id in category_ids.items():
            if cat_name == "Face_And_Neck_Lifts":
                category_map["Facelift"] = cat_id
            elif cat_name == "Fillers_And_Injectables":
                category_map["Botox"] = cat_id
                category_map["Fillers"] = cat_id
                category_map["Non-Surgical Rhinoplasty"] = cat_id
            elif cat_name == "Rhinoplasty":
                category_map["Rhinoplasty"] = cat_id
            elif cat_name == "Breast_Surgery":
                category_map["Breast Augmentation"] = cat_id
                category_map["Breast Implants"] = cat_id
                category_map["Breast Reduction"] = cat_id
                category_map["Breast Lift"] = cat_id
                category_map["Breast Revision Surgery"] = cat_id
            elif cat_name == "Body_Contouring":
                category_map["Liposuction"] = cat_id
                category_map["CoolSculpting"] = cat_id
                category_map["Mommy Makeover"] = cat_id
            elif cat_name == "Eyelid_Surgery":
                category_map["Eyelid Surgery"] = cat_id
            elif cat_name == "Lip_Enhancement":
                category_map["Fillers"] = cat_id  # Also used for lip fillers
            elif cat_name == "Abdominoplasty":
                category_map["Tummy Tuck (Abdominoplasty)"] = cat_id
            elif cat_name == "Hair_Restoration":
                category_map["Hair Transplant"] = cat_id
                category_map["Laser Hair Removal"] = cat_id
            elif cat_name == "Butt_Enhancement":
                category_map["Brazilian Butt Lift"] = cat_id
        
        return category_map, body_part_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing body parts and categories: {e}")
        raise
    finally:
        cursor.close()

def clean_numeric_value(value_str):
    """Clean and convert numeric values from the CSV."""
    if not value_str:
        return None
    
    # Remove commas, currency symbols, and other non-numeric characters
    value_str = str(value_str)
    digits_only = ''.join(c for c in value_str if c.isdigit())
    
    if digits_only:
        return int(digits_only)
    
    return None

def import_procedures(conn, category_map):
    """Import top procedures from CSV."""
    procedures_data = {}
    
    # Load procedures from CSV
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                proc_name = row.get('procedure_name', '').strip()
                if proc_name in TOP_PROCEDURES:
                    procedures_data[proc_name] = row
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return 0
    
    # Import procedures to database
    cursor = conn.cursor()
    imported_count = 0
    
    try:
        logger.info(f"Importing {len(procedures_data)} top procedures...")
        
        for proc_name, row in procedures_data.items():
            # Get category ID
            cat_id = category_map.get(proc_name)
            if not cat_id:
                logger.warning(f"No category mapping for {proc_name}")
                continue
            
            body_part_name = row.get('body_part_name', '').strip()
            if not body_part_name:
                body_part_name = "Body"  # Default
            
            # Process numeric fields
            min_cost = clean_numeric_value(row.get('min_cost', ''))
            max_cost = clean_numeric_value(row.get('max_cost', ''))
            
            # Default values for required fields
            min_cost = min_cost if min_cost is not None else 50000
            max_cost = max_cost if max_cost is not None else 200000
            
            # Ensure required fields have values
            short_description = row.get('short_description', '').strip()
            if not short_description:
                short_description = f"{proc_name} procedure."
            
            overview = row.get('overview', '').strip()
            if not overview:
                overview = f"{proc_name} is a cosmetic procedure for the {body_part_name}."
            
            procedure_details = row.get('procedure_details', '').strip()
            if not procedure_details:
                procedure_details = f"The {proc_name} procedure involves professional medical techniques."
            
            ideal_candidates = row.get('ideal_candidates', '').strip()
            if not ideal_candidates:
                ideal_candidates = f"Individuals seeking {body_part_name} enhancement."
            
            recovery_time = row.get('recovery_time', '').strip()
            if not recovery_time:
                recovery_time = "Varies by individual"
            
            risks = row.get('risks', '').strip()
            if not risks:
                risks = "All procedures carry risks. Consult with your doctor."
            
            procedure_types = row.get('procedure_types', '').strip()
            if not procedure_types:
                procedure_types = "Standard procedure"
            
            # Extract tags
            tags = row.get('tags', '').strip()
            
            # Determine body area
            body_area = body_part_name.lower()
            if body_area in ["face", "neck", "eyes", "nose", "lips", "chin", "jawline", "eyebrows", "ears"]:
                body_area = "Face"
            elif body_area in ["breasts", "chest"]:
                body_area = "Breasts"
            elif body_area in ["stomach", "abdomen", "butt", "hips", "waist", "back"]:
                body_area = "Body"
            elif body_area in ["arms", "legs", "hands", "feet"]:
                body_area = "Extremities"
            elif "genital" in body_area:
                body_area = "Intimate Areas"
            else:
                body_area = "Other"
            
            # Determine category type
            category_type = "Surgical"
            if any(term in proc_name.lower() for term in ["filler", "injectable", "non-surgical", "botox", "laser"]):
                category_type = "Non-Surgical"
            
            try:
                cursor.execute("""
                INSERT INTO procedures (
                    procedure_name,
                    alternative_names,
                    short_description,
                    overview,
                    procedure_details,
                    ideal_candidates,
                    recovery_process,
                    recovery_time,
                    procedure_duration,
                    hospital_stay_required,
                    results_duration,
                    min_cost,
                    max_cost,
                    benefits,
                    benefits_detailed,
                    risks,
                    procedure_types,
                    alternative_procedures,
                    category_id,
                    body_part,
                    created_at,
                    updated_at,
                    tags,
                    body_area,
                    category_type,
                    popularity_score,
                    avg_rating,
                    review_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s, %s, %s, %s
                )
                """, (
                    proc_name,
                    row.get('alternative_names', ''),
                    short_description,
                    overview,
                    procedure_details,
                    ideal_candidates,
                    row.get('recovery_process', ''),
                    recovery_time,
                    row.get('procedure_duration', ''),
                    row.get('hospital_stay_required', ''),
                    row.get('results_duration', ''),
                    min_cost,
                    max_cost,
                    row.get('benefits', ''),
                    row.get('benefits_detailed', ''),
                    risks,
                    procedure_types,
                    row.get('alternative_procedures', ''),
                    cat_id,
                    body_part_name,  # Store original body part name
                    tags,
                    body_area,
                    category_type,
                    5,  # Default popularity score
                    0,  # Default avg_rating
                    0   # Default review_count
                ))
                
                imported_count += 1
                logger.info(f"Added procedure: {proc_name}")
            except Exception as e:
                logger.error(f"Error adding procedure {proc_name}: {e}")
        
        conn.commit()
        logger.info(f"Imported {imported_count} top procedures")
        
        return imported_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing procedures: {e}")
        return 0
    finally:
        cursor.close()

def main():
    """Main function."""
    try:
        # Verify CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            logger.error(f"CSV file not found: {CSV_FILE_PATH}")
            sys.exit(1)
        
        # Get database connection
        conn = get_db_connection()
        
        # Reset database
        reset_database(conn)
        
        # Import body parts and categories
        category_map, body_part_ids = import_body_parts_and_categories(conn)
        
        # Import procedures
        imported_count = import_procedures(conn, category_map)
        
        # Close connection
        conn.close()
        
        logger.info(f"Import complete: {len(body_part_ids)} body parts, {len(category_map)} category mappings, {imported_count} procedures")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()