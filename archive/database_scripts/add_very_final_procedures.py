#!/usr/bin/env python3
"""
Add the very last procedures to the database.

This script adds the final procedures to reach the target of 491 unique procedures.
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
        "procedure_name": "Thread Lift",
        "short_description": "Minimally invasive procedure using threads to lift facial skin.",
        "overview": "A thread lift is a minimally invasive alternative to facelift surgery that uses special threads to reposition sagging facial tissues.",
        "body_part": "Face",
        "category_type": "Minimally Invasive",
        "min_cost": 40000,
        "max_cost": 120000,
        "risks": "Bruising, infection, asymmetry, visible threads.",
        "benefits": "Subtle lifting effect with minimal downtime.",
        "tags": ["thread lift", "suture lift", "non-surgical"],
        "procedure_details": "The procedure involves inserting temporary sutures beneath the skin to pull the face upward subtly.",
        "recovery_process": "Recovery is minimal with some tenderness and swelling that typically resolves within a few days.",
        "ideal_candidates": "People with mild to moderate facial sagging who aren't ready for a surgical facelift.",
        "recovery_time": "3-7 days",
        "procedure_duration": "30-60 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Silhouette Lift, PDO Thread Lift",
        "procedure_types": "PDO Threads, Silhouette Instalift, Novathreads",
        "results_duration": "1-2 years",
        "benefits_detailed": "Lifted facial appearance, stimulated collagen production, minimal scarring",
        "alternative_procedures": "Facelift surgery, injectable fillers, skin tightening treatments"
    },
    {
        "procedure_name": "Lip Augmentation",
        "short_description": "Procedure to enhance the volume and shape of the lips.",
        "overview": "Lip augmentation enhances the fullness of the lips using fillers, fat transfer, or implants.",
        "body_part": "Lips",
        "category_type": "Facial Enhancement",
        "min_cost": 15000,
        "max_cost": 60000,
        "risks": "Bruising, asymmetry, allergic reaction.",
        "benefits": "Fuller, more defined lips.",
        "tags": ["lip fillers", "lip enhancement", "fuller lips"],
        "procedure_details": "The procedure typically involves injecting hyaluronic acid fillers into the lips to add volume and shape.",
        "recovery_process": "Recovery is minimal with some swelling and bruising that typically resolves within a few days.",
        "ideal_candidates": "People with thin or asymmetrical lips seeking enhanced volume.",
        "recovery_time": "1-3 days",
        "procedure_duration": "15-30 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Lip Fillers, Lip Injections",
        "procedure_types": "Hyaluronic Acid Fillers, Fat Transfer, Lip Implants",
        "results_duration": "6-12 months for fillers, longer for other methods",
        "benefits_detailed": "Enhanced lip volume, improved lip symmetry, more defined lip border",
        "alternative_procedures": "Lip lift surgery for permanent results"
    },
    {
        "procedure_name": "Buccal Fat Removal",
        "short_description": "Surgical procedure to reduce fullness in the cheeks.",
        "overview": "Buccal fat removal is a surgical procedure that removes the buccal fat pads in the cheeks to thin the face and create more defined cheekbones.",
        "body_part": "Cheeks",
        "category_type": "Facial Contouring",
        "min_cost": 30000,
        "max_cost": 90000,
        "risks": "Asymmetry, excessive thinning, nerve damage.",
        "benefits": "More contoured, slimmer face.",
        "tags": ["buccal fat", "cheek reduction", "face slimming"],
        "procedure_details": "The procedure involves making small incisions inside the mouth to access and remove the buccal fat pads.",
        "recovery_process": "Recovery involves some swelling and discomfort that typically resolves within 1-2 weeks.",
        "ideal_candidates": "People with round or full cheeks seeking a more sculpted facial appearance.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "30-60 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Cheek Reduction, Bichectomy",
        "procedure_types": "Traditional Buccal Fat Removal",
        "results_duration": "Permanent",
        "benefits_detailed": "More defined cheekbones, slimmer face, enhanced facial contours",
        "alternative_procedures": "Facial fillers to enhance cheekbones, weight loss for overall facial slimming"
    },
    {
        "procedure_name": "Cheek Augmentation",
        "short_description": "Procedure to enhance the fullness and contour of the cheeks.",
        "overview": "Cheek augmentation enhances the volume and contour of the cheeks using implants, fillers, or fat transfer.",
        "body_part": "Cheeks",
        "category_type": "Facial Enhancement",
        "min_cost": 20000,
        "max_cost": 100000,
        "risks": "Asymmetry, infection, implant shifting.",
        "benefits": "Enhanced cheek volume and facial proportion.",
        "tags": ["cheek implants", "cheek fillers", "cheek enhancement"],
        "procedure_details": "The procedure may involve inserting implants through incisions inside the mouth or injecting fillers or fat to add volume.",
        "recovery_process": "Recovery varies based on the technique, with implants requiring 1-2 weeks and fillers having minimal downtime.",
        "ideal_candidates": "People with flat or hollow cheeks seeking enhanced facial contours.",
        "recovery_time": "0-14 days depending on technique",
        "procedure_duration": "30-90 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Malar Augmentation, Midface Augmentation",
        "procedure_types": "Cheek Implants, Dermal Fillers, Fat Transfer",
        "results_duration": "Implants: permanent; Fillers: 6-24 months; Fat: variable",
        "benefits_detailed": "Enhanced cheek projection, improved midface volume, youthful appearance",
        "alternative_procedures": "Facelift to address sagging cheeks, liquid facelift with multiple fillers"
    },
    {
        "procedure_name": "Labiaplasty",
        "short_description": "Surgical reshaping of the labia minora and/or majora.",
        "overview": "Labiaplasty is a surgical procedure that reduces or reshapes the labia minora or majora, which are the skin folds surrounding the vaginal opening.",
        "body_part": "Genital",
        "category_type": "Genital Surgery",
        "min_cost": 70000,
        "max_cost": 180000,
        "risks": "Scarring, asymmetry, altered sensation.",
        "benefits": "Improved comfort and appearance.",
        "tags": ["labiaplasty", "genital surgery", "labia reduction"],
        "procedure_details": "The procedure involves removing excess labial tissue and reshaping the remaining tissue to achieve the desired appearance.",
        "recovery_process": "Recovery involves some discomfort and swelling that typically resolves within 1-2 weeks, with full healing taking 6 weeks.",
        "ideal_candidates": "People with enlarged labia causing discomfort or aesthetic concerns.",
        "recovery_time": "1-2 weeks for initial healing, 6 weeks for complete healing",
        "procedure_duration": "1-2 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Labial Reduction, Nymphoplasty",
        "procedure_types": "Trim Method, Wedge Method, De-epithelialization Method",
        "results_duration": "Permanent",
        "benefits_detailed": "Reduced labial size, improved comfort during activities, enhanced appearance",
        "alternative_procedures": "Non-surgical labial rejuvenation with radiofrequency or laser treatments"
    },
    {
        "procedure_name": "Dimpleplasty",
        "short_description": "Surgical creation of dimples in the cheeks.",
        "overview": "Dimpleplasty is a surgical procedure that creates dimples in the cheeks through a small incision inside the mouth.",
        "body_part": "Cheeks",
        "category_type": "Facial Enhancement",
        "min_cost": 20000,
        "max_cost": 60000,
        "risks": "Asymmetry, infection, unnatural appearance.",
        "benefits": "Creation of facial dimples.",
        "tags": ["dimpleplasty", "cheek dimples", "dimple creation"],
        "procedure_details": "The procedure involves creating a small defect in the cheek muscle (buccinator) through an incision inside the mouth, which causes the skin to adhere to the underlying connective tissue and create a dimple when smiling.",
        "recovery_process": "Recovery involves some swelling and discomfort that typically resolves within 1 week.",
        "ideal_candidates": "People who desire dimples for aesthetic enhancement.",
        "recovery_time": "3-7 days",
        "procedure_duration": "30 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Dimple Creation Surgery",
        "procedure_types": "Traditional Dimpleplasty",
        "results_duration": "Permanent (though appearance may soften over time)",
        "benefits_detailed": "Natural-looking dimples when smiling, enhanced facial expression",
        "alternative_procedures": "Temporary dimple creation using suture techniques"
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
            
            # Count number of categories and body parts
            cursor.execute("SELECT COUNT(*) FROM categories")
            cat_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM body_parts")
            bp_count = cursor.fetchone()[0]
            logger.info(f"Total categories in database: {cat_count}")
            logger.info(f"Total body parts in database: {bp_count}")
        conn.close()

if __name__ == "__main__":
    main()