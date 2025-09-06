"""
Enhanced directory filtering system for clinics, doctors, and procedures with advanced search capabilities.
"""
from flask import Blueprint, render_template, request, jsonify
from models import db, Clinic, Doctor, Procedure, Package, Category
from sqlalchemy import text, or_, and_, func
import json

directory_bp = Blueprint('directory', __name__)

@directory_bp.route('/clinics')
def clinic_directory():
    """Enhanced clinic directory with advanced filtering."""
    # Get filter parameters
    city = request.args.get('city', '')
    specialty = request.args.get('specialty', '')
    rating = request.args.get('rating', '')
    price_range = request.args.get('price_range', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'rating')
    page = request.args.get('page', 1, type=int)
    
    # Build base query
    query = """
        SELECT DISTINCT c.*, 
               COUNT(DISTINCT p.id) as package_count,
               COUNT(DISTINCT d.id) as doctor_count,
               AVG(pkg.price_discounted) as avg_price
        FROM clinics c
        LEFT JOIN packages p ON c.id = p.clinic_id AND p.is_active = true
        LEFT JOIN doctors d ON c.id = d.clinic_id
        LEFT JOIN packages pkg ON c.id = pkg.clinic_id AND pkg.is_active = true
        WHERE c.is_approved = true
    """
    
    params = {}
    
    # Apply filters
    if city:
        query += " AND LOWER(c.city) LIKE LOWER(:city)"
        params['city'] = f"%{city}%"
    
    if specialty:
        query += " AND EXISTS (SELECT 1 FROM unnest(c.specialties) as spec WHERE LOWER(spec) LIKE LOWER(:specialty))"
        params['specialty'] = f"%{specialty}%"
    
    if rating:
        min_rating = float(rating)
        query += " AND c.rating >= :min_rating"
        params['min_rating'] = min_rating
    
    if search:
        query += """ AND (
            LOWER(c.name) LIKE LOWER(:search) OR 
            LOWER(c.description) LIKE LOWER(:search) OR
            EXISTS (SELECT 1 FROM unnest(c.specialties) as spec WHERE LOWER(spec) LIKE LOWER(:search))
        )"""
        params['search'] = f"%{search}%"
    
    query += " GROUP BY c.id"
    
    # Apply sorting
    if sort_by == 'rating':
        query += " ORDER BY c.rating DESC NULLS LAST"
    elif sort_by == 'reviews':
        query += " ORDER BY c.review_count DESC NULLS LAST"
    elif sort_by == 'name':
        query += " ORDER BY c.name ASC"
    elif sort_by == 'newest':
        query += " ORDER BY c.created_at DESC"
    elif sort_by == 'price_low':
        query += " ORDER BY avg_price ASC NULLS LAST"
    elif sort_by == 'price_high':
        query += " ORDER BY avg_price DESC NULLS LAST"
    
    # Add pagination
    limit = 12
    offset = (page - 1) * limit
    query += f" LIMIT {limit} OFFSET {offset}"
    
    clinics = db.session.execute(text(query), params).fetchall()
    
    # Get total count for pagination
    count_query = query.split('LIMIT')[0].replace('SELECT DISTINCT c.*, COUNT(DISTINCT p.id) as package_count, COUNT(DISTINCT d.id) as doctor_count, AVG(pkg.price_discounted) as avg_price', 'SELECT COUNT(DISTINCT c.id)')
    total_clinics = db.session.execute(text(count_query), params).scalar()
    
    # Get filter options
    filter_options = get_clinic_filter_options()
    
    # Pagination info
    total_pages = (total_clinics + limit - 1) // limit
    
    return render_template('directory/clinics.html',
                         clinics=clinics,
                         filter_options=filter_options,
                         current_filters={
                             'city': city,
                             'specialty': specialty,
                             'rating': rating,
                             'price_range': price_range,
                             'search': search,
                             'sort_by': sort_by
                         },
                         pagination={
                             'page': page,
                             'total_pages': total_pages,
                             'total_results': total_clinics
                         })

@directory_bp.route('/doctors')
def doctor_directory():
    """Enhanced doctor directory with advanced filtering."""
    # Get filter parameters
    city = request.args.get('city', '')
    specialty = request.args.get('specialty', '')
    experience = request.args.get('experience', '')
    consultation_fee = request.args.get('consultation_fee', '')
    rating = request.args.get('rating', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'rating')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = """
        SELECT d.*, c.name as clinic_name, c.city as clinic_city
        FROM doctors d
        LEFT JOIN clinics c ON d.clinic_id = c.id
        WHERE d.verification_status = 'approved'
    """
    
    params = {}
    
    # Apply filters
    if city:
        query += " AND LOWER(d.city) LIKE LOWER(:city)"
        params['city'] = f"%{city}%"
    
    if specialty:
        query += " AND LOWER(d.specialty) LIKE LOWER(:specialty)"
        params['specialty'] = f"%{specialty}%"
    
    if experience:
        min_exp = int(experience)
        query += " AND d.experience >= :min_exp"
        params['min_exp'] = min_exp
    
    if consultation_fee:
        if consultation_fee == 'free':
            query += " AND (d.consultation_fee = 0 OR d.consultation_fee IS NULL)"
        elif consultation_fee == 'under_1000':
            query += " AND d.consultation_fee < 1000"
        elif consultation_fee == '1000_2000':
            query += " AND d.consultation_fee BETWEEN 1000 AND 2000"
        elif consultation_fee == 'over_2000':
            query += " AND d.consultation_fee > 2000"
    
    if rating:
        min_rating = float(rating)
        query += " AND d.rating >= :min_rating"
        params['min_rating'] = min_rating
    
    if search:
        query += """ AND (
            LOWER(d.name) LIKE LOWER(:search) OR 
            LOWER(d.specialty) LIKE LOWER(:search) OR
            LOWER(d.bio) LIKE LOWER(:search)
        )"""
        params['search'] = f"%{search}%"
    
    # Apply sorting
    if sort_by == 'rating':
        query += " ORDER BY d.rating DESC NULLS LAST"
    elif sort_by == 'experience':
        query += " ORDER BY d.experience DESC"
    elif sort_by == 'reviews':
        query += " ORDER BY d.review_count DESC NULLS LAST"
    elif sort_by == 'fee_low':
        query += " ORDER BY d.consultation_fee ASC NULLS LAST"
    elif sort_by == 'fee_high':
        query += " ORDER BY d.consultation_fee DESC NULLS LAST"
    elif sort_by == 'name':
        query += " ORDER BY d.name ASC"
    
    # Add pagination
    limit = 12
    offset = (page - 1) * limit
    query += f" LIMIT {limit} OFFSET {offset}"
    
    doctors = db.session.execute(text(query), params).fetchall()
    
    # Get total count
    count_query = query.split('LIMIT')[0].replace('SELECT d.*, c.name as clinic_name, c.city as clinic_city', 'SELECT COUNT(d.id)')
    total_doctors = db.session.execute(text(count_query), params).scalar()
    
    # Get filter options
    filter_options = get_doctor_filter_options()
    
    # Pagination info
    total_pages = (total_doctors + limit - 1) // limit
    
    return render_template('directory/doctors.html',
                         doctors=doctors,
                         filter_options=filter_options,
                         current_filters={
                             'city': city,
                             'specialty': specialty,
                             'experience': experience,
                             'consultation_fee': consultation_fee,
                             'rating': rating,
                             'search': search,
                             'sort_by': sort_by
                         },
                         pagination={
                             'page': page,
                             'total_pages': total_pages,
                             'total_results': total_doctors
                         })

@directory_bp.route('/procedures')
def procedure_directory():
    """Enhanced procedure directory with advanced filtering."""
    # Get filter parameters
    body_part = request.args.get('body_part', '')
    category = request.args.get('category', '')
    price_range = request.args.get('price_range', '')
    duration = request.args.get('duration', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'popularity')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = """
        SELECT p.*, c.name as category_name, 
               COUNT(DISTINCT pkg.id) as package_count,
               COUNT(DISTINCT dp.doctor_id) as doctor_count
        FROM procedures p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN packages pkg ON pkg.category = c.name
        LEFT JOIN doctor_procedures dp ON p.id = dp.procedure_id
        WHERE 1=1
    """
    
    params = {}
    
    # Apply filters
    if body_part:
        query += " AND LOWER(p.body_part) LIKE LOWER(:body_part)"
        params['body_part'] = f"%{body_part}%"
    
    if category:
        query += " AND p.category_id = :category_id"
        params['category_id'] = int(category)
    
    if price_range:
        if price_range == 'under_50k':
            query += " AND p.max_cost < 50000"
        elif price_range == '50k_100k':
            query += " AND p.min_cost >= 50000 AND p.max_cost <= 100000"
        elif price_range == '100k_200k':
            query += " AND p.min_cost >= 100000 AND p.max_cost <= 200000"
        elif price_range == 'over_200k':
            query += " AND p.min_cost > 200000"
    
    if duration:
        if duration == 'under_1h':
            query += " AND p.procedure_duration LIKE '%min%' AND CAST(regexp_replace(p.procedure_duration, '[^0-9]', '', 'g') AS INTEGER) < 60"
        elif duration == '1h_3h':
            query += " AND ((p.procedure_duration LIKE '%hour%' AND CAST(regexp_replace(p.procedure_duration, '[^0-9]', '', 'g') AS INTEGER) BETWEEN 1 AND 3) OR (p.procedure_duration LIKE '%min%' AND CAST(regexp_replace(p.procedure_duration, '[^0-9]', '', 'g') AS INTEGER) BETWEEN 60 AND 180))"
        elif duration == 'over_3h':
            query += " AND ((p.procedure_duration LIKE '%hour%' AND CAST(regexp_replace(p.procedure_duration, '[^0-9]', '', 'g') AS INTEGER) > 3) OR p.procedure_duration LIKE '%day%')"
    
    if search:
        query += """ AND (
            LOWER(p.procedure_name) LIKE LOWER(:search) OR 
            LOWER(p.short_description) LIKE LOWER(:search) OR
            LOWER(p.body_part) LIKE LOWER(:search) OR
            LOWER(c.name) LIKE LOWER(:search)
        )"""
        params['search'] = f"%{search}%"
    
    query += " GROUP BY p.id, c.name"
    
    # Apply sorting
    if sort_by == 'popularity':
        query += " ORDER BY p.popularity_score DESC NULLS LAST"
    elif sort_by == 'price_low':
        query += " ORDER BY p.min_cost ASC"
    elif sort_by == 'price_high':
        query += " ORDER BY p.max_cost DESC"
    elif sort_by == 'rating':
        query += " ORDER BY p.avg_rating DESC NULLS LAST"
    elif sort_by == 'name':
        query += " ORDER BY p.procedure_name ASC"
    elif sort_by == 'newest':
        query += " ORDER BY p.created_at DESC"
    
    # Add pagination
    limit = 16
    offset = (page - 1) * limit
    query += f" LIMIT {limit} OFFSET {offset}"
    
    procedures = db.session.execute(text(query), params).fetchall()
    
    # Get total count
    count_query = query.split('LIMIT')[0].replace('SELECT p.*, c.name as category_name, COUNT(DISTINCT pkg.id) as package_count, COUNT(DISTINCT dp.doctor_id) as doctor_count', 'SELECT COUNT(DISTINCT p.id)')
    total_procedures = db.session.execute(text(count_query), params).scalar()
    
    # Get filter options
    filter_options = get_procedure_filter_options()
    
    # Pagination info
    total_pages = (total_procedures + limit - 1) // limit
    
    return render_template('directory/procedures.html',
                         procedures=procedures,
                         filter_options=filter_options,
                         current_filters={
                             'body_part': body_part,
                             'category': category,
                             'price_range': price_range,
                             'duration': duration,
                             'search': search,
                             'sort_by': sort_by
                         },
                         pagination={
                             'page': page,
                             'total_pages': total_pages,
                             'total_results': total_procedures
                         })

@directory_bp.route('/api/search-suggestions')
def search_suggestions():
    """Provide real-time search suggestions."""
    query = request.args.get('q', '').lower()
    if len(query) < 2:
        return jsonify([])
    
    suggestions = []
    
    # Clinic suggestions
    clinic_suggestions = db.session.execute(text("""
        SELECT DISTINCT name as suggestion, 'clinic' as type
        FROM clinics 
        WHERE LOWER(name) LIKE :query AND is_approved = true
        LIMIT 3
    """), {"query": f"%{query}%"}).fetchall()
    
    # Doctor suggestions  
    doctor_suggestions = db.session.execute(text("""
        SELECT DISTINCT name as suggestion, 'doctor' as type
        FROM doctors 
        WHERE LOWER(name) LIKE :query AND verification_status = 'approved'
        LIMIT 3
    """), {"query": f"%{query}%"}).fetchall()
    
    # Procedure suggestions
    procedure_suggestions = db.session.execute(text("""
        SELECT DISTINCT procedure_name as suggestion, 'procedure' as type
        FROM procedures 
        WHERE LOWER(procedure_name) LIKE :query
        LIMIT 4
    """), {"query": f"%{query}%"}).fetchall()
    
    # Combine suggestions
    for row in clinic_suggestions:
        suggestions.append({'text': row.suggestion, 'type': row.type})
    
    for row in doctor_suggestions:
        suggestions.append({'text': row.suggestion, 'type': row.type})
    
    for row in procedure_suggestions:
        suggestions.append({'text': row.suggestion, 'type': row.type})
    
    return jsonify(suggestions[:10])

def get_clinic_filter_options():
    """Get available filter options for clinics."""
    # Get cities
    cities = db.session.execute(text("""
        SELECT DISTINCT city, COUNT(*) as count
        FROM clinics 
        WHERE is_approved = true AND city IS NOT NULL
        GROUP BY city 
        ORDER BY count DESC, city ASC
    """)).fetchall()
    
    # Get specialties
    specialties = db.session.execute(text("""
        SELECT DISTINCT unnest(specialties) as specialty, COUNT(*) as count
        FROM clinics 
        WHERE is_approved = true AND specialties IS NOT NULL
        GROUP BY specialty 
        ORDER BY count DESC, specialty ASC
    """)).fetchall()
    
    return {
        'cities': [{'name': row.city, 'count': row.count} for row in cities],
        'specialties': [{'name': row.specialty, 'count': row.count} for row in specialties],
        'rating_options': [
            {'value': '4.5', 'label': '4.5+ Stars'},
            {'value': '4.0', 'label': '4.0+ Stars'},
            {'value': '3.5', 'label': '3.5+ Stars'},
            {'value': '3.0', 'label': '3.0+ Stars'}
        ]
    }

def get_doctor_filter_options():
    """Get available filter options for doctors."""
    # Get cities
    cities = db.session.execute(text("""
        SELECT DISTINCT city, COUNT(*) as count
        FROM doctors 
        WHERE verification_status = 'approved' AND city IS NOT NULL
        GROUP BY city 
        ORDER BY count DESC, city ASC
    """)).fetchall()
    
    # Get specialties
    specialties = db.session.execute(text("""
        SELECT DISTINCT specialty, COUNT(*) as count
        FROM doctors 
        WHERE verification_status = 'approved' AND specialty IS NOT NULL
        GROUP BY specialty 
        ORDER BY count DESC, specialty ASC
    """)).fetchall()
    
    return {
        'cities': [{'name': row.city, 'count': row.count} for row in cities],
        'specialties': [{'name': row.specialty, 'count': row.count} for row in specialties],
        'experience_options': [
            {'value': '1', 'label': '1+ Years'},
            {'value': '5', 'label': '5+ Years'},
            {'value': '10', 'label': '10+ Years'},
            {'value': '15', 'label': '15+ Years'}
        ],
        'fee_options': [
            {'value': 'free', 'label': 'Free Consultation'},
            {'value': 'under_1000', 'label': 'Under ₹1,000'},
            {'value': '1000_2000', 'label': '₹1,000 - ₹2,000'},
            {'value': 'over_2000', 'label': 'Over ₹2,000'}
        ]
    }

def get_procedure_filter_options():
    """Get available filter options for procedures."""
    # Get body parts
    body_parts = db.session.execute(text("""
        SELECT DISTINCT body_part, COUNT(*) as count
        FROM procedures 
        WHERE body_part IS NOT NULL
        GROUP BY body_part 
        ORDER BY count DESC, body_part ASC
    """)).fetchall()
    
    # Get categories
    categories = db.session.execute(text("""
        SELECT c.id, c.name, COUNT(p.id) as count
        FROM categories c
        LEFT JOIN procedures p ON c.id = p.category_id
        GROUP BY c.id, c.name 
        HAVING COUNT(p.id) > 0
        ORDER BY count DESC, c.name ASC
    """)).fetchall()
    
    return {
        'body_parts': [{'name': row.body_part, 'count': row.count} for row in body_parts],
        'categories': [{'id': row.id, 'name': row.name, 'count': row.count} for row in categories],
        'price_ranges': [
            {'value': 'under_50k', 'label': 'Under ₹50,000'},
            {'value': '50k_100k', 'label': '₹50,000 - ₹1,00,000'},
            {'value': '100k_200k', 'label': '₹1,00,000 - ₹2,00,000'},
            {'value': 'over_200k', 'label': 'Over ₹2,00,000'}
        ],
        'duration_options': [
            {'value': 'under_1h', 'label': 'Under 1 Hour'},
            {'value': '1h_3h', 'label': '1-3 Hours'},
            {'value': 'over_3h', 'label': 'Over 3 Hours'}
        ]
    }