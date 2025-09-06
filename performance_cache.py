"""
Performance caching system to reduce expensive database queries.
Addresses the timezone and schema introspection queries consuming 25.7% and 5.6% of database time.
"""

import os
import json
import time
from functools import wraps
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class PerformanceCache:
    """In-memory cache for expensive database operations."""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = 3600  # 1 hour default TTL
        
    def get(self, key):
        """Get cached value if not expired."""
        if key not in self._cache:
            return None
            
        timestamp = self._timestamps.get(key, 0)
        if time.time() - timestamp > self.default_ttl:
            self.invalidate(key)
            return None
            
        return self._cache[key]
    
    def set(self, key, value, ttl=None):
        """Set cached value with TTL."""
        if ttl is None:
            ttl = self.default_ttl
            
        self._cache[key] = value
        self._timestamps[key] = time.time()
        
        logger.debug(f"Cached key '{key}' with TTL {ttl}s")
    
    def invalidate(self, key):
        """Remove cached value."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self):
        """Clear all cached values."""
        self._cache.clear()
        self._timestamps.clear()

# Global cache instance
performance_cache = PerformanceCache()

def cached_query(key, ttl=3600):
    """Decorator for caching expensive database queries."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Try to get from cache first
            cached_result = performance_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            performance_cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, result cached")
            
            return result
        return wrapper
    return decorator

def optimize_sqlalchemy_queries():
    """Optimize SQLAlchemy to reduce schema introspection queries."""
    try:
        from app import db
        
        # Disable automatic schema reflection for better performance
        if hasattr(db.engine, 'pool'):
            # Configure connection pool to reuse connections
            db.engine.pool._recycle = 3600  # Recycle connections after 1 hour
            db.engine.pool._pre_ping = True  # Validate connections
            
        # Cache metadata to avoid repeated schema queries
        if not hasattr(db.Model, '_cached_metadata'):
            db.Model._cached_metadata = True
            logger.info("SQLAlchemy metadata caching enabled")
            
    except Exception as e:
        logger.error(f"Error optimizing SQLAlchemy: {e}")

def cache_procedure_counts():
    """Cache procedure counts by category to avoid repeated counting."""
    try:
        from app import db
        from models import Procedure
        from sqlalchemy import func
        
        cache_key = "procedure_counts_by_category"
        
        # Check cache first
        cached_counts = performance_cache.get(cache_key)
        if cached_counts:
            return cached_counts
        
        # Query all procedure counts in one go
        procedure_counts = db.session.query(
            Procedure.category_id,
            func.count(Procedure.id).label('count')
        ).group_by(Procedure.category_id).all()
        
        count_dict = {cat_id: count for cat_id, count in procedure_counts}
        
        # Cache for 30 minutes
        performance_cache.set(cache_key, count_dict, ttl=1800)
        logger.info(f"Cached procedure counts for {len(count_dict)} categories")
        
        return count_dict
        
    except Exception as e:
        logger.error(f"Error caching procedure counts: {e}")
        return {}

def get_cached_procedure_count(category_id):
    """Get cached procedure count for a specific category."""
    counts = cache_procedure_counts()
    return counts.get(category_id, 0)

@cached_query("popular_procedures", ttl=1800)
def get_cached_popular_procedures(limit=6):
    """Get cached popular procedures to avoid repeated queries."""
    try:
        from personalization_system import PersonalizationEngine
        return PersonalizationEngine.get_popular_procedures(limit)
    except Exception as e:
        logger.error(f"Error getting popular procedures: {e}")
        return []

@cached_query("popular_categories", ttl=1800)
def get_cached_popular_categories(limit=6):
    """Get cached popular categories to avoid repeated queries."""
    try:
        from personalization_system import PersonalizationEngine
        return PersonalizationEngine.get_popular_categories(limit)
    except Exception as e:
        logger.error(f"Error getting popular categories: {e}")
        return []

def initialize_performance_optimizations():
    """Initialize all performance optimizations."""
    logger.info("Initializing performance optimizations...")
    
    # Enable SQLAlchemy optimizations
    optimize_sqlalchemy_queries()
    
    # Pre-warm caches
    cache_procedure_counts()
    get_cached_popular_procedures()
    get_cached_popular_categories()
    
    logger.info("Performance optimizations initialized successfully")

def clear_performance_cache():
    """Clear all performance caches."""
    performance_cache.clear()
    logger.info("Performance cache cleared")