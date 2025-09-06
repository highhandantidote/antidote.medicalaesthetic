#!/usr/bin/env python3
"""
Simple script to test recommendations for specific procedures.
"""
import sys
import logging
from datetime import datetime
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_specific_recommendations():
    """Test recommendations for specific procedures."""
    import ai_recommendations
    import time
    import statistics
    from models import Procedure
    
    # Focus on just one procedure to avoid timeouts
    target_ids = [1]  # 1: Open Rhinoplasty
    procedure_count = Procedure.query.count()
    logger.info(f"Database contains {procedure_count} procedures")
    
    # Collect all performance metrics
    execution_times = []
    
    for procedure_id in target_ids:
        procedure = Procedure.query.get(procedure_id)
        if not procedure:
            logger.error(f"Procedure ID {procedure_id} not found")
            continue
            
        logger.info(f"Testing recommendations for '{procedure.procedure_name}' (ID: {procedure_id})")
        logger.info(f"  Body part: {procedure.body_part}, Tags: {procedure.tags}")
        logger.info(f"  Category: {procedure.category.name if procedure.category else 'None'}")
        logger.info(f"  Cost range: ${procedure.min_cost} - ${procedure.max_cost}")
        
        try:
            # Run fewer times to prevent timeouts
            times = []
            all_recommendations = []
            
            for i in range(2):  # Run just twice to avoid timeouts
                # First run with force_rebuild to measure worst-case scenario
                force_rebuild = (i == 0)
                
                # Measure performance time for recommendations
                start_time = time.time()
                
                # Get recommendations
                recommendations = ai_recommendations.get_recommendations(
                    procedure_id, 
                    num_recommendations=3,  # Reduce to 3 recommendations
                    force_rebuild=force_rebuild
                )
                
                # Store first set of recommendations for analysis
                if i == 0:
                    all_recommendations = recommendations
                
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                times.append(execution_time)
                
            # Calculate statistics
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            min_time = min(times)
            max_time = max(times)
            
            # Store for overall stats
            execution_times.extend(times)
            
            logger.info(f"  Performance with {procedure_count} procedures:")
            logger.info(f"    Average response time: {avg_time:.2f}ms")
            logger.info(f"    Median response time: {median_time:.2f}ms")
            logger.info(f"    Min response time: {min_time:.2f}ms")
            logger.info(f"    Max response time: {max_time:.2f}ms")
            
            logger.info(f"  Found {len(all_recommendations)} recommendations:")
            
            for i, rec in enumerate(all_recommendations, 1):
                similarity_factors = []
                if rec.body_part == procedure.body_part:
                    similarity_factors.append("same body part")
                if rec.category and procedure.category and rec.category.id == procedure.category.id:
                    similarity_factors.append("same category")
                if procedure.tags and rec.tags and any(t in procedure.tags for t in rec.tags):
                    similarity_factors.append("matching tags")
                
                similarity_str = f" - Similar by: {', '.join(similarity_factors)}" if similarity_factors else ""
                logger.info(f"  {i}. {rec.procedure_name} (Body part: {rec.body_part}, Tags: {rec.tags}){similarity_str}")
                
            # Check recommendation quality
            matching_body_part = sum(1 for r in all_recommendations if r.body_part == procedure.body_part)
            matching_category = sum(1 for r in all_recommendations 
                                  if r.category and procedure.category and r.category.id == procedure.category.id)
            matching_tags = sum(1 for r in all_recommendations 
                              if procedure.tags and r.tags and any(t in procedure.tags for t in r.tags))
            
            logger.info(f"  Quality metrics:")
            logger.info(f"    Body part accuracy: {matching_body_part}/{len(all_recommendations)} ({matching_body_part/len(all_recommendations)*100:.0f}%)")
            logger.info(f"    Category accuracy: {matching_category}/{len(all_recommendations)} ({matching_category/len(all_recommendations)*100:.0f}%)")
            logger.info(f"    Tags accuracy: {matching_tags}/{len(all_recommendations)} ({matching_tags/len(all_recommendations)*100:.0f}%)")
                
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            
    # Overall statistics
    if execution_times:
        overall_avg = statistics.mean(execution_times)
        overall_median = statistics.median(execution_times)
        overall_min = min(execution_times)
        overall_max = max(execution_times)
        
        logger.info(f"Overall performance statistics with {procedure_count} procedures:")
        logger.info(f"  Average response time: {overall_avg:.2f}ms")
        logger.info(f"  Median response time: {overall_median:.2f}ms")
        logger.info(f"  Min response time: {overall_min:.2f}ms")
        logger.info(f"  Max response time: {overall_max:.2f}ms")

def main():
    """Run the recommendation test."""
    logger.info("Starting simple recommendation test...")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        test_specific_recommendations()
        
    logger.info("Test completed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())