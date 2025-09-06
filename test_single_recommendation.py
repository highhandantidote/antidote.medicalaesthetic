#!/usr/bin/env python3
"""
Test a single procedure recommendation to avoid timeouts.
This script tests the recommendation for just one procedure.
"""
import time
import logging
from app import create_app
from models import Procedure
import ai_recommendations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_recommendation():
    """Test recommendations for a single procedure with performance metrics."""
    # Get all procedures
    procedures = Procedure.query.all()
    
    if not procedures:
        logger.warning("No procedures found in database for testing")
        return
        
    logger.info(f"Found {len(procedures)} procedures in database")
    
    # Select a breast procedure for testing
    breast_procedures = [p for p in procedures if p.body_part == "Breast"]
    if breast_procedures:
        test_procedure = breast_procedures[0]
    else:
        # Fallback to any procedure
        test_index = min(len(procedures) // 3, len(procedures) - 1)
        test_procedure = procedures[test_index]
    
    logger.info(f"Testing recommendations for procedure: {test_procedure.procedure_name}")
    logger.info(f"Body part: {test_procedure.body_part}, Category: {test_procedure.category.name if test_procedure.category else 'None'}")
    logger.info(f"Tags: {', '.join(test_procedure.tags) if test_procedure.tags else 'No tags'}")
    
    # Time the recommendation process
    start_time = time.time()
    recommendations = ai_recommendations.get_recommendations(test_procedure.id, num_recommendations=3)
    elapsed = time.time() - start_time
    
    logger.info(f"Recommendation time: {elapsed:.3f} seconds")
    logger.info(f"Found {len(recommendations)} recommendations")
    
    # Display recommendations
    for i, rec in enumerate(recommendations, 1):
        tags_str = ", ".join(rec.tags) if rec.tags else "no tags"
        logger.info(f"  {i}. {rec.procedure_name}")
        logger.info(f"     Body part: {rec.body_part}, Category: {rec.category.name if rec.category else 'None'}")
        logger.info(f"     Tags: {tags_str}")
        logger.info(f"     Cost range: ${rec.min_cost or 0:,} - ${rec.max_cost or 0:,}")
    
    # Log similarity patterns
    body_part_matches = sum(1 for r in recommendations if r.body_part == test_procedure.body_part)
    category_matches = sum(1 for r in recommendations 
                          if (r.category and test_procedure.category and 
                             r.category.name == test_procedure.category.name))
    
    logger.info(f"Body part matches: {body_part_matches}/{len(recommendations)}")
    logger.info(f"Category matches: {category_matches}/{len(recommendations)}")
    
def main():
    """Run the optimized recommendation test script."""
    app = create_app()
    with app.app_context():
        test_single_recommendation()

if __name__ == "__main__":
    main()