"""
Final route optimization for procedures and packages pages.
Targets sub-200ms performance for all remaining slow routes.
"""

import time
from flask import request, render_template
from models import Procedure, Category, Community, db
import logging

logger = logging.getLogger(__name__)

# Simple cache for fast pages
FAST_CACHE = {}
CACHE_TTL = 300

def get_cache_key():
    """Generate simple cache key."""
    return f"{request.endpoint}_{hash(str(sorted(request.args.items())))}"

def cached_response(func):
    """Simple caching decorator."""
    def wrapper(*args, **kwargs):
        cache_key = get_cache_key()
        
        # Check cache
        if cache_key in FAST_CACHE:
            cached_data, timestamp = FAST_CACHE[cache_key]
            if time.time() - timestamp < CACHE_TTL:
                logger.info(f"⚡ Cache HIT: {request.endpoint}")
                return cached_data
            else:
                del FAST_CACHE[cache_key]
        
        # Execute function and cache result
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start_time) * 1000
        
        FAST_CACHE[cache_key] = (result, time.time())
        logger.info(f"⚡ OPTIMIZED {request.endpoint} in {elapsed:.1f}ms")
        return result
    return wrapper

@cached_response
def fast_procedures():
    """Ultra-fast procedures route with Show More functionality."""
    try:
        # Get parameters with defaults - matching main route
        category_id = request.args.get('category_id', type=int)
        search_query = request.args.get('search', '').strip()
        body_part = request.args.get('body_part', '').strip()
        sort_by = request.args.get('sort', 'popular')
        
        # Pagination parameters for "Show More" functionality
        limit = 20  # Show 20 procedures initially (matching main route)
        
        # Optimized base query
        base_query = Procedure.query
        title = "All Procedures"
        
        # Apply search filters (matching main route logic)
        if search_query:
            base_query = base_query.filter(
                db.or_(
                    Procedure.procedure_name.ilike(f"%{search_query}%"),
                    Procedure.short_description.ilike(f"%{search_query}%"),
                    Procedure.overview.ilike(f"%{search_query}%"),
                    Procedure.body_part.ilike(f"%{search_query}%")
                )
            )
            title = f"Search results for '{search_query}'"
            
        if body_part:
            base_query = base_query.filter(Procedure.body_part.ilike(f"%{body_part}%"))
            if title == "All Procedures":
                title = f"Procedures for {body_part}"
            else:
                title += f" for {body_part}"
        
        if category_id:
            category = Category.query.get(category_id)
            if category:
                base_query = base_query.filter_by(category_id=category_id)
                title = f"Procedures in {category.name}"
                
                # Apply sorting and limit for category view
                if sort_by == 'name':
                    procedures = base_query.order_by(Procedure.procedure_name.asc()).limit(limit).all()
                elif sort_by == 'popular':
                    procedures = base_query.order_by(Procedure.id.desc()).limit(limit).all()
                else:
                    procedures = base_query.limit(limit).all()
                
                # Get total count for show more functionality
                total_count = base_query.count()
                
                return render_template('procedures.html', 
                                     procedures=procedures, 
                                     category=category, 
                                     title=title,
                                     total_count=total_count,
                                     showing_count=len(procedures),
                                     has_more=total_count > limit)
        
        # Apply sorting and limit (matching main route)
        if sort_by == 'name':
            base_query = base_query.order_by(Procedure.procedure_name.asc())
        elif sort_by == 'popular':
            base_query = base_query.order_by(Procedure.id.desc())  # Most recent as proxy for popular
        
        # Get total count before applying limit
        total_count = base_query.count()
        
        # Apply limit for initial load
        procedures = base_query.limit(limit).all()
            
        return render_template('procedures.html', 
                             procedures=procedures, 
                             title=title,
                             total_count=total_count,
                             showing_count=len(procedures),
                             has_more=total_count > limit)
    except Exception as e:
        logger.error(f"Fast procedures error: {e}")
        return render_template('procedures.html', error=str(e))

@cached_response  
def fast_packages():
    """Ultra-fast packages route."""
    try:
        # Simple packages page without complex queries
        from models import Clinic
        
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Get clinics that offer packages (simplified)
        clinics = Clinic.query.filter(
            Clinic.status == 'approved'
        ).order_by(Clinic.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        categories = Category.query.order_by(Category.name).all()
        
        return render_template('treatment_packages.html',
                             clinics=clinics.items,
                             categories=categories,
                             pagination=clinics)
    except Exception as e:
        logger.error(f"Fast packages error: {e}")
        return render_template('treatment_packages.html', error=str(e))

def register_final_optimizations(app):
    """Register final optimizations for remaining slow routes."""
    
    # Remove existing slow routes
    routes_to_replace = ['/procedures', '/packages']
    for route_path in routes_to_replace:
        for rule in list(app.url_map.iter_rules()):
            if rule.rule == route_path:
                app.url_map._rules.remove(rule)
                break
    
    # Register ultra-fast routes
    app.add_url_rule('/procedures', 'fast_procedures', fast_procedures, methods=['GET'])
    app.add_url_rule('/packages', 'fast_packages', fast_packages, methods=['GET'])
    
    logger.info("🚀 Final route optimizations registered - targeting sub-200ms")

def clear_fast_cache():
    """Clear the fast cache."""
    global FAST_CACHE
    FAST_CACHE.clear()
    logger.info("🗑️ Fast cache cleared")