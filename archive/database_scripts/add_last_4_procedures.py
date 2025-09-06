#!/usr/bin/env python3
"""
Add the last 4 procedures to the database.

This script adds the final 4 procedures to reach the target of 491 unique procedures.
"""
import os
import logging
import psycopg2
from psycopg2 import sql

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# List of procedures to add (these are essential procedures that are missing)
PROCEDURES_TO_ADD = [
    {
        "procedure_name": "Genioplasty",
        "short_description": "Surgical reshaping of the chin bone.",
        "overview": "Genioplasty is a surgical procedure that reshapes the chin bone to improve facial balance and proportion.",
        "body_part": "Chin",
        "category_type": "Bone Restructuring",
        "min_cost": 100000,
        "max_cost": 250000,
        "risks": "Infection, nerve damage, asymmetry.",
        "benefits": "Improved chin definition and facial proportion.",
        "tags": ["genioplasty", "chin surgery", "chin bone"],
        "procedure_details": "The procedure involves cutting the chin bone, moving it forward, backward, up, or down, and securing it with plates and screws.",
        "recovery_process": "Recovery involves swelling and discomfort that typically resolves within 2-3 weeks.",
        "ideal_candidates": "People with receding chins or disproportionate facial features.",
        "recovery_time": "2-3 weeks",
        "procedure_duration": "1-2 hours",
        "hospital_stay_required": "Sometimes",
        "alternative_names": "Sliding Genioplasty, Mentoplasty",
        "procedure_types": "Advancement Genioplasty, Reduction Genioplasty, Vertical Genioplasty",
        "results_duration": "Permanent",
        "benefits_detailed": "Improved facial balance, enhanced profile, better proportion",
        "alternative_procedures": "Chin implant for less invasive chin enhancement"
    },
    {
        "procedure_name": "Jawline Contouring",
        "short_description": "Surgical or non-surgical enhancement of the jawline.",
        "overview": "Jawline contouring enhances the definition and shape of the jawline through surgical procedures, fillers, or implants.",
        "body_part": "Jaw",
        "category_type": "Facial Contouring",
        "min_cost": 40000,
        "max_cost": 200000,
        "risks": "Asymmetry, infection, nerve damage.",
        "benefits": "Enhanced jaw definition and facial structure.",
        "tags": ["jawline", "jaw contouring", "jaw sculpting"],
        "procedure_details": "The procedure may involve surgical bone reshaping, implant placement, or injection of fillers along the mandible.",
        "recovery_process": "Recovery depends on the technique, with surgical approaches requiring 2-4 weeks and non-surgical options having minimal downtime.",
        "ideal_candidates": "People with weak jawlines or desiring more defined facial contours.",
        "recovery_time": "0-4 weeks depending on technique",
        "procedure_duration": "1-3 hours for surgery, 30 minutes for fillers",
        "hospital_stay_required": "Sometimes for surgical approaches",
        "alternative_names": "Mandibular Contouring, Jaw Sculpting",
        "procedure_types": "Surgical Jaw Reshaping, Jaw Implants, Dermal Fillers",
        "results_duration": "Permanent for surgery, 1-2 years for fillers",
        "benefits_detailed": "More defined jawline, improved facial proportions, enhanced profile",
        "alternative_procedures": "Neck liposuction to better define the jawline"
    },
    {
        "procedure_name": "Lip Reduction",
        "short_description": "Surgical procedure to reduce the size of overly large lips.",
        "overview": "Lip reduction is a surgical procedure that decreases the size of the lips by removing excess tissue and reshaping the remaining lip.",
        "body_part": "Lips",
        "category_type": "Lip Reshaping",
        "min_cost": 30000,
        "max_cost": 90000,
        "risks": "Scarring, asymmetry, altered sensation.",
        "benefits": "More proportionate lip size.",
        "tags": ["lip reduction", "lip surgery", "lip reshaping"],
        "procedure_details": "The procedure involves making incisions inside the mouth and removing excess lip tissue to achieve the desired size and shape.",
        "recovery_process": "Recovery involves some swelling and discomfort that typically resolves within 1-2 weeks.",
        "ideal_candidates": "People with naturally overly large lips who desire a reduction in size.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "1-2 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Lip Reshaping Surgery",
        "procedure_types": "Upper Lip Reduction, Lower Lip Reduction, Bilateral Lip Reduction",
        "results_duration": "Permanent",
        "benefits_detailed": "More proportionate lip size, improved facial balance, reduced self-consciousness",
        "alternative_procedures": "None that effectively reduce lip size"
    },
    {
        "procedure_name": "Facial Fat Grafting",
        "short_description": "Procedure to transfer fat to add volume to the face.",
        "overview": "Facial fat grafting transfers fat from other body areas to restore volume and rejuvenate the face.",
        "body_part": "Face",
        "category_type": "Volume Restoration",
        "min_cost": 50000,
        "max_cost": 150000,
        "risks": "Uneven absorption, bruising, swelling.",
        "benefits": "Natural-looking volume restoration.",
        "tags": ["fat grafting", "fat transfer", "facial volume"],
        "procedure_details": "The procedure involves harvesting fat from areas like the abdomen or thighs, processing it, and injecting it into facial areas that need volume.",
        "recovery_process": "Recovery involves some swelling and bruising that typically resolves within 1-2 weeks.",
        "ideal_candidates": "People with facial volume loss due to aging or weight loss.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "1-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Facial Fat Transfer, Microlipoinjection",
        "procedure_types": "Structural Fat Grafting, Micro-Fat Grafting, Nano-Fat Grafting",
        "results_duration": "Long-lasting (though some fat may be reabsorbed)",
        "benefits_detailed": "Natural volume enhancement, improved skin quality, long-lasting results",
        "alternative_procedures": "Dermal fillers for temporary volume enhancement"
    }
]

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def get_category_id(conn, body_part_name, category_type):
    """Get category ID by name and body part."""
    with conn.cursor() as cursor:
        # First check if category already exists with the display name
        category_display_name = f"{body_part_name}_{category_type}"
        cursor.execute(
            "SELECT id FROM categories WHERE display_name = %s",
            (category_display_name,)
        )
        result = cursor.fetchone()
        if result:
            logger.info(f"Found existing category: {category_display_name}")
            return result[0]

        # Get body part ID
        cursor.execute(
            "SELECT id FROM body_parts WHERE name = %s",
            (body_part_name,)
        )
        body_part_result = cursor.fetchone()
        if not body_part_result:
            # Create body part if it doesn't exist
            cursor.execute(
                "INSERT INTO body_parts (name) VALUES (%s) RETURNING id",
                (body_part_name,)
            )
            body_part_id = cursor.fetchone()[0]
            logger.info(f"Created new body part: {body_part_name}")
        else:
            body_part_id = body_part_result[0]

        # Check if category with this name already exists (but with a different body part)
        cursor.execute(
            "SELECT id FROM categories WHERE name = %s",
            (category_type,)
        )
        existing_category = cursor.fetchone()
        
        if existing_category:
            # If category exists with this name but different body part, modify the name to make it unique
            modified_name = f"{category_type} ({body_part_name})"
            cursor.execute(
                """
                INSERT INTO categories (name, body_part_id, display_name) 
                VALUES (%s, %s, %s) RETURNING id
                """,
                (modified_name, body_part_id, category_display_name)
            )
            category_id = cursor.fetchone()[0]
            logger.info(f"Created category with modified name: {modified_name} (display: {category_display_name})")
        else:
            # Create category with original name
            cursor.execute(
                """
                INSERT INTO categories (name, body_part_id, display_name) 
                VALUES (%s, %s, %s) RETURNING id
                """,
                (category_type, body_part_id, category_display_name)
            )
            category_id = cursor.fetchone()[0]
            logger.info(f"Created category: {category_display_name}")
            
        return category_id

def add_procedures():
    """Add procedures to the database."""
    conn = get_db_connection()
    if not conn:
        return 0

    logger.info(f"Adding {len(PROCEDURES_TO_ADD)} procedures...")
    added_count = 0

    for procedure in PROCEDURES_TO_ADD:
        try:
            # Check if procedure already exists
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM procedures WHERE procedure_name = %s",
                    (procedure["procedure_name"],)
                )
                if cursor.fetchone():
                    logger.info(f"Procedure already exists: {procedure['procedure_name']}")
                    continue

            # Get or create category
            category_id = get_category_id(conn, procedure["body_part"], procedure["category_type"])

            # Convert tags to PostgreSQL array format
            tags = procedure.get("tags", [])
            if not tags:
                tags = [procedure["procedure_name"].lower()]

            # Insert procedure
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO procedures (
                        procedure_name, short_description, overview, body_part, category_id,
                        min_cost, max_cost, risks, benefits, tags,
                        body_area, category_type, procedure_details, recovery_process, 
                        ideal_candidates, alternative_names, recovery_time, procedure_duration,
                        hospital_stay_required, procedure_types, results_duration, 
                        benefits_detailed, alternative_procedures
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, 
                        %s, %s
                    )
                    """,
                    (
                        procedure["procedure_name"],
                        procedure["short_description"],
                        procedure["overview"],
                        procedure["body_part"],
                        category_id,
                        procedure["min_cost"],
                        procedure["max_cost"],
                        procedure["risks"],
                        procedure["benefits"],
                        tags,
                        procedure["body_part"],  # body_area is same as body_part
                        procedure["category_type"],
                        procedure.get("procedure_details", ""),
                        procedure.get("recovery_process", ""),
                        procedure.get("ideal_candidates", ""),
                        procedure.get("alternative_names", ""),
                        procedure.get("recovery_time", ""),
                        procedure.get("procedure_duration", ""),
                        procedure.get("hospital_stay_required", ""),
                        procedure.get("procedure_types", ""),
                        procedure.get("results_duration", ""),
                        procedure.get("benefits_detailed", ""),
                        procedure.get("alternative_procedures", "")
                    )
                )
                logger.info(f"Added procedure: {procedure['procedure_name']}")
                added_count += 1
        except Exception as e:
            logger.error(f"Error adding procedure {procedure['procedure_name']}: {e}")

    logger.info(f"Added {added_count} procedures.")
    return added_count

def get_import_summary():
    """Get a summary of the import."""
    conn = get_db_connection()
    if not conn:
        return

    with conn.cursor() as cursor:
        # Count procedures
        cursor.execute("SELECT COUNT(*) FROM procedures")
        procedure_count = cursor.fetchone()[0]
        
        # Count categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]
        
        # Count body parts
        cursor.execute("SELECT COUNT(*) FROM body_parts")
        body_part_count = cursor.fetchone()[0]
        
        logger.info(f"Import Summary:")
        logger.info(f"Total procedures: {procedure_count}")
        logger.info(f"Total categories: {category_count}")
        logger.info(f"Total body parts: {body_part_count}")
        
        # Get top categories
        cursor.execute("""
            SELECT c.name, COUNT(p.id) 
            FROM categories c 
            JOIN procedures p ON c.id = p.category_id 
            GROUP BY c.name 
            ORDER BY COUNT(p.id) DESC 
            LIMIT 5
        """)
        logger.info("Top 5 categories by procedure count:")
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]} procedures")
        
        # Get top body parts
        cursor.execute("""
            SELECT body_part, COUNT(*) 
            FROM procedures 
            GROUP BY body_part 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        """)
        logger.info("Top 5 body parts by procedure count:")
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]} procedures")

def main():
    """Run the procedure addition script."""
    added_count = add_procedures()
    logger.info(f"Total procedures added: {added_count}")
    
    # Get import summary
    get_import_summary()

if __name__ == "__main__":
    main()