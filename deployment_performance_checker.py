"""
Deployment Performance Checker
Tool to diagnose performance issues on deployed domains.
"""

import requests
import time
import json
import logging

logger = logging.getLogger(__name__)

class DeploymentPerformanceChecker:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.results = {}
    
    def check_endpoint(self, endpoint, name=None):
        """Check performance of a specific endpoint."""
        if not name:
            name = endpoint
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=30)
            elapsed = (time.time() - start_time) * 1000
            
            self.results[name] = {
                'url': url,
                'status_code': response.status_code,
                'response_time_ms': round(elapsed, 1),
                'content_length': len(response.content),
                'headers': dict(response.headers)
            }
            
            logger.info(f"✅ {name}: {elapsed:.1f}ms (Status: {response.status_code})")
            return elapsed
            
        except Exception as e:
            self.results[name] = {
                'url': url,
                'error': str(e),
                'response_time_ms': None
            }
            logger.error(f"❌ {name}: {str(e)}")
            return None
    
    def run_comprehensive_check(self):
        """Run comprehensive performance check."""
        print(f"\n🔍 DEPLOYMENT PERFORMANCE ANALYSIS")
        print(f"Testing domain: {self.base_url}")
        print("=" * 50)
        
        # Test critical endpoints
        endpoints = [
            ('/', 'Homepage'),
            ('/doctors', 'Doctors Page'),
            ('/procedures', 'Procedures Page'),
            ('/community', 'Community Page'),
            ('/face-analysis/', 'Face Analysis'),
            ('/clinic/all', 'Clinic Directory'),
            ('/health', 'Health Check'),
            ('/static/css/style.css', 'Static CSS')
        ]
        
        for endpoint, name in endpoints:
            self.check_endpoint(endpoint, name)
            time.sleep(0.5)  # Brief pause between requests
        
        # Analyze results
        self.analyze_results()
        return self.results
    
    def analyze_results(self):
        """Analyze performance results and provide recommendations."""
        print(f"\n📊 PERFORMANCE ANALYSIS RESULTS")
        print("=" * 40)
        
        slow_endpoints = []
        fast_endpoints = []
        errors = []
        
        for name, result in self.results.items():
            if 'error' in result:
                errors.append(name)
                print(f"❌ {name}: ERROR - {result['error']}")
            elif result['response_time_ms']:
                time_ms = result['response_time_ms']
                if time_ms > 1000:
                    slow_endpoints.append((name, time_ms))
                    print(f"🐌 {name}: {time_ms}ms (SLOW)")
                elif time_ms > 500:
                    print(f"⚠️  {name}: {time_ms}ms (MODERATE)")
                else:
                    fast_endpoints.append((name, time_ms))
                    print(f"⚡ {name}: {time_ms}ms (FAST)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("=" * 20)
        
        if slow_endpoints:
            print("🔧 PERFORMANCE ISSUES DETECTED:")
            for name, time_ms in slow_endpoints:
                print(f"   • {name}: {time_ms}ms - Needs optimization")
            
            print("\n🚀 SUGGESTED SOLUTIONS:")
            print("   1. Database connection pooling")
            print("   2. Enable response caching")
            print("   3. Optimize database queries")
            print("   4. Add CDN for static assets")
            print("   5. Use Redis for session storage")
        
        if errors:
            print(f"\n❌ ERRORS DETECTED:")
            for error in errors:
                print(f"   • {error}: Check logs for details")
        
        if len(fast_endpoints) == len([r for r in self.results.values() if 'error' not in r]):
            print("🎉 ALL ENDPOINTS PERFORMING WELL!")
    
    def generate_report(self, filename='deployment_performance_report.json'):
        """Generate detailed performance report."""
        report = {
            'domain': self.base_url,
            'timestamp': time.time(),
            'results': self.results,
            'summary': {
                'total_endpoints': len(self.results),
                'errors': len([r for r in self.results.values() if 'error' in r]),
                'slow_endpoints': len([r for r in self.results.values() 
                                     if r.get('response_time_ms', 0) > 1000]),
                'average_response_time': sum([r.get('response_time_ms', 0) 
                                            for r in self.results.values()]) / len(self.results)
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Report saved to: {filename}")
        return report

def run_deployment_check(domain):
    """Run performance check on deployed domain."""
    checker = DeploymentPerformanceChecker(domain)
    results = checker.run_comprehensive_check()
    checker.generate_report()
    return results

if __name__ == "__main__":
    # Example usage
    domain = "https://antidote.fit"
    run_deployment_check(domain)