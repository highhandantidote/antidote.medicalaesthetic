#!/usr/bin/env python3
"""
Import categories from procedures CSV file.

This script extracts unique category names per body part and creates category entries in the database.
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
from models import BodyPart, Category

# Path to CSV file
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"

def import_categories():
    """Import categories from CSV file."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return False
    
    try:
        # Create application context
        app = create_app()
        with app.app_context():
            # Collect all unique category-body part combinations
            unique_categories = {}  # {(body_part_name, category_name): None}
            
            with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    body_part_name = row.get('body_part_name', '').strip()
                    category_name = row.get('category_name', '').strip()
                    
                    if body_part_name and category_name:
                        unique_categories[(body_part_name, category_name)] = None
            
            # Create categories in database
            categories_added = 0
            
            # First get all body parts for reference
            body_parts = {bp.name: bp.id for bp in BodyPart.query.all()}
            
            for (body_part_name, category_name) in unique_categories:
                # Skip if body part doesn't exist
                if body_part_name not in body_parts:
                    logger.warning(f"Body part not found for category: {body_part_name} - {category_name}")
                    continue
                
                body_part_id = body_parts[body_part_name]
                
                # Check if category already exists (checking name and body_part_id for uniqueness)
                existing = Category.query.filter_by(name=category_name, body_part_id=body_part_id).first()
                if existing:
                    logger.info(f"Category already exists: {category_name} under {body_part_name}")
                    continue
                
                # Create new category
                category = Category()
                category.name = category_name
                category.description = f"{category_name} procedures for {body_part_name}"
                category.body_part_id = body_part_id
                category.popularity_score = 0  # Default popularity
                
                db.session.add(category)
                categories_added += 1
                
                # Commit every 10 categories to avoid timeout
                if categories_added % 10 == 0:
                    db.session.commit()
            
            # Final commit
            db.session.commit()
            logger.info(f"Successfully imported {categories_added} categories")
            
            # Print sample categories for verification
            all_categories = Category.query.limit(10).all()
            logger.info(f"Sample categories in database:")
            for cat in all_categories:
                body_part = BodyPart.query.get(cat.body_part_id)
                logger.info(f"Category: {cat.name} under {body_part.name if body_part else 'Unknown'} (ID: {cat.id})")
            
            return True
    except Exception as e:
        logger.error(f"Error importing categories: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    import_categories()