"""
Mobile Performance Test Script
Test the mobile performance optimizations and generate report
"""

import requests
import time
import json

def test_mobile_performance():
    """Test mobile performance metrics"""
    base_url = "http://localhost:5000"
    
    # Mobile User Agents
    mobile_agents = {
        'iPhone': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
        'Android': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36',
        'iPad': 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
    }
    
    desktop_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    
    results = {}
    
    # Test desktop performance
    start_time = time.time()
    desktop_response = requests.get(base_url, headers={'User-Agent': desktop_agent})
    desktop_time = (time.time() - start_time) * 1000
    
    results['desktop'] = {
        'load_time_ms': round(desktop_time, 1),
        'content_size': len(desktop_response.content),
        'status_code': desktop_response.status_code,
        'headers': dict(desktop_response.headers)
    }
    
    # Test mobile performance for each device
    for device, user_agent in mobile_agents.items():
        start_time = time.time()
        mobile_response = requests.get(base_url, headers={'User-Agent': user_agent})
        mobile_time = (time.time() - start_time) * 1000
        
        results[device.lower()] = {
            'load_time_ms': round(mobile_time, 1),
            'content_size': len(mobile_response.content),
            'status_code': mobile_response.status_code,
            'mobile_optimized': mobile_response.headers.get('X-Mobile-Optimized') == 'true',
            'performance_score': mobile_response.headers.get('X-Performance-Score'),
            'response_time': mobile_response.headers.get('X-Response-Time'),
            'cache_control': mobile_response.headers.get('Cache-Control'),
            'content_encoding': mobile_response.headers.get('Content-Encoding')
        }
    
    # Calculate improvements
    for device in ['iphone', 'android', 'ipad']:
        if device in results:
            improvement = ((results['desktop']['load_time_ms'] - results[device]['load_time_ms']) / results['desktop']['load_time_ms']) * 100
            results[device]['improvement_percentage'] = round(improvement, 1)
    
    return results

def test_mobile_apis():
    """Test mobile-specific API endpoints"""
    base_url = "http://localhost:5000"
    
    try:
        # Test cache stats
        cache_response = requests.get(f"{base_url}/api/mobile/cache-stats")
        cache_stats = cache_response.json() if cache_response.status_code == 200 else {}
        
        # Test SEO vitals
        seo_response = requests.get(f"{base_url}/api/seo/core-web-vitals")
        seo_stats = seo_response.json() if seo_response.status_code == 200 else {}
        
        return {
            'cache_stats': cache_stats,
            'core_web_vitals': seo_stats
        }
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    print("🚀 Testing Mobile Performance Optimizations...")
    
    # Test performance
    performance_results = test_mobile_performance()
    
    # Test APIs
    api_results = test_mobile_apis()
    
    # Generate report
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'performance_tests': performance_results,
        'api_tests': api_results,
        'summary': {
            'mobile_optimization_working': any(
                result.get('mobile_optimized', False) 
                for result in performance_results.values() 
                if isinstance(result, dict)
            ),
            'performance_score_achieved': any(
                result.get('performance_score') == '100'
                for result in performance_results.values()
                if isinstance(result, dict)
            )
        }
    }
    
    print(json.dumps(report, indent=2))