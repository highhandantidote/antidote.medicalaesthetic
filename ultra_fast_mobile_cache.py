"""
Ultra-Fast Mobile Cache System for 100% Performance Score
Advanced caching specifically optimized for mobile performance
"""

import time
import json
import hashlib
from functools import wraps
from flask import request, make_response, current_app
import pickle
import gzip

class UltraFastMobileCache:
    """Ultra-fast caching system for mobile performance"""
    
    def __init__(self):
        self.memory_cache = {}
        self.mobile_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'mobile_hits': 0
        }
    
    def is_mobile(self):
        """Detect mobile requests"""
        user_agent = request.headers.get('User-Agent', '').lower()
        return any(keyword in user_agent for keyword in [
            'mobile', 'iphone', 'android', 'tablet', 'ipad'
        ])
    
    def generate_cache_key(self, *args, **kwargs):
        """Generate cache key with mobile consideration"""
        base_key = f"{request.path}:{request.query_string.decode()}"
        if self.is_mobile():
            base_key = f"mobile:{base_key}"
        
        # Add additional arguments
        if args or kwargs:
            params = f"{args}:{sorted(kwargs.items())}"
            base_key = f"{base_key}:{params}"
        
        return hashlib.md5(base_key.encode()).hexdigest()
    
    def cache_response(self, timeout=300, mobile_timeout=600):
        """Cache decorator optimized for mobile"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.generate_cache_key(*args, **kwargs)
                
                # Check cache
                cached_data = self.get_cached_response(cache_key)
                if cached_data:
                    self.cache_stats['hits'] += 1
                    if self.is_mobile():
                        self.cache_stats['mobile_hits'] += 1
                    
                    # Return cached response
                    response = make_response(cached_data['content'])
                    response.headers.update(cached_data['headers'])
                    response.headers['X-Cache'] = 'HIT'
                    response.headers['X-Cache-Key'] = cache_key[:8]
                    return response
                
                # Cache miss - generate response
                self.cache_stats['misses'] += 1
                response = func(*args, **kwargs)
                
                # Cache the response
                cache_timeout = mobile_timeout if self.is_mobile() else timeout
                self.set_cached_response(cache_key, response, cache_timeout)
                
                response.headers['X-Cache'] = 'MISS'
                response.headers['X-Cache-Key'] = cache_key[:8]
                return response
            
            return wrapper
        return decorator
    
    def get_cached_response(self, cache_key):
        """Get cached response data"""
        cache_store = self.mobile_cache if self.is_mobile() else self.memory_cache
        
        if cache_key in cache_store:
            cached_item = cache_store[cache_key]
            
            # Check expiration
            if time.time() < cached_item['expires']:
                return cached_item['data']
            else:
                # Remove expired item
                del cache_store[cache_key]
        
        return None
    
    def set_cached_response(self, cache_key, response, timeout):
        """Cache response data"""
        cache_store = self.mobile_cache if self.is_mobile() else self.memory_cache
        
        # Prepare cache data
        cache_data = {
            'content': response.get_data(as_text=True),
            'headers': dict(response.headers)
        }
        
        # Store in cache
        cache_store[cache_key] = {
            'data': cache_data,
            'expires': time.time() + timeout,
            'created': time.time()
        }
        
        # Limit cache size (keep only 1000 most recent items)
        if len(cache_store) > 1000:
            oldest_key = min(cache_store.keys(), 
                           key=lambda k: cache_store[k]['created'])
            del cache_store[oldest_key]
    
    def cache_database_query(self, timeout=600):
        """Cache database queries for ultra-fast mobile performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key for database query
                cache_key = f"db:{func.__name__}:{self.generate_cache_key(*args, **kwargs)}"
                
                # Check cache
                if cache_key in self.memory_cache:
                    cached_item = self.memory_cache[cache_key]
                    if time.time() < cached_item['expires']:
                        return cached_item['data']
                    else:
                        del self.memory_cache[cache_key]
                
                # Execute query
                result = func(*args, **kwargs)
                
                # Cache result
                self.memory_cache[cache_key] = {
                    'data': result,
                    'expires': time.time() + timeout,
                    'created': time.time()
                }
                
                return result
            
            return wrapper
        return decorator
    
    def preload_mobile_content(self, app):
        """Preload critical content for mobile users"""
        with app.app_context():
            try:
                # Preload homepage data
                from models import Procedure, Doctor, Clinic
                
                # Cache popular procedures for mobile
                popular_procedures = Procedure.query.limit(10).all()
                mobile_key = "mobile:preload:procedures"
                self.mobile_cache[mobile_key] = {
                    'data': [{'id': p.id, 'name': p.procedure_name} for p in popular_procedures],
                    'expires': time.time() + 3600,
                    'created': time.time()
                }
                
                # Cache featured doctors for mobile
                featured_doctors = Doctor.query.limit(8).all()
                mobile_key = "mobile:preload:doctors"
                self.mobile_cache[mobile_key] = {
                    'data': [{'id': d.id, 'name': d.name} for d in featured_doctors],
                    'expires': time.time() + 3600,
                    'created': time.time()
                }
                
                current_app.logger.info("✅ Mobile content preloaded for ultra-fast performance")
                
            except Exception as e:
                current_app.logger.warning(f"Mobile preload failed: {e}")
    
    def get_cache_stats(self):
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate': f"{hit_rate:.1f}%",
            'total_hits': self.cache_stats['hits'],
            'mobile_hits': self.cache_stats['mobile_hits'],
            'total_misses': self.cache_stats['misses'],
            'cache_size': len(self.memory_cache),
            'mobile_cache_size': len(self.mobile_cache)
        }

# Global cache instance
mobile_cache = UltraFastMobileCache()

def register_ultra_fast_mobile_cache(app):
    """Register ultra-fast mobile cache system"""
    
    # Preload mobile content on startup
    mobile_cache.preload_mobile_content(app)
    
    # Add cache stats endpoint
    @app.route('/api/mobile/cache-stats')
    def mobile_cache_stats():
        """Mobile cache performance statistics"""
        return mobile_cache.get_cache_stats()
    
    app.logger.info("✅ Ultra-fast mobile cache system registered")
    return mobile_cache