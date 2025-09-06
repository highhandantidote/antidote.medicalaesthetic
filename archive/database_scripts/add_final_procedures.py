#!/usr/bin/env python
"""
Add the final procedures to the database.
This script adds the remaining procedures to reach the target of 491 unique procedures.
"""
import os
import logging
import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# List of procedures to add (these are essential procedures that are missing)
PROCEDURES_TO_ADD = [
    {
        "procedure_name": "Blepharoplasty",
        "short_description": "Removes excess eyelid skin for a more youthful look.",
        "overview": "Blepharoplasty is a surgical procedure that removes excess skin and fat from the eyelids to create a more youthful appearance.",
        "body_part": "Eyes",
        "category_type": "Eyelid Enhancement",
        "min_cost": 80000,
        "max_cost": 180000,
        "risks": "Dry eyes, infection, scarring.",
        "benefits": "More youthful eye appearance.",
        "tags": ["blepharoplasty", "eye lift", "eyelid"],
        "procedure_details": "The procedure involves removing excess skin and sometimes fat from the upper or lower eyelids.",
        "recovery_process": "Recovery typically involves swelling and bruising that subsides within 1-2 weeks.",
        "ideal_candidates": "People with droopy eyelids or bags under the eyes.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "1-2 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Eyelid Surgery, Eye Lift",
        "procedure_types": "Upper Blepharoplasty, Lower Blepharoplasty",
        "results_duration": "5-7 years",
        "benefits_detailed": "Improved field of vision, more youthful appearance, reduced tired appearance",
        "alternative_procedures": "Non-surgical eyelid lift using fillers or lasers"
    },
    {
        "procedure_name": "Chin Augmentation",
        "short_description": "Enhances chin size and shape for better facial balance.",
        "overview": "Chin augmentation is a surgical procedure that enhances the size and shape of the chin using implants or bone reshaping.",
        "body_part": "Chin",
        "category_type": "Facial Implants",
        "min_cost": 70000,
        "max_cost": 150000,
        "risks": "Infection, implant shifting.",
        "benefits": "Improved facial balance.",
        "tags": ["chin implant", "mentoplasty"],
        "procedure_details": "The procedure involves placing a silicone implant over the chin bone or moving the chin bone forward.",
        "recovery_process": "Recovery typically involves swelling and bruising that subsides within 1-2 weeks.",
        "ideal_candidates": "People with a receding or weak chin seeking improved facial proportion.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "1 hour",
        "hospital_stay_required": "No",
        "alternative_names": "Chin Implant, Mentoplasty",
        "procedure_types": "Chin Implant, Sliding Genioplasty",
        "results_duration": "Lifetime with implant maintenance",
        "benefits_detailed": "Improved profile, better facial balance, enhanced jawline definition",
        "alternative_procedures": "Filler injections for non-surgical chin augmentation"
    },
    {
        "procedure_name": "Hair Transplant",
        "short_description": "Moves hair follicles from one part of the body to balding areas.",
        "overview": "Hair transplantation is a surgical procedure that moves hair follicles from a donor site to a balding or thinning area.",
        "body_part": "Hair",
        "category_type": "Hair Restoration",
        "min_cost": 100000,
        "max_cost": 300000,
        "risks": "Infection, scarring, unnatural appearance.",
        "benefits": "Natural-looking hair regrowth.",
        "tags": ["hair restoration", "FUE", "FUT"],
        "procedure_details": "The procedure involves harvesting hair follicles individually (FUE) or as a strip (FUT) and transplanting them to balding areas.",
        "recovery_process": "Recovery typically involves some scabbing and redness that subsides within 1-2 weeks.",
        "ideal_candidates": "People with pattern baldness who have sufficient donor hair.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "4-8 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Hair Restoration, Hair Replacement Surgery",
        "procedure_types": "FUE (Follicular Unit Extraction), FUT (Follicular Unit Transplantation)",
        "results_duration": "Permanent (transplanted hair)",
        "benefits_detailed": "Permanent hair restoration, natural-looking results, increased confidence",
        "alternative_procedures": "PRP therapy, minoxidil, finasteride treatments"
    }
]

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    return conn

def get_category_id(conn, body_part_name, category_type):
    """Get category ID by name and body part."""
    with conn.cursor() as cursor:
        # Get body part ID
        cursor.execute("SELECT id FROM body_parts WHERE name = %s", (body_part_name,))
        body_part_result = cursor.fetchone()
        if not body_part_result:
            logger.warning(f"Body part not found: {body_part_name}")
            return None
        
        body_part_id = body_part_result[0]
        
        # Try combined name
        combined_name = f"{body_part_name}_{category_type}"
        cursor.execute("SELECT id FROM categories WHERE name = %s", (combined_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Try display name
        cursor.execute(
            "SELECT id FROM categories WHERE display_name = %s AND body_part_id = %s",
            (category_type, body_part_id)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Create category if not found
        try:
            cursor.execute(
                """
                INSERT INTO categories (name, display_name, body_part_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (combined_name, category_type, body_part_id)
            )
            result = cursor.fetchone()
            if result:
                logger.info(f"Created category: {combined_name}")
                return result[0]
        except Exception as e:
            logger.error(f"Error creating category {combined_name}: {e}")
        
        return None

def add_procedures():
    """Add the missing procedures to the database."""
    logger.info(f"Adding {len(PROCEDURES_TO_ADD)} procedures...")
    
    added_count = 0
    for procedure in PROCEDURES_TO_ADD:
        with get_db_connection() as conn:
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
                
                # Get category ID
                category_id = get_category_id(conn, procedure["body_part"], procedure["category_type"])
                if not category_id:
                    logger.error(f"Could not get category for {procedure['procedure_name']}")
                    continue
                
                # Process tags
                tags = [tag[:20] for tag in procedure.get("tags", [])]
                
                # Add procedure
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
    total_added = add_procedures()
    logger.info(f"Total procedures added: {total_added}")

if __name__ == "__main__":
    main()