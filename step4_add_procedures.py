#!/usr/bin/env python3
"""
Step 4: Add essential procedures to the database.

This is the fourth step in a multi-step import process.
"""

import os
import psycopg2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False
    return conn

def get_category_mapping():
    """Get mapping of procedure names to category IDs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    category_mapping = {}
    
    try:
        # Get all categories
        cursor.execute("""
            SELECT c.id, c.name, bp.name 
            FROM categories c
            JOIN body_parts bp ON c.body_part_id = bp.id
        """)
        
        categories = {}
        for cat_id, cat_name, bp_name in cursor.fetchall():
            categories[(bp_name, cat_name)] = cat_id
        
        # Map procedures to categories
        procedure_categories = {
            "Rhinoplasty": ("Nose", "Rhinoplasty"),
            "Breast Augmentation": ("Breasts", "Breast_Surgery"),
            "Facelift": ("Face", "Face_And_Neck_Lifts"),
            "Liposuction": ("Body", "Body_Contouring"),
            "Botox": ("Face", "Fillers_And_Injectables"),
            "Tummy Tuck": ("Stomach", "Abdominoplasty"),
            "Brazilian Butt Lift": ("Butt", "Butt_Enhancement"),
            "Eyelid Surgery": ("Eyes", "Eyelid_Surgery"),
            "Lip Fillers": ("Lips", "Lip_Enhancement"),
            "Hair Transplant": ("Hair", "Hair_Restoration")
        }
        
        # Create final mapping
        for proc_name, cat_key in procedure_categories.items():
            cat_id = categories.get(cat_key)
            if cat_id:
                category_mapping[proc_name] = cat_id
            else:
                logger.warning(f"No category found for {proc_name} -> {cat_key}")
        
        return category_mapping
    except Exception as e:
        logger.error(f"Error getting category mapping: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def add_procedures():
    """Add essential procedures to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    
    try:
        # Get category mapping
        category_mapping = get_category_mapping()
        
        if not category_mapping:
            logger.error("Failed to get category mapping. Run Steps 2 and 3 first.")
            return 0
        
        # Procedure details
        procedures = [
            {
                "name": "Rhinoplasty",
                "alt_names": "Nose Job, Nasal Reshaping",
                "short_desc": "Reshapes the nose for aesthetic or functional reasons.",
                "overview": "Rhinoplasty modifies nasal shape for cosmetic reasons or to correct breathing issues or trauma deformities.",
                "details": "Open or closed technique; cartilage reshaping, bone trimming or grafting may be done.",
                "ideal_candidates": "Individuals with nasal asymmetry, humps, or breathing problems.",
                "recovery_time": "1-2 weeks",
                "procedure_duration": "1-3 hours",
                "hospital_stay": "No",
                "min_cost": 120000,
                "max_cost": 250000,
                "risks": "Bleeding, infection, breathing issues, dissatisfaction with results.",
                "body_part": "Nose",
                "body_area": "Face",
                "category_type": "Surgical"
            },
            {
                "name": "Breast Augmentation",
                "alt_names": "Boob Job, Breast Enhancement Surgery",
                "short_desc": "Enhances breast size using implants or fat transfer.",
                "overview": "Breast augmentation involves increasing the size or enhancing the shape of breasts using implants or fat grafting.",
                "details": "Performed under general anesthesia; involves placing silicone or saline implants or injecting fat tissue into breasts.",
                "ideal_candidates": "Women with small or asymmetrical breasts, post-pregnancy changes.",
                "recovery_time": "1-2 weeks",
                "procedure_duration": "1-2 hours",
                "hospital_stay": "No",
                "min_cost": 150000,
                "max_cost": 350000,
                "risks": "Infection, capsular contracture, implant rupture.",
                "body_part": "Breasts",
                "body_area": "Breasts",
                "category_type": "Surgical"
            },
            {
                "name": "Facelift",
                "alt_names": "Rhytidectomy, Face Rejuvenation",
                "short_desc": "Reduces signs of aging in the face and neck.",
                "overview": "A facelift improves visible signs of aging by tightening facial tissues and removing excess skin.",
                "details": "Involves incisions around ears and hairline, separating skin from tissues, repositioning deeper layers, and removing excess skin.",
                "ideal_candidates": "People with sagging facial skin, jowls, and deep wrinkles.",
                "recovery_time": "2-3 weeks",
                "procedure_duration": "2-4 hours",
                "hospital_stay": "Sometimes",
                "min_cost": 200000,
                "max_cost": 450000,
                "risks": "Scarring, nerve injury, hematoma, infection.",
                "body_part": "Face",
                "body_area": "Face",
                "category_type": "Surgical"
            },
            {
                "name": "Liposuction",
                "alt_names": "Lipo, Fat Removal, Body Contouring",
                "short_desc": "Removes stubborn fat deposits to contour body areas.",
                "overview": "Liposuction removes localized fat deposits that are resistant to diet and exercise, improving body contours.",
                "details": "A cannula (thin tube) is inserted through small incisions to suction out fat from specific areas.",
                "ideal_candidates": "People at a stable weight with good skin elasticity and stubborn fat pockets.",
                "recovery_time": "1-2 weeks",
                "procedure_duration": "1-4 hours",
                "hospital_stay": "No",
                "min_cost": 80000,
                "max_cost": 300000,
                "risks": "Contour irregularities, numbness, infection, fluid accumulation.",
                "body_part": "Body",
                "body_area": "Body",
                "category_type": "Surgical"
            },
            {
                "name": "Botox",
                "alt_names": "Botulinum Toxin, Anti-wrinkle Injections",
                "short_desc": "Reduces wrinkles and fine lines with injectable neuromodulator.",
                "overview": "Botox temporarily paralyzes muscles to reduce the appearance of wrinkles and prevent new wrinkles from forming.",
                "details": "Small amounts of botulinum toxin are injected into specific muscles, blocking nerve signals that cause muscle contractions.",
                "ideal_candidates": "People with dynamic wrinkles like crow's feet, forehead lines, and frown lines.",
                "recovery_time": "0-1 days",
                "procedure_duration": "15-30 minutes",
                "hospital_stay": "No",
                "min_cost": 15000,
                "max_cost": 50000,
                "risks": "Bruising, headache, temporary facial weakness, drooping eyelid.",
                "body_part": "Face",
                "body_area": "Face",
                "category_type": "Non-Surgical"
            }
        ]
        
        # Add each procedure
        for proc in procedures:
            cat_id = category_mapping.get(proc["name"])
            if not cat_id:
                logger.warning(f"No category ID for {proc['name']}. Skipping.")
                continue
            
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
                body_part,
                body_area,
                category_type,
                category_id,
                created_at,
                updated_at,
                popularity_score,
                avg_rating,
                review_count
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s
            )
            """, (
                proc["name"],
                proc["alt_names"],
                proc["short_desc"],
                proc["overview"],
                proc["details"],
                proc["ideal_candidates"],
                "Standard recovery process",  # recovery_process
                proc["recovery_time"],
                proc["procedure_duration"],
                proc["hospital_stay"],
                "Results vary by individual",  # results_duration
                proc["min_cost"],
                proc["max_cost"],
                "Improved appearance and confidence",  # benefits
                "Enhanced aesthetics and self-image",  # benefits_detailed
                proc["risks"],
                "Standard procedure",  # procedure_types
                "Various alternatives available",  # alternative_procedures
                proc["body_part"],
                proc["body_area"],
                proc["category_type"],
                cat_id,
                5,  # popularity_score
                0,  # avg_rating
                0   # review_count
            ))
            
            count += 1
            logger.info(f"Added procedure: {proc['name']}")
        
        conn.commit()
        logger.info(f"Added {count} procedures")
        return count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding procedures: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to execute Step 4."""
    try:
        logger.info("Step 4: Add essential procedures to the database")
        
        # Add procedures
        count = add_procedures()
        
        logger.info(f"Step 4 complete. Added {count} procedures to the database.")
        logger.info("Import process complete. The database now has essential procedures, categories, and body parts.")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()