#!/usr/bin/env python3
"""
Test the recommendation endpoint instead of the full algorithm.
"""
import sys
import json
import requests

def test_api_recommendation(procedure_id, description=""):
    """Test the API endpoint for recommendations for a specific procedure."""
    import time
    
    try:
        # Record start time for performance measurement
        start_time = time.time()
        
        # Make API request
        print(f"Testing recommendation API for {description} (ID: {procedure_id})")
        response = requests.get(f"http://localhost:5000/api/procedures/{procedure_id}/recommendations")
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Print performance metrics
        print(f"Response time: {response_time:.2f}ms")
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            
            # Check if data is in 'data' field per our API design
            recommendations = data.get('data', [])
            
            print(f"API returned {len(recommendations)} recommendations")
            
            # Print recommendation details with proper formatting
            for i, rec in enumerate(recommendations, 1):
                procedure_name = rec.get('procedure_name')
                body_part = rec.get('body_part')
                category = rec.get('category', {}).get('name', 'None')
                tags = ', '.join(rec.get('tags', [])) if rec.get('tags') else 'None'
                cost_range = f"${rec.get('min_cost')} - ${rec.get('max_cost')}"
                
                print(f"{i}. {procedure_name}")
                print(f"   Body part: {body_part}")
                print(f"   Category: {category}")
                print(f"   Tags: {tags}")
                print(f"   Cost: {cost_range}")
                
                # Handle potentially None values with proper formatting
                avg_rating = rec.get('avg_rating')
                if avg_rating is not None:
                    rating_str = f"{float(avg_rating):.1f}"
                else:
                    rating_str = "0.0"
                    
                review_count = rec.get('review_count', 0)
                print(f"   Rating: {rating_str}/5.0 ({review_count} reviews)")
                print()
            
            return True, response_time
        else:
            print(f"API returned status code {response.status_code}")
            print(response.text)
            return False, 0
    
    except Exception as e:
        print(f"Error testing recommendation API: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0

def main():
    """Run the test script for specific procedures."""
    print("Starting recommendation API test...\n")
    
    # Test procedures required by the task
    test_procedures = [
        (1, "Rhinoplasty (facial procedure)"),
        (13, "Breast Augmentation (breast procedure)")
    ]
    
    all_success = True
    response_times = []
    
    # Test each procedure and collect performance metrics
    for proc_id, description in test_procedures:
        print("-" * 50)
        success, response_time = test_api_recommendation(proc_id, description)
        print("-" * 50 + "\n")
        
        all_success = all_success and success
        if response_time > 0:
            response_times.append(response_time)
    
    # Report overall results
    if all_success:
        print("✅ All API tests completed successfully")
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"Average response time: {avg_time:.2f}ms")
        return 0
    else:
        print("❌ API test failed for one or more procedures")
        return 1

if __name__ == "__main__":
    sys.exit(main())