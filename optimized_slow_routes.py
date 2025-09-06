"""
Optimized implementations of slow routes for Antidote Medical Platform
Replaces the slow /doctors, /packages, /procedures, /clinics, /community routes
with ultra-fast cached versions.
"""
import logging
from flask import Blueprint, render_template, request, jsonify
from ultra_fast_route_optimizer import (
    UltraFastDataLoader, 
    ultra_fast_route, 
    monitor_performance,
    UltraFastRouteCache
)
from app import db
from models import Category, BodyPart
import time

logger = logging.getLogger(__name__)

# Create blueprint for optimized routes
optimized_routes = Blueprint('optimized_routes', __name__)

@optimized_routes.route('/doctors')
@monitor_performance('doctors_page')
@ultra_fast_route(lambda: f"doctors_{request.query_string.decode()}")
def optimized_doctors():
    """Ultra-fast doctors page with optimized data loading."""
    try:
        start_time = time.time()
        
        # Get search parameters
        search_query = request.args.get('search', '').strip()
        location = request.args.get('location', '').strip()
        specialty = request.args.get('specialty', '').strip()
        sort_by = request.args.get('sort_by', 'rating_desc')
        
        # Load optimized doctors data
        doctors_data = UltraFastDataLoader.get_optimized_doctors_data(limit=200)
        
        # Apply client-side-compatible filters
        if search_query:
            doctors_data = [
                doc for doc in doctors_data 
                if (search_query.lower() in doc.get('name', '').lower() or 
                    search_query.lower() in doc.get('specialty', '').lower() or
                    search_query.lower() in doc.get('bio', '').lower())
            ]
        
        if location:
            doctors_data = [
                doc for doc in doctors_data 
                if location.lower() in doc.get('city', '').lower()
            ]
        
        if specialty:
            doctors_data = [
                doc for doc in doctors_data 
                if specialty.lower() in doc.get('specialty', '').lower()
            ]
        
        # Apply sorting
        if sort_by == 'rating_desc':
            doctors_data.sort(key=lambda x: x.get('rating', 0) or 0, reverse=True)
        elif sort_by == 'experience_desc':
            doctors_data.sort(key=lambda x: x.get('experience', 0) or 0, reverse=True)
        elif sort_by == 'fee_asc':
            doctors_data.sort(key=lambda x: x.get('consultation_fee', 999999) or 999999)
        elif sort_by == 'name_asc':
            doctors_data.sort(key=lambda x: x.get('name', ''))
        
        # Build title
        title = "All Doctors"
        if search_query:
            title = f"Search results for '{search_query}'"
        if location:
            title += f" in {location}" if "Search results" in title else f"Doctors in {location}"
        if specialty:
            title += f" specializing in {specialty}"
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"🚀 Optimized doctors page loaded in {elapsed:.2f}ms with {len(doctors_data)} doctors")
        
        return render_template('doctors.html', 
                             doctors=doctors_data, 
                             title=title,
                             current_sort=sort_by,
                             is_optimized=True)
        
    except Exception as e:
        logger.error(f"Error in optimized doctors route: {str(e)}")
        return render_template('doctors.html', 
                             doctors=[], 
                             title="Doctors", 
                             error="Unable to load doctors data")

@optimized_routes.route('/procedures')
@monitor_performance('procedures_page')
@ultra_fast_route(lambda: f"procedures_{request.query_string.decode()}")
def optimized_procedures():
    """Ultra-fast procedures page with optimized data loading."""
    try:
        start_time = time.time()
        
        # Get search parameters
        search_query = request.args.get('search', '').strip()
        body_part = request.args.get('body_part', '').strip()
        category_id = request.args.get('category_id', type=int)
        sort_by = request.args.get('sort', 'popular')
        
        # Load optimized procedures data
        procedures_data = UltraFastDataLoader.get_optimized_procedures_data(limit=200)
        
        # Apply filters
        if search_query:
            procedures_data = [
                proc for proc in procedures_data 
                if (search_query.lower() in proc.get('procedure_name', '').lower() or 
                    search_query.lower() in proc.get('short_description', '').lower() or
                    search_query.lower() in proc.get('body_part', '').lower())
            ]
        
        if body_part:
            procedures_data = [
                proc for proc in procedures_data 
                if body_part.lower() in proc.get('body_part', '').lower()
            ]
        
        if category_id:
            procedures_data = [
                proc for proc in procedures_data 
                if proc.get('category_id') == category_id
            ]
        
        # Apply sorting
        if sort_by == 'popular':
            procedures_data.sort(key=lambda x: x.get('popularity_score', 0) or 0, reverse=True)
        elif sort_by == 'name':
            procedures_data.sort(key=lambda x: x.get('procedure_name', ''))
        elif sort_by == 'rating':
            procedures_data.sort(key=lambda x: x.get('avg_rating', 0) or 0, reverse=True)
        elif sort_by == 'cost_low':
            procedures_data.sort(key=lambda x: x.get('min_cost', 999999) or 999999)
        elif sort_by == 'cost_high':
            procedures_data.sort(key=lambda x: x.get('max_cost', 0) or 0, reverse=True)
        
        # Build title
        title = "All Procedures"
        if search_query:
            title = f"Search results for '{search_query}'"
        if body_part:
            title += f" for {body_part}" if "Search results" in title else f"Procedures for {body_part}"
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"🚀 Optimized procedures page loaded in {elapsed:.2f}ms with {len(procedures_data)} procedures")
        
        return render_template('procedures.html', 
                             procedures=procedures_data, 
                             title=title,
                             is_optimized=True)
        
    except Exception as e:
        logger.error(f"Error in optimized procedures route: {str(e)}")
        return render_template('procedures.html', 
                             procedures=[], 
                             title="Procedures", 
                             error="Unable to load procedures data")

@optimized_routes.route('/community')
@monitor_performance('community_page')
@ultra_fast_route(lambda: f"community_{request.query_string.decode()}")
def optimized_community():
    """Ultra-fast community page with optimized data loading."""
    try:
        start_time = time.time()
        
        # Get search parameters
        search_query = request.args.get('search', '').strip()
        category_filter = request.args.get('category', '').strip()
        sort_by = request.args.get('sort', 'latest')
        
        # Load optimized community data
        threads_data = UltraFastDataLoader.get_optimized_community_data(limit=100)
        
        # Apply filters
        if search_query:
            threads_data = [
                thread for thread in threads_data 
                if (search_query.lower() in thread.get('title', '').lower() or 
                    search_query.lower() in thread.get('content', '').lower())
            ]
        
        if category_filter:
            try:
                category_id = int(category_filter)
                threads_data = [
                    thread for thread in threads_data 
                    if thread.get('category_id') == category_id
                ]
            except ValueError:
                threads_data = [
                    thread for thread in threads_data 
                    if (thread.get('category_name', '').lower() == category_filter.lower())
                ]
        
        # Apply sorting
        if sort_by == 'latest':
            threads_data.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == 'popular':
            threads_data.sort(key=lambda x: x.get('upvotes', 0) or 0, reverse=True)
        elif sort_by == 'oldest':
            threads_data.sort(key=lambda x: x.get('created_at', ''))
        elif sort_by == 'most_replies':
            threads_data.sort(key=lambda x: x.get('reply_count', 0) or 0, reverse=True)
        
        # Get categories for filter dropdown (cached)
        categories_cache_key = "community_categories"
        categories = UltraFastRouteCache.get(categories_cache_key)
        if not categories:
            try:
                categories = Category.query.limit(20).all()
                UltraFastRouteCache.set(categories_cache_key, categories)
            except:
                categories = []
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"🚀 Optimized community page loaded in {elapsed:.2f}ms with {len(threads_data)} threads")
        
        return render_template('community_modern.html', 
                             threads=threads_data, 
                             categories=categories,
                             search_query=search_query,
                             category_filter=category_filter,
                             sort_by=sort_by,
                             is_optimized=True)
        
    except Exception as e:
        logger.error(f"Error in optimized community route: {str(e)}")
        return render_template('community_modern.html', 
                             threads=[], 
                             categories=[],
                             search_query='',
                             category_filter='',
                             sort_by='latest',
                             error="Unable to load community data")

@optimized_routes.route('/packages')
@monitor_performance('packages_page')
@ultra_fast_route(lambda: f"packages_{request.query_string.decode()}")
def optimized_packages():
    """Ultra-fast packages page with optimized data loading."""
    try:
        start_time = time.time()
        
        # Get search parameters
        search_query = request.args.get('search', '').strip()
        location = request.args.get('location', '').strip()
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        sort_by = request.args.get('sort', 'featured')
        
        # Load optimized packages data
        packages_data = UltraFastDataLoader.get_optimized_packages_data(limit=100)
        
        # Apply filters
        if search_query:
            packages_data = [
                pkg for pkg in packages_data 
                if (search_query.lower() in pkg.get('title', '').lower() or 
                    search_query.lower() in pkg.get('description', '').lower() or
                    search_query.lower() in pkg.get('clinic_name', '').lower())
            ]
        
        if location:
            packages_data = [
                pkg for pkg in packages_data 
                if location.lower() in pkg.get('clinic_city', '').lower()
            ]
        
        if min_price:
            packages_data = [
                pkg for pkg in packages_data 
                if (pkg.get('discounted_price') or pkg.get('price', 0)) >= min_price
            ]
        
        if max_price:
            packages_data = [
                pkg for pkg in packages_data 
                if (pkg.get('discounted_price') or pkg.get('price', 999999)) <= max_price
            ]
        
        # Apply sorting
        if sort_by == 'featured':
            packages_data.sort(key=lambda x: (x.get('is_featured', False), x.get('created_at', '')), reverse=True)
        elif sort_by == 'price_low':
            packages_data.sort(key=lambda x: x.get('discounted_price') or x.get('price', 999999) or 999999)
        elif sort_by == 'price_high':
            packages_data.sort(key=lambda x: x.get('discounted_price') or x.get('price', 0) or 0, reverse=True)
        elif sort_by == 'newest':
            packages_data.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == 'clinic_rating':
            packages_data.sort(key=lambda x: x.get('google_rating', 0) or 0, reverse=True)
        
        # Build title
        title = "Treatment Packages"
        if search_query:
            title = f"Package search results for '{search_query}'"
        if location:
            title += f" in {location}" if "search results" in title else f"Treatment Packages in {location}"
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"🚀 Optimized packages page loaded in {elapsed:.2f}ms with {len(packages_data)} packages")
        
        return render_template('packages.html', 
                             packages=packages_data, 
                             title=title,
                             current_sort=sort_by,
                             is_optimized=True)
        
    except Exception as e:
        logger.error(f"Error in optimized packages route: {str(e)}")
        return render_template('packages.html', 
                             packages=[], 
                             title="Treatment Packages", 
                             error="Unable to load packages data")

@optimized_routes.route('/clinics')
@monitor_performance('clinics_page')
@ultra_fast_route(lambda: f"clinics_{request.query_string.decode()}")
def optimized_clinics():
    """Ultra-fast clinics page with optimized data loading."""
    try:
        start_time = time.time()
        
        # Get search parameters
        search_query = request.args.get('search', '').strip()
        location = request.args.get('location', '').strip()
        specialty = request.args.get('specialty', '').strip()
        min_rating = request.args.get('min_rating', type=float)
        sort_by = request.args.get('sort', 'rating')
        
        # Load optimized clinics data
        clinics_data = UltraFastDataLoader.get_optimized_clinics_data(limit=100)
        
        # Apply filters
        if search_query:
            clinics_data = [
                clinic for clinic in clinics_data 
                if (search_query.lower() in clinic.get('name', '').lower() or 
                    search_query.lower() in clinic.get('description', '').lower() or
                    search_query.lower() in clinic.get('specialties', '').lower())
            ]
        
        if location:
            clinics_data = [
                clinic for clinic in clinics_data 
                if location.lower() in clinic.get('city', '').lower()
            ]
        
        if specialty:
            clinics_data = [
                clinic for clinic in clinics_data 
                if specialty.lower() in clinic.get('specialties', '').lower()
            ]
        
        if min_rating:
            clinics_data = [
                clinic for clinic in clinics_data 
                if (clinic.get('google_rating', 0) or 0) >= min_rating
            ]
        
        # Apply sorting
        if sort_by == 'rating':
            clinics_data.sort(key=lambda x: x.get('google_rating', 0) or 0, reverse=True)
        elif sort_by == 'reviews':
            clinics_data.sort(key=lambda x: x.get('google_review_count', 0) or 0, reverse=True)
        elif sort_by == 'name':
            clinics_data.sort(key=lambda x: x.get('name', ''))
        elif sort_by == 'packages':
            clinics_data.sort(key=lambda x: x.get('package_count', 0) or 0, reverse=True)
        elif sort_by == 'doctors':
            clinics_data.sort(key=lambda x: x.get('doctor_count', 0) or 0, reverse=True)
        
        # Build title
        title = "Verified Clinics"
        if search_query:
            title = f"Clinic search results for '{search_query}'"
        if location:
            title += f" in {location}" if "search results" in title else f"Verified Clinics in {location}"
        
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"🚀 Optimized clinics page loaded in {elapsed:.2f}ms with {len(clinics_data)} clinics")
        
        return render_template('clinics.html', 
                             clinics=clinics_data, 
                             title=title,
                             current_sort=sort_by,
                             is_optimized=True)
        
    except Exception as e:
        logger.error(f"Error in optimized clinics route: {str(e)}")
        return render_template('clinics.html', 
                             clinics=[], 
                             title="Verified Clinics", 
                             error="Unable to load clinics data")

def register_optimized_routes(app):
    """Register optimized routes to replace slow ones."""
    
    # Register the blueprint
    app.register_blueprint(optimized_routes)
    
    # Add route monitoring
    @app.route('/admin/route-performance')
    def route_performance_dashboard():
        """Admin dashboard for route performance monitoring."""
        return jsonify({
            'cache_stats': {
                'cached_items': len(UltraFastRouteCache._cache),
                'cache_keys': list(UltraFastRouteCache._cache.keys())
            },
            'status': 'Optimized routes active'
        })
    
    logger.info("✅ Optimized slow routes registered successfully")