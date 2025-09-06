#!/usr/bin/env python3
"""
Add a single body part to test the import process.

This script adds a single body part to the database.
"""

import logging
from app import db
from models import BodyPart

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_body_part():
    """Add a single body part for testing."""
    try:
        # Check if body part already exists
        body_part_name = "Face"
        existing = BodyPart.query.filter_by(name=body_part_name).first()
        
        if existing:
            logger.info(f"Body part already exists: {body_part_name}")
            return True
        
        # Create new body part
        body_part = BodyPart()
        body_part.name = body_part_name
        body_part.description = f"Procedures related to the {body_part_name.lower()}"
        body_part.icon_url = f"/static/images/body_parts/{body_part_name.lower()}.svg"
        
        db.session.add(body_part)
        db.session.commit()
        
        logger.info(f"Successfully added body part: {body_part_name}")
        return True
    except Exception as e:
        logger.error(f"Error adding body part: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    add_body_part()