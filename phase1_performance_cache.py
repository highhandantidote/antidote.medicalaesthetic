"""
Phase 1 Performance Cache System
Advanced caching for database queries to reduce response times from 504ms to <200ms
"""

import time
import json
import logging
from functools import wraps
from flask import current_app
from app import db
from models import Category, Procedure, Doctor, Clinic, Package, Community, User

logger = logging.getLogger(__name__)

class Phase1PerformanceCache:
    """Advanced caching system for Phase 1 performance optimization"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = 1800  # 30 minutes
        self.short_ttl = 300     # 5 minutes for frequently changing data
        self.long_ttl = 3600     # 1 hour for stable data
        
    def get(self, key):
        """Get cached value if not expired"""
        if key not in self._cache:
            return None
            
        timestamp = self._timestamps.get(key, 0)
        if time.time() - timestamp > self.default_ttl:
            self.invalidate(key)
            return None
            
        logger.debug(f"Cache HIT for key: {key}")
        return self._cache[key]
    
    def set(self, key, value, ttl=None):
        """Set cached value with TTL"""
        if ttl is None:
            ttl = self.default_ttl
            
        self._cache[key] = value
        self._timestamps[key] = time.time()
        logger.debug(f"Cache SET for key: {key} (TTL: {ttl}s)")
    
    def invalidate(self, key):
        """Remove cached value"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        logger.debug(f"Cache INVALIDATED for key: {key}")
    
    def clear_all(self):
        """Clear all cached values"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("All cache cleared")

# Global cache instance
phase1_cache = Phase1PerformanceCache()

def cached_query(cache_key, ttl=None):
    """Decorator for caching database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get from cache first
            cached_result = phase1_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Cache the result
            phase1_cache.set(cache_key, result, ttl)
            logger.info(f"Query executed and cached: {cache_key} ({execution_time:.2f}ms)")
            
            return result
        return wrapper
    return decorator

class HomepageDataCache:
    """Specialized cache for homepage data to reduce 504ms response times"""
    
    @staticmethod
    @cached_query("homepage_categories", ttl=1800)  # 30 minutes
    def get_cached_categories():
        """Get cached popular categories for homepage"""
        try:
            categories = Category.query.limit(6).all()
            if categories:
                # Convert to dict to avoid SQLAlchemy session issues
                category_dicts = []
                for cat in categories:
                    category_dicts.append({
                        'id': cat.id,
                        'name': cat.name,
                        'description': getattr(cat, 'description', ''),
                        'image_url': getattr(cat, 'image_url', ''),
                        'slug': getattr(cat, 'slug', '')
                    })
                return category_dicts
            return []
        except Exception as e:
            logger.error(f"Error caching categories: {e}")
            return []
    
    @staticmethod
    @cached_query("homepage_procedures", ttl=1800)  # 30 minutes  
    def get_cached_procedures():
        """Get cached popular procedures for homepage"""
        try:
            procedures = Procedure.query.limit(6).all()
            if procedures:
                # Convert to dict to avoid SQLAlchemy session issues
                procedure_dicts = []
                for proc in procedures:
                    procedure_dicts.append({
                        'id': proc.id,
                        'procedure_name': proc.procedure_name,
                        'description': getattr(proc, 'description', ''),
                        'image_url': getattr(proc, 'image_url', ''),
                        'category_id': getattr(proc, 'category_id', None)
                    })
                return procedure_dicts
            return []
        except Exception as e:
            logger.error(f"Error caching procedures: {e}")
            return []
    
    @staticmethod
    @cached_query("homepage_doctors", ttl=900)  # 15 minutes
    def get_cached_doctors():
        """Get cached top doctors for homepage"""
        try:
            doctors = Doctor.query.order_by(Doctor.experience.desc().nulls_last()).limit(9).all()
            if doctors:
                # Convert to dict to avoid SQLAlchemy session issues
                doctor_dicts = []
                for doc in doctors:
                    doctor_dicts.append({
                        'id': doc.id,
                        'name': doc.name,
                        'specialization': getattr(doc, 'specialization', ''),
                        'specialty': getattr(doc, 'specialty', ''),
                        'qualification': getattr(doc, 'qualification', ''),
                        'experience': getattr(doc, 'experience', 0),
                        'rating': getattr(doc, 'rating', 0),
                        'profile_image': getattr(doc, 'profile_image', ''),
                        'profile_picture': getattr(doc, 'profile_image', ''),  # Keep both for compatibility
                        'city': getattr(doc, 'city', ''),
                        'bio': getattr(doc, 'bio', ''),
                        'is_verified': getattr(doc, 'is_verified', False)
                    })
                return doctor_dicts
            return []
        except Exception as e:
            logger.error(f"Error caching doctors: {e}")
            return []
    
    @staticmethod
    @cached_query("homepage_packages_featured", ttl=600)  # 10 minutes
    def get_cached_featured_packages():
        """Get cached featured packages for homepage"""
        # Force cache invalidation to refresh with new discount_percentage field
        phase1_cache.invalidate("homepage_packages_featured")
        try:
            result = db.session.execute(db.text("""
                SELECT p.id, p.title, p.price_actual, p.price_discounted, 
                       c.name as clinic_name, c.city as clinic_city, c.rating as clinic_rating,
                       CASE 
                           WHEN p.price_discounted IS NOT NULL AND p.price_discounted > 0 AND p.price_actual > 0
                           THEN ROUND(((p.price_actual - p.price_discounted) * 100.0 / p.price_actual))
                           ELSE 0
                       END as discount_percentage
                FROM packages p 
                JOIN clinics c ON p.clinic_id = c.id 
                WHERE p.is_active = true AND c.is_approved = true
                ORDER BY p.created_at DESC
                LIMIT 6
            """)).fetchall()
            
            return [dict(row._mapping) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error caching featured packages: {e}")
            db.session.rollback()
            return []
    
    @staticmethod
    @cached_query("homepage_packages_affordable", ttl=600)  # 10 minutes
    def get_cached_affordable_packages():
        """Get cached affordable packages for homepage"""
        # Force cache invalidation to refresh with new discount_percentage field
        phase1_cache.invalidate("homepage_packages_affordable")
        try:
            result = db.session.execute(db.text("""
                SELECT p.id, p.title, p.price_actual, p.price_discounted, 
                       c.name as clinic_name, c.city as clinic_city,
                       CASE 
                           WHEN p.price_discounted IS NOT NULL AND p.price_discounted > 0 AND p.price_actual > 0
                           THEN ROUND(((p.price_actual - p.price_discounted) * 100.0 / p.price_actual))
                           ELSE 0
                       END as discount_percentage
                FROM packages p 
                JOIN clinics c ON p.clinic_id = c.id 
                WHERE p.is_active = true AND c.is_approved = true
                AND COALESCE(p.price_discounted, p.price_actual) <= 5000
                ORDER BY COALESCE(p.price_discounted, p.price_actual) ASC
                LIMIT 6
            """)).fetchall()
            
            return [dict(row._mapping) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error caching affordable packages: {e}")
            db.session.rollback()
            return []
    
    @staticmethod
    @cached_query("homepage_community_threads", ttl=300)  # 5 minutes
    def get_cached_community_threads():
        """Get cached community threads for homepage"""
        try:
            threads = Community.query.filter(
                Community.is_deleted == False,
                Community.parent_id == None
            ).order_by(Community.created_at.desc()).limit(5).all()
            
            if threads:
                # Convert to dict to avoid SQLAlchemy session issues
                thread_dicts = []
                for thread in threads:
                    # Get user data
                    user_name = 'Anonymous User'
                    if thread.user_id:
                        user = User.query.get(thread.user_id)
                        if user:
                            user_name = user.username if not thread.is_anonymous else 'Anonymous User'
                    
                    thread_dicts.append({
                        'id': thread.id,
                        'title': getattr(thread, 'title', ''),
                        'content': getattr(thread, 'content', ''),
                        'user_id': thread.user_id,
                        'author_name': user_name,
                        'is_anonymous': getattr(thread, 'is_anonymous', False),
                        'created_at': thread.created_at,
                        'view_count': getattr(thread, 'view_count', 0),
                        'upvotes': getattr(thread, 'upvotes', 0),
                        'reply_count': getattr(thread, 'reply_count', 0)
                    })
                return thread_dicts
            return []
        except Exception as e:
            logger.error(f"Error caching community threads: {e}")
            db.session.rollback()
            return []
    
    @staticmethod
    @cached_query("homepage_all_procedures", ttl=3600)  # 1 hour (stable data)
    def get_cached_all_procedures():
        """Get cached all procedures for booking forms"""
        try:
            procedures = Procedure.query.order_by(Procedure.procedure_name).all()
            if procedures:
                # Convert to dict to avoid SQLAlchemy session issues
                procedure_dicts = []
                for proc in procedures:
                    procedure_dicts.append({
                        'id': proc.id,
                        'procedure_name': proc.procedure_name,
                        'description': getattr(proc, 'description', ''),
                        'category_id': getattr(proc, 'category_id', None)
                    })
                return procedure_dicts
            return []
        except Exception as e:
            logger.error(f"Error caching all procedures: {e}")
            return []

def optimize_homepage_queries():
    """Pre-warm cache with homepage data"""
    logger.info("Pre-warming homepage data cache...")
    
    try:
        HomepageDataCache.get_cached_categories()
        HomepageDataCache.get_cached_procedures()
        HomepageDataCache.get_cached_doctors()
        HomepageDataCache.get_cached_featured_packages()
        HomepageDataCache.get_cached_affordable_packages()
        HomepageDataCache.get_cached_community_threads()
        HomepageDataCache.get_cached_all_procedures()
        
        logger.info("Homepage data cache pre-warmed successfully")
    except Exception as e:
        logger.error(f"Error pre-warming cache: {e}")

def clear_homepage_cache():
    """Clear homepage-related cache entries"""
    cache_keys = [
        "homepage_categories",
        "homepage_procedures", 
        "homepage_doctors",
        "homepage_packages_featured",
        "homepage_packages_affordable",
        "homepage_community_threads",
        "homepage_all_procedures"
    ]
    
    for key in cache_keys:
        phase1_cache.invalidate(key)
    
    logger.info("Homepage cache cleared")