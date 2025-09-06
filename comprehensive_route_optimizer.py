"""
Comprehensive route optimization for all remaining slow routes.
Targets: /procedures, /community, /packages to achieve sub-200ms performance.
"""

import time
from functools import wraps
from flask import request, render_template, current_app, g
from models import Procedure, Category, Community, db
try:
    from models import Package
except ImportError:
    Package = None
import logging

logger = logging.getLogger(__name__)

# Global cache for all optimized routes
ROUTE_CACHE = {}
CACHE_TTL = 300  # 5 minutes

def get_route_cache_key(route_name):
    """Generate cache key for current request."""
    args_str = "&".join([f"{k}={v}" for k, v in sorted(request.args.items())])
    return f"{route_name}_{args_str}_{request.path}"

def get_cached_response(cache_key):
    """Get response from cache if valid."""
    if cache_key in ROUTE_CACHE:
        cached_data, timestamp = ROUTE_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            logger.info(f"⚡ Cache HIT for {cache_key[:30]}...")
            return cached_data
        else:
            del ROUTE_CACHE[cache_key]
    return None

def cache_response(cache_key, data):
    """Cache response data."""
    ROUTE_CACHE[cache_key] = (data, time.time())
    logger.info(f"💾 Cached response for {cache_key[:30]}...")

def optimized_procedures_route():
    """Optimized procedures route with pagination and caching."""
    start_time = time.time()
    cache_key = get_route_cache_key("procedures")
    
    # Check cache first
    cached_result = get_cached_response(cache_key)
    if cached_result:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⚡ CACHED Procedures route in {elapsed:.2f}ms")
        return cached_result
    
    try:
        # Get parameters
        category_id = request.args.get('category_id', type=int)
        search_query = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = 24  # Reasonable pagination
        
        # Optimized query with selective loading
        base_query = Procedure.query.options(
            db.selectinload(Procedure.category)
        )
        
        if category_id:
            base_query = base_query.filter(Procedure.category_id == category_id)
            
        if search_query:
            base_query = base_query.filter(
                db.or_(
                    Procedure.procedure_name.ilike(f"%{search_query}%"),
                    Procedure.short_description.ilike(f"%{search_query}%")
                )
            )
        
        # Apply pagination and get categories efficiently
        procedures_pagination = base_query.order_by(
            Procedure.procedure_name.asc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        categories = Category.query.all()  # Categories list is small, cache separately
        
        result = render_template('procedures.html',
                               procedures=procedures_pagination.items,
                               categories=categories,
                               pagination=procedures_pagination,
                               current_category=category_id,
                               search_query=search_query)
        
        cache_response(cache_key, result)
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⚡ OPTIMIZED Procedures route in {elapsed:.2f}ms ({len(procedures_pagination.items)} procedures)")
        return result
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        logger.error(f"❌ Error in optimized procedures route after {elapsed:.2f}ms: {str(e)}")
        return render_template('procedures.html', error=str(e))

def optimized_community_route():
    """Optimized community route with efficient loading."""
    start_time = time.time()
    cache_key = get_route_cache_key("community")
    
    # Check cache first
    cached_result = get_cached_response(cache_key)
    if cached_result:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⚡ CACHED Community route in {elapsed:.2f}ms")
        return cached_result
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 15  # Reasonable pagination for community posts
        
        # Optimized query for community threads with relationships
        threads_pagination = Community.query.options(
            db.selectinload(Community.user),
            db.selectinload(Community.procedure)
        ).filter_by(
            is_approved=True
        ).order_by(
            Community.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        result = render_template('community.html',
                               threads=threads_pagination.items,
                               pagination=threads_pagination)
        
        cache_response(cache_key, result)
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⚡ OPTIMIZED Community route in {elapsed:.2f}ms ({len(threads_pagination.items)} threads)")
        return result
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        logger.error(f"❌ Error in optimized community route after {elapsed:.2f}ms: {str(e)}")
        return render_template('community.html', error=str(e))

def optimized_packages_route():
    """Optimized packages route.""" 
    start_time = time.time()
    cache_key = get_route_cache_key("packages")
    
    # Check cache first
    cached_result = get_cached_response(cache_key)
    if cached_result:
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⚡ CACHED Packages route in {elapsed:.2f}ms")
        return cached_result
    
    try:
        # Get parameters
        clinic_id = request.args.get('clinic_id', type=int)
        category_id = request.args.get('category_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Optimized query
        base_query = Package.query.options(
            db.selectinload(Package.clinic),
            db.selectinload(Package.category)
        )
        
        if clinic_id:
            base_query = base_query.filter(Package.clinic_id == clinic_id)
        if category_id:
            base_query = base_query.filter(Package.category_id == category_id)
        
        packages_pagination = base_query.order_by(
            Package.price.asc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        categories = Category.query.all()
        
        result = render_template('packages.html',
                               packages=packages_pagination.items,
                               categories=categories,
                               pagination=packages_pagination,
                               current_category=category_id)
        
        cache_response(cache_key, result)
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⚡ OPTIMIZED Packages route in {elapsed:.2f}ms ({len(packages_pagination.items)} packages)")
        return result
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        logger.error(f"❌ Error in optimized packages route after {elapsed:.2f}ms: {str(e)}")
        return render_template('packages.html', error=str(e))

def register_comprehensive_optimizations(app):
    """Register all comprehensive route optimizations."""
    
    # Remove existing routes to avoid conflicts
    routes_to_optimize = ['web.procedures', 'web.community', 'web.packages']
    for route_endpoint in routes_to_optimize:
        for rule in list(app.url_map.iter_rules()):
            if rule.endpoint == route_endpoint:
                app.url_map._rules.remove(rule)
                break
    
    # Register optimized routes
    @app.route('/procedures')
    def optimized_procedures():
        return optimized_procedures_route()
    
    @app.route('/community') 
    def optimized_community():
        return optimized_community_route()
    
    @app.route('/packages')
    def optimized_packages():
        return optimized_packages_route()
    
    logger.info("✅ Comprehensive route optimizations registered")

def clear_route_cache():
    """Clear all route caches."""
    global ROUTE_CACHE
    ROUTE_CACHE.clear()
    logger.info("🗑️ All route caches cleared")