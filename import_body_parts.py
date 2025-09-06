#!/usr/bin/env python3
"""
Import body parts from procedures CSV file.

This script extracts unique body part names and creates body part entries in the database.
"""

import os
import csv
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import required models and app
from app import create_app, db
from models import BodyPart

# Path to CSV file
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"

def import_body_parts():
    """Import body parts from CSV file."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return False
    
    try:
        # Create application context
        app = create_app()
        with app.app_context():
            # Collect all unique body parts
            unique_body_parts = set()
            
            with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    body_part_name = row.get('body_part_name', '').strip()
                    if body_part_name:
                        unique_body_parts.add(body_part_name)
            
            # Create body parts in database
            body_parts_added = 0
            
            for body_part_name in unique_body_parts:
                # Check if body part already exists
                existing = BodyPart.query.filter_by(name=body_part_name).first()
                if existing:
                    logger.info(f"Body part already exists: {body_part_name}")
                    continue
                
                # Create new body part
                body_part = BodyPart()
                body_part.name = body_part_name
                body_part.description = f"Procedures related to the {body_part_name.lower()}"
                body_part.icon_url = f"/static/images/body_parts/{body_part_name.lower().replace(' ', '_')}.svg"
                
                db.session.add(body_part)
                body_parts_added += 1
            
            # Commit changes
            db.session.commit()
            logger.info(f"Successfully imported {body_parts_added} body parts")
            
            # Print all body parts for verification
            all_body_parts = BodyPart.query.all()
            logger.info(f"Total body parts in database: {len(all_body_parts)}")
            for bp in all_body_parts:
                logger.info(f"Body part: {bp.name} (ID: {bp.id})")
            
            return True
    except Exception as e:
        logger.error(f"Error importing body parts: {str(e)}")
        return False

if __name__ == "__main__":
    import_body_parts()