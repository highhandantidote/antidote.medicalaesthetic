#!/usr/bin/env python3
"""
Add procedures directly to the database using SQLAlchemy with the Flask app context.

This script works directly with the Flask app to add procedures to the database.
"""

import os
import csv
import logging
from datetime import datetime
from flask import Flask
from models import db, BodyPart, Category, Procedure

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to CSV file
PROCEDURES_CSV = "attached_assets/new_procedure_details - Sheet1.csv"
START_ROW = 25  # Skip rows that are already imported
MAX_ROWS = 25  # How many rows to import in this run

def clean_integer(value):
    """Clean cost values by removing commas and converting to integer."""
    if value is None or value == "":
        return 0
    
    # Remove commas, spaces, and non-numeric characters except for the first minus sign
    value = str(value)
    clean_value = ''.join(c for c in value if c.isdigit() or (c == '-' and value.index(c) == 0))
    
    try:
        return int(clean_value or 0)
    except ValueError:
        return 0

def import_procedures():
    """Import procedures from CSV using SQLAlchemy."""
    if not os.path.exists(PROCEDURES_CSV):
        logger.error(f"Procedures CSV file not found: {PROCEDURES_CSV}")
        return False
    
    # Create Flask app and initialize database
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    with app.app_context():
        try:
            # Read CSV file
            procedures = []
            with open(PROCEDURES_CSV, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for i, row in enumerate(reader):
                    if i < START_ROW:
                        continue
                    if i >= START_ROW + MAX_ROWS:
                        break
                    procedures.append(row)
            
            logger.info(f"Found {len(procedures)} procedures to import")
            
            # Import each procedure
            procedures_added = 0
            
            for procedure_data in procedures:
                body_part_name = procedure_data.get('body_part_name', '').strip()
                category_name = procedure_data.get('category_name', '').strip()
                procedure_name = procedure_data.get('procedure_name', '').strip()
                
                if not body_part_name or not category_name or not procedure_name:
                    logger.warning(f"Skipping procedure with missing data: {procedure_name}")
                    continue
                
                # Check if procedure already exists
                existing_procedure = Procedure.query.filter_by(procedure_name=procedure_name).first()
                if existing_procedure:
                    logger.info(f"Procedure already exists: {procedure_name} (ID: {existing_procedure.id})")
                    continue
                
                # Handle body part
                body_part = BodyPart.query.filter_by(name=body_part_name).first()
                if not body_part:
                    # Create body part
                    body_part = BodyPart(
                        name=body_part_name,
                        description=f"Procedures related to the {body_part_name.lower()}",
                        icon_url=f"/static/images/body_parts/{body_part_name.lower().replace(' ', '_')}.svg",
                        created_at=datetime.utcnow()
                    )
                    db.session.add(body_part)
                    db.session.flush()  # Get ID without committing
                    logger.info(f"Created body part: {body_part_name} (ID: {body_part.id})")
                
                # Handle category
                category = Category.query.filter_by(name=category_name, body_part_id=body_part.id).first()
                if not category:
                    # Check if category exists with another body part
                    existing_category = Category.query.filter_by(name=category_name).first()
                    if existing_category:
                        category = existing_category
                        logger.info(f"Using existing category: {category_name} (ID: {category.id})")
                    else:
                        # Create category
                        category = Category(
                            name=category_name,
                            description=f"{category_name} procedures for {body_part_name}",
                            body_part_id=body_part.id,
                            popularity_score=0,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(category)
                        db.session.flush()  # Get ID without committing
                        logger.info(f"Created category: {category_name} under {body_part_name} (ID: {category.id})")
                
                # Clean cost values
                min_cost = clean_integer(procedure_data.get('min_cost', '0'))
                max_cost = clean_integer(procedure_data.get('max_cost', '0'))
                
                # Create procedure
                procedure = Procedure(
                    procedure_name=procedure_name,
                    alternative_names=procedure_data.get('alternative_names', ''),
                    short_description=procedure_data.get('short_description', ''),
                    overview=procedure_data.get('overview', ''),
                    procedure_details=procedure_data.get('procedure_details', ''),
                    ideal_candidates=procedure_data.get('ideal_candidates', ''),
                    recovery_process=procedure_data.get('recovery_process', ''),
                    recovery_time=procedure_data.get('recovery_time', ''),
                    procedure_duration=procedure_data.get('procedure_duration', ''),
                    hospital_stay_required=procedure_data.get('hospital_stay_required', 'No'),
                    results_duration=procedure_data.get('results_duration', ''),
                    min_cost=min_cost,
                    max_cost=max_cost,
                    benefits=procedure_data.get('benefits', ''),
                    benefits_detailed=procedure_data.get('benefits_detailed', ''),
                    risks=procedure_data.get('risks', ''),
                    procedure_types=procedure_data.get('procedure_types', ''),
                    alternative_procedures=procedure_data.get('alternative_procedures', ''),
                    category_id=category.id,
                    popularity_score=50,
                    avg_rating=0.0,
                    review_count=0,
                    body_part=body_part_name
                )
                db.session.add(procedure)
                db.session.flush()  # Get ID without committing
                logger.info(f"Created procedure: {procedure_name} (ID: {procedure.id})")
                procedures_added += 1
            
            # Commit all changes at once
            db.session.commit()
            logger.info(f"Successfully imported {procedures_added} procedures")
            
            # Return starting row for next run
            return START_ROW + MAX_ROWS
        
        except Exception as e:
            logger.error(f"Error importing procedures: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    logger.info("Starting procedure import")
    result = import_procedures()
    if result:
        logger.info(f"Import complete. Next start row: {result}")
    else:
        logger.error("Import failed")