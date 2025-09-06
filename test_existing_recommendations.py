#!/usr/bin/env python3
"""
Test the recommendation system with existing procedures in the database.
This script uses a simpler approach to avoid timeouts.
"""
import logging
import sys
from datetime import datetime
from app import create_app

# Configure logging
LOG_FILE = f"test_existing_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_recommendations():
    """Test recommendations with the existing procedures in the database."""
    import time
    from models import Procedure
    
    # Test with our existing procedures
    test_ids = [1, 13]  # 1: Rhinoplasty, 13: Breast Augmentation
    
    total_procedures = Procedure.query.count()
    logger.info(f"Testing recommendations with {total_procedures} procedures in the database")
    
    # Import inside function to avoid loading before app context
    from ai_recommendations import get_recommendations
    
    for procedure_id in test_ids:
        procedure = Procedure.query.get(procedure_id)
        if not procedure:
            logger.error(f"Procedure ID {procedure_id} not found")
            continue
            
        logger.info(f"Testing recommendations for '{procedure.procedure_name}' (ID: {procedure_id})")
        logger.info(f"  Body part: {procedure.body_part}, Tags: {procedure.tags}")
        logger.info(f"  Category: {procedure.category.name if procedure.category else 'None'}")
        logger.info(f"  Cost range: ${procedure.min_cost} - ${procedure.max_cost}")
        
        try:
            # Measure performance time for recommendations
            start_time = time.time()
            
            # Get recommendations
            recommendations = get_recommendations(
                procedure_id,
                num_recommendations=3,
                force_rebuild=True  # Force rebuild to test performance
            )
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            logger.info(f"  Found {len(recommendations)} recommendations in {execution_time:.2f}ms:")
            
            for i, rec in enumerate(recommendations, 1):
                similarity_factors = []
                if rec.body_part == procedure.body_part:
                    similarity_factors.append("same body part")
                if rec.category and procedure.category and rec.category.id == procedure.category.id:
                    similarity_factors.append("same category")
                if procedure.tags and rec.tags and any(t in procedure.tags for t in rec.tags):
                    similarity_factors.append("matching tags")
                
                similarity_str = f" - Similar by: {', '.join(similarity_factors)}" if similarity_factors else ""
                logger.info(f"    {i}. {rec.procedure_name} (Body part: {rec.body_part}, Tags: {rec.tags}){similarity_str}")
                
        except Exception as e:
            logger.error(f"Error testing recommendations: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

def main():
    """Run the recommendation test script."""
    logger.info("Starting recommendation test...")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        test_recommendations()
        
    logger.info("Test completed")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())