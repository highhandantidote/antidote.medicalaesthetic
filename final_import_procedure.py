#!/usr/bin/env python3
"""
Final procedure import script.

This script handles all required fields and imports procedures
from the CSV file in small batches to avoid timeouts.
"""

import os
import sys
import csv
import time
import logging
from datetime import datetime
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
CSV_FILE_PATH = 'uploads/procedures.csv'
BATCH_SIZE = 5  # Import just a few procedures at a time

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False  # We'll manage transactions manually
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def create_sample_procedures(conn):
    """Create sample procedures with all required fields populated."""
    cursor = conn.cursor()
    
    try:
        # First check if we already have procedures
        cursor.execute("SELECT COUNT(*) FROM procedures")
        count = cursor.fetchone()[0]
        
        if count > 0:
            logger.info(f"Found {count} existing procedures in database")
            return
        
        # Now let's insert a few sample procedures with all required fields
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
            category_id,
            created_at, 
            updated_at
        ) VALUES (
            'Rhinoplasty',
            'Nose Job, Nasal Reshaping',
            'Reshapes the nose for aesthetic or functional reasons.',
            'Rhinoplasty modifies nasal shape for cosmetic reasons or to correct breathing issues or trauma deformities.',
            'Open or closed technique; cartilage reshaping, bone trimming or grafting may be done.',
            'Individuals with nasal asymmetry, humps, or breathing problems.',
            'Recovery involves nasal congestion, swelling, and bruising for several weeks.',
            '1–2 weeks',
            '1–3 hours',
            'No',
            'Permanent with proper care',
            120000,
            250000,
            'Improved facial harmony, corrected breathing issues, enhanced self-confidence.',
            'Improved facial profile, better breathing, correction of defects from injury.',
            'Bleeding, infection, scarring, breathing difficulties, dissatisfaction with results.',
            'Open rhinoplasty, Closed rhinoplasty, Revision rhinoplasty',
            'Non-surgical nose job with fillers',
            'Nose',
            10,
            NOW(),
            NOW()
        )
        """)
        
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
            category_id,
            created_at, 
            updated_at
        ) VALUES (
            'Breast Augmentation',
            'Boob Job, Breast Enhancement Surgery',
            'Enhances breast size using implants or fat transfer.',
            'Breast augmentation involves increasing the size or enhancing the shape of breasts using implants or fat grafting.',
            'Performed under general anesthesia; involves placing silicone or saline implants or injecting fat tissue into breasts.',
            'Women with small or asymmetrical breasts, post-pregnancy changes.',
            'Initial recovery takes 1-2 weeks with full recovery in 6-8 weeks. Limited arm movement initially.',
            '1–2 weeks',
            '1–2 hours',
            'No',
            '10-20 years for implants, permanent for fat transfer',
            150000,
            350000,
            'Enhanced breast size and shape, improved body proportion, increased confidence.',
            'More balanced figure, restoration of pre-pregnancy volume, correction of asymmetry.',
            'Capsular contracture, implant rupture, infection, changes in nipple sensation, scarring.',
            'Silicone implants, Saline implants, Fat transfer',
            'Breast lift, Non-surgical options like padded bras',
            'Breasts',
            11,
            NOW(),
            NOW()
        )
        """)
        
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
            category_id,
            created_at, 
            updated_at
        ) VALUES (
            'Facelift',
            'Rhytidectomy',
            'Tightens facial skin and muscles for a youthful look.',
            'A facelift reduces signs of aging by tightening the skin, removing excess fat, and smoothing wrinkles.',
            'Involves incisions around the ear, removal of excess skin, and repositioning underlying muscles.',
            'Individuals with sagging skin, deep wrinkles, and jowls.',
            'Initial swelling and bruising subsides in 2-3 weeks. Full recovery takes 2-3 months.',
            '2–4 weeks',
            '3–5 hours',
            'Yes',
            '7-10 years',
            250000,
            550000,
            'Smoother, firmer facial appearance, reduced visible signs of aging, long-lasting results.',
            'Reduced jowls, tightened facial contours, improved neck appearance, more youthful jawline.',
            'Scarring, nerve damage, infection, hematoma, asymmetry, dissatisfaction with results.',
            'Traditional facelift, Mini facelift, Deep plane facelift',
            'Thread lift, Fillers, Botox',
            'Face',
            8,
            NOW(),
            NOW()
        )
        """)
        
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
            category_id,
            created_at, 
            updated_at
        ) VALUES (
            'Liposuction',
            'Fat Removal Surgery, Liposculpture',
            'Removes unwanted fat from specific areas of the body.',
            'Liposuction targets stubborn fat deposits and sculpts body contours by removing fat through suction.',
            'Small incisions are made, and fat is removed using a suction device.',
            'Individuals with localized fat pockets or areas resistant to diet and exercise.',
            'Swelling and bruising for 1-2 weeks. Compression garments worn for 4-6 weeks.',
            '1–2 weeks',
            '1–3 hours',
            'No',
            'Permanent if weight is maintained',
            100000,
            350000,
            'Improved body contours, removal of stubborn fat deposits, more proportionate figure.',
            'Enhanced body shape, better-fitting clothes, permanent fat cell removal from treated areas.',
            'Swelling, bruising, skin irregularities, infection, fluid accumulation, uneven results.',
            'Traditional liposuction, Tumescent liposuction, Ultrasound-assisted liposuction',
            'CoolSculpting, Laser lipolysis, Non-surgical fat reduction',
            'Body',
            12,
            NOW(),
            NOW()
        )
        """)
        
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
            category_id,
            created_at, 
            updated_at
        ) VALUES (
            'Botox',
            'Botulinum Toxin Injections',
            'Reduces wrinkles and fine lines.',
            'Botox injections temporarily paralyze facial muscles to smooth wrinkles and fine lines, typically on the forehead, around the eyes, and between the brows.',
            'Small injections are made into facial muscles to reduce muscle movement and soften wrinkles.',
            'Individuals with wrinkles and fine lines, seeking a youthful appearance.',
            'Minimal downtime. Possible mild bruising or swelling at injection sites for 1-2 days.',
            '1–2 days',
            '10–20 minutes',
            'No',
            '3-4 months',
            15000,
            40000,
            'Reduced appearance of wrinkles, prevention of new wrinkles, quick treatment with minimal downtime.',
            'Smoother forehead, reduced crow''s feet, minimized frown lines, prevention of deepening wrinkles.',
            'Bruising, headache, drooping eyelid, unnatural expression, allergic reaction, temporary facial weakness.',
            'Cosmetic Botox, Medical Botox for conditions like hyperhidrosis',
            'Dermal fillers, Chemical peels, Microdermabrasion',
            'Face',
            9,
            NOW(),
            NOW()
        )
        """)
        
        conn.commit()
        
        # Verify the import
        cursor.execute("SELECT COUNT(*) FROM procedures")
        count = cursor.fetchone()[0]
        logger.info(f"Successfully imported {count} sample procedures")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating sample procedures: {e}")
        raise
    finally:
        cursor.close()

def import_procedures_from_csv(conn, start_index, batch_size):
    """Import a batch of procedures from the CSV file."""
    cursor = conn.cursor()
    imported_count = 0
    
    try:
        # Read the CSV file and get a batch of procedures
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            procedures = list(reader)
            
            # Skip to the start index
            if start_index >= len(procedures):
                logger.info(f"No more procedures to import (start_index: {start_index}, total: {len(procedures)})")
                return 0
            
            # Get the batch
            end_index = min(start_index + batch_size, len(procedures))
            batch = procedures[start_index:end_index]
            
            logger.info(f"Importing procedures {start_index+1} to {end_index} (of {len(procedures)})")
            
            # First get body part and category mappings
            body_parts_map = {}
            categories_map = {}
            
            cursor.execute("SELECT id, name FROM body_parts")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    body_parts_map[row[1]] = row[0]
            
            cursor.execute("SELECT c.id, c.name, b.name FROM categories c JOIN body_parts b ON c.body_part_id = b.id")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    categories_map[(row[1], row[2])] = row[0]
            
            # Now import each procedure in the batch
            for i, proc in enumerate(batch):
                try:
                    # Get body part and category
                    body_part_name = proc.get('body_part_name', '')
                    category_name = proc.get('category_name', '')
                    procedure_name = proc.get('procedure_name', '')
                    
                    if not all([body_part_name, category_name, procedure_name]):
                        logger.warning(f"Skipping procedure {i+1}: Missing required fields")
                        continue
                    
                    # Find matching category
                    category_id = None
                    for (cat_name, bp_name), cat_id in categories_map.items():
                        if cat_name.startswith(category_name.replace(' ', '_').replace('&', 'and')) and bp_name == body_part_name:
                            category_id = cat_id
                            break
                    
                    if not category_id:
                        logger.warning(f"Skipping procedure {procedure_name}: Category not found")
                        continue
                    
                    # Parse costs
                    min_cost = None
                    if proc.get('min_cost'):
                        try:
                            min_cost_str = ''.join(c for c in proc['min_cost'] if c.isdigit())
                            min_cost = int(min_cost_str) if min_cost_str else 10000
                        except (ValueError, TypeError):
                            min_cost = 10000
                    else:
                        min_cost = 10000
                    
                    max_cost = None
                    if proc.get('max_cost'):
                        try:
                            max_cost_str = ''.join(c for c in proc['max_cost'] if c.isdigit())
                            max_cost = int(max_cost_str) if max_cost_str else 100000
                        except (ValueError, TypeError):
                            max_cost = 100000
                    else:
                        max_cost = 100000
                    
                    # Parse tags
                    tags = []
                    if proc.get('tags'):
                        tags = [tag.strip() for tag in proc['tags'].split(',') if tag.strip()]
                    
                    # Handle required fields that might be missing
                    short_description = proc.get('short_description', 'Description not available.')
                    if not short_description:
                        short_description = f"{procedure_name} procedure for {body_part_name}."
                    
                    overview = proc.get('overview', 'Overview not available.')
                    if not overview:
                        overview = f"{procedure_name} is a cosmetic procedure for enhancing {body_part_name}."
                    
                    procedure_details = proc.get('procedure_details', 'Details not available.')
                    if not procedure_details:
                        procedure_details = f"The {procedure_name} procedure involves professional medical techniques."
                    
                    ideal_candidates = proc.get('ideal_candidates', 'Consult with a doctor to determine candidacy.')
                    if not ideal_candidates:
                        ideal_candidates = f"Individuals seeking {body_part_name} enhancement."
                    
                    recovery_process = proc.get('recovery_process', 'Recovery varies by individual.')
                    if not recovery_process:
                        recovery_process = "Recovery time varies by individual. Follow doctor's instructions."
                    
                    recovery_time = proc.get('recovery_time', '1-3 weeks')
                    if not recovery_time:
                        recovery_time = "1-3 weeks"
                    
                    risks = proc.get('risks', 'All procedures carry some risks. Consult with your doctor.')
                    if not risks:
                        risks = "All procedures carry risks including infection, bleeding, and dissatisfaction with results."
                    
                    procedure_types = proc.get('procedure_types', 'Standard procedure')
                    if not procedure_types:
                        procedure_types = "Standard procedure"
                    
                    # Insert the procedure
                    cursor.execute(
                        """
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
                            tags,
                            category_id,
                            created_at, 
                            updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            procedure_name,
                            proc.get('alternative_names', ''),
                            short_description,
                            overview,
                            procedure_details,
                            ideal_candidates,
                            recovery_process,
                            recovery_time,
                            proc.get('procedure_duration', '1-3 hours'),
                            proc.get('hospital_stay_required', 'Varies'),
                            proc.get('results_duration', 'Results vary'),
                            min_cost,
                            max_cost,
                            proc.get('benefits', 'Enhanced appearance and confidence.'),
                            proc.get('benefits_detailed', 'Benefits include improved aesthetics and self-confidence.'),
                            risks,
                            procedure_types,
                            proc.get('alternative_procedures', ''),
                            body_part_name,
                            tags,
                            category_id,
                            datetime.utcnow(),
                            datetime.utcnow()
                        )
                    )
                    
                    imported_count += 1
                    logger.info(f"Imported procedure: {procedure_name}")
                    
                except Exception as e:
                    logger.error(f"Error importing procedure {proc.get('procedure_name', 'unknown')}: {e}")
                    # Continue with next procedure
            
            # Commit the batch
            conn.commit()
            logger.info(f"Successfully imported {imported_count} procedures in this batch")
            
            return imported_count
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing procedures from CSV: {e}")
        raise
    finally:
        cursor.close()

def main():
    """Main function to import procedures."""
    start_time = time.time()
    logger.info("Starting procedure import")
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # First create some sample procedures with all required fields
        create_sample_procedures(conn)
        
        # Get the current count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM procedures")
        result = cursor.fetchone()
        start_count = result[0] if result else 0
        cursor.close()
        
        # Import a batch from the CSV file if we have more procedures to add
        # We'll continue from where we left off
        start_index = max(0, start_count - 5)  # Subtract sample procedures
        imported = import_procedures_from_csv(conn, start_index, BATCH_SIZE)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        logger.info(f"Import completed in {elapsed_time:.2f} seconds")
        
        # Get final counts
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM body_parts")
        result = cursor.fetchone()
        body_part_count = result[0] if result else 0
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        result = cursor.fetchone()
        category_count = result[0] if result else 0
        
        cursor.execute("SELECT COUNT(*) FROM procedures")
        result = cursor.fetchone()
        procedure_count = result[0] if result else 0
        
        cursor.close()
        
        logger.info(f"Current database state: {body_part_count} body parts, {category_count} categories, {procedure_count} procedures")
        logger.info(f"Imported {imported} procedures in this run")
        
        if imported < BATCH_SIZE:
            logger.info("All procedures have been imported or reached the end of the CSV file")
        else:
            logger.info(f"To import more procedures, run this script again (next batch will start at index {start_index + BATCH_SIZE})")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()