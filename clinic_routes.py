"""
Clinic & Package Marketplace Routes
Implementation following Antidote Core System Architecture Documentation
Korean clinic marketplace experience adapted for Indian market
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from sqlalchemy import desc, and_, or_, text
from models import db, Clinic, Lead, CreditTransaction, User, Procedure, Category
from credit_billing_system import CreditBillingService
from datetime import datetime
import logging
import time
import pytz

# Create blueprint for clinic marketplace
clinic_bp = Blueprint('clinic', __name__, url_prefix='/clinic')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_day_hours(working_hours_str):
    """
    Extract and format current day's working hours in IST timezone.
    
    Args:
        working_hours_str: String containing working hours for all days
        
    Returns:
        String with current day's hours or "Closed" if not available
    """
    if not working_hours_str:
        return ""
    
    try:
        # Get current day in IST
        ist = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist)
        current_day = current_time_ist.strftime('%A')  # Monday, Tuesday, etc.
        
        # Parse working hours string
        working_hours_str = str(working_hours_str)
        
        # Split by semicolon to get individual day entries
        day_entries = working_hours_str.split(';')
        
        for entry in day_entries:
            entry = entry.strip()
            if entry.startswith(current_day + ':'):
                # Extract the timing part after the day name
                timing = entry.split(':', 1)[1].strip()
                
                # Clean up the timing format
                if 'Closed' in timing or timing == '':
                    return "Closed Today"
                
                return f"Today: {timing}"
        
        # If current day not found, return empty
        return ""
        
    except Exception as e:
        logger.error(f"Error parsing working hours: {e}")
        return ""

# ============================================================================
# PUBLIC CLINIC MARKETPLACE PAGES
# ============================================================================

@clinic_bp.route('/')
def clinic_marketplace():
    """Main clinic marketplace page - Korean aesthetic clinic style."""
    try:
        # Get featured clinics using correct column names
        featured_clinics_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE is_approved = true 
            ORDER BY rating DESC NULLS LAST
            LIMIT 8
        """)).fetchall()
        
        # Convert to list of dictionaries for template
        featured_clinics = [dict(row._mapping) for row in featured_clinics_result]
        
        # Get all clinics for general display
        all_clinics_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE is_approved = true 
            ORDER BY rating DESC NULLS LAST, review_count DESC NULLS LAST
            LIMIT 12
        """)).fetchall()
        
        all_clinics = [dict(row._mapping) for row in all_clinics_result]
        
        # Get cities with clinic presence
        cities_result = db.session.execute(text("""
            SELECT DISTINCT city FROM clinics 
            WHERE is_approved = true 
            ORDER BY city 
            LIMIT 15
        """)).fetchall()
        
        cities = [row[0] for row in cities_result if row[0]]
        
        # Get categories for filtering (fallback to simple list)
        try:
            categories_result = db.session.execute(text("SELECT DISTINCT category_type FROM categories LIMIT 10")).fetchall()
            categories = [{'category_type': row[0]} for row in categories_result if row[0]]
        except:
            categories = [
                {'category_type': 'Facial Treatment'}, 
                {'category_type': 'Body Contouring'}, 
                {'category_type': 'Skin Care'},
                {'category_type': 'Hair Treatment'}
            ]
        
        # Package data (simplified for now)
        popular_packages = []
        
        return render_template('clinic/marketplace.html', 
                             featured_clinics=featured_clinics,
                             all_clinics=all_clinics,
                             popular_packages=popular_packages,
                             categories=categories,
                             cities=cities)
                             
    except Exception as e:
        logger.error(f"Error loading clinic marketplace: {e}")
        flash('Error loading clinic marketplace. Please try again.', 'error')
        return render_template('clinic/marketplace.html', 
                             featured_clinics=[],
                             popular_packages=[],
                             categories=[],
                             cities=[])

@clinic_bp.route('/all')
def all_clinics():
    """Display all verified clinics in a grid layout."""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 24  # Show 24 clinics per page for better performance
        
        logger.info(f"Loading clinic page {page} with per_page {per_page}")
        
        # Get only essential columns for listing page to improve performance
        all_clinics_result = db.session.execute(text("""
            SELECT 
                id, name, city, state, rating, review_count, 
                profile_image, contact_number, email,
                specialties, is_approved, created_at, slug,
                google_rating, google_review_count, description
            FROM clinics 
            WHERE is_approved = true 
            ORDER BY 
                COALESCE(rating, google_rating, 0) DESC, 
                COALESCE(review_count, google_review_count, 0) DESC
            LIMIT :limit OFFSET :offset
        """), {
            'limit': per_page,
            'offset': (page - 1) * per_page
        }).fetchall()
        
        # Convert to list of objects for template (to support dot notation access)
        class ClinicObject:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        clinics = [ClinicObject(dict(row._mapping)) for row in all_clinics_result]
        
        logger.info(f"Found {len(clinics)} clinics for page {page}")
        
        # Get total count for pagination
        total_count_result = db.session.execute(text("""
            SELECT COUNT(*) FROM clinics WHERE is_approved = true
        """)).scalar()
        
        logger.info(f"Total approved clinics: {total_count_result}")
        
        # Get cities for filtering (limit to prevent slow queries)
        cities_result = db.session.execute(text("""
            SELECT DISTINCT city FROM clinics 
            WHERE is_approved = true AND city IS NOT NULL
            ORDER BY city 
            LIMIT 50
        """)).fetchall()
        
        cities = [row[0] for row in cities_result if row[0]]
        
        # Calculate pagination info
        total_pages = (total_count_result + per_page - 1) // per_page
        
        logger.info(f"Rendering template with {len(clinics)} clinics, total_count: {total_count_result}, total_pages: {total_pages}")
        
        return render_template('clinic/all_clinics.html', 
                             clinics=clinics,
                             cities=cities,
                             total_count=total_count_result,
                             current_page=page,
                             total_pages=total_pages,
                             per_page=per_page)
                             
    except Exception as e:
        logger.error(f"Error loading all clinics: {e}")
        flash('Error loading clinics. Please try again.', 'error')
        return redirect(url_for('clinic.clinic_marketplace'))

@clinic_bp.route('/directory')
def clinic_directory():
    """Display all clinics with enhanced filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 12
        offset = (page - 1) * per_page
        
        # Get all approved clinics
        clinics_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE is_approved = true 
            ORDER BY 
                COALESCE(rating, google_rating, 0) DESC, 
                COALESCE(review_count, google_review_count, 0) DESC
            LIMIT :limit OFFSET :offset
        """), {'limit': per_page, 'offset': offset}).fetchall()
        
        clinics = [dict(row._mapping) for row in clinics_result]
        
        # Add current day hours to each clinic
        for clinic in clinics:
            if clinic.get('working_hours'):
                clinic['current_day_hours'] = get_current_day_hours(clinic['working_hours'])
            else:
                clinic['current_day_hours'] = ""
        
        # Get total count
        total_count = db.session.execute(text("SELECT COUNT(*) FROM clinics WHERE is_approved = true")).scalar()
        
        # Get filter options for UI
        cities_result = db.session.execute(text("SELECT DISTINCT city FROM clinics WHERE is_approved = true AND city IS NOT NULL ORDER BY city")).fetchall()
        cities = [city[0] for city in cities_result if city[0]]
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page if total_count else 1
        
        return render_template('clinic/all_clinics.html',
                             clinics=clinics,
                             cities=cities,
                             total_count=total_count,
                             current_page=page,
                             total_pages=total_pages,
                             per_page=per_page)
                             
    except Exception as e:
        logger.error(f"Error loading all clinics: {e}")
        flash('Error loading clinics. Please try again.', 'error')
        return redirect(url_for('clinic.clinic_marketplace'))

@clinic_bp.route('/packages')
def all_packages():
    """Display all available treatment packages with show more functionality."""
    try:
        from models import Package
        
        # Get filter parameters
        search_query = request.args.get('search', '').strip()
        location = request.args.get('location', '').strip()
        category = request.args.get('category', '').strip()
        sort_by = request.args.get('sort', 'popular')
        
        # Pagination parameters for "Show More" functionality
        limit = 20  # Show 20 packages initially
        
        # Base query
        base_query = Package.query.filter(Package.is_active == True)
        
        # Apply search filters
        if search_query:
            base_query = base_query.filter(
                db.or_(
                    Package.title.ilike(f"%{search_query}%"),
                    Package.description.ilike(f"%{search_query}%"),
                    Package.procedure_info.ilike(f"%{search_query}%")
                )
            )
            
        if location:
            # Join with clinic to filter by location
            base_query = base_query.join(Clinic).filter(Clinic.city.ilike(f"%{location}%"))
            
        if category:
            base_query = base_query.filter(Package.category.ilike(f"%{category}%"))
        
        # Apply sorting
        if sort_by == 'price_asc':
            base_query = base_query.order_by(Package.price.asc().nulls_last())
        elif sort_by == 'price_desc':
            base_query = base_query.order_by(Package.price.desc().nulls_last())
        elif sort_by == 'rating':
            base_query = base_query.order_by(Package.rating.desc().nulls_last())
        elif sort_by == 'popular':
            # Sort by popularity (using created_at as proxy)
            base_query = base_query.order_by(Package.created_at.desc())
        else:
            base_query = base_query.order_by(Package.created_at.desc())
        
        # Get total count before applying limit
        total_count = base_query.count()
        
        # Apply limit for initial load
        packages = base_query.limit(limit).all()
        
        # Debug logging
        logger.info(f"📦 Packages pagination: total={total_count}, showing={len(packages)}, limit={limit}, has_more={total_count > limit}")
        
        return render_template('packages/directory.html', 
                             packages=packages,
                             total_count=total_count,
                             showing_count=len(packages),
                             has_more=total_count > limit,
                             filter_params={
                                 'search': search_query,
                                 'location': location,
                                 'category': category,
                                 'sort': sort_by
                             })
                             
    except Exception as e:
        logger.error(f"Error loading packages: {e}")
        flash('Error loading packages. Please try again.', 'error')
        # Fallback to basic template with empty data
        return render_template('packages/directory.html', 
                             packages=[],
                             total_count=0,
                             showing_count=0,
                             has_more=False,
                             filter_params={})

@clinic_bp.route('/api/packages/load-more')
def api_packages_load_more():
    """API endpoint for loading more packages (Show More functionality)."""
    try:
        from models import Package
        
        # Get pagination parameters
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # Get filter parameters (same as main packages route)
        search_query = request.args.get('search', '').strip()
        location = request.args.get('location', '').strip()
        category = request.args.get('category', '').strip()
        sort_by = request.args.get('sort', 'popular')
        
        # Build query with same filters as main route
        base_query = Package.query.filter(Package.is_active == True)
        
        if search_query:
            base_query = base_query.filter(
                db.or_(
                    Package.title.ilike(f"%{search_query}%"),
                    Package.description.ilike(f"%{search_query}%"),
                    Package.procedure_info.ilike(f"%{search_query}%")
                )
            )
            
        if location:
            base_query = base_query.join(Clinic).filter(Clinic.city.ilike(f"%{location}%"))
            
        if category:
            base_query = base_query.filter(Package.category.ilike(f"%{category}%"))
        
        # Apply sorting
        if sort_by == 'price_asc':
            base_query = base_query.order_by(Package.price.asc().nulls_last())
        elif sort_by == 'price_desc':
            base_query = base_query.order_by(Package.price.desc().nulls_last())
        elif sort_by == 'rating':
            base_query = base_query.order_by(Package.rating.desc().nulls_last())
        elif sort_by == 'popular':
            base_query = base_query.order_by(Package.created_at.desc())
        else:
            base_query = base_query.order_by(Package.created_at.desc())
        
        # Get total count and paginated results
        total_count = base_query.count()
        packages = base_query.offset(offset).limit(limit).all()
        
        # Format packages for JSON response
        packages_data = []
        for package in packages:
            packages_data.append({
                'id': package.id,
                'package_name': package.package_name,
                'description': package.description,
                'price': package.price,
                'rating': package.rating,
                'procedures_included': package.procedures_included,
                'clinic_name': package.clinic.name if package.clinic else None,
                'clinic_city': package.clinic.city if package.clinic else None,
                'image_url': package.image_url if hasattr(package, 'image_url') else None
            })
        
        return jsonify({
            'success': True,
            'packages': packages_data,
            'total_count': total_count,
            'has_more': (offset + limit) < total_count
        })
        
    except Exception as e:
        logger.error(f"Error loading more packages: {e}")
        return jsonify({
            'success': False,
            'message': 'Error loading more packages'
        }), 500

# DISABLED: Using comprehensive clinic profile system instead
@clinic_bp.route('/profile/<slug>')
def clinic_profile(slug):
    """Redirect to the comprehensive clinic profile page."""
    return redirect(url_for('clinic.clinic_detail', slug=slug))

@clinic_bp.route('/search')
def search_clinics():
    """Enhanced search clinics with comprehensive filtering."""
    try:
        # Get search parameters
        query = request.args.get('q', '').strip()
        location = request.args.get('location', request.args.get('city', ''))
        specialty = request.args.get('specialty', request.args.get('category', ''))
        rating = request.args.get('rating', type=float)
        verified = request.args.get('verified', '')
        sort_by = request.args.get('sort', 'rating')
        page = request.args.get('page', 1, type=int)
        
        # Build search query using raw SQL with correct column names
        sql_conditions = ["is_approved = true"]
        sql_params = {}
        
        # Enhanced search - searches across multiple fields
        if query:
            sql_conditions.append("""
                (name ILIKE :query 
                OR address ILIKE :query 
                OR city ILIKE :query 
                OR state ILIKE :query
                OR description ILIKE :query)
            """)
            sql_params['query'] = f'%{query}%'
        
        if location:
            sql_conditions.append("(city ILIKE :location OR state ILIKE :location)")
            sql_params['location'] = f'%{location}%'
        
        if specialty:
            # This would need to be enhanced when specialty/category data is available
            sql_conditions.append("description ILIKE :specialty")
            sql_params['specialty'] = f'%{specialty}%'
        
        if rating:
            sql_conditions.append("google_rating >= :rating")
            sql_params['rating'] = rating
        
        if verified == 'true':
            sql_conditions.append("is_verified = true")
        elif verified == 'false':
            sql_conditions.append("is_verified = false")
        
        # Build ORDER BY clause with improved rating logic
        order_by = "COALESCE(rating, google_rating, 0) DESC, COALESCE(review_count, google_review_count, 0) DESC"
        if sort_by == 'reviews':
            order_by = "COALESCE(review_count, google_review_count, 0) DESC, COALESCE(rating, google_rating, 0) DESC"
        elif sort_by == 'newest':
            order_by = "created_at DESC"
        elif sort_by == 'alphabetical':
            order_by = "name ASC"
        elif sort_by == 'distance':
            order_by = "city ASC, name ASC"  # Would need geolocation for true distance
        
        # Build final query
        where_clause = " AND ".join(sql_conditions)
        per_page = 12
        offset = (page - 1) * per_page
        
        # Execute search query
        search_sql = f"""
            SELECT * FROM clinics 
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
        """
        
        sql_params.update({'limit': per_page, 'offset': offset})
        clinics_result = db.session.execute(text(search_sql), sql_params).fetchall()
        clinics = [dict(row._mapping) for row in clinics_result]
        
        # Add current day hours to each clinic
        for clinic in clinics:
            if clinic.get('working_hours'):
                clinic['current_day_hours'] = get_current_day_hours(clinic['working_hours'])
            else:
                clinic['current_day_hours'] = ""
        
        # Get total count
        count_sql = f"SELECT COUNT(*) FROM clinics WHERE {where_clause}"
        total_clinics = db.session.execute(text(count_sql), {k: v for k, v in sql_params.items() if k not in ['limit', 'offset']}).scalar()
        
        # Get filter options for UI using raw SQL
        cities_result = db.session.execute(text("SELECT DISTINCT city FROM clinics WHERE is_approved = true AND city IS NOT NULL ORDER BY city")).fetchall()
        cities = [city[0] for city in cities_result if city[0]]
        
        # Calculate pagination info
        total_pages = (total_clinics + per_page - 1) // per_page if total_clinics else 1
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('clinic/all_clinics.html',
                             clinics=clinics,
                             cities=cities,
                             total_count=total_clinics,
                             current_page=page,
                             total_pages=total_pages,
                             per_page=per_page,
                             has_prev=has_prev,
                             has_next=has_next)
                             
    except Exception as e:
        logger.error(f"Error in clinic search: {e}")
        flash('Error performing search. Please try again.', 'error')
        return redirect(url_for('clinic.clinic_marketplace'))

# ============================================================================
# API ENDPOINTS FOR CLINIC FILTERING
# ============================================================================

@clinic_bp.route('/api/clinic/search')
def api_clinic_search():
    """API endpoint for clinic search suggestions."""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify({'success': False, 'message': 'Query too short'})
        
        # Search across clinics, doctors, and specialties
        suggestions = []
        
        # Clinic name suggestions
        clinic_results = db.session.execute(text("""
            SELECT name, city, state FROM clinics 
            WHERE name ILIKE :query AND is_approved = true
            LIMIT 5
        """), {'query': f'%{query}%'}).fetchall()
        
        for clinic in clinic_results:
            suggestions.append({
                'text': clinic[0],
                'subtitle': f"{clinic[1]}, {clinic[2]}",
                'icon': 'fa-hospital'
            })
        
        # Location suggestions
        location_results = db.session.execute(text("""
            SELECT DISTINCT city, state FROM clinics 
            WHERE (city ILIKE :query OR state ILIKE :query) AND is_approved = true
            LIMIT 3
        """), {'query': f'%{query}%'}).fetchall()
        
        for location in location_results:
            suggestions.append({
                'text': f"{location[0]}, {location[1]}",
                'subtitle': 'Location',
                'icon': 'fa-map-marker-alt'
            })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Error in clinic search API: {e}")
        return jsonify({'success': False, 'message': 'Search failed'})

@clinic_bp.route('/api/clinic/locations')
def api_clinic_locations():
    """API endpoint for clinic locations."""
    try:
        locations_result = db.session.execute(text("""
            SELECT DISTINCT city, state FROM clinics 
            WHERE is_approved = true AND city IS NOT NULL AND state IS NOT NULL
            ORDER BY city
        """)).fetchall()
        
        locations = [f"{location[0]}, {location[1]}" for location in locations_result]
        
        return jsonify({
            'success': True,
            'locations': locations
        })
        
    except Exception as e:
        logger.error(f"Error getting clinic locations: {e}")
        return jsonify({'success': False, 'message': 'Failed to load locations'})

@clinic_bp.route('/api/clinic/specialties')
def api_clinic_specialties():
    """API endpoint for clinic specialties."""
    try:
        # For now, return common specialties
        # This would be enhanced when specialty data is properly structured
        specialties = [
            'Dermatology',
            'Plastic Surgery',
            'Cosmetic Surgery',
            'Hair Transplant',
            'Laser Treatment',
            'Skin Care',
            'Anti-Aging',
            'Aesthetic Medicine',
            'Reconstructive Surgery',
            'Facial Surgery',
            'Body Contouring',
            'Non-Surgical Treatments'
        ]
        
        return jsonify({
            'success': True,
            'specialties': specialties
        })
        
    except Exception as e:
        logger.error(f"Error getting clinic specialties: {e}")
        return jsonify({'success': False, 'message': 'Failed to load specialties'})

@clinic_bp.route('/api/geocode/reverse')
def api_reverse_geocode():
    """API endpoint for reverse geocoding (coordinates to location name)."""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        if not lat or not lng:
            return jsonify({'success': False, 'message': 'Invalid coordinates'})
        
        # Use a simple reverse geocoding service or return a generic response
        # For now, return a placeholder since we don't have a configured geocoding service
        return jsonify({
            'success': True,
            'city': 'Current Location',
            'message': 'Location detected'
        })
        
    except Exception as e:
        logger.error(f"Error in reverse geocoding: {e}")
        return jsonify({'success': False, 'message': 'Geocoding failed'})

@clinic_bp.route('/view/<slug>')
def clinic_detail(slug):
    """Comprehensive clinic profile page with all management sections."""
    try:
        import json
        
        # Get clinic basic information by slug or ID
        clinic_id = slug if slug.isdigit() else 0
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE (slug = :slug OR id = :clinic_id) AND is_approved = true
            LIMIT 1
        """), {"slug": slug, "clinic_id": clinic_id}).fetchone()
        
        if not clinic_result:
            flash('Clinic not found or not approved.', 'error')
            return redirect(url_for('clinic.clinic_marketplace'))
        
        clinic = dict(clinic_result._mapping)
        clinic_id = clinic['id']  # Get the actual clinic ID from the result
        
        # Parse JSON fields
        if clinic.get('clinic_highlights'):
            try:
                # Handle both string and list formats
                if isinstance(clinic['clinic_highlights'], str):
                    clinic['clinic_highlights'] = json.loads(clinic['clinic_highlights'])
                # If it's already a list, use it as is
                logger.info(f"Clinic highlights for clinic {clinic_id}: {clinic['clinic_highlights']}")
            except Exception as e:
                logger.error(f"Error parsing clinic highlights for clinic {clinic_id}: {e}")
                clinic['clinic_highlights'] = []
        else:
            logger.info(f"No clinic highlights found for clinic {clinic_id}")
        
        # Parse working hours - handle both JSON and plain text formats
        if clinic.get('working_hours'):
            try:
                working_hours_str = clinic['working_hours']
                if isinstance(working_hours_str, str):
                    # Try to parse as JSON first (legacy format)
                    try:
                        hours_data = json.loads(working_hours_str)
                        # Convert JSON hours to the format expected by the template
                        formatted_hours = []
                        for day, hours in hours_data.items():
                            if hours:
                                # Clean Unicode characters and normalize format
                                clean_hours = hours.replace('\u202f', ' ').replace('to', '–')
                                formatted_hours.append(f"{day}: {clean_hours}")
                        clinic['working_hours'] = '; '.join(formatted_hours)
                    except json.JSONDecodeError:
                        # Already in plain text format (Google Places format)
                        # Just clean Unicode characters
                        clinic['working_hours'] = working_hours_str.replace('\u202f', ' ').replace('to', '–')
                    
                    logger.info(f"Formatted working hours for clinic {clinic_id}: {clinic['working_hours']}")
            except Exception as e:
                logger.error(f"Error parsing working hours for clinic {clinic_id}: {e}")
                clinic['working_hours'] = clinic.get('operating_hours', '')
            clinic['clinic_highlights'] = []
        
        if clinic.get('popular_procedures'):
            try:
                popular_procedure_ids = json.loads(clinic['popular_procedures'])
                # Get popular procedures details
                if popular_procedure_ids:
                    placeholders = ','.join([':id{}'.format(i) for i in range(len(popular_procedure_ids))])
                    params = {f'id{i}': pid for i, pid in enumerate(popular_procedure_ids)}
                    
                    popular_procedures_result = db.session.execute(text(f"""
                        SELECT * FROM procedures WHERE id IN ({placeholders})
                    """), params).fetchall()
                    popular_procedures = [dict(row._mapping) for row in popular_procedures_result]
                else:
                    popular_procedures = []
            except:
                popular_procedures = []
        else:
            popular_procedures = []
        
        # Get clinic specialties - handle both ID format and text format
        clinic_specialties = []
        if clinic.get('specialties'):
            try:
                # First try to parse as specialty IDs (legacy format)
                specialty_ids = [int(x) for x in clinic['specialties'].split(',') if x.strip().isdigit()]
                if specialty_ids:
                    placeholders = ','.join([':id{}'.format(i) for i in range(len(specialty_ids))])
                    params = {f'id{i}': sid for i, sid in enumerate(specialty_ids)}
                    
                    specialties_result = db.session.execute(text(f"""
                        SELECT * FROM categories WHERE id IN ({placeholders})
                    """), params).fetchall()
                    clinic_specialties = [dict(row._mapping) for row in specialties_result]
                else:
                    # Handle text format specialties (current format)
                    specialty_names = [x.strip() for x in clinic['specialties'].split(',') if x.strip()]
                    clinic_specialties = [{'name': name} for name in specialty_names]
            except:
                # Fallback: treat as text format
                try:
                    specialty_names = [x.strip() for x in clinic['specialties'].split(',') if x.strip()]
                    clinic_specialties = [{'name': name} for name in specialty_names]
                except:
                    pass
        
        # Get clinic packages
        packages_result = db.session.execute(text("""
            SELECT * FROM packages 
            WHERE clinic_id = :clinic_id AND is_active = true
            ORDER BY is_featured DESC, created_at DESC
        """), {"clinic_id": clinic_id}).fetchall()
        
        packages = [dict(row._mapping) for row in packages_result]
        
        # Get clinic doctors
        clinic_doctors_result = db.session.execute(text("""
            SELECT d.*, cd.role, cd.is_primary 
            FROM doctors d
            JOIN clinic_doctors cd ON d.id = cd.doctor_id
            WHERE cd.clinic_id = :clinic_id AND cd.is_active = true
            ORDER BY cd.is_primary DESC, d.rating DESC NULLS LAST
        """), {"clinic_id": clinic_id}).fetchall()
        
        clinic_doctors = [dict(row._mapping) for row in clinic_doctors_result]
        
        # Get before/after photos from packages
        before_after_photos = []
        for package in packages:
            if package.get('results_gallery'):
                try:
                    # Handle both string and list formats
                    results = package['results_gallery']
                    if isinstance(results, str):
                        results = json.loads(results)
                    
                    # Handle new format: list of result objects with before/after images
                    if isinstance(results, list):
                        for result in results:
                            if isinstance(result, dict) and result.get('before_image') and result.get('after_image'):
                                before_after_photos.append({
                                    'procedure_name': result.get('title') or package.get('title', 'Treatment Results'),
                                    'doctor_name': result.get('doctor_name', ''),
                                    'description': result.get('description', ''),
                                    'before_image': result.get('before_image'),
                                    'after_image': result.get('after_image')
                                })
                    # Handle old format: dict with images array
                    elif isinstance(results, dict) and results.get('images'):
                        images = results.get('images', [])
                        if len(images) >= 2:
                            before_after_photos.append({
                                'procedure_name': package.get('title', 'Treatment Results'),
                                'doctor_name': '',
                                'description': '',
                                'before_image': images[0],
                                'after_image': images[1]
                            })
                except Exception as e:
                    logger.error(f"Error processing package results_gallery: {e}")
                    continue
        
        # Also get results from clinic's results_gallery if available
        if clinic.get('results_gallery'):
            try:
                # Handle both string and dict formats
                clinic_results = clinic['results_gallery']
                if isinstance(clinic_results, str):
                    clinic_results = json.loads(clinic_results)
                
                if clinic_results and clinic_results.get('before_after'):
                    for result in clinic_results['before_after']:
                        before_after_photos.append({
                            'procedure_name': result.get('procedure', 'Treatment Results'),
                            'before_image': result.get('before'),
                            'after_image': result.get('after')
                        })
            except Exception as e:
                logger.error(f"Error processing clinic results_gallery: {e}")
                pass
        
        # Get Google reviews for testimonials
        google_reviews_result = db.session.execute(text("""
            SELECT * FROM google_reviews 
            WHERE clinic_id = :clinic_id AND is_active = true
            ORDER BY time DESC
            LIMIT 5
        """), {"clinic_id": clinic_id}).fetchall()
        
        google_reviews = [dict(row._mapping) for row in google_reviews_result]
        
        # Update view count
        db.session.execute(text("""
            UPDATE clinics SET view_count = COALESCE(view_count, 0) + 1 
            WHERE id = :clinic_id
        """), {"clinic_id": clinic_id})
        db.session.commit()
        
        # Check if current user is the clinic owner for admin controls
        is_clinic_owner = (current_user.is_authenticated and 
                          clinic.get('owner_user_id') == current_user.id)
        
        return render_template('clinic/profile.html',
                             clinic=clinic,
                             popular_procedures=popular_procedures,
                             clinic_specialties=clinic_specialties,
                             packages=packages,
                             clinic_doctors=clinic_doctors,
                             before_after_photos=before_after_photos,
                             google_reviews=google_reviews,
                             is_clinic_owner=is_clinic_owner)
                             
    except Exception as e:
        logger.error(f"Error loading clinic profile {slug}: {e}")
        flash('Clinic not found.', 'error')
        return redirect(url_for('clinic.clinic_marketplace'))

@clinic_bp.route('/profile/<slug>/packages')
def clinic_packages(slug):
    """Display all packages for a specific clinic."""
    try:
        # Get clinic by slug or ID
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE (slug = :slug OR id = :clinic_id) AND is_approved = true
            LIMIT 1
        """), {'slug': slug, 'clinic_id': slug if slug.isdigit() else 0}).fetchone()
        
        if not clinic_result:
            flash('Clinic not found.', 'error')
            return redirect(url_for('clinic.clinic_marketplace'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get all packages for this clinic
        packages_result = db.session.execute(text("""
            SELECT * FROM packages 
            WHERE clinic_id = :clinic_id AND is_active = true
            ORDER BY created_at DESC
        """), {'clinic_id': clinic['id']}).fetchall()
        packages = [dict(row._mapping) for row in packages_result]
        
        # Check if current user is the clinic owner
        is_clinic_owner = (current_user.is_authenticated and 
                          clinic.get('owner_user_id') == current_user.id)
        
        return render_template('clinic/packages.html',
                             clinic=clinic,
                             packages=packages,
                             is_clinic_owner=is_clinic_owner)
                             
    except Exception as e:
        logger.error(f"Error loading clinic packages for {slug}: {e}")
        flash('Error loading packages.', 'error')
        return redirect(url_for('clinic.clinic_detail', slug=slug))

# ============================================================================
# LEAD GENERATION & CONTACT SYSTEM
# ============================================================================

@clinic_bp.route('/contact/<int:clinic_id>', methods=['POST'])
def contact_clinic():
    """Submit lead for clinic contact - dynamic pricing based on package value."""
    try:
        clinic_id = request.form.get('clinic_id', type=int)
        package_id = request.form.get('package_id', type=int)
        contact_type = request.form.get('contact_type', 'inquiry')  # inquiry, chat, call
        
        # Validate required fields
        patient_name = request.form.get('patient_name', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        city = request.form.get('city', '').strip()
        procedure_name = request.form.get('procedure_name', '').strip()
        message = request.form.get('message', '').strip()
        
        if not all([patient_name, mobile_number, city, procedure_name]):
            return jsonify({'success': False, 'message': 'Please fill all required fields'})
        
        # Validate mobile number (Indian format)
        if not mobile_number.isdigit() or len(mobile_number) != 10:
            return jsonify({'success': False, 'message': 'Please enter a valid 10-digit mobile number'})
        
        # Get clinic and verify it exists
        clinic_result = db.session.execute(
            text("SELECT * FROM clinics WHERE id = :clinic_id AND is_approved = true"),
            {'clinic_id': clinic_id}
        ).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_dict = dict(clinic_result._mapping)
        
        # Get package details for dynamic pricing
        if not package_id:
            return jsonify({'success': False, 'message': 'Package information required'})
        
        package_result = db.session.execute(
            text("SELECT * FROM packages WHERE id = :package_id"),
            {'package_id': package_id}
        ).fetchone()
        
        if not package_result:
            return jsonify({'success': False, 'message': 'Package not found'})
        
        package_dict = dict(package_result._mapping)
        package_price = package_dict.get('price_actual', 0)
        
        # Calculate dynamic credit cost based on package price
        credit_cost = CreditBillingService.calculate_lead_cost(package_price)
        
        # Check if clinic allows negative balance (as per requirements)
        current_balance = CreditBillingService.get_clinic_credit_balance(clinic_id)
        
        # Create lead record first
        lead_sql = """
            INSERT INTO leads (clinic_id, package_id, source, contact_info, created_at, status)
            VALUES (:clinic_id, :package_id, 'package_marketplace', :contact_info, :created_at, 'pending')
            RETURNING id
        """
        
        contact_info = f"{patient_name}, {mobile_number}, {city}, {procedure_name}"
        if message:
            contact_info += f", Message: {message}"
            
        lead_result = db.session.execute(text(lead_sql), {
            'clinic_id': clinic_id,
            'package_id': package_id,
            'contact_info': contact_info,
            'created_at': datetime.utcnow()
        }).fetchone()
        
        lead_id = lead_result[0] if lead_result else None
        
        if not lead_id:
            return jsonify({'success': False, 'message': 'Failed to create lead record'})
        
        # Process credit deduction using billing service
        billing_result = CreditBillingService.deduct_credits_for_lead(
            clinic_id=clinic_id,
            lead_id=lead_id,
            package_id=package_id,
            action_type=contact_type
        )
        
        if not billing_result['success']:
            # Rollback lead creation if billing fails
            db.session.execute(text("DELETE FROM leads WHERE id = :lead_id"), {'lead_id': lead_id})
            db.session.commit()
            return jsonify({
                'success': False,
                'message': billing_result['message']
            })
        
        # Send notification to clinic about new lead
        try:
            db.session.execute(text("""
                INSERT INTO clinic_notifications (clinic_id, title, message, notification_type, created_at)
                VALUES (:clinic_id, :title, :message, 'new_lead', CURRENT_TIMESTAMP)
            """), {
                'clinic_id': clinic_id,
                'title': 'New Lead Received',
                'message': f'New {contact_type} lead for {procedure_name} - ₹{credit_cost} credits charged'
            })
        except Exception as e:
            logger.warning(f"Failed to create clinic notification: {e}")
        
        # Prepare success response with dynamic pricing info
        success_message = f'Lead submitted successfully. Dynamic pricing: ₹{credit_cost} credits (Package value: ₹{package_price:,})'
        
        # Add low balance warning if applicable
        if billing_result.get('low_balance_alert'):
            success_message += f" Warning: Balance is now ₹{billing_result['new_balance']}. Consider topping up soon."
        
        return jsonify({
            'success': True,
            'message': success_message,
            'lead_id': lead_id,
            'billing_details': {
                'credit_cost': credit_cost,
                'package_price': package_price,
                'previous_balance': billing_result['previous_balance'],
                'new_balance': billing_result['new_balance'],
                'low_balance_alert': billing_result.get('low_balance_alert', False)
            },
            'clinic_contact': {
                'name': clinic_dict.get('name', 'N/A'),
                'phone': clinic_dict.get('contact_number', 'N/A'),
                'address': clinic_dict.get('address', 'N/A')
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting clinic contact: {e}")
        return jsonify({'success': False, 'message': 'Error submitting inquiry. Please try again.'})

# ============================================================================
# CLINIC DASHBOARD MANAGEMENT ROUTES
# ============================================================================

@clinic_bp.route('/leads/<int:lead_id>/status', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    """Update lead status for clinic dashboard."""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'contacted', 'completed', 'cancelled']:
            return jsonify({'success': False, 'message': 'Invalid status'})
        
        # Verify lead belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Update lead status
        db.session.execute(text("""
            UPDATE leads 
            SET status = :status, updated_at = :updated_at 
            WHERE id = :lead_id AND clinic_id = :clinic_id
        """), {
            'status': new_status,
            'updated_at': datetime.utcnow(),
            'lead_id': lead_id,
            'clinic_id': clinic_id
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Lead status updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating lead status: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating lead status'})

@clinic_bp.route('/leads/export')
@login_required
def export_leads():
    """Export clinic leads to CSV."""
    try:
        # Get clinic for current user
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic_id = clinic_result[0]
        
        # Get all leads for the clinic
        leads_result = db.session.execute(text("""
            SELECT l.created_at, l.contact_info, l.source, l.status,
                   p.title as package_title,
                   CASE WHEN l.contact_info LIKE '%whatsapp%' THEN 300 ELSE 500 END as credit_cost
            FROM leads l
            LEFT JOIN packages p ON l.package_id = p.id
            WHERE l.clinic_id = :clinic_id
            ORDER BY l.created_at DESC
        """), {'clinic_id': clinic_id}).fetchall()
        
        # Create CSV response
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Date', 'Contact Info', 'Source', 'Action Type', 'Status', 'Package', 'Credit Cost'])
        
        # Write data
        for lead in leads_result:
            writer.writerow([
                lead.created_at.strftime('%Y-%m-%d %H:%M') if lead.created_at else '',
                lead.contact_info or '',
                lead.source or '',
                'contact',
                lead.status or '',
                lead.package_title or '',
                f"₹{lead.credit_cost}"
            ])
        
        # Create response
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=clinic_leads_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        flash('Error exporting leads', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

# ============================================================================
# CREDIT MANAGEMENT SYSTEM
# ============================================================================

@clinic_bp.route('/credits/topup', methods=['POST'])
@login_required
def topup_credits():
    """Handle credit top-up requests."""
    try:
        data = request.get_json()
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'razorpay')
        
        if not amount or amount <= 0:
            return jsonify({'success': False, 'message': 'Invalid amount'})
        
        # Get clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Create transaction record
        transaction_id = db.session.execute(text("""
            INSERT INTO credit_transactions (clinic_id, amount, transaction_type, status, payment_method, created_at)
            VALUES (:clinic_id, :amount, 'topup', 'pending', :payment_method, CURRENT_TIMESTAMP)
            RETURNING id
        """), {
            'clinic_id': clinic_id,
            'amount': amount,
            'payment_method': payment_method
        }).fetchone()[0]
        
        # Simulate successful payment and update clinic balance
        db.session.execute(text("""
            UPDATE credit_transactions 
            SET status = 'completed', transaction_reference = :ref
            WHERE id = :transaction_id
        """), {
            'transaction_id': transaction_id,
            'ref': f'TXN_{transaction_id}_{int(datetime.now().timestamp())}'
        })
        
        # Update clinic balance
        db.session.execute(text("""
            UPDATE clinics 
            SET credit_balance = COALESCE(credit_balance, 0) + :amount
            WHERE id = :clinic_id
        """), {
            'amount': amount,
            'clinic_id': clinic_id
        })
        
        # Create notification
        db.session.execute(text("""
            INSERT INTO clinic_notifications (clinic_id, title, message, notification_type, created_at)
            VALUES (:clinic_id, :title, :message, 'success', CURRENT_TIMESTAMP)
        """), {
            'clinic_id': clinic_id,
            'title': 'Credit Top-up Successful',
            'message': f'₹{amount:,.0f} has been added to your account. Transaction ID: TXN_{transaction_id}'
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'₹{amount:,.0f} credited successfully to your account',
            'new_balance': amount
        })
        
    except Exception as e:
        logger.error(f"Error processing credit top-up: {e}")
        return jsonify({'success': False, 'message': 'Error processing payment'})

@clinic_bp.route('/credits/history')
@login_required
def credit_history():
    """Display credit transaction history."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic_id = clinic_result[0]
        
        # Get transaction history
        transactions = db.session.execute(text("""
            SELECT * FROM credit_transactions 
            WHERE clinic_id = :clinic_id 
            ORDER BY created_at DESC 
            LIMIT 50
        """), {'clinic_id': clinic_id}).fetchall()
        
        return render_template('clinic/credit_history.html', transactions=transactions)
        
    except Exception as e:
        logger.error(f"Error loading credit history: {e}")
        flash('Error loading credit history', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

# ============================================================================
# NOTIFICATION SYSTEM
# ============================================================================

@clinic_bp.route('/notifications')
@login_required
def notifications():
    """Display clinic notifications."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic_id = clinic_result[0]
        
        # Get notifications
        notifications = db.session.execute(text("""
            SELECT * FROM clinic_notifications 
            WHERE clinic_id = :clinic_id 
            ORDER BY created_at DESC 
            LIMIT 20
        """), {'clinic_id': clinic_id}).fetchall()
        
        # Mark notifications as read
        db.session.execute(text("""
            UPDATE clinic_notifications 
            SET is_read = true 
            WHERE clinic_id = :clinic_id AND is_read = false
        """), {'clinic_id': clinic_id})
        
        db.session.commit()
        
        return render_template('clinic/notifications.html', notifications=notifications)
        
    except Exception as e:
        logger.error(f"Error loading notifications: {e}")
        flash('Error loading notifications', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

@clinic_bp.route('/api/notifications/unread-count')
@login_required
def unread_notifications_count():
    """Get count of unread notifications."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            return jsonify({'count': 0})
        
        clinic_id = clinic_result[0]
        
        # Get unread count
        count = db.session.execute(text("""
            SELECT COUNT(*) FROM clinic_notifications 
            WHERE clinic_id = :clinic_id AND is_read = false
        """), {'clinic_id': clinic_id}).scalar()
        
        return jsonify({'count': count or 0})
        
    except Exception as e:
        logger.error(f"Error getting notification count: {e}")
        return jsonify({'count': 0})

# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================

# Profile update functionality implemented above at line 637

# Lead status update functionality is already implemented above

@clinic_bp.route('/packages/<int:package_id>/toggle', methods=['POST'])
@login_required
def toggle_package_status(package_id):
    """Toggle package active/inactive status."""
    try:
        # Verify package belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Get current package status
        package_result = db.session.execute(text("""
            SELECT is_active FROM packages 
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {'package_id': package_id, 'clinic_id': clinic_id}).fetchone()
        
        if not package_result:
            return jsonify({'success': False, 'message': 'Package not found'})
        
        # Toggle status
        new_status = not package_result[0]
        
        db.session.execute(text("""
            UPDATE packages 
            SET is_active = :is_active, updated_at = CURRENT_TIMESTAMP 
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {
            'is_active': new_status,
            'package_id': package_id,
            'clinic_id': clinic_id
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Package {"activated" if new_status else "deactivated"} successfully',
            'is_active': new_status
        })
        
    except Exception as e:
        logger.error(f"Error toggling package status: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating package status'})

# Disabled - using enhanced edit route instead
# @clinic_bp.route('/packages/<int:package_id>/edit', methods=['GET', 'POST'])
# @login_required
def edit_package_old(package_id):
    """Edit package page and handle updates with form validation."""
    try:
        from forms import PackageEditForm
        from werkzeug.utils import secure_filename
        import os
        
        # Verify package belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Get package details
        package_result = db.session.execute(text("""
            SELECT * FROM packages 
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {'package_id': package_id, 'clinic_id': clinic_id}).fetchone()
        
        if not package_result:
            return jsonify({'success': False, 'message': 'Package not found'})
        
        package = dict(package_result._mapping)
        
        if request.method == 'POST':
            # Handle AJAX form submission
            if request.is_json or request.content_type == 'application/json':
                return jsonify({'success': False, 'message': 'Use form data for file uploads'})
            
            form = PackageEditForm()
            
            if form.validate_on_submit():
                # Handle file uploads
                featured_image_path = package.get('featured_image')
                gallery_images = package.get('gallery_images', [])
                
                # Upload featured image if provided
                if form.featured_image.data:
                    filename = secure_filename(form.featured_image.data.filename)
                    if filename:
                        upload_path = f'/static/uploads/packages/{package_id}'
                        os.makedirs(upload_path, exist_ok=True)
                        file_path = f'{upload_path}/{filename}'
                        form.featured_image.data.save(f'.{file_path}')
                        featured_image_path = file_path
                
                # Handle gallery images
                if form.gallery_images.data:
                    filename = secure_filename(form.gallery_images.data.filename)
                    if filename:
                        upload_path = f'/static/uploads/packages/{package_id}/gallery'
                        os.makedirs(upload_path, exist_ok=True)
                        file_path = f'{upload_path}/{filename}'
                        form.gallery_images.data.save(f'.{file_path}')
                        if isinstance(gallery_images, list):
                            gallery_images.append(file_path)
                        else:
                            gallery_images = [file_path]
                
                # Calculate discount percentage if not provided
                discount_percentage = form.discount_percentage.data
                if form.price_discounted.data and form.price_actual.data:
                    if not discount_percentage:
                        discount_percentage = int(((form.price_actual.data - form.price_discounted.data) / form.price_actual.data) * 100)
                
                # Update package
                db.session.execute(text("""
                    UPDATE packages 
                    SET title = :title,
                        description = :description,
                        category = :category,
                        duration = :duration,
                        price_actual = :price_actual,
                        price_discounted = :price_discounted,
                        discount_percentage = :discount_percentage,
                        procedure_info = :procedure_info,
                        downtime = :downtime,
                        recommended_for = :recommended_for,
                        side_effects = :side_effects,
                        featured_image = :featured_image,
                        gallery_images = :gallery_images,
                        is_active = :is_active,
                        is_featured = :is_featured,
                        updated_at = :updated_at
                    WHERE id = :package_id AND clinic_id = :clinic_id
                """), {
                    'title': form.title.data,
                    'description': form.description.data,
                    'category': form.category.data,
                    'duration': form.duration.data,
                    'price_actual': form.price_actual.data,
                    'price_discounted': form.price_discounted.data,
                    'discount_percentage': discount_percentage,
                    'procedure_info': form.procedure_info.data,
                    'downtime': form.downtime.data,
                    'recommended_for': form.recommended_for.data,
                    'side_effects': form.side_effects.data,
                    'featured_image': featured_image_path,
                    'gallery_images': gallery_images,
                    'is_active': form.is_active.data,
                    'is_featured': form.is_featured.data,
                    'updated_at': datetime.utcnow(),
                    'package_id': package_id,
                    'clinic_id': clinic_id
                })
                
                db.session.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Package updated successfully',
                    'redirect': url_for('clinic.clinic_dashboard')
                })
            else:
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        errors.append(f"{field}: {error}")
                return jsonify({'success': False, 'message': '; '.join(errors)})
        
        # GET request - show edit form
        form = PackageEditForm(data=package)
        return render_template('clinic/package_edit.html', package=package, form=form)
        
    except Exception as e:
        logger.error(f"Error in edit package: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating package'})

@clinic_bp.route('/packages/<int:package_id>/delete', methods=['POST'])
@login_required
def delete_package(package_id):
    """Delete a package."""
    try:
        # Verify package belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Check if package exists and belongs to clinic
        package_result = db.session.execute(text("""
            SELECT id FROM packages 
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {'package_id': package_id, 'clinic_id': clinic_id}).fetchone()
        
        if not package_result:
            return jsonify({'success': False, 'message': 'Package not found'})
        
        # Delete package images first
        db.session.execute(text("""
            DELETE FROM package_images 
            WHERE package_id = :package_id
        """), {'package_id': package_id})
        
        # Delete package
        db.session.execute(text("""
            DELETE FROM packages 
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {'package_id': package_id, 'clinic_id': clinic_id})
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Package deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting package: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error deleting package'})

@clinic_bp.route('/packages/<int:package_id>/analytics')
@login_required
def package_analytics(package_id):
    """Package analytics page."""
    try:
        # Verify package belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic_id = clinic_result[0]
        
        # Get package details with analytics
        package_result = db.session.execute(text("""
            SELECT p.*, 
                   COUNT(l.id) as total_leads,
                   COUNT(CASE WHEN l.created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as monthly_leads,
                   COUNT(CASE WHEN l.contact_info LIKE '%whatsapp%' THEN 1 END) as chat_leads,
                   COUNT(CASE WHEN l.contact_info NOT LIKE '%whatsapp%' THEN 1 END) as call_leads
            FROM packages p
            LEFT JOIN leads l ON p.id = l.package_id
            WHERE p.id = :package_id AND p.clinic_id = :clinic_id
            GROUP BY p.id
        """), {'package_id': package_id, 'clinic_id': clinic_id}).fetchone()
        
        if not package_result:
            flash('Package not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        package = dict(package_result._mapping)
        
        # Get recent leads for this package
        recent_leads_result = db.session.execute(text("""
            SELECT * FROM leads 
            WHERE package_id = :package_id 
            ORDER BY created_at DESC 
            LIMIT 10
        """), {'package_id': package_id}).fetchall()
        
        recent_leads = [dict(row._mapping) for row in recent_leads_result]
        
        return render_template('clinic/package_analytics.html', 
                             package=package, 
                             recent_leads=recent_leads)
        
    except Exception as e:
        logger.error(f"Error loading package analytics: {e}")
        flash('Error loading analytics', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

@clinic_bp.route('/packages/<int:package_id>/analytics/export')
@login_required
def export_package_analytics(package_id):
    """Export package analytics to CSV."""
    try:
        # Verify package belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic not found', 'error')
            return redirect(url_for('clinic.package_analytics', package_id=package_id))
        
        clinic_id = clinic_result[0]
        
        # Get package details
        package_result = db.session.execute(text("""
            SELECT p.*, 
                   COUNT(l.id) as total_leads,
                   COUNT(CASE WHEN l.created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as monthly_leads,
                   COUNT(CASE WHEN l.action_type = 'chat' THEN 1 END) as chat_leads,
                   COUNT(CASE WHEN l.action_type = 'call' THEN 1 END) as call_leads
            FROM packages p
            LEFT JOIN leads l ON p.id = l.package_id
            WHERE p.id = :package_id AND p.clinic_id = :clinic_id
            GROUP BY p.id
        """), {'package_id': package_id, 'clinic_id': clinic_id}).fetchone()
        
        if not package_result:
            flash('Package not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        package = dict(package_result._mapping)
        
        # Get all leads for this package
        leads_result = db.session.execute(text("""
            SELECT l.created_at, l.contact_info, l.action_type, l.status,
                   CASE WHEN l.action_type = 'chat' THEN 300 ELSE 500 END as credit_cost
            FROM leads l
            WHERE l.package_id = :package_id
            ORDER BY l.created_at DESC
        """), {'package_id': package_id}).fetchall()
        
        # Create CSV response
        from io import StringIO
        import csv
        from flask import make_response
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write package summary
        writer.writerow(['Package Analytics Report'])
        writer.writerow(['Package Name', package['title']])
        writer.writerow(['Category', package['category']])
        writer.writerow(['Price', f"₹{package['price_actual']}"])
        writer.writerow(['Total Views', package['view_count'] or 0])
        writer.writerow(['Total Leads', package['total_leads'] or 0])
        writer.writerow(['Monthly Leads', package['monthly_leads'] or 0])
        writer.writerow(['WhatsApp Leads', package['chat_leads'] or 0])
        writer.writerow(['Phone Leads', package['call_leads'] or 0])
        writer.writerow(['Conversion Rate', f"{package['conversion_rate'] or 0:.1f}%"])
        writer.writerow([])  # Empty row
        
        # Write leads header
        writer.writerow(['Date', 'Contact Info', 'Method', 'Status', 'Credit Cost'])
        
        # Write leads data
        for lead in leads_result:
            writer.writerow([
                lead.created_at.strftime('%Y-%m-%d %H:%M') if lead.created_at else '',
                lead.contact_info or '',
                'WhatsApp' if lead.action_type == 'chat' else 'Phone Call',
                lead.status or '',
                f"₹{lead.credit_cost}"
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=package_analytics_{package_id}_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting package analytics: {e}")
        flash('Error exporting analytics', 'error')
        return redirect(url_for('clinic.package_analytics', package_id=package_id))

# Clinic profile update is handled by unified_clinic_dashboard.py to avoid conflicts

@clinic_bp.route('/packages/<int:package_id>/update', methods=['POST'])
@login_required
def update_package(package_id):
    """Update package information."""
    try:
        # Verify package belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        duration = request.form.get('duration')
        price_original = request.form.get('price_original', type=float)
        price_discounted = request.form.get('price_discounted', type=float) or None
        procedure_info = request.form.get('procedure_info')
        downtime = request.form.get('downtime')
        results = request.form.get('results')
        recommended_for = request.form.get('recommended_for')
        side_effects = request.form.get('side_effects')
        is_active = request.form.get('is_active') == 'on'
        
        # Update package
        db.session.execute(text("""
            UPDATE packages 
            SET title = :title,
                description = :description,
                category = :category,
                duration = :duration,
                price_original = :price_original,
                price_discounted = :price_discounted,
                procedure_info = :procedure_info,
                downtime = :downtime,
                results = :results,
                recommended_for = :recommended_for,
                side_effects = :side_effects,
                is_active = :is_active,
                updated_at = :updated_at
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {
            'title': title,
            'description': description,
            'category': category,
            'duration': duration,
            'price_original': price_original,
            'price_discounted': price_discounted,
            'procedure_info': procedure_info,
            'downtime': downtime,
            'results': results,
            'recommended_for': recommended_for,
            'side_effects': side_effects,
            'is_active': is_active,
            'updated_at': datetime.utcnow(),
            'package_id': package_id,
            'clinic_id': clinic_id
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Package updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating package: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating package'})

@clinic_bp.route('/packages/<int:package_id>/duplicate', methods=['POST'])
@login_required
def duplicate_package(package_id):
    """Duplicate an existing package."""
    try:
        # Verify package belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic_result[0]
        
        # Get original package
        package_result = db.session.execute(text("""
            SELECT * FROM packages 
            WHERE id = :package_id AND clinic_id = :clinic_id
        """), {'package_id': package_id, 'clinic_id': clinic_id}).fetchone()
        
        if not package_result:
            return jsonify({'success': False, 'message': 'Package not found'})
        
        package = dict(package_result._mapping)
        
        # Create duplicate
        duplicate_result = db.session.execute(text("""
            INSERT INTO packages (
                clinic_id, title, description, category, duration,
                price_original, price_discounted, procedure_info,
                downtime, results, recommended_for, side_effects,
                is_active, created_at, updated_at
            ) VALUES (
                :clinic_id, :title, :description, :category, :duration,
                :price_original, :price_discounted, :procedure_info,
                :downtime, :results, :recommended_for, :side_effects,
                false, :created_at, :updated_at
            ) RETURNING id
        """), {
            'clinic_id': clinic_id,
            'title': f"{package['title']} (Copy)",
            'description': package['description'],
            'category': package['category'],
            'duration': package['duration'],
            'price_original': package['price_original'],
            'price_discounted': package['price_discounted'],
            'procedure_info': package['procedure_info'],
            'downtime': package['downtime'],
            'results': package['results'],
            'recommended_for': package['recommended_for'],
            'side_effects': package['side_effects'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }).fetchone()
        
        new_package_id = duplicate_result[0]
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Package duplicated successfully',
            'new_package_id': new_package_id
        })
        
    except Exception as e:
        logger.error(f"Error duplicating package: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error duplicating package'})



@clinic_bp.route('/packages/<int:package_id>/export')
@login_required
def export_package_data(package_id):
    """Export package analytics to CSV."""
    try:
        # Verify package belongs to current user's clinic
        clinic_result = db.session.execute(text("SELECT id FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        if not clinic_result:
            flash('Clinic not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic_id = clinic_result[0]
        
        # Get package and its leads
        analytics_result = db.session.execute(text("""
            SELECT p.title, p.category, p.price_original, p.price_discounted,
                   l.created_at as lead_date, l.action_type, l.source_page, l.contact_info,
                   CASE WHEN l.action_type = 'chat' THEN 300 ELSE 500 END as credit_cost
            FROM packages p
            LEFT JOIN leads l ON p.id = l.package_id
            WHERE p.id = :package_id AND p.clinic_id = :clinic_id
            ORDER BY l.created_at DESC
        """), {'package_id': package_id, 'clinic_id': clinic_id}).fetchall()
        
        # Create CSV response
        from io import StringIO
        import csv
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Package', 'Category', 'Original Price', 'Discounted Price', 
                        'Lead Date', 'Action Type', 'Source', 'Contact Info', 'Credit Cost'])
        
        # Write data
        for row in analytics_result:
            writer.writerow([
                row.title,
                row.category,
                f"₹{row.price_original}",
                f"₹{row.price_discounted}" if row.price_discounted else "",
                row.lead_date.strftime('%Y-%m-%d %H:%M') if row.lead_date else '',
                row.action_type or '',
                row.source_page or '',
                row.contact_info or '',
                f"₹{row.credit_cost}" if row.credit_cost else ''
            ])
        
        # Create response
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=package_analytics_{package_id}_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting package analytics: {e}")
        flash('Error exporting analytics', 'error')
        return redirect(url_for('clinic.package_analytics', package_id=package_id))

# ============================================================================
# CLINIC DASHBOARD & MANAGEMENT
# ============================================================================

@clinic_bp.route('/dashboard')
@login_required
def clinic_dashboard():
    """Clinic owner dashboard for managing profile and leads with billing integration."""
    try:
        # Get clinic for current user
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic profile found. Please create your clinic profile first.', 'info')
            return redirect(url_for('clinic.create_clinic'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get clinic packages
        packages_result = db.session.execute(text("SELECT * FROM packages WHERE clinic_id = :clinic_id ORDER BY created_at DESC"), {'clinic_id': clinic['id']}).fetchall()
        clinic['packages'] = [dict(row._mapping) for row in packages_result]
        
        # Get current credit balance from billing system
        try:
            from integrated_billing_system import BillingService
            credit_balance = BillingService.get_clinic_credit_balance(clinic['id'])
        except Exception as e:
            logger.warning(f"Error getting credit balance: {e}")
            credit_balance = 0
        
        # Get dashboard metrics using raw SQL
        total_leads = db.session.execute(text("SELECT COUNT(*) FROM leads WHERE clinic_id = :clinic_id"), {'clinic_id': clinic['id']}).scalar() or 0
        pending_leads = db.session.execute(text("SELECT COUNT(*) FROM leads WHERE clinic_id = :clinic_id AND status = 'pending'"), {'clinic_id': clinic['id']}).scalar() or 0
        this_month_leads = db.session.execute(text("SELECT COUNT(*) FROM leads WHERE clinic_id = :clinic_id AND created_at >= date_trunc('month', CURRENT_DATE)"), {'clinic_id': clinic['id']}).scalar() or 0
        
        # Get recent leads with more details
        recent_leads_result = db.session.execute(text("""
            SELECT l.*, p.title as package_title 
            FROM leads l 
            LEFT JOIN packages p ON l.package_id = p.id 
            WHERE l.clinic_id = :clinic_id 
            ORDER BY l.created_at DESC 
            LIMIT 20
        """), {'clinic_id': clinic['id']}).fetchall()
        recent_leads = [dict(row._mapping) for row in recent_leads_result]
        
        # Get credit transactions
        recent_transactions_result = db.session.execute(text("SELECT * FROM credit_transactions WHERE clinic_id = :clinic_id ORDER BY created_at DESC LIMIT 15"), {'clinic_id': clinic['id']}).fetchall()
        recent_transactions = [dict(row._mapping) for row in recent_transactions_result]
        
        # Get current credit balance using proper calculation
        balance_result = db.session.execute(text("""
            SELECT COALESCE(
                (SELECT SUM(amount) FROM credit_transactions 
                 WHERE clinic_id = :clinic_id AND transaction_type = 'credit') -
                (SELECT ABS(SUM(amount)) FROM credit_transactions 
                 WHERE clinic_id = :clinic_id AND transaction_type = 'deduction'),
                0
            ) as balance
        """), {'clinic_id': clinic['id']}).fetchone()
        clinic['credit_balance'] = balance_result[0] if balance_result else 0
        
        # Get credit spending this month
        monthly_spending = db.session.execute(text("""
            SELECT COALESCE(ABS(SUM(amount)), 0) 
            FROM credit_transactions 
            WHERE clinic_id = :clinic_id 
            AND transaction_type = 'deduction'
            AND created_at >= date_trunc('month', CURRENT_DATE)
        """), {'clinic_id': clinic['id']}).scalar() or 0
        
        return render_template('clinic/dashboard.html',
                             clinic=clinic,
                             total_leads=total_leads,
                             pending_leads=pending_leads,
                             this_month_leads=this_month_leads,
                             monthly_spending=monthly_spending,
                             recent_leads=recent_leads,
                             recent_transactions=recent_transactions)
                             
    except Exception as e:
        logger.error(f"Error loading clinic dashboard: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('web.index'))

@clinic_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_clinic():
    """Create new clinic profile."""
    try:
        # Check if user already has a clinic
        existing_clinic = Clinic.query.filter_by(user_id=current_user.id).first()
        if existing_clinic:
            flash('You already have a clinic profile.', 'info')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name', '').strip()
            address = request.form.get('address', '').strip()
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()
            pincode = request.form.get('pincode', '').strip()
            contact_number = request.form.get('contact_number', '').strip()
            email = request.form.get('email', '').strip()
            description = request.form.get('description', '').strip()
            
            # Validate required fields
            if not all([name, address, city, state, contact_number]):
                flash('Please fill all required fields.', 'error')
                return render_template('clinic/create.html')
            
            # Generate unique slug
            base_slug = name.lower().replace(' ', '-').replace('&', 'and')
            slug = base_slug
            counter = 1
            while Clinic.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Create clinic using raw SQL to avoid model issues
            clinic_sql = """
                INSERT INTO clinics (name, slug, address, city, state, pincode, contact_number, email, description, credit_balance, is_verified, created_at)
                VALUES (:name, :slug, :address, :city, :state, :pincode, :contact_number, :email, :description, 0, false, :created_at)
                RETURNING id
            """
            
            clinic_result = db.session.execute(text(clinic_sql), {
                'name': name,
                'slug': slug,
                'address': address,
                'city': city,
                'state': state,
                'pincode': pincode,
                'contact_number': contact_number,
                'email': email or current_user.email,
                'description': description,
                'created_at': datetime.utcnow()
            }).fetchone()
            
            db.session.commit()
            
            flash('Clinic profile created successfully! It will be reviewed and approved within 24 hours.', 'success')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        return render_template('clinic/create.html')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating clinic: {e}")
        flash('Error creating clinic profile. Please try again.', 'error')
        return render_template('clinic/create.html')

@clinic_bp.route('/package/add', methods=['GET', 'POST'])
@login_required
def add_package():
    """Redirect to enhanced package creation form."""
    return redirect(url_for('enhanced_package.add_package_enhanced'))

@clinic_bp.route('/package/add-legacy', methods=['GET', 'POST'])
@login_required
def add_package_legacy():
    """Add a new package to the clinic (legacy version)."""
    try:
        # Get clinic for current user
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic profile found.', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic = dict(clinic_result._mapping)
        
        if request.method == 'POST':
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description')
            procedure_info = request.form.get('procedure_info')
            price_actual = request.form.get('price_actual')
            price_discounted = request.form.get('price_discounted')
            discount_percentage = request.form.get('discount_percentage')
            category = request.form.get('category')
            downtime = request.form.get('downtime')
            duration = request.form.get('duration')
            anesthetic = request.form.get('anesthetic')
            results = request.form.get('results')
            recommended_for = request.form.get('recommended_for')
            side_effects = request.form.get('side_effects')
            is_active = request.form.get('is_active') == 'on'
            
            # Validate required fields
            if not all([title, description, price_actual]):
                flash('Please fill in all required fields.', 'error')
                return render_template('clinic/add_package.html', clinic=clinic)
            
            # Generate slug
            import re
            base_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower() if title else '')
            base_slug = re.sub(r'\s+', '-', base_slug.strip())
            
            slug = base_slug
            counter = 1
            while db.session.execute(text("SELECT id FROM packages WHERE slug = :slug"), {'slug': slug}).fetchone():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Insert package
            package_sql = """
                INSERT INTO packages (clinic_id, title, slug, description, procedure_info, price_actual, 
                                    price_discounted, discount_percentage, category, downtime, duration, 
                                    anesthetic, results, recommended_for, side_effects, is_active, created_at)
                VALUES (:clinic_id, :title, :slug, :description, :procedure_info, :price_actual, 
                        :price_discounted, :discount_percentage, :category, :downtime, :duration, 
                        :anesthetic, :results, :recommended_for, :side_effects, :is_active, :created_at)
            """
            
            db.session.execute(text(package_sql), {
                'clinic_id': clinic['id'],
                'title': title,
                'slug': slug,
                'description': description,
                'procedure_info': procedure_info,
                'price_actual': float(price_actual) if price_actual and price_actual.strip() else 0,
                'price_discounted': float(price_discounted) if price_discounted and price_discounted.strip() else None,
                'discount_percentage': int(discount_percentage) if discount_percentage and discount_percentage.strip() else None,
                'category': category,
                'downtime': downtime,
                'duration': duration,
                'anesthetic': anesthetic,
                'results': results,
                'recommended_for': recommended_for,
                'side_effects': side_effects,
                'is_active': is_active,
                'created_at': datetime.utcnow()
            })
            
            db.session.commit()
            flash('Package created successfully!', 'success')
            return redirect(url_for('clinic.clinic_dashboard') + '#packages')
        
        return render_template('clinic/add_package.html', clinic=clinic)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding package: {e}")
        flash('Error creating package. Please try again.', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

@clinic_bp.route('/package/<int:package_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_clinic_package(package_id):
    """Edit an existing package."""
    try:
        # Get clinic and package
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic profile found.', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get package
        package_result = db.session.execute(text("SELECT * FROM packages WHERE id = :id AND clinic_id = :clinic_id"), 
                                          {'id': package_id, 'clinic_id': clinic['id']}).fetchone()
        
        if not package_result:
            flash('Package not found.', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        package = dict(package_result._mapping)
        
        if request.method == 'POST':
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description')
            procedure_info = request.form.get('procedure_info')
            price_actual = request.form.get('price_actual')
            price_discounted = request.form.get('price_discounted')
            discount_percentage = request.form.get('discount_percentage')
            category = request.form.get('category')
            downtime = request.form.get('downtime')
            duration = request.form.get('duration')
            anesthetic = request.form.get('anesthetic')
            
            # Update package
            update_sql = """
                UPDATE packages SET 
                    title = :title,
                    description = :description,
                    procedure_info = :procedure_info,
                    price_actual = :price_actual,
                    price_discounted = :price_discounted,
                    discount_percentage = :discount_percentage,
                    category = :category,
                    downtime = :downtime,
                    duration = :duration,
                    anesthetic = :anesthetic,
                    updated_at = :updated_at
                WHERE id = :id
            """
            
            db.session.execute(text(update_sql), {
                'id': package_id,
                'title': title,
                'description': description,
                'procedure_info': procedure_info,
                'price_actual': float(price_actual),
                'price_discounted': float(price_discounted) if price_discounted else None,
                'discount_percentage': int(discount_percentage) if discount_percentage else None,
                'category': category,
                'downtime': downtime,
                'duration': duration,
                'anesthetic': anesthetic,
                'updated_at': datetime.utcnow()
            })
            
            db.session.commit()
            flash('Package updated successfully!', 'success')
            return redirect(url_for('clinic.clinic_dashboard') + '#packages')
        
        return render_template('clinic/edit_package.html', clinic=clinic, package=package)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing package: {e}")
        flash('Error updating package. Please try again.', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

@clinic_bp.route('/package/<int:package_id>/toggle', methods=['POST'])
@login_required
def toggle_clinic_package_status(package_id):
    """Toggle package active/inactive status."""
    try:
        # Verify ownership
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic = dict(clinic_result._mapping)
        
        # Get current status
        package_result = db.session.execute(text("SELECT is_active FROM packages WHERE id = :id AND clinic_id = :clinic_id"), 
                                          {'id': package_id, 'clinic_id': clinic['id']}).fetchone()
        
        if not package_result:
            return jsonify({'success': False, 'message': 'Package not found'})
        
        current_status = package_result[0]
        new_status = not current_status
        
        # Update status
        db.session.execute(text("UPDATE packages SET is_active = :status WHERE id = :id"), 
                         {'status': new_status, 'id': package_id})
        db.session.commit()
        
        status_text = 'activated' if new_status else 'deactivated'
        return jsonify({'success': True, 'message': f'Package {status_text} successfully', 'new_status': new_status})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling package status: {e}")
        return jsonify({'success': False, 'message': 'Error updating package status'})

@clinic_bp.route('/package/<int:package_id>/delete', methods=['POST'])
@login_required
def delete_clinic_package(package_id):
    """Delete a package."""
    try:
        # Verify ownership
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic = dict(clinic_result._mapping)
        
        # Check if package exists and belongs to clinic
        package_result = db.session.execute(text("SELECT id FROM packages WHERE id = :id AND clinic_id = :clinic_id"), 
                                          {'id': package_id, 'clinic_id': clinic['id']}).fetchone()
        
        if not package_result:
            return jsonify({'success': False, 'message': 'Package not found'})
        
        # Delete package
        db.session.execute(text("DELETE FROM packages WHERE id = :id"), {'id': package_id})
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Package deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting package: {e}")
        return jsonify({'success': False, 'message': 'Error deleting package'})

@clinic_bp.route('/profile/update', methods=['POST'])
@login_required
def update_clinic_profile():
    """Update clinic profile information."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("SELECT * FROM clinics WHERE owner_user_id = :user_id"), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic = dict(clinic_result._mapping)
        
        # Get form data
        name = request.form.get('name', '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        city = request.form.get('city', '').strip()
        address = request.form.get('address', '').strip()
        description = request.form.get('description', '').strip()
        website = request.form.get('website', '').strip()
        specialties_str = request.form.get('specialties', '').strip()
        services_str = request.form.get('services_offered', '').strip()
        
        # Validate required fields
        if not all([name, contact_number, city, address]):
            return jsonify({'success': False, 'message': 'Please fill all required fields'})
        
        # Process array fields
        specialties = [s.strip() for s in specialties_str.split(',') if s.strip()] if specialties_str else []
        services_offered = [s.strip() for s in services_str.split(',') if s.strip()] if services_str else []
        
        # Update clinic profile
        update_sql = """
            UPDATE clinics SET 
                name = :name,
                contact_number = :contact_number,
                city = :city,
                address = :address,
                description = :description,
                website = :website,
                specialties = :specialties,
                services_offered = :services_offered,
                updated_at = :updated_at
            WHERE id = :id
        """
        
        db.session.execute(text(update_sql), {
            'id': clinic['id'],
            'name': name,
            'contact_number': contact_number,
            'city': city,
            'address': address,
            'description': description,
            'website': website,
            'specialties': specialties,
            'services_offered': services_offered,
            'updated_at': datetime.utcnow()
        })
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating clinic profile: {e}")
        return jsonify({'success': False, 'message': 'Error updating profile'})

# Register the blueprint
def register_clinic_routes(app):
    """Register clinic marketplace routes with the Flask app."""
    app.register_blueprint(clinic_bp)
    logger.info("Clinic marketplace routes registered successfully")