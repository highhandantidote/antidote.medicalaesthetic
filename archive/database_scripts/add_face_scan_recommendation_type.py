#!/usr/bin/env python3
"""
Add recommendation_type column to face_scan_recommendations table.

This script adds the recommendation_type column to support distinguishing between 
procedure and treatment recommendations in the face scan feature.
"""

import os
import logging
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add recommendation_type column to face_scan_recommendations table."""
    try:
        # Get the database URL from environment variables
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not set.")
            return
        
        # Create database engine
        engine = create_engine(db_url)
        
        # Check if the column already exists
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='face_scan_recommendations' 
                AND column_name='recommendation_type';
            """))
            column_exists = result.fetchone() is not None
            
            if column_exists:
                logger.info("Column recommendation_type already exists in face_scan_recommendations table.")
                return
            
            # Add the recommendation_type column with default value 'procedure'
            connection.execute(text("""
                ALTER TABLE face_scan_recommendations 
                ADD COLUMN recommendation_type TEXT DEFAULT 'procedure';
            """))
            connection.commit()
            
            logger.info("Successfully added recommendation_type column to face_scan_recommendations table.")
    except Exception as e:
        logger.error(f"Error adding column: {e}")

if __name__ == "__main__":
    run_migration()