#!/usr/bin/env python3
"""
Add high-demand procedures to the database.

This script adds specific high-demand procedures to ensure they are available
for display on the homepage.
"""
import os
import logging
from datetime import datetime
from flask import Flask
from models import Procedure, Category, BodyPart

# Import Flask app and database from main application
import main
from app import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_or_create_category(name, body_part_name):
    """Get an existing category or create a new one if needed."""
    # Get or create body part
    body_part = BodyPart.query.filter_by(name=body_part_name).first()
    if not body_part:
        body_part = BodyPart(
            name=body_part_name,
            display_name=body_part_name,
            description=f"Body part for {body_part_name} procedures"
        )
        db.session.add(body_part)
        db.session.commit()
        logger.info(f"Created new body part: {body_part_name}")
    
    # Get or create category
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category(
            name=name,
            display_name=name,
            description=f"Category for {name} procedures",
            body_part_id=body_part.id
        )
        db.session.add(category)
        db.session.commit()
        logger.info(f"Created new category: {name}")
    
    return category

def create_procedure(name, category_name, body_part_name, min_cost=15000, max_cost=150000):
    """Create a procedure if it doesn't exist."""
    # Check if procedure already exists
    existing = Procedure.query.filter_by(procedure_name=name).first()
    if existing:
        logger.info(f"Procedure already exists: {name}")
        
        # Update popularity score to ensure it's high
        existing.popularity_score = 100
        db.session.commit()
        logger.info(f"Updated popularity score for: {name}")
        
        return existing
    
    # Get appropriate category for the procedure
    category = get_or_create_category(category_name, body_part_name)
    
    # Create the procedure
    procedure = Procedure(
        procedure_name=name,
        short_description=f"Professional {name} procedure with excellent results.",
        overview=f"Overview of {name} procedure. This is a highly sought-after procedure.",
        procedure_details=f"Details about {name} procedure. This procedure is known for its effectiveness.",
        ideal_candidates=f"Ideal candidates for {name} are individuals looking for quality results.",
        recovery_process="Varies depending on individual factors",
        risks=f"Risks associated with {name} are minimal when performed by qualified professionals.",
        benefits=f"Benefits of {name} include improved appearance and confidence.",
        category_id=category.id,
        body_part=body_part_name,
        min_cost=min_cost,
        max_cost=max_cost,
        popularity_score=100,  # Set a high popularity score
        recovery_time="Varies depending on individual factors",
        created_at=datetime.utcnow()
    )
    
    db.session.add(procedure)
    db.session.commit()
    logger.info(f"Created new procedure: {name}")
    
    return procedure

def add_high_demand_procedures():
    """Add high-demand procedures to the database."""
    try:
        # List of high-demand procedures to add or update
        procedures = [
            {
                "name": "Lumpectomy", 
                "category": "Breast Surgery", 
                "body_part": "Breast"
            },
            {
                "name": "Six Month Smiles", 
                "category": "Dental", 
                "body_part": "Face"
            },
            {
                "name": "Hymenoplasty", 
                "category": "Gynecological", 
                "body_part": "Reproductive"
            },
            {
                "name": "Lash Lift", 
                "category": "Cosmetic", 
                "body_part": "Face"
            },
            {
                "name": "Punch Excision", 
                "category": "Dermatological", 
                "body_part": "Skin"
            },
            {
                "name": "NuFace", 
                "category": "Non-Surgical", 
                "body_part": "Face"
            }
        ]
        
        added_count = 0
        updated_count = 0
        
        # Add each procedure
        for proc in procedures:
            existing = Procedure.query.filter_by(procedure_name=proc["name"]).first()
            result = create_procedure(proc["name"], proc["category"], proc["body_part"])
            
            if existing:
                updated_count += 1
            else:
                added_count += 1
        
        logger.info(f"Added {added_count} new procedures and updated {updated_count} existing procedures")
        
        return True
    except Exception as e:
        logger.error(f"Error adding high-demand procedures: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    # Run within application context
    from app import app
    with app.app_context():
        add_high_demand_procedures()