#!/usr/bin/env python3
"""
Add the last 2 procedures to the database.

This script adds the final 2 procedures to reach the target of 491 unique procedures.
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
        "procedure_name": "Forehead Reduction",
        "short_description": "Surgical procedure to reduce the height of the forehead.",
        "overview": "Forehead reduction surgery, also known as hairline lowering, reduces the height of the forehead by bringing the hairline forward.",
        "body_part": "Forehead",
        "category_type": "Hairline Surgery",
        "min_cost": 70000,
        "max_cost": 180000,
        "risks": "Scarring, nerve damage, asymmetry.",
        "benefits": "Balanced facial proportions.",
        "tags": ["forehead reduction", "hairline lowering", "forehead"],
        "procedure_details": "The procedure involves making an incision at the hairline, removing a strip of forehead skin, and advancing the scalp forward.",
        "recovery_process": "Recovery involves swelling and discomfort that typically resolves within 2-3 weeks.",
        "ideal_candidates": "People with high foreheads or receding hairlines who desire a more balanced facial appearance.",
        "recovery_time": "2-3 weeks",
        "procedure_duration": "2-4 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Hairline Lowering, Hairline Advancement",
        "procedure_types": "Surgical Hairline Advancement, Pretrichial Forehead Reduction",
        "results_duration": "Permanent",
        "benefits_detailed": "Reduced forehead height, more balanced facial proportions, improved self-confidence",
        "alternative_procedures": "Hair transplantation to lower the hairline"
    },
    {
        "procedure_name": "Hand Rejuvenation",
        "short_description": "Procedures to restore a youthful appearance to aging hands.",
        "overview": "Hand rejuvenation encompasses various treatments to improve the appearance of aging hands, including fat grafting, fillers, laser treatments, and chemical peels.",
        "body_part": "Hands",
        "category_type": "Anti-Aging Treatments",
        "min_cost": 20000,
        "max_cost": 90000,
        "risks": "Bruising, swelling, uneven results.",
        "benefits": "More youthful appearance of hands.",
        "tags": ["hand rejuvenation", "hand fillers", "hand treatment"],
        "procedure_details": "The procedures may include injecting fillers or fat to restore volume, laser treatments to reduce pigmentation, or chemical peels to improve skin texture.",
        "recovery_process": "Recovery is minimal, with some swelling and bruising that typically resolves within a few days to a week.",
        "ideal_candidates": "People with thin, veiny hands showing signs of aging.",
        "recovery_time": "1-7 days depending on treatment",
        "procedure_duration": "30-90 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Hand Fillers, Hand Lift",
        "procedure_types": "Dermal Fillers, Fat Grafting, Laser Skin Resurfacing, Chemical Peels",
        "results_duration": "6 months to several years depending on treatment",
        "benefits_detailed": "Restored volume, reduced veins and tendons visibility, improved skin texture",
        "alternative_procedures": "Retinoid creams and strict sun protection for maintenance"
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