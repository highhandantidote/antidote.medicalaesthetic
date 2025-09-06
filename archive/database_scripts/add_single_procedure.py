#!/usr/bin/env python3
"""
Add a single procedure to the database.

This script adds a single procedure with all required fields populated.
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def add_rhinoplasty_procedure():
    """Add a Rhinoplasty procedure to the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if we have any categories
        cursor.execute("SELECT id, name FROM categories WHERE name LIKE '%Rhinoplasty%' LIMIT 1")
        category = cursor.fetchone()
        
        if not category:
            logger.error("No Rhinoplasty category found. Please run the import_categories.py script first.")
            return False
        
        category_id = category[0]
        
        # Now add the procedure
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
            category_id,
            body_part,
            created_at,
            updated_at
        ) VALUES (
            'Rhinoplasty',
            'Nose Job, Nasal Reshaping',
            'Reshapes the nose for aesthetic or functional reasons.',
            'Rhinoplasty modifies nasal shape for cosmetic reasons or to correct breathing issues or trauma deformities.',
            'Open or closed technique; cartilage reshaping, bone trimming or grafting may be done.',
            'Individuals with nasal asymmetry, humps, or breathing problems.',
            'Recovery involves swelling and bruising that gradually subsides over several weeks.',
            '1-2 weeks',
            '1-3 hours',
            'No',
            'Permanent with proper care',
            120000,
            250000,
            'Improved facial harmony, better breathing',
            'Enhanced facial profile, correction of breathing issues',
            'Swelling, bruising, infection, dissatisfaction with results',
            'Open and closed rhinoplasty',
            'Non-surgical rhinoplasty with fillers',
            %s,
            'Nose',
            NOW(),
            NOW()
        )
        """, (category_id,))
        
        conn.commit()
        logger.info("Rhinoplasty procedure added successfully")
        
        # Now verify
        cursor.execute("SELECT COUNT(*) FROM procedures")
        count = cursor.fetchone()[0]
        logger.info(f"Total procedures count: {count}")
        
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error adding Rhinoplasty procedure: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function."""
    try:
        success = add_rhinoplasty_procedure()
        if success:
            logger.info("Import completed successfully")
        else:
            logger.error("Import failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()