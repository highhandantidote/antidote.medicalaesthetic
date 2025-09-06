#!/usr/bin/env python3
"""
Add a small batch of procedures to the database.

This script adds a small batch of procedures to avoid timeouts.
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
        "procedure_name": "Neck Lift",
        "short_description": "Surgical procedure to improve the appearance of the neck.",
        "overview": "A neck lift is a surgical procedure that improves visible signs of aging in the jawline and neck, such as excess fat and skin relaxation in the lower face.",
        "body_part": "Neck",
        "category_type": "Neck Rejuvenation",  # Changed from "Facial Rejuvenation" to avoid conflict
        "min_cost": 90000,
        "max_cost": 200000,
        "risks": "Scarring, asymmetry, nerve damage.",
        "benefits": "More youthful neck contour.",
        "tags": ["neck lift", "neck surgery", "cervicoplasty"],
        "procedure_details": "The procedure involves removing excess skin, tightening underlying muscles, and often includes liposuction to remove fat.",
        "recovery_process": "Recovery typically involves swelling and bruising that subsides within 2-3 weeks.",
        "ideal_candidates": "People with excess neck skin, visible neck bands, or a double chin.",
        "recovery_time": "2-3 weeks",
        "procedure_duration": "2-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Cervicoplasty, Platysmaplasty",
        "procedure_types": "Traditional Neck Lift, Limited Incision Neck Lift",
        "results_duration": "5-10 years",
        "benefits_detailed": "Refined jaw and neck contour, reduced sagging, more youthful profile",
        "alternative_procedures": "Neck liposuction for patients with good skin elasticity"
    },
    {
        "procedure_name": "Botox Injection",
        "short_description": "Non-surgical treatment to reduce facial wrinkles.",
        "overview": "Botox injections use a toxin to temporarily paralyze muscle activity, reducing the appearance of facial wrinkles.",
        "body_part": "Face",
        "category_type": "Non-Surgical Treatments",
        "min_cost": 15000,
        "max_cost": 50000,
        "risks": "Bruising, headache, temporary facial drooping.",
        "benefits": "Reduced appearance of wrinkles.",
        "tags": ["botox", "botulinum toxin", "wrinkle treatment"],
        "procedure_details": "The procedure involves injecting small amounts of botulinum toxin into specific muscles to temporarily reduce muscle activity.",
        "recovery_process": "Recovery is minimal with results appearing within 3-7 days and lasting 3-4 months.",
        "ideal_candidates": "People with dynamic wrinkles caused by facial expressions.",
        "recovery_time": "0-1 day",
        "procedure_duration": "10-30 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Botulinum Toxin Type A, Dysport, Xeomin",
        "procedure_types": "Cosmetic Botox, Therapeutic Botox",
        "results_duration": "3-4 months",
        "benefits_detailed": "Reduced appearance of forehead lines, crow's feet, and frown lines",
        "alternative_procedures": "Dermal fillers, laser treatments, chemical peels"
    },
    {
        "procedure_name": "Dermal Fillers",
        "short_description": "Injectable treatments to add volume and reduce wrinkles.",
        "overview": "Dermal fillers are gel-like substances injected beneath the skin to restore lost volume, smooth lines, soften creases, or enhance facial contours.",
        "body_part": "Face",
        "category_type": "Non-Surgical Treatments",  # Reusing existing category
        "min_cost": 20000,
        "max_cost": 80000,
        "risks": "Bruising, redness, lumps, asymmetry.",
        "benefits": "Restored volume, smoother skin.",
        "tags": ["fillers", "dermal fillers", "facial fillers"],
        "procedure_details": "The procedure involves injecting hyaluronic acid, calcium hydroxylapatite, or other substances beneath the skin surface.",
        "recovery_process": "Recovery is minimal with temporary swelling and bruising possible for a few days.",
        "ideal_candidates": "People with static wrinkles, volume loss, or desire for lip enhancement.",
        "recovery_time": "0-2 days",
        "procedure_duration": "15-60 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Facial Fillers, Injectable Fillers",
        "procedure_types": "Hyaluronic Acid Fillers, Calcium Hydroxylapatite, Poly-L-lactic Acid",
        "results_duration": "6-24 months depending on filler type",
        "benefits_detailed": "Immediate volume restoration, wrinkle reduction, enhanced facial contours",
        "alternative_procedures": "Fat transfer, facial implants, laser treatments"
    },
    {
        "procedure_name": "Laser Skin Resurfacing",
        "short_description": "Non-surgical treatment to improve skin texture and appearance.",
        "overview": "Laser skin resurfacing uses laser energy to improve skin texture and appearance by removing damaged skin layers and stimulating new collagen production.",
        "body_part": "Face",
        "category_type": "Skin Rejuvenation",  # Changed to avoid duplicate
        "min_cost": 30000,
        "max_cost": 100000,
        "risks": "Redness, swelling, changes in skin color.",
        "benefits": "Smoother, more youthful-looking skin.",
        "tags": ["laser resurfacing", "skin resurfacing", "laser treatment"],
        "procedure_details": "The procedure involves directing short, concentrated pulsating beams of light at irregular skin, precisely removing skin layer by layer.",
        "recovery_process": "Recovery depends on treatment intensity, ranging from a few days for non-ablative to 1-2 weeks for ablative lasers.",
        "ideal_candidates": "People with acne scars, age spots, fine lines, or uneven skin tone.",
        "recovery_time": "3-14 days depending on treatment intensity",
        "procedure_duration": "30 minutes - 2 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Laser Peel, Lasabrasion",
        "procedure_types": "Ablative Laser Resurfacing, Non-ablative Laser Resurfacing, Fractional Laser Treatment",
        "results_duration": "1-5 years depending on treatment type",
        "benefits_detailed": "Reduced fine lines, improved skin texture, more even skin tone",
        "alternative_procedures": "Chemical peels, microdermabrasion, microneedling"
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

def main():
    """Run the procedure addition script."""
    added_count = add_procedures()
    logger.info(f"Total procedures added: {added_count}")
    
    # Get current procedure count
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            count = cursor.fetchone()[0]
            logger.info(f"Total procedures in database: {count}")
        conn.close()

if __name__ == "__main__":
    main()