"""
Targeted optimization for the slow /doctors route.
Replaces the inefficient .all() query with pagination and caching.
"""

import time
from functools import wraps
from flask import request, render_template, current_app, g
from models import Doctor, Category, Procedure, DoctorCategory, DoctorProcedure, db
import logging

logger = logging.getLogger(__name__)

# In-memory cache for doctors route
DOCTORS_CACHE = {}
CACHE_TTL = 300  # 5 minutes

def cache_key_for_doctors_request():
    """Generate cache key for current doctors request."""
    return f"doctors_{request.args.get('category_id', 'none')}_{request.args.get('procedure_id', 'none')}_{request.args.get('sort_by', 'experience_desc')}_{request.args.get('search', '')}_{request.args.get('location', '')}_{request.args.get('specialty', '')}_{request.args.get('rating', '')}_{request.args.get('page', 1)}"

def get_cached_doctors(cache_key):
    """Get doctors from cache if valid."""
    if cache_key in DOCTORS_CACHE:
        cached_data, timestamp = DOCTORS_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            logger.info(f"⚡ Doctors cache HIT for key: {cache_key[:50]}...")
            return cached_data
        else:
            del DOCTORS_CACHE[cache_key]
    return None

def cache_doctors(cache_key, data):
    """Cache doctors data."""
    DOCTORS_CACHE[cache_key] = (data, time.time())
    logger.info(f"💾 Doctors cached for key: {cache_key[:50]}...")

def optimized_doctors_route():
    """Optimized version of the doctors route with pagination and caching."""
    start_time = time.time()
    
    try:
        # Get request parameters
        category_id = request.args.get('category_id', type=int)
        procedure_id = request.args.get('procedure_id', type=int)
        sort_by = request.args.get('sort_by', 'experience_desc')
        search_query = request.args.get('search', '').strip()
        location = request.args.get('location', '').strip()
        specialty = request.args.get('specialty', '').strip()
        rating_filter = request.args.get('rating', '')
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Limit to 20 doctors per page
        
        # Check cache first
        cache_key = cache_key_for_doctors_request()
        cached_result = get_cached_doctors(cache_key)
        if cached_result:
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"⚡ CACHED Doctors route completed in {elapsed:.2f}ms")
            return cached_result
        
        title = "All Doctors"
        subtitle = None
        
        # Optimized base query with selective loading
        base_query = Doctor.query.options(
            db.joinedload(Doctor.clinic),  # Load clinic data if needed
        )
        
        # Apply search filters efficiently
        if search_query:
            # Use full-text search if available, otherwise use ILIKE
            search_filter = db.or_(
                Doctor.name.ilike(f"%{search_query}%"),
                Doctor.specialty.ilike(f"%{search_query}%"),
                Doctor.bio.ilike(f"%{search_query}%")
            )
            base_query = base_query.filter(search_filter)
            title = f"Search results for '{search_query}'"
            
        if location:
            base_query = base_query.filter(Doctor.city.ilike(f"%{location}%"))
            if title == "All Doctors":
                title = f"Doctors in {location}"
            else:
                title += f" in {location}"
                
        if specialty:
            base_query = base_query.filter(Doctor.specialty.ilike(f"%{specialty}%"))
            if title == "All Doctors":
                title = f"Doctors specializing in {specialty}"
            else:
                title += f" specializing in {specialty}"
                
        if rating_filter:
            try:
                min_rating = float(rating_filter)
                base_query = base_query.filter(Doctor.rating >= min_rating)
            except ValueError:
                pass
        
        # Handle category and procedure filters with efficient joins
        if category_id:
            category = Category.query.get(category_id)
            if category:
                base_query = base_query.join(DoctorCategory).filter(
                    DoctorCategory.category_id == category_id
                )
                title = f"Doctors specializing in {category.name}"
                subtitle = category.description
        elif procedure_id:
            procedure = Procedure.query.get(procedure_id)
            if procedure:
                base_query = base_query.join(DoctorProcedure).filter(
                    DoctorProcedure.procedure_id == procedure_id
                )
                title = f"Doctors performing {procedure.procedure_name}"
                subtitle = procedure.short_description
        
        # Apply sorting
        if sort_by == 'experience_desc':
            base_query = base_query.order_by(Doctor.experience.desc().nulls_last())
        elif sort_by == 'experience_asc':
            base_query = base_query.order_by(Doctor.experience.asc().nulls_last())
        elif sort_by == 'rating_desc':
            base_query = base_query.order_by(Doctor.rating.desc().nulls_last())
        elif sort_by == 'fee_asc':
            base_query = base_query.order_by(Doctor.consultation_fee.asc().nulls_last())
        elif sort_by == 'fee_desc':
            base_query = base_query.order_by(Doctor.consultation_fee.desc().nulls_last())
        elif sort_by == 'name_asc':
            base_query = base_query.order_by(Doctor.name.asc())
        else:
            base_query = base_query.order_by(Doctor.experience.desc().nulls_last())
        
        # Apply pagination instead of .all()
        doctors_pagination = base_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        doctors = doctors_pagination.items
        
        # Update title with sorting info
        sort_descriptions = {
            'experience_desc': " - Sorted by Experience (Most First)",
            'experience_asc': " - Sorted by Experience (Least First)",
            'rating_desc': " - Sorted by Rating (Highest First)",
            'fee_asc': " - Sorted by Fee (Lowest First)",
            'fee_desc': " - Sorted by Fee (Highest First)",
            'name_asc': " - Sorted by Name (A-Z)"
        }
        title += sort_descriptions.get(sort_by, "")
        
        # Calculate pagination variables for "Show More" functionality
        total_count = doctors_pagination.total if doctors_pagination.total is not None else 0
        showing_count = per_page  # Initially show per_page items (20)
        has_more = total_count > per_page  # Has more if total is greater than first batch
        
        # Prepare response
        result = render_template('doctors.html',
                               doctors=doctors,
                               title=title,
                               subtitle=subtitle,
                               current_sort=sort_by,
                               pagination=doctors_pagination,
                               total_count=total_count,
                               showing_count=showing_count,
                               has_more=has_more)
        
        # Cache the result
        cache_doctors(cache_key, result)
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"⚡ OPTIMIZED Doctors route completed in {elapsed:.2f}ms (page {page}, {len(doctors)} doctors)")
        
        return result
        
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        logger.error(f"❌ Error in optimized doctors route after {elapsed:.2f}ms: {str(e)}")
        return render_template('doctors.html', error=str(e))

def register_optimized_doctors_route(app):
    """Register the optimized doctors route."""
    
    # Remove existing doctors route
    for rule in list(app.url_map.iter_rules()):
        if rule.endpoint == 'web.doctors':
            app.url_map._rules.remove(rule)
            break
    
    # Add optimized route
    @app.route('/doctors')
    def optimized_doctors():
        return optimized_doctors_route()
    
    logger.info("✅ Optimized doctors route registered")

def clear_doctors_cache():
    """Clear the doctors route cache."""
    global DOCTORS_CACHE
    DOCTORS_CACHE.clear()
    logger.info("🗑️ Doctors cache cleared")