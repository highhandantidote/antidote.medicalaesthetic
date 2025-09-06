#!/usr/bin/env python3
"""
Test recommendations for multiple procedures without rebuilding the cache each time.
This script tests recommendations for 3 different procedures.
"""
import time
import logging
import statistics
from app import create_app
from models import Procedure
import ai_recommendations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_procedure_recommendations(procedure, force_rebuild=False):
    """Test recommendations for a single procedure."""
    logger.info(f"Testing recommendations for procedure: {procedure.procedure_name}")
    logger.info(f"Body part: {procedure.body_part}, Category: {procedure.category.name if procedure.category else 'None'}")
    logger.info(f"Tags: {', '.join(procedure.tags) if procedure.tags else 'No tags'}")
    
    # Time the recommendation process
    start_time = time.time()
    recommendations = ai_recommendations.get_recommendations(procedure.id, num_recommendations=3, force_rebuild=force_rebuild)
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
    body_part_matches = sum(1 for r in recommendations if r.body_part == procedure.body_part)
    category_matches = sum(1 for r in recommendations 
                          if (r.category and procedure.category and 
                             r.category.name == procedure.category.name))
    
    logger.info(f"Body part matches: {body_part_matches}/{len(recommendations)}")
    logger.info(f"Category matches: {category_matches}/{len(recommendations)}")
    logger.info("-" * 80)
    
    return elapsed, recommendations

def test_multiple_procedures():
    """Test recommendations for three different procedures."""
    # Get all procedures
    procedures = Procedure.query.all()
    
    if not procedures:
        logger.warning("No procedures found in database for testing")
        return
        
    logger.info(f"Found {len(procedures)} procedures in database")
    
    # Select a few diverse procedures to test
    chosen_indices = []
    for body_part_type in ["Face", "Breast", "Body"]:
        matches = [i for i, p in enumerate(procedures) if p.body_part == body_part_type]
        if matches:
            chosen_indices.append(matches[0])
    
    # If we didn't find procedures matching our criteria, pick based on index
    if len(chosen_indices) < 3:
        num_procs = len(procedures)
        chosen_indices = [
            0,  # First procedure
            num_procs // 2,  # Middle procedure
            num_procs - 1,  # Last procedure
        ][:min(3, num_procs)]
    
    # Test each procedure
    response_times = []
    
    # For the first procedure, force a rebuild of the matrix
    test_proc = procedures[chosen_indices[0]]
    elapsed, _ = test_procedure_recommendations(test_proc, force_rebuild=True)
    response_times.append(elapsed)
    
    # For the remaining procedures, use the cached matrix
    for idx in chosen_indices[1:3]:
        if idx < len(procedures):
            test_proc = procedures[idx]
            elapsed, _ = test_procedure_recommendations(test_proc)
            response_times.append(elapsed)
    
    # Summarize performance
    if response_times:
        avg_time = statistics.mean(response_times)
        if len(response_times) > 1:
            min_time = min(response_times)
            max_time = max(response_times)
            logger.info(f"Performance summary: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")
        else:
            logger.info(f"Performance summary: time={avg_time:.3f}s")
    
def main():
    """Run the multi-procedure test script."""
    app = create_app()
    with app.app_context():
        test_multiple_procedures()

if __name__ == "__main__":
    main()