#!/usr/bin/env python3
"""
Step 2: Add top 10 procedures to the database.

This is the second step in a multi-step import process.
Uses category IDs from Step 1.
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

def load_category_ids():
    """Load category IDs from file created in Step 1."""
    category_map = {}
    procedure_categories = {}
    
    try:
        with open('category_ids.txt', 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 3:
                    body_part, name, cat_id = parts
                    category_map[(body_part, name)] = int(cat_id)
        
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
        
        logger.info(f"Loaded {len(category_map)} category IDs from file")
        
        return category_map, procedure_categories
    except Exception as e:
        logger.error(f"Error loading category IDs: {e}")
        return {}, {}

def add_procedures():
    """Add top 10 procedures to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    
    try:
        # Load category IDs
        category_map, procedure_categories = load_category_ids()
        
        if not category_map or not procedure_categories:
            logger.error("Failed to load category IDs. Run Step 1 first.")
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
            },
            {
                "name": "Tummy Tuck",
                "alt_names": "Abdominoplasty, Belly Fat Removal Surgery",
                "short_desc": "Removes excess skin and fat, tightens abdominal muscles.",
                "overview": "A tummy tuck improves abdominal contour by removing excess skin and fat, and tightening abdominal muscles.",
                "details": "Full or mini abdominoplasty depending on extent. Involves incision from hip to hip, muscle tightening, skin removal.",
                "ideal_candidates": "Individuals with loose skin post-pregnancy or weight loss.",
                "recovery_time": "2-4 weeks",
                "procedure_duration": "2-4 hours",
                "hospital_stay": "Yes",
                "min_cost": 180000,
                "max_cost": 380000,
                "risks": "Scarring, infection, seroma, poor wound healing.",
                "body_part": "Stomach",
                "body_area": "Body",
                "category_type": "Surgical"
            },
            {
                "name": "Brazilian Butt Lift",
                "alt_names": "BBL, Butt Enhancement Surgery",
                "short_desc": "Enhances buttocks using fat transfer from other areas.",
                "overview": "A BBL involves liposuction of fat from areas like the abdomen or thighs, then injecting purified fat into the buttocks.",
                "details": "Fat is harvested via liposuction, processed, and strategically injected into buttocks for volume and shape.",
                "ideal_candidates": "People with enough fat for harvesting and seeking natural butt enhancement.",
                "recovery_time": "2-3 weeks",
                "procedure_duration": "2-3 hours",
                "hospital_stay": "No",
                "min_cost": 200000,
                "max_cost": 400000,
                "risks": "Fat reabsorption, infection, asymmetry, fat embolism.",
                "body_part": "Butt",
                "body_area": "Body",
                "category_type": "Surgical"
            },
            {
                "name": "Eyelid Surgery",
                "alt_names": "Blepharoplasty, Eye Lift",
                "short_desc": "Removes excess skin, muscle, and fat from eyelids.",
                "overview": "Eyelid surgery rejuvenates the eyes by addressing sagging skin, bags, and puffiness around the eyes.",
                "details": "Incisions along natural eyelid creases to remove excess tissue and fat from upper and/or lower eyelids.",
                "ideal_candidates": "People with droopy upper eyelids or puffy lower eyelids that affect appearance or vision.",
                "recovery_time": "1-2 weeks",
                "procedure_duration": "1-2 hours",
                "hospital_stay": "No",
                "min_cost": 80000,
                "max_cost": 200000,
                "risks": "Dry eyes, irritation, temporary vision changes, asymmetry.",
                "body_part": "Eyes",
                "body_area": "Face",
                "category_type": "Surgical"
            },
            {
                "name": "Lip Fillers",
                "alt_names": "Lip Injections, Lip Augmentation",
                "short_desc": "Enhances lip volume and shape with dermal fillers.",
                "overview": "Lip fillers involve injecting hyaluronic acid-based dermal fillers to add volume, define shape, and address asymmetry.",
                "details": "A series of small injections to add volume to the lips, vermillion border, and perioral lines.",
                "ideal_candidates": "People seeking fuller lips or correction of lip asymmetries.",
                "recovery_time": "1-3 days",
                "procedure_duration": "15-30 minutes",
                "hospital_stay": "No",
                "min_cost": 20000,
                "max_cost": 50000,
                "risks": "Bruising, swelling, lumps, asymmetry, allergic reaction.",
                "body_part": "Lips",
                "body_area": "Face",
                "category_type": "Non-Surgical"
            },
            {
                "name": "Hair Transplant",
                "alt_names": "Hair Restoration, FUE, FUT",
                "short_desc": "Restores hair growth in balding or thinning areas.",
                "overview": "Hair transplantation involves extracting hair follicles from donor areas and implanting them in areas with hair loss.",
                "details": "FUE (Follicular Unit Extraction) or FUT (Follicular Unit Transplantation) techniques to relocate hair follicles.",
                "ideal_candidates": "People with pattern baldness and healthy donor hair areas.",
                "recovery_time": "1-2 weeks",
                "procedure_duration": "4-8 hours",
                "hospital_stay": "No",
                "min_cost": 100000,
                "max_cost": 300000,
                "risks": "Scarring, infection, grafts not taking, unnatural appearance.",
                "body_part": "Hair",
                "body_area": "Face",
                "category_type": "Surgical"
            }
        ]
        
        for proc in procedures:
            # Get category ID
            cat_key = procedure_categories.get(proc["name"])
            if not cat_key:
                logger.warning(f"No category mapping for {proc['name']}")
                continue
                
            category_id = category_map.get(cat_key)
            if not category_id:
                logger.warning(f"Category ID not found for {cat_key}")
                continue
            
            cursor.execute("""
            INSERT INTO procedures (
                procedure_name,
                alternative_names,
                short_description,
                overview,
                procedure_details,
                ideal_candidates,
                recovery_time,
                procedure_duration,
                hospital_stay_required,
                min_cost,
                max_cost,
                risks,
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
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s
            )
            """, (
                proc["name"],
                proc["alt_names"],
                proc["short_desc"],
                proc["overview"],
                proc["details"],
                proc["ideal_candidates"],
                proc["recovery_time"],
                proc["procedure_duration"],
                proc["hospital_stay"],
                proc["min_cost"],
                proc["max_cost"],
                proc["risks"],
                proc["body_part"],
                proc["body_area"],
                proc["category_type"],
                category_id,
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
    """Main function to execute Step 2."""
    try:
        logger.info("Step 2: Add top 10 procedures to the database")
        
        # Add procedures
        count = add_procedures()
        
        logger.info(f"Step 2 complete. Added {count} procedures to the database.")
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()