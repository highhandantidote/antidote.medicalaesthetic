#!/usr/bin/env python3
"""
Performance test for AI recommendation systems.
This script evaluates the performance of our AI recommendation system.
"""
import logging
import time
from app import create_app, db
from models import Procedure

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_accuracy(actual, predicted, threshold=0.7):
    """
    Calculate a simple accuracy metric for recommendations.
    
    Args:
        actual: The actual procedure's attributes
        predicted: The recommended procedure's attributes
        threshold: Similarity threshold (default: 0.7)
        
    Returns:
        Accuracy score between 0 and 1
    """
    # Basic accuracy based on category and body area matching
    score = 0.0
    total_weight = 0.0
    
    # Category match (weight: 0.4)
    if actual.category_type == predicted.category_type:
        score += 0.4
    total_weight += 0.4
        
    # Body area match (weight: 0.3)
    if actual.body_area == predicted.body_area:
        score += 0.3
    total_weight += 0.3
    
    # Cost range overlap (weight: 0.3)
    actual_min = actual.min_cost
    actual_max = actual.max_cost
    pred_min = predicted.min_cost
    pred_max = predicted.max_cost
    
    if (pred_min <= actual_max and pred_max >= actual_min):
        # Calculate overlap percentage
        overlap_min = max(actual_min, pred_min)
        overlap_max = min(actual_max, pred_max)
        actual_range = actual_max - actual_min
        if actual_range > 0:
            overlap_pct = (overlap_max - overlap_min) / actual_range
            score += 0.3 * overlap_pct
    total_weight += 0.3
    
    # Normalize score
    if total_weight > 0:
        return score / total_weight
    return 0.0

def test_recommendation_quality():
    """Test the quality of our recommendation system."""
    logger.info("Testing recommendation quality...")
    
    # Get all procedures
    procedures = Procedure.query.all()
    
    if not procedures or len(procedures) < 5:
        logger.warning(f"Not enough procedures for meaningful test (found {len(procedures)})")
        return
        
    logger.info(f"Found {len(procedures)} procedures for testing")
    
    # Track metrics
    total_time = 0
    recommendation_count = 0
    accuracy_scores = []
    results_by_category = {}
    results_by_body_area = {}
    
    # Test each procedure as a target
    for procedure in procedures[:5]:  # Limit to 5 procedures for performance
        logger.info(f"Testing recommendations for '{procedure.procedure_name}'")
        
        # Find similar procedures using simple filtering (SQL-based approach)
        start_time = time.time()
        
        # Get procedures with same category
        category_matches = Procedure.query.filter(
            Procedure.category_type == procedure.category_type,
            Procedure.id != procedure.id
        ).all()
        
        # Get procedures with same body area
        body_area_matches = Procedure.query.filter(
            Procedure.body_area == procedure.body_area,
            Procedure.id != procedure.id
        ).all()
        
        # Combine and rank by simple weighting
        recommendations = []
        
        for p in set(category_matches + body_area_matches):
            score = calculate_accuracy(procedure, p)
            recommendations.append((p, score))
            
        # Sort by score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        top_recommendations = recommendations[:3] if recommendations else []
        
        end_time = time.time()
        elapsed = end_time - start_time
        total_time += elapsed
        recommendation_count += 1
        
        # Log results
        logger.info(f"Found {len(top_recommendations)} recommendations in {elapsed:.3f} seconds")
        
        if top_recommendations:
            for i, (rec, score) in enumerate(top_recommendations):
                logger.info(f"  {i+1}. {rec.procedure_name} (Score: {score:.2f}, Category: {rec.category_type}, Body Area: {rec.body_area})")
                accuracy_scores.append(score)
                
                # Track by category
                if rec.category_type not in results_by_category:
                    results_by_category[rec.category_type] = []
                results_by_category[rec.category_type].append(score)
                
                # Track by body area
                if rec.body_area not in results_by_body_area:
                    results_by_body_area[rec.body_area] = []
                results_by_body_area[rec.body_area].append(score)
    
    # Report overall performance
    if recommendation_count > 0:
        avg_time = total_time / recommendation_count
        logger.info(f"Average recommendation time: {avg_time:.3f} seconds")
        
    if accuracy_scores:
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        logger.info(f"Average recommendation accuracy: {avg_accuracy:.2f}")
        
        # Report by category
        logger.info("Accuracy by category:")
        for category, scores in results_by_category.items():
            category_avg = sum(scores) / len(scores)
            logger.info(f"  {category}: {category_avg:.2f}")
            
        # Report by body area
        logger.info("Accuracy by body area:")
        for area, scores in results_by_body_area.items():
            area_avg = sum(scores) / len(scores)
            logger.info(f"  {area}: {area_avg:.2f}")
    
def main():
    """Run the recommendation performance test."""
    logger.info("Starting recommendation performance test...")
    
    app = create_app()
    
    with app.app_context():
        test_recommendation_quality()
    
    logger.info("Recommendation performance test completed")
    
if __name__ == "__main__":
    main()