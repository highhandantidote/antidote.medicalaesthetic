#!/usr/bin/env python3
"""
Add specialized medical procedures to the Antidote platform database.

This script adds a set of high-value, specialized cosmetic procedures to enhance 
the medical marketplace offerings.
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
                    "SELECT id FROM body_parts WHERE name ILIKE %s",
                    (f"%{body_part_name[:4]}%",)  # Try with just first few chars
                )
                result = cursor.fetchone()
                
            if not result:
                # Last resort, get any body part
                cursor.execute("SELECT id FROM body_parts LIMIT 1")
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
                # Try a more general search
                cursor.execute(
                    "SELECT id FROM categories WHERE body_part_id = %s LIMIT 1",
                    (body_part_id,)
                )
                result = cursor.fetchone()
                
            if not result:
                # Last resort, get any category
                cursor.execute("SELECT id FROM categories LIMIT 1")
                result = cursor.fetchone()
            
            return result[0] if result else None
            
    except Exception as e:
        logger.error(f"Error finding category ID: {str(e)}")
        return None

def add_procedures():
    """Add specialized procedures to the database."""
    conn = get_db_connection()
    procedures_added = 0
    
    try:
        # Specialized medical procedures with detailed information
        specialized_procedures = [
            {
                "name": "Advanced Microneedling with Growth Factors",
                "body_part": "Face",
                "category": "Non-surgical",
                "short_description": "Premium microneedling treatment enhanced with growth factors",
                "overview": "This advanced treatment combines traditional microneedling with specialized growth factors to stimulate collagen production and enhance skin regeneration.",
                "min_cost": 15000,
                "max_cost": 30000,
                "procedure_details": "The procedure uses a medical-grade microneedling device to create micro-channels in the skin, followed by the application of premium growth factors derived from human cells.",
                "recovery_time": "3-5 days of redness and mild swelling",
                "risks": "Temporary redness, mild swelling, potential infection if aftercare instructions not followed",
                "procedure_types": "Basic, Premium, and Platinum options available depending on growth factor concentration",
                "recovery_process": "Gentle cleansing, avoiding sun exposure, and applying recommended post-treatment serums",
                "benefits": "Improved skin texture, reduced fine lines, and enhanced overall complexion",
                "alternative_procedures": "Chemical peels, laser resurfacing, or standard microneedling",
                "ideal_candidates": "Adults with signs of aging, acne scarring, or uneven skin tone",
                "benefits_detailed": "Stimulates natural collagen production, reduces appearance of scars, improves skin elasticity, and creates a more youthful appearance",
                "results_duration": "Results may last 6-12 months with proper skincare maintenance",
                "hospital_stay_required": "No",
                "procedure_duration": "60-90 minutes"
            },
            {
                "name": "360° Jawline Contouring",
                "body_part": "Face",
                "category": "Surgical",
                "short_description": "Comprehensive jawline enhancement through multiple techniques",
                "overview": "A complete approach to jawline definition combining surgical and non-surgical techniques for optimal facial harmony.",
                "min_cost": 80000,
                "max_cost": 150000,
                "procedure_details": "This procedure may involve implant placement, liposuction under the chin, bone reshaping, and strategic filler placement for a balanced result.",
                "recovery_time": "10-14 days before returning to normal activities",
                "risks": "Swelling, bruising, temporary numbness, potential infection, asymmetry",
                "procedure_types": "Surgical, Hybrid (surgical + non-surgical), or Non-surgical options",
                "recovery_process": "Initial rest period, cold compresses, prescribed medications, and gradual return to activities",
                "benefits": "Enhanced facial proportions, more defined profile, and improved confidence",
                "alternative_procedures": "Fillers alone, chin implant only, or neck liposuction",
                "ideal_candidates": "Adults with weak jawline definition, excess submental fat, or facial asymmetry",
                "benefits_detailed": "Creates a more balanced facial appearance, enhances profile aesthetics, improves perceived facial strength, and creates a more youthful neck-jaw transition",
                "results_duration": "Permanent for surgical components, 1-2 years for any fillers used",
                "hospital_stay_required": "Sometimes, depending on extent of procedure",
                "procedure_duration": "2-4 hours"
            },
            {
                "name": "Radio-Frequency Assisted Lipolysis",
                "body_part": "Body",
                "category": "Minimally-invasive",
                "short_description": "Advanced fat removal and skin tightening procedure",
                "overview": "This technology uses radio-frequency energy to simultaneously melt fat and tighten skin for improved body contouring results.",
                "min_cost": 60000,
                "max_cost": 120000,
                "procedure_details": "A small wand is inserted through tiny incisions to deliver radio-frequency energy, liquefying fat cells while stimulating collagen production in the skin.",
                "recovery_time": "3-7 days before returning to normal activities",
                "risks": "Temporary swelling, bruising, numbness, minor scarring at insertion points",
                "procedure_types": "Small area, Medium area, or Full body treatments",
                "recovery_process": "Wearing compression garments, light activity for first week, avoiding strenuous exercise for 2-3 weeks",
                "benefits": "Fat reduction with simultaneous skin tightening for a smoother result",
                "alternative_procedures": "Traditional liposuction, non-invasive fat reduction, or surgical body contouring",
                "ideal_candidates": "Adults with localized fat deposits and mild to moderate skin laxity",
                "benefits_detailed": "Removes unwanted fat, tightens loose skin, requires only local anesthesia, and results in minimal downtime compared to traditional procedures",
                "results_duration": "Permanent fat removal with proper weight management",
                "hospital_stay_required": "No",
                "procedure_duration": "1-3 hours depending on treatment area"
            },
            {
                "name": "Stem Cell Hair Restoration",
                "body_part": "Scalp",
                "category": "Regenerative",
                "short_description": "Cutting-edge hair loss treatment using stem cell technology",
                "overview": "This innovative treatment harnesses the regenerative power of stem cells to stimulate dormant hair follicles and promote new growth.",
                "min_cost": 75000,
                "max_cost": 150000,
                "procedure_details": "Stem cells are extracted from the patient's own tissues, processed to concentrate growth factors, and then injected into the scalp to stimulate hair follicles.",
                "recovery_time": "1-2 days of minor scalp sensitivity",
                "risks": "Temporary discomfort, potential for insufficient response in advanced hair loss",
                "procedure_types": "Basic treatment, Premium package with PRP, or Comprehensive program with maintenance sessions",
                "recovery_process": "Avoiding harsh hair products, limiting sun exposure, and following specialized hair care protocol",
                "benefits": "Natural hair regrowth without surgery or daily medication",
                "alternative_procedures": "Hair transplantation, medication therapy, or PRP treatment alone",
                "ideal_candidates": "Adults with early to moderate hair thinning with viable hair follicles",
                "benefits_detailed": "Strengthens existing hair, promotes new growth, improves hair density and quality, and requires no incisions or sutures",
                "results_duration": "Results typically last 1-2 years with maintenance treatments recommended",
                "hospital_stay_required": "No",
                "procedure_duration": "90-120 minutes"
            },
            {
                "name": "HD Body Sculpting",
                "body_part": "Body",
                "category": "Surgical",
                "short_description": "Precise body contouring for athletic definition",
                "overview": "A specialized liposculpture technique that not only removes fat but strategically sculpts the body to enhance muscular definition.",
                "min_cost": 100000,
                "max_cost": 200000,
                "procedure_details": "This advanced technique uses specialized cannulas to precisely remove fat around muscle groups while preserving fat in other areas to create a defined, athletic appearance.",
                "recovery_time": "7-14 days before returning to normal activities",
                "risks": "Swelling, bruising, temporary numbness, contour irregularities if aftercare not followed",
                "procedure_types": "Targeted area treatment, Athletic definition package, or Complete body transformation",
                "recovery_process": "Compression garments, lymphatic massage, and gradual return to physical activity",
                "benefits": "Athletic-looking physique without extreme diet and exercise regimens",
                "alternative_procedures": "Traditional liposuction, non-invasive fat reduction, or regular exercise programs",
                "ideal_candidates": "Adults within 30% of ideal body weight with good skin elasticity",
                "benefits_detailed": "Creates the appearance of a fit, toned physique, enhances existing muscle definition, removes stubborn fat deposits, and provides long-lasting results",
                "results_duration": "Permanent with proper weight management and lifestyle",
                "hospital_stay_required": "Sometimes for extensive procedures",
                "procedure_duration": "3-6 hours depending on areas treated"
            },
            {
                "name": "Combination Thread and Filler Lift",
                "body_part": "Face",
                "category": "Non-surgical",
                "short_description": "Advanced facial rejuvenation using threads and fillers",
                "overview": "This innovative combination treatment uses dissolvable threads to lift sagging tissue and strategic filler placement to restore volume.",
                "min_cost": 45000,
                "max_cost": 90000,
                "procedure_details": "Specialized threads are inserted under the skin to create a supportive structure, while premium hyaluronic acid fillers are placed to restore lost volume and enhance contours.",
                "recovery_time": "3-7 days of mild swelling and potential bruising",
                "risks": "Temporary discomfort, swelling, bruising, thread visibility in thin skin (rare)",
                "procedure_types": "Basic lift, Premium combination, or Ultimate transformation with maintenance plan",
                "recovery_process": "Avoiding facial massage, sleeping with head elevated, and limiting extreme facial expressions for first week",
                "benefits": "Noticeable lift and volume restoration without surgery",
                "alternative_procedures": "Surgical facelift, fillers alone, or thread lift alone",
                "ideal_candidates": "Adults with mild to moderate facial sagging and volume loss",
                "benefits_detailed": "Lifts sagging facial tissues, restores natural facial contours, adds volume to hollow areas, and creates a refreshed appearance without surgery",
                "results_duration": "1-2 years with maintenance treatments recommended",
                "hospital_stay_required": "No",
                "procedure_duration": "60-90 minutes"
            }
        ]
        
        # Process each procedure
        for proc in specialized_procedures:
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
                    # Instead of skipping, let's try to get any category
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT id FROM categories LIMIT 1")
                        result = cursor.fetchone()
                        if result:
                            category_id = result[0]
                        else:
                            logger.error("No categories found in database")
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
                            proc["procedure_details"],
                            proc["recovery_time"],
                            proc["risks"],
                            proc["procedure_types"],
                            proc["recovery_process"],
                            proc["benefits"],
                            proc["alternative_procedures"],
                            proc["ideal_candidates"],
                            proc["benefits_detailed"],
                            proc["results_duration"],
                            proc["hospital_stay_required"],
                            proc["procedure_duration"]
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
    logger.info(f"Added {procedures_added} specialized procedures in {elapsed:.2f} seconds")
    
    logger.info("Specialized procedures import complete!")

if __name__ == "__main__":
    main()