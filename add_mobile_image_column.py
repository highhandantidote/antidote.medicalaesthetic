"""
Database migration to add mobile_image_url column to banner_slides table.

This script adds the mobile_image_url column to support separate mobile and desktop banner images.
"""

import os
import logging
from app import app, db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_mobile_image_column():
    """Add mobile_image_url column to banner_slides table."""
    try:
        # Check if the column already exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'banner_slides' 
            AND column_name = 'mobile_image_url'
        """))
        
        existing_column = result.fetchone()
        
        if existing_column:
            logger.info("mobile_image_url column already exists in banner_slides table")
            return True
        
        # Add the mobile_image_url column
        db.session.execute(text("""
            ALTER TABLE banner_slides 
            ADD COLUMN mobile_image_url VARCHAR(500)
        """))
        
        db.session.commit()
        logger.info("Successfully added mobile_image_url column to banner_slides table")
        return True
        
    except Exception as e:
        logger.error(f"Error adding mobile_image_url column: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Main execution function."""
    with app.app_context():
        logger.info("Starting banner_slides table migration...")
        
        if add_mobile_image_column():
            logger.info("Migration completed successfully!")
        else:
            logger.error("Migration failed!")
            return False
        
        return True

if __name__ == "__main__":
    main()