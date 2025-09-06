#!/usr/bin/env python3
"""
Test script for AI recommendations with expanded dataset.

This script tests the recommendation system with our expanded dataset of 117 procedures.
"""
import sys
import logging
from app import create_app
from models import Procedure, Category, BodyPart
from sqlalchemy import func

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_procedure_details(procedure):
    """Get formatted procedure details for display."""
    return (
        f"Name: {procedure.procedure_name}\n"
        f"Body part: {procedure.body_part}\n"
        f"Category: {procedure.category.name if procedure.category else 'None'}\n"
        f"Tags: {', '.join(procedure.tags) if procedure.tags else 'None'}\n"
        f"Cost: ${procedure.min_cost or 0:,} - ${procedure.max_cost or 0:,}\n"
    )

def test_recommendations_by_body_part():
    """Test recommendations for procedures from different body parts."""
    from ai_recommendations import get_recommendations
    
    logger.info("Testing recommendations by body part...")
    
    # Get one procedure from each body part
    body_parts = ["Face", "Breast", "Body", "Skin"]
    
    for body_part in body_parts:
        # Get first procedure from this body part
        procedure = Procedure.query.filter_by(body_part=body_part).first()
        
        if not procedure:
            logger.warning(f"No procedures found for body part: {body_part}")
            continue
            
        logger.info(f"\nTesting recommendations for '{procedure.procedure_name}' (Body part: {body_part})")
        logger.info(get_procedure_details(procedure))
        
        # Get recommendations
        recommendations = get_recommendations(procedure.id, num_recommendations=3)
        
        # Print recommendations
        logger.info(f"Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"{i}. {rec.procedure_name}")
            logger.info(get_procedure_details(rec))
            
        # Count how many recommendations are from the same body part
        same_body_part = sum(1 for rec in recommendations if rec.body_part == procedure.body_part)
        logger.info(f"Same body part: {same_body_part}/{len(recommendations)}")

def test_recommendations_by_category():
    """Test recommendations for procedures from different categories."""
    from ai_recommendations import get_recommendations
    
    logger.info("Testing recommendations by category...")
    
    # Get categories with at least 3 procedures
    categories = Category.query.join(Procedure).group_by(Category.id).having(func.count(Procedure.id) >= 3).limit(3).all()
    
    for category in categories:
        # Get first procedure from this category
        procedure = Procedure.query.filter_by(category_id=category.id).first()
        
        if not procedure:
            continue
            
        logger.info(f"\nTesting recommendations for '{procedure.procedure_name}' (Category: {category.name})")
        logger.info(get_procedure_details(procedure))
        
        # Get recommendations
        recommendations = get_recommendations(procedure.id, num_recommendations=3)
        
        # Print recommendations
        logger.info(f"Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"{i}. {rec.procedure_name}")
            logger.info(get_procedure_details(rec))
            
        # Count how many recommendations are from the same category
        same_category = sum(1 for rec in recommendations if rec.category_id == procedure.category_id)
        logger.info(f"Same category: {same_category}/{len(recommendations)}")

def test_surgical_vs_nonsurgical():
    """Test recommendations for surgical vs non-surgical procedures."""
    from ai_recommendations import get_recommendations
    
    logger.info("Testing surgical vs non-surgical recommendations...")
    
    # Find a surgical procedure
    surgical = Procedure.query.filter(Procedure.tags.contains(['Surgical'])).first()
    
    if surgical:
        logger.info(f"\nTesting recommendations for surgical procedure '{surgical.procedure_name}'")
        logger.info(get_procedure_details(surgical))
        
        # Get recommendations
        recommendations = get_recommendations(surgical.id, num_recommendations=3)
        
        # Print recommendations
        logger.info(f"Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"{i}. {rec.procedure_name}")
            logger.info(get_procedure_details(rec))
            
        # Count surgical vs non-surgical
        surgical_recs = sum(1 for rec in recommendations if rec.tags and 'Surgical' in rec.tags)
        logger.info(f"Surgical recommendations: {surgical_recs}/{len(recommendations)}")
    
    # Find a non-surgical procedure
    nonsurgical = Procedure.query.filter(Procedure.tags.contains(['Non-Surgical'])).first()
    
    if nonsurgical:
        logger.info(f"\nTesting recommendations for non-surgical procedure '{nonsurgical.procedure_name}'")
        logger.info(get_procedure_details(nonsurgical))
        
        # Get recommendations
        recommendations = get_recommendations(nonsurgical.id, num_recommendations=3)
        
        # Print recommendations
        logger.info(f"Found {len(recommendations)} recommendations:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"{i}. {rec.procedure_name}")
            logger.info(get_procedure_details(rec))
            
        # Count surgical vs non-surgical
        nonsurgical_recs = sum(1 for rec in recommendations if rec.tags and 'Non-Surgical' in rec.tags)
        logger.info(f"Non-surgical recommendations: {nonsurgical_recs}/{len(recommendations)}")

def main():
    """Run the test script."""
    app = create_app()
    
    with app.app_context():
        # Count procedures
        count = Procedure.query.count()
        logger.info(f"Database contains {count} procedures")
        
        # Test by body part (one test only to avoid timeout)
        test_recommendations_by_body_part()
        
        return 0

if __name__ == "__main__":
    sys.exit(main())