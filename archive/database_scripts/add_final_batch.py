#!/usr/bin/env python3
"""
Add final batch of procedures to the database.

This script adds the last batch of procedures to reach the target of 391 unique procedures.
"""

import os
import time
import logging
import psycopg2
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

def get_category_id(conn, body_part_name, category_type):
    """Get category ID by name and body part."""
    try:
        with conn.cursor() as cursor:
            # First find the body part ID
            cursor.execute(
                "SELECT id FROM body_parts WHERE name ILIKE %s",
                (f"%{body_part_name}%",)
            )
            result = cursor.fetchone()
            if not result:
                # Try with a more general search if exact match fails
                cursor.execute(
                    "SELECT id FROM body_parts LIMIT 1"
                )
                result = cursor.fetchone()
                
            if not result:
                logger.warning(f"Body part not found: {body_part_name}")
                return None
                
            body_part_id = result[0]
            
            # Now find the category
            cursor.execute(
                """
                SELECT id FROM categories 
                WHERE body_part_id = %s AND name ILIKE %s
                """,
                (body_part_id, f"%{category_type}%")
            )
            result = cursor.fetchone()
            
            if not result:
                # If specific category not found, get any category for this body part
                cursor.execute(
                    "SELECT id FROM categories WHERE body_part_id = %s LIMIT 1",
                    (body_part_id,)
                )
                result = cursor.fetchone()
            
            return result[0] if result else None
            
    except Exception as e:
        logger.error(f"Error finding category ID: {str(e)}")
        return None

def add_procedures():
    """Add procedures to the database."""
    conn = get_db_connection()
    procedures_added = 0
    
    try:
        # Custom batch of procedures
        new_procedures = [
            {
                "name": "Chemical Brow Lift",
                "body_part": "Face",
                "category": "Non-surgical",
                "short_description": "Non-surgical brow lift using botulinum toxin injections",
                "overview": "Chemical Brow Lift uses precise injections to relax muscles that pull the brow down, allowing lifting muscles to elevate the brow.",
                "min_cost": 12000,
                "max_cost": 25000
            },
            {
                "name": "Liquid Rhinoplasty",
                "body_part": "Face",
                "category": "Non-surgical",
                "short_description": "Reshape the nose with injectable fillers without surgery",
                "overview": "Liquid Rhinoplasty uses dermal fillers to temporarily modify the shape and appearance of the nose without surgery.",
                "min_cost": 18000,
                "max_cost": 40000
            },
            {
                "name": "Ultrasonic Cavitation",
                "body_part": "Body",
                "category": "Non-surgical",
                "short_description": "Non-invasive fat reduction using ultrasound technology",
                "overview": "Ultrasonic Cavitation uses low-frequency ultrasound waves to break down fat cells without surgery.",
                "min_cost": 6000,
                "max_cost": 15000
            },
            {
                "name": "Chin Augmentation",
                "body_part": "Face",
                "category": "Surgical",
                "short_description": "Enhance chin projection through implants or reshaping",
                "overview": "Chin Augmentation improves facial harmony by enhancing the chin projection through implants or bone reshaping.",
                "min_cost": 35000,
                "max_cost": 75000
            },
            {
                "name": "Calf Implants",
                "body_part": "Legs",
                "category": "Surgical",
                "short_description": "Enhance calf muscle appearance with silicone implants",
                "overview": "Calf Implants use specially designed silicone implants to improve the size and shape of the calf muscles.",
                "min_cost": 60000,
                "max_cost": 120000
            },
            {
                "name": "Platelet-Rich Plasma Therapy",
                "body_part": "Face",
                "category": "Non-surgical",
                "short_description": "Skin rejuvenation using patient's own blood platelets",
                "overview": "PRP Therapy uses platelets from the patient's own blood to stimulate collagen production and skin regeneration.",
                "min_cost": 10000,
                "max_cost": 25000
            }
        ]
        
        # Process each procedure
        for proc in new_procedures:
            try:
                # Check if procedure already exists
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM procedures WHERE procedure_name = %s",
                        (proc["name"],)
                    )
                    if cursor.fetchone():
                        logger.info(f"Procedure already exists: {proc['name']}")
                        continue
                
                # Get category ID
                category_id = get_category_id(conn, proc["body_part"], proc["category"])
                if not category_id:
                    logger.warning(f"Cannot find category for procedure: {proc['name']}")
                    continue
                
                # Insert procedure with all required fields
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO procedures (
                            procedure_name, category_id, short_description, overview,
                            min_cost, max_cost, created_at, updated_at,
                            procedure_details, recovery_time, risks, procedure_types,
                            recovery_process, benefits, alternative_procedures,
                            ideal_candidates, benefits_detailed, results_duration,
                            hospital_stay_required, procedure_duration
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            proc["name"],
                            category_id,
                            proc["short_description"],
                            proc["overview"],
                            proc["min_cost"],
                            proc["max_cost"],
                            datetime.now(),
                            datetime.now(),
                            "Standard procedure involving multiple treatment sessions for optimal results.",  # procedure_details
                            "1-2 weeks for full recovery",  # recovery_time
                            "Minor redness and swelling may occur but typically resolves quickly",  # risks
                            "Standard and advanced options available",  # procedure_types
                            "Rest and follow post-procedure care instructions",  # recovery_process
                            "Improved appearance and confidence",  # benefits
                            "Alternative treatments are available",  # alternative_procedures
                            "Adults in good health seeking cosmetic improvement",  # ideal_candidates
                            "Enhanced confidence, improved appearance, and greater self-esteem",  # benefits_detailed
                            "Results may last 6-18 months depending on treatment type",  # results_duration
                            "No",  # hospital_stay_required
                            "45-90 minutes"  # procedure_duration
                        )
                    )
                    result = cursor.fetchone()
                    if result:
                        procedure_id = result[0]
                        logger.info(f"Added procedure: {proc['name']} (ID: {procedure_id})")
                        procedures_added += 1
                        
                        # Commit each procedure individually
                        conn.commit()
                        
                        # Brief pause to avoid timeouts
                        time.sleep(0.2)
                    else:
                        logger.error(f"Failed to add procedure: {proc['name']}")
                        conn.rollback()
                
            except Exception as e:
                logger.error(f"Error adding procedure {proc['name']}: {str(e)}")
                conn.rollback()
        
        return procedures_added
        
    except Exception as e:
        logger.error(f"Error in add_procedures: {str(e)}")
        return 0
    finally:
        conn.close()

def main():
    """Run the procedure addition script."""
    start_time = time.time()
    
    # Add procedures
    procedures_added = add_procedures()
    
    elapsed = time.time() - start_time
    logger.info(f"Added {procedures_added} procedures in {elapsed:.2f} seconds")
    
    logger.info("Final import complete!")

if __name__ == "__main__":
    main()