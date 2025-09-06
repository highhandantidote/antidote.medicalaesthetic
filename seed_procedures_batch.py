#!/usr/bin/env python3
"""
Seed procedures to the database in small batches to avoid timeouts.

This script systematically adds all 117 procedures required for the RealSelf hierarchy schema.
It uses direct SQL and small batch transactions with progress reporting.
"""
import os
import sys
import psycopg2
import logging
from datetime import datetime
import time
import random

# Configure logging
LOG_FILE = f"procedure_seeding_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 5  # Small batches to avoid timeouts
TARGET_TOTAL = 117  # Target total procedures

def connect_to_db():
    """Connect to the PostgreSQL database."""
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False  # Manual transaction control
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to the database: {str(e)}")
        raise

def get_existing_data(conn):
    """Get existing data from the database to avoid duplicates."""
    logger.info("Retrieving existing data...")
    existing_body_parts = {}
    existing_categories = {}
    existing_procedures = []
    
    try:
        with conn.cursor() as cur:
            # Get body parts
            cur.execute("SELECT id, name FROM body_parts")
            for row in cur.fetchall():
                existing_body_parts[row[1]] = row[0]
            logger.info(f"Found {len(existing_body_parts)} existing body parts")
            
            # Get categories
            cur.execute("SELECT id, name, body_part_id FROM categories")
            for row in cur.fetchall():
                existing_categories[row[1]] = {"id": row[0], "body_part_id": row[2]}
            logger.info(f"Found {len(existing_categories)} existing categories")
            
            # Get procedure names
            cur.execute("SELECT id, procedure_name FROM procedures")
            existing_procedures = [(row[0], row[1]) for row in cur.fetchall()]
            logger.info(f"Found {len(existing_procedures)} existing procedures")
            
        return existing_body_parts, existing_categories, existing_procedures
    except Exception as e:
        logger.error(f"Error retrieving existing data: {str(e)}")
        conn.rollback()
        raise

def ensure_body_parts_exist(conn, needed_body_parts, existing_body_parts):
    """Ensure all needed body parts exist in the database."""
    logger.info("Ensuring required body parts exist...")
    body_parts = existing_body_parts.copy()
    
    try:
        with conn.cursor() as cur:
            for name in needed_body_parts:
                if name not in body_parts:
                    logger.info(f"Adding body part: {name}")
                    cur.execute(
                        "INSERT INTO body_parts (name, description, created_at) VALUES (%s, %s, %s) RETURNING id",
                        (name, f"The {name.lower()} area", datetime.utcnow())
                    )
                    body_part_id = cur.fetchone()[0]
                    body_parts[name] = body_part_id
                    logger.info(f"Added body part {name} with id {body_part_id}")
        
        conn.commit()
        return body_parts
    except Exception as e:
        logger.error(f"Error ensuring body parts: {str(e)}")
        conn.rollback()
        raise

def ensure_categories_exist(conn, needed_categories, existing_body_parts, existing_categories):
    """Ensure all needed categories exist in the database."""
    logger.info("Ensuring required categories exist...")
    categories = existing_categories.copy()
    
    try:
        with conn.cursor() as cur:
            for body_part, category_names in needed_categories.items():
                if body_part in existing_body_parts:
                    body_part_id = existing_body_parts[body_part]
                    
                    for category_name in category_names:
                        if category_name not in categories:
                            logger.info(f"Adding category: {category_name} for body part: {body_part}")
                            cur.execute(
                                "INSERT INTO categories (name, body_part_id, description, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
                                (category_name, body_part_id, f"{category_name} for {body_part}", datetime.utcnow())
                            )
                            category_id = cur.fetchone()[0]
                            categories[category_name] = {"id": category_id, "body_part_id": body_part_id}
                            logger.info(f"Added category {category_name} with id {category_id}")
        
        conn.commit()
        return categories
    except Exception as e:
        logger.error(f"Error ensuring categories: {str(e)}")
        conn.rollback()
        raise

def generate_procedure_data(body_part, category_name, procedure_num):
    """Generate procedure data for the given body part and category."""
    # Base procedure names by body part
    procedure_names = {
        "Face": [
            "Rhinoplasty", "Facelift", "Brow Lift", "Eyelid Surgery", "Otoplasty",
            "Facial Implants", "Lip Augmentation", "Chin Augmentation", "Neck Lift",
            "Cheek Augmentation", "Botox", "Facial Fillers", "Chemical Peel",
            "Microdermabrasion", "Laser Skin Resurfacing", "Facial Fat Transfer",
            "Thread Lift", "Non-Surgical Facelift", "Facial Liposuction",
            "Jawline Contouring", "Dimple Creation", "Forehead Reduction",
            "Lip Lift", "Lip Reduction", "Buccal Fat Removal"
        ],
        "Breast": [
            "Breast Augmentation", "Breast Lift", "Breast Reduction", "Breast Reconstruction",
            "Breast Implant Removal", "Breast Implant Exchange", "Breast Implant Revision",
            "Nipple Correction", "Areola Reduction", "Male Breast Reduction",
            "Breast Fat Transfer", "Tuberous Breast Correction"
        ],
        "Body": [
            "Liposuction", "Tummy Tuck", "Brazilian Butt Lift", "Body Lift",
            "Arm Lift", "Thigh Lift", "Mommy Makeover", "Labiaplasty",
            "Vaginoplasty", "Buttock Implants", "Calf Implants", "Male Enhancement",
            "Body Contouring", "Post-Bariatric Surgery", "CoolSculpting",
            "SculpSure", "Smart Lipo", "Cellulite Treatment", "Stretch Mark Removal"
        ]
    }
    
    # Use a base procedure name or generate a variation
    base_names = procedure_names.get(body_part, ["Generic Procedure"])
    
    if procedure_num < len(base_names):
        procedure_name = base_names[procedure_num]
    else:
        # Create variations if we've used all base names
        base_name = random.choice(base_names)
        variations = ["Advanced", "Modern", "Refined", "Premium", "Enhanced", "Ultra", "Precision", "Natural"]
        procedure_name = f"{random.choice(variations)} {base_name}"
    
    # Generate cost range based on body part
    if body_part == "Face":
        min_cost = random.randint(1000, 8000)
        max_cost = min_cost + random.randint(2000, 7000)
    elif body_part == "Breast":
        min_cost = random.randint(4000, 9000)
        max_cost = min_cost + random.randint(3000, 8000)
    else:  # Body
        min_cost = random.randint(2000, 10000)
        max_cost = min_cost + random.randint(3000, 10000)
    
    return {
        "name": procedure_name,
        "body_part": body_part,
        "category_name": category_name,
        "min_cost": min_cost,
        "max_cost": max_cost,
        "short_description": f"A {body_part.lower()} procedure for enhancing appearance.",
        "overview": f"This {procedure_name} procedure focuses on enhancing the {body_part.lower()} area.",
        "procedure_details": f"The {procedure_name} procedure involves using advanced techniques to improve {body_part.lower()} aesthetics.",
        "ideal_candidates": f"Ideal candidates for {procedure_name} are individuals who wish to enhance their {body_part.lower()} appearance.",
        "recovery_time": f"{random.randint(1, 14)} days",
        "risks": "Infection, scarring, asymmetry, anesthesia risks",
        "procedure_types": f"{procedure_name} Standard, {procedure_name} Premium",
        "tags": [body_part, category_name, procedure_name.split()[0]]
    }

def add_procedures_batch(conn, batch, existing_procedures, categories):
    """Add a batch of procedures to the database."""
    added_count = 0
    
    try:
        with conn.cursor() as cur:
            for proc in batch:
                # Check if procedure name already exists
                if any(p[1] == proc["name"] for p in existing_procedures):
                    logger.info(f"Procedure {proc['name']} already exists, skipping")
                    continue
                
                # Get category ID
                if proc["category_name"] in categories:
                    category_id = categories[proc["category_name"]]["id"]
                    
                    # Format tags for array
                    tags_arr = "{" + ",".join(f'"{tag}"' for tag in proc["tags"]) + "}"
                    
                    # Insert procedure
                    cur.execute("""
                        INSERT INTO procedures 
                        (procedure_name, short_description, overview, procedure_details, ideal_candidates, 
                        recovery_time, min_cost, max_cost, risks, procedure_types, category_id, body_part, created_at,
                        tags)
                        VALUES 
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        proc["name"],
                        proc["short_description"],
                        proc["overview"],
                        proc["procedure_details"],
                        proc["ideal_candidates"],
                        proc["recovery_time"],
                        proc["min_cost"],
                        proc["max_cost"],
                        proc["risks"],
                        proc["procedure_types"],
                        category_id,
                        proc["body_part"],
                        datetime.utcnow(),
                        tags_arr
                    ))
                    
                    proc_id = cur.fetchone()[0]
                    existing_procedures.append((proc_id, proc["name"]))
                    added_count += 1
                    logger.info(f"Added procedure {proc['name']} with id {proc_id}")
                else:
                    logger.warning(f"Skipping procedure {proc['name']}: category {proc['category_name']} not found")
            
            # Commit after processing the batch
            conn.commit()
            logger.info(f"Batch committed successfully, added {added_count} procedures")
            
            return added_count
    except Exception as e:
        logger.error(f"Error adding procedure batch: {str(e)}")
        conn.rollback()
        raise

def main():
    """Run the procedure seeding script with batching."""
    logger.info("Starting procedure seeding script with batching...")
    start_time = time.time()
    
    try:
        # Connect to the database
        conn = connect_to_db()
        
        # Get existing data
        body_parts, categories, existing_procedures = get_existing_data(conn)
        
        # Check if we already have enough procedures
        if len(existing_procedures) >= TARGET_TOTAL:
            logger.info(f"Already have {len(existing_procedures)} procedures, which meets or exceeds the target of {TARGET_TOTAL}")
            conn.close()
            return 0
        
        # Check database connection timeout settings
        with conn.cursor() as cur:
            try:
                cur.execute("SHOW statement_timeout")
                result = cur.fetchone()
                timeout = result[0] if result else None
                logger.info(f"Database statement timeout: {timeout}")
            except Exception as e:
                logger.warning(f"Could not check statement_timeout: {e}")
                timeout = None
            
            # Set a shorter timeout if needed
            if timeout is None or timeout == '0':  # None or 0 means no timeout
                logger.info("Setting statement timeout to 30s for safety")
                cur.execute("SET statement_timeout = '30s'")
        
        conn.commit()
        
        # Ensure all needed body parts exist
        needed_body_parts = ["Face", "Breast", "Body"]
        body_parts = ensure_body_parts_exist(conn, needed_body_parts, body_parts)
        
        # Ensure all needed categories exist
        needed_categories = {
            "Face": ["Facial Procedures", "Facial Rejuvenation", "Minimally Invasive"],
            "Breast": ["Breast Augmentation", "Breast Reconstruction", "Breast Reduction"],
            "Body": ["Body Contouring", "Post-Weight Loss", "Body Sculpting"]
        }
        categories = ensure_categories_exist(conn, needed_categories, body_parts, categories)
        
        # Calculate how many more procedures we need
        remaining = TARGET_TOTAL - len(existing_procedures)
        logger.info(f"Need to add {remaining} more procedures to reach target of {TARGET_TOTAL}")
        
        # Generate procedures with proper distribution
        all_procedures = []
        
        # Distribute procedures across body parts (50% Face, 30% Breast, 20% Body)
        face_count = int(remaining * 0.5)
        breast_count = int(remaining * 0.3)
        body_count = remaining - face_count - breast_count
        
        logger.info(f"Distribution plan: Face: {face_count}, Breast: {breast_count}, Body: {body_count}")
        
        # Generate Face procedures
        for i in range(face_count):
            category = random.choice(needed_categories["Face"])
            all_procedures.append(generate_procedure_data("Face", category, i))
        
        # Generate Breast procedures
        for i in range(breast_count):
            category = random.choice(needed_categories["Breast"])
            all_procedures.append(generate_procedure_data("Breast", category, i))
        
        # Generate Body procedures
        for i in range(body_count):
            category = random.choice(needed_categories["Body"])
            all_procedures.append(generate_procedure_data("Body", category, i))
        
        # Add procedures in small batches
        total_added = 0
        for i in range(0, len(all_procedures), BATCH_SIZE):
            batch = all_procedures[i:i+BATCH_SIZE]
            logger.info(f"Processing batch {i//BATCH_SIZE + 1} of {(len(all_procedures) + BATCH_SIZE - 1) // BATCH_SIZE}")
            
            try:
                added = add_procedures_batch(conn, batch, existing_procedures, categories)
                total_added += added
                logger.info(f"Progress: {total_added}/{len(all_procedures)} procedures added")
                
                # Brief pause between batches to avoid overwhelming the database
                if i + BATCH_SIZE < len(all_procedures):
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error processing batch {i//BATCH_SIZE + 1}: {str(e)}")
                # Continue with next batch even if one fails
        
        # Final count
        final_count = len(existing_procedures)
        logger.info(f"Seeding completed. Added {total_added} new procedures.")
        logger.info(f"Total procedures in database: {final_count}")
        
        if final_count >= TARGET_TOTAL:
            logger.info(f"Successfully reached target of {TARGET_TOTAL} procedures.")
        else:
            logger.warning(f"Only added {final_count}/{TARGET_TOTAL} procedures. May need to run again.")
        
        # Close connection
        conn.close()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Total execution time: {elapsed_time:.2f} seconds")
        logger.info(f"Full log available at: {LOG_FILE}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error in procedure seeding: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())