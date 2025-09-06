#!/usr/bin/env python3
"""
SEO Health Check for Antidote Medical Marketplace
Comprehensive testing and validation of all SEO systems
"""

import requests
import json
import sys
import time
from datetime import datetime

class SEOHealthChecker:
    """Comprehensive SEO system health checker"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
        
    def check_endpoint(self, endpoint, description):
        """Check a single endpoint and return status"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    # Try to parse JSON if applicable
                    if 'application/json' in response.headers.get('content-type', ''):
                        data = response.json()
                        return True, f"✅ {description}: OK", data
                    else:
                        return True, f"✅ {description}: OK", response.text[:200]
                except:
                    return True, f"✅ {description}: OK (Non-JSON)", response.text[:200]
            else:
                return False, f"❌ {description}: HTTP {response.status_code}", None
                
        except requests.exceptions.RequestException as e:
            return False, f"❌ {description}: Connection Error - {str(e)}", None
    
    def run_comprehensive_check(self):
        """Run comprehensive SEO health check"""
        print("🔍 Starting Comprehensive SEO Health Check for Antidote")
        print("=" * 60)
        
        # Core SEO endpoints
        seo_endpoints = [
            ("/api/seo/core-web-vitals", "Core Web Vitals API"),
            ("/api/seo/performance-metrics", "Performance Metrics API"),
            ("/sitemap.xml", "XML Sitemap"),
            ("/robots.txt", "Robots.txt"),
            ("/opensearch.xml", "OpenSearch XML"),
        ]
        
        # Local SEO endpoints
        local_seo_endpoints = [
            ("/api/local-seo/cities", "Supported Cities API"),
            ("/city/mumbai", "Mumbai Landing Page"),
            ("/city/delhi", "Delhi Landing Page"),
            ("/city/bangalore", "Bangalore Landing Page"),
        ]
        
        # Medical content endpoints
        medical_content_endpoints = [
            ("/api/medical-content/optimize-procedure/1", "Procedure Optimization API"),
            ("/api/medical-content/optimize-doctor/1", "Doctor Optimization API"),
        ]
        
        # Link building endpoints
        link_building_endpoints = [
            ("/api/link-building/strategy", "Link Building Strategy API"),
            ("/api/link-building/opportunities", "Link Opportunities API"),
            ("/api/authority-building/profile/1", "Authority Profile API"),
        ]
        
        # Enhanced procedure endpoints
        enhanced_procedure_endpoints = [
            ("/api/enhanced-procedures/generate/1", "Enhanced Procedure API"),
        ]
        
        all_endpoints = [
            ("Core SEO Systems", seo_endpoints),
            ("Local SEO Systems", local_seo_endpoints),
            ("Medical Content Systems", medical_content_endpoints),
            ("Link Building Systems", link_building_endpoints),
            ("Enhanced Procedure Systems", enhanced_procedure_endpoints),
        ]
        
        total_checks = 0
        passed_checks = 0
        
        for category_name, endpoints in all_endpoints:
            print(f"\n📋 {category_name}")
            print("-" * 40)
            
            for endpoint, description in endpoints:
                success, message, data = self.check_endpoint(endpoint, description)
                print(message)
                
                total_checks += 1
                if success:
                    passed_checks += 1
                    
                # Store detailed results
                self.results[endpoint] = {
                    'success': success,
                    'description': description,
                    'data': data
                }
                
                time.sleep(0.5)  # Rate limiting
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 SEO Health Check Summary")
        print("=" * 60)
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {total_checks - passed_checks}")
        print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%")
        
        # Detailed analysis
        self.analyze_results()
        
        return passed_checks, total_checks
    
    def analyze_results(self):
        """Analyze results and provide recommendations"""
        print(f"\n🔬 Detailed Analysis")
        print("-" * 40)
        
        # Check sitemap content
        if '/sitemap.xml' in self.results:
            sitemap_data = self.results['/sitemap.xml'].get('data', '')
            if '<url>' in sitemap_data:
                print("✅ Sitemap contains URL entries")
            else:
                print("⚠️ Sitemap appears empty - check database connections")
        
        # Check performance metrics
        if '/api/seo/performance-metrics' in self.results:
            metrics = self.results['/api/seo/performance-metrics'].get('data', {})
            if isinstance(metrics, dict):
                total_content = sum([
                    metrics.get('total_procedures', 0),
                    metrics.get('total_doctors', 0),
                    metrics.get('total_clinics', 0),
                    metrics.get('total_packages', 0)
                ])
                
                if total_content > 0:
                    print(f"✅ Content available: {total_content} total items")
                else:
                    print("⚠️ No content found - using fallback estimates")
        
        # Check city pages
        city_pages_working = 0
        for endpoint in self.results:
            if '/city/' in endpoint and self.results[endpoint]['success']:
                city_pages_working += 1
        
        if city_pages_working > 0:
            print(f"✅ Local SEO: {city_pages_working} city pages working")
        
        # Recommendations
        print(f"\n💡 Recommendations")
        print("-" * 40)
        
        failed_endpoints = [ep for ep, result in self.results.items() if not result['success']]
        
        if failed_endpoints:
            print("🔧 Fix these endpoints:")
            for endpoint in failed_endpoints:
                print(f"   - {endpoint}: {self.results[endpoint]['description']}")
        
        if not failed_endpoints:
            print("🎉 All SEO systems are operational!")
            print("📈 Ready for Google rankings improvement")
        
        print(f"\n🚀 Next Steps:")
        print("1. Submit sitemap to Google Search Console")
        print("2. Set up Google Business Profiles for major cities")
        print("3. Begin medical directory submissions")
        print("4. Monitor Core Web Vitals improvements")
        print("5. Track keyword ranking progress")

def main():
    """Main function to run SEO health check"""
    checker = SEOHealthChecker()
    
    try:
        passed, total = checker.run_comprehensive_check()
        
        if passed == total:
            print(f"\n🎯 RESULT: All {total} SEO systems are working perfectly!")
            sys.exit(0)
        else:
            print(f"\n⚠️ RESULT: {passed}/{total} systems working. Check failures above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Health check failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()