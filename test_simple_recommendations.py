#!/usr/bin/env python3
"""
Simple test script for AI recommendations with expanded dataset.
"""
import logging
import sys
from app import create_app
from models import Procedure
from ai_recommendations import get_recommendations, compute_similarity_matrix

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_single_procedure_recommendation():
    """Test recommendation for a single procedure."""
    # Get a procedure from the database
    procedure = Procedure.query.first()
    
    if not procedure:
        logger.error("No procedures found in the database")
        return False
        
    logger.info(f"Testing recommendations for procedure: {procedure.procedure_name}")
    logger.info(f"Body part: {procedure.body_part}")
    logger.info(f"Category: {procedure.category.name if procedure.category else 'None'}")
    logger.info(f"Tags: {procedure.tags}")
    
    # Get recommendations
    recommendations = get_recommendations(procedure.id, num_recommendations=3, force_rebuild=True)
    
    # Check if we got recommendations
    if not recommendations:
        logger.error("No recommendations returned")
        return False
        
    logger.info(f"Got {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        logger.info(f"{i}. {rec.procedure_name}")
        logger.info(f"   Body part: {rec.body_part}")
        logger.info(f"   Category: {rec.category.name if rec.category else 'None'}")
        logger.info(f"   Tags: {rec.tags}")
    
    return True

def main():
    """Run the test script."""
    logger.info("Starting simple recommendation test...")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        try:
            # Count procedures
            count = Procedure.query.count()
            logger.info(f"Found {count} procedures in the database")
            
            # Run simple test
            success = test_single_procedure_recommendation()
            
            if success:
                logger.info("Test completed successfully.")
            else:
                logger.error("Test failed.")
                return 1
                
        except Exception as e:
            logger.error(f"Error in testing: {str(e)}")
            return 1
            
    return 0

if __name__ == "__main__":
    sys.exit(main())