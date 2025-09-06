#!/usr/bin/env python3
"""
Update procedure_id in face_scan_recommendations to allow NULL values.

This script modifies the NOT NULL constraint on the procedure_id column
to allow NULL values for treatment recommendations.
"""

import os
import logging
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Modify the procedure_id column to allow NULL values."""
    try:
        # Get the database URL from environment variables
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not set.")
            return
        
        # Create database engine
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            # Check if we need to drop the constraint
            result = connection.execute(text("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name = 'face_scan_recommendations'
                AND constraint_type = 'CHECK'
                AND constraint_name LIKE '%procedure_id%not_null%';
            """))
            constraint = result.fetchone()
            
            # If constraint exists, drop it
            if constraint:
                constraint_name = constraint[0]
                connection.execute(text(f"""
                    ALTER TABLE face_scan_recommendations
                    DROP CONSTRAINT "{constraint_name}";
                """))
                connection.commit()
                logger.info(f"Dropped constraint: {constraint_name}")
            
            # Modify the column to allow NULL values
            connection.execute(text("""
                ALTER TABLE face_scan_recommendations
                ALTER COLUMN procedure_id DROP NOT NULL;
            """))
            connection.commit()
            
            logger.info("Successfully modified procedure_id to allow NULL values")
    except Exception as e:
        logger.error(f"Error modifying constraint: {e}")

if __name__ == "__main__":
    run_migration()