
# Advanced Caching Configuration
import redis
from functools import wraps
import json
import hashlib

class AdvancedCache:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_available = True
        except:
            self.redis_available = False
            self.memory_cache = {}
    
    def cache_key(self, prefix, *args, **kwargs):
        """Generate cache key from function args"""
        key_data = str(args) + str(sorted(kwargs.items()))
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key):
        """Get value from cache"""
        if self.redis_available:
            try:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            except:
                pass
        return self.memory_cache.get(key)
    
    def set(self, key, value, timeout=3600):
        """Set value in cache"""
        if self.redis_available:
            try:
                self.redis_client.setex(key, timeout, json.dumps(value))
                return
            except:
                pass
        self.memory_cache[key] = value
    
    def delete(self, key):
        """Delete key from cache"""
        if self.redis_available:
            try:
                self.redis_client.delete(key)
                return
            except:
                pass
        self.memory_cache.pop(key, None)

# Global cache instance
advanced_cache = AdvancedCache()

def cache_result(prefix, timeout=3600):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = advanced_cache.cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = advanced_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            advanced_cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
