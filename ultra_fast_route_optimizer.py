"""
Ultra-Fast Route Optimizer for Antidote Medical Platform
Optimizes the slow routes (/doctors, /packages, /procedures, /clinics, /community) 
that are taking 10+ seconds to load on production.
"""
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, render_template
from sqlalchemy import text, func
from app import db
import time

logger = logging.getLogger(__name__)

class UltraFastRouteCache:
    """Cache system for ultra-fast route loading."""
    
    _cache = {}
    _cache_timestamps = {}
    CACHE_DURATION = 300  # 5 minutes in seconds
    
    @classmethod
    def get(cls, key):
        """Get cached data if valid."""
        if key in cls._cache and key in cls._cache_timestamps:
            if time.time() - cls._cache_timestamps[key] < cls.CACHE_DURATION:
                return cls._cache[key]
        return None
    
    @classmethod
    def set(cls, key, data):
        """Set cache data."""
        cls._cache[key] = data
        cls._cache_timestamps[key] = time.time()
    
    @classmethod
    def clear(cls, pattern=None):
        """Clear cache entries matching pattern."""
        if pattern:
            keys_to_remove = [k for k in cls._cache.keys() if pattern in k]
            for key in keys_to_remove:
                cls._cache.pop(key, None)
                cls._cache_timestamps.pop(key, None)
        else:
            cls._cache.clear()
            cls._cache_timestamps.clear()

def ultra_fast_route(cache_key_func=None):
    """Decorator for ultra-fast route optimization."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func()
            else:
                cache_key = f"{f.__name__}_{request.endpoint}_{request.query_string.decode()}"
            
            # Try to get from cache
            cached_result = UltraFastRouteCache.get(cache_key)
            if cached_result:
                logger.info(f"⚡ Ultra-fast cache hit for {f.__name__}: {(time.time() - start_time)*1000:.2f}ms")
                return cached_result
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache the result
            UltraFastRouteCache.set(cache_key, result)
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"🚀 Ultra-fast route {f.__name__} completed: {elapsed:.2f}ms")
            
            return result
        return decorated_function
    return decorator

class UltraFastDataLoader:
    """Ultra-optimized data loading for slow routes."""
    
    @staticmethod
    def get_optimized_doctors_data(limit=100):
        """Get doctors data with single optimized query."""
        try:
            start_time = time.time()
            
            # Single query with all necessary data using raw SQL for maximum performance
            doctors_query = text("""
                SELECT 
                    d.id, d.name, d.specialty, d.experience, d.city, d.state, 
                    d.hospital, d.consultation_fee, d.is_verified, d.rating, 
                    d.review_count, d.bio, d.profile_image, d.success_stories,
                    d.medical_license_number, d.qualification, d.verification_status,
                    c.name as clinic_name, c.city as clinic_city, c.google_rating as clinic_rating
                FROM doctors d
                LEFT JOIN clinics c ON d.clinic_id = c.id
                WHERE d.verification_status IN ('approved', 'pending')
                ORDER BY d.rating DESC NULLS LAST, d.experience DESC NULLS LAST
                LIMIT :limit
            """)
            
            result = db.session.execute(doctors_query, {'limit': limit})
            doctors = [dict(row._mapping) for row in result.fetchall()]
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"✅ Optimized doctors data loaded: {elapsed:.2f}ms ({len(doctors)} doctors)")
            
            return doctors
            
        except Exception as e:
            logger.error(f"Error loading optimized doctors data: {str(e)}")
            return []
    
    @staticmethod
    def get_optimized_procedures_data(limit=100):
        """Get procedures data with single optimized query."""
        try:
            start_time = time.time()
            
            procedures_query = text("""
                SELECT 
                    p.id, p.procedure_name, p.short_description, p.overview,
                    p.min_cost, p.max_cost, p.recovery_time, p.procedure_duration,
                    p.popularity_score, p.avg_rating, p.review_count, p.is_featured,
                    p.body_part, p.tags, p.image_url,
                    c.id as category_id, c.name as category_name
                FROM procedures p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.popularity_score DESC NULLS LAST, p.avg_rating DESC NULLS LAST
                LIMIT :limit
            """)
            
            result = db.session.execute(procedures_query, {'limit': limit})
            procedures = [dict(row._mapping) for row in result.fetchall()]
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"✅ Optimized procedures data loaded: {elapsed:.2f}ms ({len(procedures)} procedures)")
            
            return procedures
            
        except Exception as e:
            logger.error(f"Error loading optimized procedures data: {str(e)}")
            return []
    
    @staticmethod
    def get_optimized_community_data(limit=50):
        """Get community data with single optimized query."""
        try:
            start_time = time.time()
            
            community_query = text("""
                SELECT 
                    co.id, co.title, co.content, co.is_anonymous, co.created_at,
                    co.view_count, co.upvotes, co.featured, co.tags, co.source_type,
                    co.is_professional_verified,
                    u.id as user_id, u.username, u.name as user_name, u.role,
                    c.id as category_id, c.name as category_name,
                    p.id as procedure_id, p.procedure_name,
                    (SELECT COUNT(*) FROM community WHERE parent_id = co.id) as reply_count
                FROM community co
                LEFT JOIN users u ON co.user_id = u.id
                LEFT JOIN categories c ON co.category_id = c.id
                LEFT JOIN procedures p ON co.procedure_id = p.id
                WHERE co.parent_id IS NULL
                ORDER BY co.created_at DESC
                LIMIT :limit
            """)
            
            result = db.session.execute(community_query, {'limit': limit})
            threads = [dict(row._mapping) for row in result.fetchall()]
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"✅ Optimized community data loaded: {elapsed:.2f}ms ({len(threads)} threads)")
            
            return threads
            
        except Exception as e:
            logger.error(f"Error loading optimized community data: {str(e)}")
            return []
    
    @staticmethod
    def get_optimized_packages_data(limit=50):
        """Get packages data with single optimized query."""
        try:
            start_time = time.time()
            
            packages_query = text("""
                SELECT 
                    pkg.id, pkg.title, pkg.description, pkg.price, pkg.discounted_price,
                    pkg.procedure_ids, pkg.is_featured, pkg.is_active, pkg.created_at,
                    pkg.image_url, pkg.highlight_features, pkg.original_price,
                    c.id as clinic_id, c.name as clinic_name, c.city as clinic_city,
                    c.google_rating, c.google_review_count, c.slug as clinic_slug,
                    d.id as doctor_id, d.name as doctor_name, d.specialty as doctor_specialty,
                    d.experience as doctor_experience, d.rating as doctor_rating
                FROM packages pkg
                LEFT JOIN clinics c ON pkg.clinic_id = c.id
                LEFT JOIN doctors d ON pkg.doctor_id = d.id
                WHERE pkg.is_active = true
                ORDER BY pkg.is_featured DESC, pkg.created_at DESC
                LIMIT :limit
            """)
            
            result = db.session.execute(packages_query, {'limit': limit})
            packages = [dict(row._mapping) for row in result.fetchall()]
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"✅ Optimized packages data loaded: {elapsed:.2f}ms ({len(packages)} packages)")
            
            return packages
            
        except Exception as e:
            logger.error(f"Error loading optimized packages data: {str(e)}")
            return []
    
    @staticmethod
    def get_optimized_clinics_data(limit=50):
        """Get clinics data with single optimized query."""
        try:
            start_time = time.time()
            
            clinics_query = text("""
                SELECT 
                    c.id, c.name, c.description, c.city, c.state, c.country,
                    c.address, c.phone, c.email, c.website, c.google_rating,
                    c.google_review_count, c.is_approved, c.slug, c.image_url,
                    c.specialties, c.established_year, c.clinic_type,
                    (SELECT COUNT(*) FROM packages WHERE clinic_id = c.id AND is_active = true) as package_count,
                    (SELECT COUNT(*) FROM doctors WHERE clinic_id = c.id) as doctor_count,
                    (SELECT AVG(rating) FROM doctors WHERE clinic_id = c.id) as avg_doctor_rating
                FROM clinics c
                WHERE c.is_approved = true
                ORDER BY c.google_review_count DESC, c.google_rating DESC
                LIMIT :limit
            """)
            
            result = db.session.execute(clinics_query, {'limit': limit})
            clinics = [dict(row._mapping) for row in result.fetchall()]
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"✅ Optimized clinics data loaded: {elapsed:.2f}ms ({len(clinics)} clinics)")
            
            return clinics
            
        except Exception as e:
            logger.error(f"Error loading optimized clinics data: {str(e)}")
            return []

# Performance monitoring decorator
def monitor_performance(route_name):
    """Monitor route performance and log slow requests."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                
                elapsed = (time.time() - start_time) * 1000
                
                if elapsed > 1000:  # Log if over 1 second
                    logger.warning(f"⚠️ SLOW ROUTE: {route_name} took {elapsed:.2f}ms")
                elif elapsed > 500:  # Log if over 500ms
                    logger.info(f"🐌 Moderate performance: {route_name} took {elapsed:.2f}ms")
                else:
                    logger.info(f"⚡ Fast route: {route_name} took {elapsed:.2f}ms")
                
                return result
                
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"❌ ERROR in {route_name} after {elapsed:.2f}ms: {str(e)}")
                raise
                
        return decorated_function
    return decorator

def register_ultra_fast_optimizations(app):
    """Register ultra-fast route optimizations."""
    
    @app.before_request
    def before_ultra_fast_request():
        """Set up performance monitoring for each request."""
        request.start_time = time.time()
    
    @app.after_request
    def after_ultra_fast_request(response):
        """Log request performance."""
        if hasattr(request, 'start_time'):
            elapsed = (time.time() - request.start_time) * 1000
            if elapsed > 2000:  # Log very slow requests
                logger.warning(f"🚨 VERY SLOW REQUEST: {request.endpoint} took {elapsed:.2f}ms")
        return response
    
    logger.info("✅ Ultra-fast route optimizations registered")
    
    logger.info("✅ Ultra-fast route optimizations registered")