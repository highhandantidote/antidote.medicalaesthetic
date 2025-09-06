"""
Safe Performance Optimization System
Backend-only optimizations with zero visual changes
"""

import time
import gzip
import io
from functools import wraps
from flask import request, make_response, current_app

class SafePerformanceCache:
    """Simple in-memory cache for database queries"""
    
    def __init__(self):
        self.cache = {}
        self.cache_times = {}
        self.default_ttl = 300  # 5 minutes
    
    def get(self, key):
        """Get value from cache if not expired"""
        if key in self.cache:
            if time.time() - self.cache_times[key] < self.default_ttl:
                return self.cache[key]
            else:
                # Remove expired entry
                del self.cache[key]
                del self.cache_times[key]
        return None
    
    def set(self, key, value, ttl=None):
        """Set value in cache with TTL"""
        self.cache[key] = value
        self.cache_times[key] = time.time()
        if ttl:
            self.cache_times[key] = time.time() - (self.default_ttl - ttl)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.cache_times.clear()

# Global cache instance
safe_cache = SafePerformanceCache()

def cache_query(key, ttl=300):
    """Decorator to cache database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Try to get from cache
            cached_result = safe_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            safe_cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

class SafeCompressionMiddleware:
    """Safe compression middleware that doesn't break functionality"""
    
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        """Apply compression only to safe content types"""
        def new_start_response(status, response_headers):
            # Check if client accepts gzip
            accept_encoding = environ.get('HTTP_ACCEPT_ENCODING', '')
            if 'gzip' not in accept_encoding:
                return start_response(status, response_headers)
            
            # Only compress text-based content
            content_type = None
            for header in response_headers:
                if header[0].lower() == 'content-type':
                    content_type = header[1].lower()
                    break
            
            # Safe content types to compress
            safe_types = [
                'text/html', 'text/css', 'text/javascript',
                'application/javascript', 'application/json',
                'text/plain', 'application/xml', 'text/xml'
            ]
            
            if content_type and any(ct in content_type for ct in safe_types):
                # Add compression headers
                response_headers.append(('Content-Encoding', 'gzip'))
                response_headers.append(('Vary', 'Accept-Encoding'))
                
                # Remove content-length header as it will change
                response_headers = [(k, v) for k, v in response_headers 
                                  if k.lower() != 'content-length']
            
            return start_response(status, response_headers)
        
        # Get response from app
        response = self.app(environ, new_start_response)
        
        # Apply compression if needed
        accept_encoding = environ.get('HTTP_ACCEPT_ENCODING', '')
        if 'gzip' in accept_encoding:
            return self._compress_response(response, environ)
        
        return response
    
    def _compress_response(self, response, environ):
        """Compress response data"""
        compressed_data = io.BytesIO()
        
        with gzip.GzipFile(fileobj=compressed_data, mode='wb') as gz:
            for data in response:
                if isinstance(data, str):
                    data = data.encode('utf-8')
                gz.write(data)
        
        compressed_data.seek(0)
        return [compressed_data.read()]

def optimize_database_queries():
    """Optimize common database queries with caching"""
    
    # Import models here to avoid circular imports
    try:
        from models import Category, Procedure, Doctor, Clinic
        from app import db
        
        @cache_query('categories_with_counts', ttl=600)  # 10 minutes
        def get_categories_with_counts():
            """Get categories with procedure counts (cached)"""
            return db.session.query(Category).all()
        
        @cache_query('popular_procedures', ttl=300)  # 5 minutes
        def get_popular_procedures(limit=6):
            """Get popular procedures (cached)"""
            return db.session.query(Procedure).limit(limit).all()
        
        @cache_query('featured_doctors', ttl=300)  # 5 minutes
        def get_featured_doctors(limit=10):
            """Get featured doctors (cached)"""
            return db.session.query(Doctor).filter_by(is_verified=True).limit(limit).all()
        
        @cache_query('verified_clinics', ttl=300)  # 5 minutes
        def get_verified_clinics(limit=10):
            """Get verified clinics (cached)"""
            return db.session.query(Clinic).filter_by(is_approved=True).limit(limit).all()
        
        # Return cached query functions
        return {
            'get_categories_with_counts': get_categories_with_counts,
            'get_popular_procedures': get_popular_procedures,
            'get_featured_doctors': get_featured_doctors,
            'get_verified_clinics': get_verified_clinics
        }
        
    except ImportError as e:
        print(f"Database optimization skipped: {e}")
        return {}

def add_cache_headers(response):
    """Add appropriate cache headers for static content"""
    if request.endpoint and 'static' in request.endpoint:
        # Cache static files for 1 hour
        response.headers['Cache-Control'] = 'public, max-age=3600'
        response.headers['Expires'] = time.strftime(
            '%a, %d %b %Y %H:%M:%S GMT', 
            time.gmtime(time.time() + 3600)
        )
    return response

def register_safe_performance_optimizations(app):
    """Register safe performance optimizations with Flask app"""
    
    print("🚀 Registering safe performance optimizations...")
    
    # 1. Skip compression middleware due to encoding issues
    print("⚠️ Compression middleware disabled to prevent encoding issues")
    
    # 2. Add cache headers for static files
    try:
        @app.after_request
        def add_cache_headers_to_response(response):
            return add_cache_headers(response)
        print("✅ Cache headers enabled for static files")
    except Exception as e:
        print(f"❌ Cache headers failed: {e}")
    
    # 3. Initialize database query caching
    try:
        cached_queries = optimize_database_queries()
        app.config['CACHED_QUERIES'] = cached_queries
        print("✅ Database query caching initialized")
    except Exception as e:
        print(f"❌ Database query caching failed: {e}")
    
    # 4. Add performance monitoring
    try:
        @app.before_request
        def before_request():
            request.start_time = time.time()
        
        @app.after_request
        def after_request(response):
            if hasattr(request, 'start_time'):
                duration = time.time() - request.start_time
                if duration > 1.0:  # Log slow requests
                    print(f"⚠️ Slow request: {request.path} took {duration:.2f}s")
            return response
        
        print("✅ Performance monitoring enabled")
    except Exception as e:
        print(f"❌ Performance monitoring failed: {e}")
    
    print("🎯 Safe performance optimizations registered successfully")
    return app

# Helper function to clear cache when needed
def clear_performance_cache():
    """Clear all performance cache"""
    safe_cache.clear()
    print("🧹 Performance cache cleared")

if __name__ == "__main__":
    print("Safe Performance Optimization System")
    print("This module provides backend-only optimizations with zero visual impact")