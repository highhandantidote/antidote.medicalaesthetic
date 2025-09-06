#!/usr/bin/env python3
"""
Test the optimized recommendation system with current procedures in the database.
This script shows performance metrics for the enhanced recommendation system.
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

def test_recommendations():
    """Test the optimized recommendation system with performance metrics."""
    # Get all procedures
    procedures = Procedure.query.all()
    
    if not procedures:
        logger.warning("No procedures found in database for testing")
        return
        
    logger.info(f"Testing with {len(procedures)} procedures")
    
    # Track performance metrics
    response_times = []
    recommendations_count = {}
    body_part_hits = {}
    category_hits = {}
    
    # Force rebuild of similarity matrix to ensure fresh test
    first_proc = procedures[0]
    rebuild_start = time.time()
    ai_recommendations.get_recommendations(first_proc.id, force_rebuild=True)
    rebuild_time = time.time() - rebuild_start
    logger.info(f"Initial matrix build time: {rebuild_time:.3f} seconds")
    
    # Test recommendations for each procedure
    for p in procedures[:min(20, len(procedures))]:  # Test up to 20 procedures to avoid timeout
        start_time = time.time()
        recommendations = ai_recommendations.get_recommendations(p.id, num_recommendations=3)
        elapsed = time.time() - start_time
        response_times.append(elapsed)
        
        # Count how many recommendations were returned
        rec_count = len(recommendations)
        recommendations_count[rec_count] = recommendations_count.get(rec_count, 0) + 1
        
        # Track if recommendations match body part or category
        for rec in recommendations:
            # Body part hits
            if p.body_part and rec.body_part and p.body_part == rec.body_part:
                body_part_hits[p.body_part] = body_part_hits.get(p.body_part, 0) + 1
            
            # Category hits    
            if (p.category and rec.category and 
                p.category.name and rec.category.name and 
                p.category.name == rec.category.name):
                category_hits[p.category.name] = category_hits.get(p.category.name, 0) + 1
                
        # Log sample recommendations
        if len(response_times) <= 3:  # Only log details for first few procedures
            logger.info(f"For '{p.procedure_name}' (body: {p.body_part}, category: {p.category.name if p.category else 'None'})")
            for i, rec in enumerate(recommendations, 1):
                tags_str = ", ".join(rec.tags) if rec.tags else "no tags"
                logger.info(f"  {i}. {rec.procedure_name} - body: {rec.body_part}, " +
                           f"category: {rec.category.name if rec.category else 'None'}, tags: {tags_str}")
    
    # Log performance metrics
    if response_times:
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        if len(response_times) >= 2:
            p95 = sorted(response_times)[int(len(response_times) * 0.95)]
            stddev = statistics.stdev(response_times)
            logger.info(f"Response time stats: avg={avg_time:.3f}s, min={min_time:.3f}s, " + 
                       f"max={max_time:.3f}s, p95={p95:.3f}s, stddev={stddev:.3f}s")
        else:
            logger.info(f"Response time: {avg_time:.3f}s")
            
        logger.info(f"Recommendations count distribution: {recommendations_count}")
        logger.info(f"Body part hits: {body_part_hits}")
        logger.info(f"Category hits: {category_hits}")
    
def main():
    """Run the optimized recommendation test script."""
    app = create_app()
    with app.app_context():
        test_recommendations()

if __name__ == "__main__":
    main()