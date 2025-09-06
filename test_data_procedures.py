#!/usr/bin/env python3
"""
Create procedures for testing
"""
import logging
from datetime import datetime
from app import create_app, db
from models import Procedure, Category

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Create procedures for testing."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Creating procedures...")
            
            # Get category
            surgical_category = Category.query.filter_by(name="Surgical").first()
            if not surgical_category:
                logger.error("Surgical category not found")
                return
            
            # Create procedures (5)
            procedures = [
                {
                    "procedure_name": "Rhinoplasty",
                    "short_description": "Nose reshaping surgery",
                    "overview": "Rhinoplasty is surgery that changes the shape of the nose.",
                    "procedure_details": "The surgery involves reshaping the bone and cartilage.",
                    "ideal_candidates": "Good candidates are those looking to improve the appearance of their nose.",
                    "recovery_process": "Follow doctor's instructions",
                    "recovery_time": "1-2 weeks",
                    "results_duration": "Permanent",
                    "min_cost": 5000,
                    "max_cost": 15000,
                    "benefits": "Improved appearance",
                    "benefits_detailed": "Enhanced facial harmony",
                    "risks": "Swelling, bruising, and potential breathing difficulties",
                    "procedure_types": "Open Rhinoplasty, Closed Rhinoplasty",
                    "category_id": surgical_category.id
                },
                {
                    "procedure_name": "Facelift",
                    "short_description": "Facial rejuvenation surgery",
                    "overview": "A facelift tightens sagging facial tissues.",
                    "procedure_details": "Removes excess skin, tightens tissue, redrapes skin.",
                    "ideal_candidates": "People with facial sagging.",
                    "recovery_process": "Gradual healing over several weeks",
                    "recovery_time": "2-4 weeks",
                    "results_duration": "5-10 years",
                    "min_cost": 7000,
                    "max_cost": 25000,
                    "benefits": "Younger appearance",
                    "benefits_detailed": "Reduced signs of aging",
                    "risks": "Scarring, nerve damage, infection",
                    "procedure_types": "Traditional, Mini, Thread",
                    "category_id": surgical_category.id
                },
                {
                    "procedure_name": "Eyelid Surgery",
                    "short_description": "Removes excess skin around eyes",
                    "overview": "Eyelid surgery improves the appearance of upper/lower eyelids.",
                    "procedure_details": "Removes excess skin and fat.",
                    "ideal_candidates": "People with droopy eyelids.",
                    "recovery_process": "Rest with reduced activity",
                    "recovery_time": "1-3 weeks",
                    "results_duration": "5-7 years",
                    "min_cost": 3000,
                    "max_cost": 8000,
                    "benefits": "More alert appearance",
                    "benefits_detailed": "Better vision and youthful look",
                    "risks": "Dry eyes, asymmetry, scarring",
                    "procedure_types": "Upper, Lower, Double",
                    "category_id": surgical_category.id
                }
            ]
            
            for proc_data in procedures:
                existing = Procedure.query.filter_by(procedure_name=proc_data["procedure_name"]).first()
                if not existing:
                    procedure = Procedure(**proc_data, created_at=datetime.utcnow())
                    db.session.add(procedure)
                    db.session.commit()
                    logger.info(f"Created procedure: {proc_data['procedure_name']}")
                else:
                    logger.info(f"Procedure {proc_data['procedure_name']} already exists")
            
            logger.info("Procedures created successfully")
        
        except Exception as e:
            logger.error(f"Error creating procedures: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()