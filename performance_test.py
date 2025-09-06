#!/usr/bin/env python3
"""
Performance testing for doctor verification workflow.

This script tests the performance of the doctor verification workflow API endpoints.
"""
import requests
import time
import json
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base URL for API requests - use localhost for local testing
BASE_URL = "http://localhost:5000"

def test_api_endpoint_performance(endpoint, method="GET", data=None, expected_status=200):
    """Test the performance of a specific API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json.dumps(data), headers=headers)
        else:
            logger.error(f"Unsupported method: {method}")
            return None
        
        elapsed_time = time.time() - start_time
        status_code = response.status_code
        
        # Check if status code matches expected
        status_match = status_code == expected_status
        
        # Format response data
        try:
            response_data = response.json()
        except:
            response_data = response.text
            
        result = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'status_match': status_match,
            'elapsed_time': elapsed_time,
            'response': response_data
        }
        
        return result
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error testing endpoint {endpoint}: {str(e)}")
        
        return {
            'endpoint': endpoint,
            'method': method,
            'status_code': None,
            'status_match': False,
            'elapsed_time': elapsed_time,
            'error': str(e)
        }

def run_performance_tests():
    """Run performance tests on doctor verification API endpoints."""
    logger.info("Starting performance tests for doctor verification API...")
    
    # Test endpoints
    endpoints = [
        # GET endpoints
        {'endpoint': '/api/verification/doctors/pending', 'method': 'GET'},
        {'endpoint': '/api/verification/doctors/104', 'method': 'GET'},
        {'endpoint': '/api/verification/stats', 'method': 'GET'},
        {'endpoint': '/api/verification/doctors/search?status=pending', 'method': 'GET'},
        
        # POST endpoints - use with caution as they modify data
        # {'endpoint': '/api/verification/doctors/104/approve', 'method': 'POST', 'data': {'admin_id': 1}},
        # {'endpoint': '/api/verification/doctors/105/reject', 'method': 'POST', 'data': {'admin_id': 1, 'reason': 'Test rejection'}},
    ]
    
    results = []
    
    for ep in endpoints:
        endpoint = ep['endpoint']
        method = ep['method']
        data = ep.get('data')
        expected_status = ep.get('expected_status', 200)
        
        logger.info(f"Testing {method} {endpoint}...")
        result = test_api_endpoint_performance(endpoint, method, data, expected_status)
        results.append(result)
        
        # Display results
        if result:
            logger.info(f"  Status: {'✓' if result['status_match'] else '✗'} ({result['status_code']})")
            logger.info(f"  Time: {result['elapsed_time']:.4f} seconds")
            
            # For brevity, don't log the full response
            if isinstance(result.get('response'), dict) and 'success' in result['response']:
                logger.info(f"  Success: {result['response']['success']}")
            
            # Add some delay between requests
            time.sleep(0.5)
    
    # Calculate average response time
    response_times = [r['elapsed_time'] for r in results if r]
    avg_time = sum(response_times) / len(response_times) if response_times else 0
    
    logger.info(f"\nPerformance test summary:")
    logger.info(f"  Total requests: {len(results)}")
    logger.info(f"  Successful requests: {sum(1 for r in results if r and r['status_match'])}")
    logger.info(f"  Failed requests: {sum(1 for r in results if not r or not r['status_match'])}")
    logger.info(f"  Average response time: {avg_time:.4f} seconds")
    
    return results

if __name__ == "__main__":
    run_performance_tests()