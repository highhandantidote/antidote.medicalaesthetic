#!/usr/bin/env python3
"""
Final attempt to add the remaining procedures directly to the database.
This script uses hardcoded values for maximum reliability.
"""
import os
import psycopg2
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_connection():
    """Get a database connection."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def add_remaining_procedures():
    """Add the remaining procedures one by one."""
    procedures = [
        {"name": "Jewel Tone Facial", "description": "Luxury facial with gemstone-infused products."},
        {"name": "Kaya Deep Cleanse", "description": "Deep pore cleansing treatment for oily skin."},
        {"name": "Luminous Lift Pro", "description": "Lifting and firming treatment for sagging skin."},
        {"name": "Micro Touch Therapy", "description": "Microcurrent treatment that tones facial muscles."},
        {"name": "Natural Radiance Boost", "description": "Organic treatment that enhances skin's natural glow."},
        {"name": "Oxygen Infusion Facial", "description": "Treatment that infuses oxygen into the skin."},
        {"name": "Pristine Peel Treatment", "description": "Gentle peel that improves skin texture."},
        {"name": "Quantum Skin Renewal", "description": "Advanced treatment that accelerates skin renewal."},
        {"name": "Radiance Restore Pro", "description": "Restores radiance to dull, dehydrated skin."},
        {"name": "Silken Smooth Facial", "description": "Leaves skin with a silky smooth texture."},
        {"name": "Timeless Beauty Ritual", "description": "Anti-aging ritual with multiple steps."},
        {"name": "Ultra Glow Treatment", "description": "Instant glow-boosting treatment."},
        {"name": "Vital Rejuvenation", "description": "Comprehensive facial rejuvenation treatment."},
        {"name": "Wellness Facial Therapy", "description": "Holistic facial that promotes overall wellness."},
        {"name": "Xcelerate Skin Renew", "description": "Accelerates skin cell turnover."},
        {"name": "Youth Extend Facial", "description": "Anti-aging treatment that extends youthful appearance."},
        {"name": "Zenith Beauty Treatment", "description": "Ultimate luxury facial experience."}
    ]
    
    # First, get or create Body Part and Category
    conn = get_connection()
    body_part_id = None
    category_id = None
    
    try:
        with conn.cursor() as cursor:
            # Get or create Face body part
            cursor.execute("SELECT id FROM body_parts WHERE name = 'Face'")
            result = cursor.fetchone()
            if result:
                body_part_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO body_parts (name, created_at) VALUES ('Face', %s) RETURNING id",
                    (datetime.utcnow(),)
                )
                body_part_id = cursor.fetchone()[0]
                conn.commit()
            
            # Get or create Facial Treatments category
            cursor.execute("SELECT id FROM categories WHERE name = 'Facial Treatments'")
            result = cursor.fetchone()
            if result:
                category_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO categories (name, body_part_id, created_at) VALUES ('Facial Treatments', %s, %s) RETURNING id",
                    (body_part_id, datetime.utcnow())
                )
                category_id = cursor.fetchone()[0]
                conn.commit()
    except Exception as e:
        logger.error(f"Error getting body part and category: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
    if not body_part_id or not category_id:
        logger.error("Failed to get body part ID or category ID. Cannot continue.")
        return 0
    
    logger.info(f"Using body_part_id={body_part_id}, category_id={category_id}")
    
    # Add procedures one by one
    added_count = 0
    
    for procedure in procedures:
        # Skip if procedure already exists
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM procedures WHERE procedure_name = %s",
                    (procedure["name"],)
                )
                if cursor.fetchone():
                    logger.info(f"Procedure {procedure['name']} already exists. Skipping.")
                    conn.close()
                    continue
            
            # Add new procedure with separate connection
            conn.close()
            conn = get_connection()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO procedures (
                        procedure_name, 
                        short_description, 
                        overview, 
                        procedure_details, 
                        ideal_candidates, 
                        recovery_time, 
                        min_cost, 
                        max_cost, 
                        risks, 
                        procedure_types, 
                        category_id, 
                        body_part, 
                        tags, 
                        body_area, 
                        category_type, 
                        created_at, 
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    procedure["name"],
                    procedure["description"],
                    f"A premium facial treatment for rejuvenation and beauty enhancement.",
                    f"The {procedure['name']} is performed by trained aestheticians.",
                    "Adults seeking facial rejuvenation",
                    "1-3 days",
                    10000,
                    30000,
                    "Minor redness or irritation (temporary)",
                    "Standard",
                    category_id,
                    "Face",
                    ["facial", "cosmetic", "rejuvenation"],
                    "Face",
                    "Facial Treatments",
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                conn.commit()
                
                added_count += 1
                logger.info(f"Successfully added procedure {added_count}: {procedure['name']}")
        
        except Exception as e:
            logger.error(f"Error adding procedure {procedure['name']}: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    # Get final count
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            final_count = cursor.fetchone()[0]
            logger.info(f"Final procedure count: {final_count}")
    finally:
        conn.close()
    
    return added_count

def main():
    """Run the final procedure import."""
    logger.info("Starting final procedure import")
    start_time = datetime.now()
    
    # Get initial procedure count
    conn = get_connection()
    initial_count = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            initial_count = cursor.fetchone()[0]
            logger.info(f"Initial procedure count: {initial_count}")
    finally:
        conn.close()
    
    # Add remaining procedures
    added_count = add_remaining_procedures()
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Added {added_count} procedures in {elapsed:.2f} seconds")
    logger.info(f"Initial count: {initial_count}, Final count: {initial_count + added_count}")

if __name__ == "__main__":
    main()