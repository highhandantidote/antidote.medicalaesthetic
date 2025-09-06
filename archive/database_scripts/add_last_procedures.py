#!/usr/bin/env python3
"""
Add the remaining procedures to the database.

This script adds the very last batch of procedures to reach the target of 491 unique procedures.
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
        "procedure_name": "Gynecomastia Surgery",
        "short_description": "Surgical correction of enlarged male breasts.",
        "overview": "Gynecomastia surgery reduces breast size in men, flattening and enhancing the chest contours through tissue excision and/or liposuction.",
        "body_part": "Chest",
        "category_type": "Male Chest Enhancement",
        "min_cost": 80000,
        "max_cost": 200000,
        "risks": "Asymmetry, scarring, changes in nipple sensation.",
        "benefits": "Flatter, more masculine chest contour.",
        "tags": ["gynecomastia", "male breast", "chest"], # shortened tags to fit 20 char limit
        "procedure_details": "The procedure may involve excision of glandular tissue, liposuction, or both, depending on the composition of the breast tissue.",
        "recovery_process": "Recovery typically involves wearing a compression garment for several weeks and avoiding strenuous activity.",
        "ideal_candidates": "Men with excess breast tissue not responding to diet and exercise.",
        "recovery_time": "1-3 weeks",
        "procedure_duration": "1-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Male Breast Reduction",
        "procedure_types": "Liposuction-Only, Excision Technique, Combined Approach",
        "results_duration": "Permanent (assuming weight is maintained)",
        "benefits_detailed": "Improved chest contour, better proportions, increased confidence",
        "alternative_procedures": "Hormone therapy for hormone-related gynecomastia"
    },
    {
        "procedure_name": "Non-Surgical Fat Reduction",
        "short_description": "Non-invasive treatments to reduce localized fat deposits.",
        "overview": "Non-surgical fat reduction includes various techniques to reduce fat without surgery, such as cryolipolysis (freezing fat), radiofrequency treatments, and injectable fat dissolvers.",
        "body_part": "Multiple",
        "category_type": "Non-Surgical Treatments",
        "min_cost": 30000,
        "max_cost": 120000,
        "risks": "Temporary redness, bruising, uneven results.",
        "benefits": "Reduced fat without surgery.",
        "tags": ["coolsculpting", "fat reduction", "non-surgical"],
        "procedure_details": "The procedures may involve applying devices that freeze fat cells, deliver heat via radiofrequency energy, or inject compounds that dissolve fat.",
        "recovery_process": "Recovery is minimal, with patients typically resuming normal activities immediately.",
        "ideal_candidates": "People with small, stubborn fat deposits who are near their ideal weight.",
        "recovery_time": "0-2 days",
        "procedure_duration": "30-90 minutes per area",
        "hospital_stay_required": "No",
        "alternative_names": "CoolSculpting, SculpSure, Kybella",
        "procedure_types": "Cryolipolysis (Fat Freezing), Radiofrequency Treatments, Injectable Fat Dissolvers",
        "results_duration": "Long-lasting with stable weight",
        "benefits_detailed": "Reduced fat bulges, improved contours, no surgical downtime",
        "alternative_procedures": "Liposuction for more dramatic or immediate results"
    },
    {
        "procedure_name": "Breast Lift",
        "short_description": "Surgical procedure to lift and reshape sagging breasts.",
        "overview": "A breast lift, or mastopexy, raises and firms the breasts by removing excess skin and tightening the surrounding tissue to reshape and support the new breast contour.",
        "body_part": "Breast",
        "category_type": "Breast Enhancement",
        "min_cost": 90000,
        "max_cost": 250000,
        "risks": "Scarring, changes in nipple sensation, asymmetry.",
        "benefits": "Lifted, firmer breast contour.",
        "tags": ["breast lift", "mastopexy", "breast reshaping"],
        "procedure_details": "The procedure involves making incisions to remove excess skin and reshape breast tissue, repositioning the nipple and areola to a more youthful height.",
        "recovery_process": "Recovery typically involves wearing a support bra and limited activity for 1-2 weeks.",
        "ideal_candidates": "People with sagging breasts due to pregnancy, weight fluctuations, or aging.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "2-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Mastopexy",
        "procedure_types": "Crescent Lift, Peri-Areolar Lift, Vertical Lift, Anchor Lift",
        "results_duration": "5-10 years (affected by aging, gravity, pregnancy)",
        "benefits_detailed": "Elevated breast position, improved shape, repositioned nipples",
        "alternative_procedures": "Breast augmentation with lift for volume and position improvement"
    },
    {
        "procedure_name": "Microdermabrasion",
        "short_description": "Non-invasive exfoliation treatment for skin renewal.",
        "overview": "Microdermabrasion is a minimally invasive procedure that uses fine crystals or a diamond-tipped wand to gently sand away the outer layer of skin to rejuvenate skin appearance.",
        "body_part": "Face",
        "category_type": "Skin Rejuvenation",
        "min_cost": 8000,
        "max_cost": 30000,
        "risks": "Temporary redness, dryness, sun sensitivity.",
        "benefits": "Smoother, more evenly toned skin.",
        "tags": ["microdermabrasion", "exfoliation", "skin renewal"],
        "procedure_details": "The procedure involves using a device that sprays microcrystals onto the skin or a diamond-tipped wand to exfoliate the skin's surface layers.",
        "recovery_process": "Recovery is minimal, with temporary redness that subsides within hours.",
        "ideal_candidates": "People with fine lines, uneven skin tone, mild acne scars, or clogged pores.",
        "recovery_time": "0-1 day",
        "procedure_duration": "30-60 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Micro-resurfacing, Power Peel",
        "procedure_types": "Crystal Microdermabrasion, Diamond-Tip Microdermabrasion",
        "results_duration": "1 month (requires maintenance treatments)",
        "benefits_detailed": "Smoother texture, enhanced product absorption, temporary collagen stimulation",
        "alternative_procedures": "Chemical peels, dermaplaning, hydrafacial treatments"
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