#!/usr/bin/env python3
"""
Add the very last procedure to the database.

This script adds the final procedure to reach the target of 491 unique procedures.
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

# The very last procedure to add
PROCEDURE_TO_ADD = {
    "procedure_name": "Skin Boosters",
    "short_description": "Injectable skin hydration treatments.",
    "overview": "Skin boosters are injectable treatments that deliver hyaluronic acid directly into the skin to improve hydration, elasticity, and overall skin quality.",
    "body_part": "Face",
    "category_type": "Skin Hydration",
    "min_cost": 15000,
    "max_cost": 60000,
    "risks": "Bruising, swelling, uneven results.",
    "benefits": "Improved skin hydration and texture.",
    "tags": ["skin boosters", "hydration", "mesotherapy"],
    "procedure_details": "The procedure involves multiple micro-injections of hyaluronic acid and potentially other nutrients into the superficial layers of the skin.",
    "recovery_process": "Recovery is minimal with some potential redness and tiny injection marks that typically resolve within 24-48 hours.",
    "ideal_candidates": "People with dehydrated, dull skin or early signs of aging.",
    "recovery_time": "1-2 days",
    "procedure_duration": "30-45 minutes",
    "hospital_stay_required": "No",
    "alternative_names": "Skin Hydrators, Mesotherapy, Injectable Moisturizers",
    "procedure_types": "Hyaluronic Acid Skin Boosters, Polynucleotide Skin Boosters, Vitamin Cocktails",
    "results_duration": "4-6 months",
    "benefits_detailed": "Improved skin hydration, subtle glow, refined texture, reduced fine lines",
    "alternative_procedures": "Topical skincare, chemical peels, laser treatments"
}

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

def add_procedure():
    """Add the final procedure to the database."""
    conn = get_db_connection()
    if not conn:
        return 0

    logger.info(f"Adding procedure: {PROCEDURE_TO_ADD['procedure_name']}...")
    added = False

    try:
        # Check if procedure already exists
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM procedures WHERE procedure_name = %s",
                (PROCEDURE_TO_ADD["procedure_name"],)
            )
            if cursor.fetchone():
                logger.info(f"Procedure already exists: {PROCEDURE_TO_ADD['procedure_name']}")
                return 0

        # Get or create category
        category_id = get_category_id(conn, PROCEDURE_TO_ADD["body_part"], PROCEDURE_TO_ADD["category_type"])

        # Convert tags to PostgreSQL array format
        tags = PROCEDURE_TO_ADD.get("tags", [])
        if not tags:
            tags = [PROCEDURE_TO_ADD["procedure_name"].lower()]

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
                    PROCEDURE_TO_ADD["procedure_name"],
                    PROCEDURE_TO_ADD["short_description"],
                    PROCEDURE_TO_ADD["overview"],
                    PROCEDURE_TO_ADD["body_part"],
                    category_id,
                    PROCEDURE_TO_ADD["min_cost"],
                    PROCEDURE_TO_ADD["max_cost"],
                    PROCEDURE_TO_ADD["risks"],
                    PROCEDURE_TO_ADD["benefits"],
                    tags,
                    PROCEDURE_TO_ADD["body_part"],  # body_area is same as body_part
                    PROCEDURE_TO_ADD["category_type"],
                    PROCEDURE_TO_ADD.get("procedure_details", ""),
                    PROCEDURE_TO_ADD.get("recovery_process", ""),
                    PROCEDURE_TO_ADD.get("ideal_candidates", ""),
                    PROCEDURE_TO_ADD.get("alternative_names", ""),
                    PROCEDURE_TO_ADD.get("recovery_time", ""),
                    PROCEDURE_TO_ADD.get("procedure_duration", ""),
                    PROCEDURE_TO_ADD.get("hospital_stay_required", ""),
                    PROCEDURE_TO_ADD.get("procedure_types", ""),
                    PROCEDURE_TO_ADD.get("results_duration", ""),
                    PROCEDURE_TO_ADD.get("benefits_detailed", ""),
                    PROCEDURE_TO_ADD.get("alternative_procedures", "")
                )
            )
            logger.info(f"Added procedure: {PROCEDURE_TO_ADD['procedure_name']}")
            added = True
    except Exception as e:
        logger.error(f"Error adding procedure {PROCEDURE_TO_ADD['procedure_name']}: {e}")

    return 1 if added else 0

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
        
        # Check if we've reached target
        if procedure_count >= 491:
            logger.info("🎉 SUCCESS! Target of 491 procedures reached! 🎉")
        else:
            logger.info(f"Almost there! {491 - procedure_count} more procedures needed to reach target.")

def main():
    """Run the procedure addition script."""
    added_count = add_procedure()
    logger.info(f"Total procedures added: {added_count}")
    
    # Get import summary
    get_import_summary()

if __name__ == "__main__":
    main()