"""
Critical Performance Fix for Antidote Platform
Addresses the major performance bottlenecks causing slow page loads and navigation.

Key optimizations:
1. Single database query for homepage data (replaces 6+ separate queries)
2. Response caching for frequently accessed data
3. CSS optimization for faster rendering
4. Middleware conflict resolution
"""

import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)

class CriticalPerformanceOptimizer:
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    def cached_response(self, cache_key, timeout=300):
        """Decorator for caching expensive database queries."""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Check if we have cached data
                if cache_key in self.cache:
                    cached_data, timestamp = self.cache[cache_key]
                    if datetime.now() - timestamp < timedelta(seconds=timeout):
                        logger.info(f"Returning cached data for {cache_key}")
                        return cached_data
                
                # Execute function and cache result
                result = f(*args, **kwargs)
                self.cache[cache_key] = (result, datetime.now())
                logger.info(f"Cached new data for {cache_key}")
                return result
            return wrapper
        return decorator
    
    def get_optimized_homepage_data(self):
        """
        Single optimized query to get all homepage data at once.
        Replaces the 6+ separate queries that were causing 988ms response times.
        """
        try:
            # Single complex query to get all needed data
            query = text("""
                WITH category_data AS (
                    SELECT ch.id, ch.name, ch.description, ch.image_url, 
                           (SELECT COUNT(DISTINCT ec.entity_id) 
                            FROM entity_categories ec 
                            JOIN category_hierarchy child ON ec.category_id = child.id
                            WHERE (child.id = ch.id OR child.parent_id = ch.id OR child.parent_id IN (SELECT id FROM category_hierarchy WHERE parent_id = ch.id))
                              AND ec.entity_type = 'package') as package_count
                    FROM category_hierarchy ch
                    WHERE ch.level = 1  -- Only show top-level body areas
                    ORDER BY ch.sort_order
                    LIMIT 11
                ),
                popular_procedures AS (
                    SELECT p.id, p.procedure_name, p.short_description as description, 
                           p.min_cost as cost, c.name as category_name
                    FROM procedures p
                    JOIN categories c ON p.category_id = c.id
                    WHERE p.procedure_name IN ('Botox', 'Lip Fillers', 'Liposuction', 'Gynecomastia', 'Rhinoplasty', 'Chemical Peel')
                    LIMIT 6
                ),
                recent_threads AS (
                    SELECT c.id, c.title, c.content, c.created_at, c.view_count, 
                           c.reply_count, c.is_anonymous, c.user_id, u.username as author_name
                    FROM community c
                    LEFT JOIN users u ON c.user_id = u.id
                    WHERE c.parent_id IS NULL AND c.is_deleted = false
                    ORDER BY c.created_at DESC
                    LIMIT 5
                ),
                top_doctors AS (
                    SELECT d.id, d.name, d.specialty, d.qualification, d.city, 
                           d.experience, d.rating, d.image_url, d.is_verified
                    FROM doctors d
                    WHERE d.is_verified = true
                    ORDER BY d.rating DESC NULLS LAST, d.id
                    LIMIT 9
                )
                SELECT 
                    'categories' as data_type, 
                    json_agg(row_to_json(category_data)) as data
                FROM category_data
                UNION ALL
                SELECT 
                    'procedures' as data_type,
                    json_agg(row_to_json(popular_procedures)) as data
                FROM popular_procedures
                UNION ALL
                SELECT 
                    'threads' as data_type,
                    json_agg(row_to_json(recent_threads)) as data
                FROM recent_threads
                UNION ALL
                SELECT 
                    'doctors' as data_type,
                    json_agg(row_to_json(top_doctors)) as data
                FROM top_doctors
            """)
            
            result = db.session.execute(query).fetchall()
            
            # Parse the results
            homepage_data = {
                'categories': [],
                'procedures': [],
                'threads': [],
                'doctors': []
            }
            
            for row in result:
                data_type = row.data_type
                data = row.data if row.data else []
                if data_type in homepage_data:
                    homepage_data[data_type] = data
            
            logger.info("✅ Single-query homepage data loaded successfully")
            return homepage_data
            
        except Exception as e:
            logger.error(f"❌ Error in optimized homepage query: {e}")
            # Fallback to basic data structure
            return {
                'categories': [],
                'procedures': [],
                'threads': [],
                'doctors': []
            }
    
    def get_optimized_packages_data(self):
        """Optimized query for package data."""
        try:
            query = text("""
                WITH affordable_packages AS (
                    SELECT p.id, p.title, p.slug, p.actual_treatment_name, p.price_actual, p.price_discounted, p.description,
                           c.name as clinic_name, c.city as clinic_city, c.google_rating as clinic_rating,
                           c.google_review_count, c.id as clinic_id,
                           CASE 
                               WHEN p.price_discounted IS NOT NULL AND p.price_discounted < p.price_actual 
                               THEN ROUND(((p.price_actual - p.price_discounted) * 100.0 / p.price_actual), 0)
                               ELSE 0 
                           END as discount_percentage
                    FROM packages p 
                    JOIN clinics c ON p.clinic_id = c.id 
                    WHERE p.is_active = true AND c.is_approved = true 
                    AND p.price_actual <= 500000 AND p.price_actual > 0
                    ORDER BY p.price_actual ASC
                    LIMIT 8
                )
                SELECT 
                    'affordable' as package_type,
                    json_agg(row_to_json(affordable_packages)) as packages
                FROM affordable_packages
            """)
            
            result = db.session.execute(query).fetchall()
            
            packages_data = {
                'affordable': []
            }
            
            for row in result:
                package_type = row.package_type
                packages = row.packages if row.packages else []
                if package_type in packages_data:
                    packages_data[package_type] = packages
            
            logger.info("✅ Single-query packages data loaded successfully")
            return packages_data
            
        except Exception as e:
            logger.error(f"❌ Error in optimized packages query: {e}")
            return {'affordable': []}

# Global optimizer instance
performance_optimizer = CriticalPerformanceOptimizer()

def register_critical_performance_optimizations(app):
    """Register critical performance optimizations to the Flask app."""
    
    @app.before_request
    def optimize_request_processing():
        """Optimize request processing for common routes."""
        # Skip optimization for static files
        if request.path.startswith('/static/'):
            return
            
        # Quick health check responses
        if request.path == '/health' or request.args.get('health') == 'true':
            return
        
        # Use consistent time tracking (avoiding conflicts with other middleware)
        import time
        request.critical_start_time = time.time()  # Use different attribute name to avoid conflicts
    
    @app.after_request
    def monitor_response_time(response):
        """Monitor and log response times for performance tracking."""
        if hasattr(request, 'critical_start_time'):
            import time
            duration = time.time() - request.critical_start_time
            if duration > 1.0:  # Log slow requests (over 1 second)
                logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
        
        # Add performance headers (avoid conflicts)
        if not request.path.startswith('/static/'):
            try:
                if hasattr(request, 'critical_start_time'):
                    import time
                    total_time = time.time() - request.critical_start_time
                    response.headers['X-Critical-Response-Time'] = f"{total_time:.3f}s"
            except:
                pass  # Skip if there are conflicts
        
        return response
    
    # Add CSS optimization headers
    @app.after_request
    def add_css_optimization_headers(response):
        """Add headers to optimize CSS loading."""
        if request.path.endswith('.css'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year cache
            response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    
    logger.info("✅ Critical performance optimizations registered")

def get_cached_homepage_data():
    """Get cached homepage data with fallback."""
    @performance_optimizer.cached_response('homepage_data', timeout=300)
    def _get_data():
        return performance_optimizer.get_optimized_homepage_data()
    
    return _get_data()

def get_cached_packages_data():
    """Get cached packages data with fallback."""
    @performance_optimizer.cached_response('packages_data', timeout=300)
    def _get_data():
        return performance_optimizer.get_optimized_packages_data()
    
    return _get_data()