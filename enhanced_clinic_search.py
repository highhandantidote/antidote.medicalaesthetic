"""
Enhanced Search & Filter System for Clinic Marketplace
Advanced location-based search with price filtering and amenity filters
"""

from flask import Blueprint, render_template, request, jsonify
from app import db
from models import Clinic, ClinicSpecialty, Category, ClinicAmenity
from sqlalchemy import func, and_, or_
import logging

logger = logging.getLogger(__name__)

enhanced_search_bp = Blueprint('enhanced_search', __name__, url_prefix='/search')

# Real Indian city data with coordinates
INDIAN_CITIES = {
    'Mumbai': {'lat': 19.0760, 'lng': 72.8777, 'state': 'Maharashtra'},
    'Delhi': {'lat': 28.7041, 'lng': 77.1025, 'state': 'Delhi'},
    'Bangalore': {'lat': 12.9716, 'lng': 77.5946, 'state': 'Karnataka'},
    'Hyderabad': {'lat': 17.3850, 'lng': 78.4867, 'state': 'Telangana'},
    'Chennai': {'lat': 13.0827, 'lng': 80.2707, 'state': 'Tamil Nadu'},
    'Kolkata': {'lat': 22.5726, 'lng': 88.3639, 'state': 'West Bengal'},
    'Pune': {'lat': 18.5204, 'lng': 73.8567, 'state': 'Maharashtra'},
    'Ahmedabad': {'lat': 23.0225, 'lng': 72.5714, 'state': 'Gujarat'},
    'Jaipur': {'lat': 26.9124, 'lng': 75.7873, 'state': 'Rajasthan'},
    'Lucknow': {'lat': 26.8467, 'lng': 80.9462, 'state': 'Uttar Pradesh'},
    'Kanpur': {'lat': 26.4499, 'lng': 80.3319, 'state': 'Uttar Pradesh'},
    'Nagpur': {'lat': 21.1458, 'lng': 79.0882, 'state': 'Maharashtra'},
    'Indore': {'lat': 22.7196, 'lng': 75.8577, 'state': 'Madhya Pradesh'},
    'Thane': {'lat': 19.2183, 'lng': 72.9781, 'state': 'Maharashtra'},
    'Bhopal': {'lat': 23.2599, 'lng': 77.4126, 'state': 'Madhya Pradesh'},
    'Visakhapatnam': {'lat': 17.6868, 'lng': 83.2185, 'state': 'Andhra Pradesh'},
    'Pimpri-Chinchwad': {'lat': 18.6298, 'lng': 73.7997, 'state': 'Maharashtra'},
    'Patna': {'lat': 25.5941, 'lng': 85.1376, 'state': 'Bihar'},
    'Vadodara': {'lat': 22.3072, 'lng': 73.1812, 'state': 'Gujarat'},
    'Agra': {'lat': 27.1767, 'lng': 78.0081, 'state': 'Uttar Pradesh'},
    'Ludhiana': {'lat': 30.9010, 'lng': 75.8573, 'state': 'Punjab'},
    'Nashik': {'lat': 19.9975, 'lng': 73.7898, 'state': 'Maharashtra'},
    'Faridabad': {'lat': 28.4089, 'lng': 77.3178, 'state': 'Haryana'},
    'Meerut': {'lat': 28.9845, 'lng': 77.7064, 'state': 'Uttar Pradesh'},
    'Rajkot': {'lat': 22.3039, 'lng': 70.8022, 'state': 'Gujarat'},
    'Kalyan-Dombivli': {'lat': 19.2403, 'lng': 73.1305, 'state': 'Maharashtra'},
    'Vasai-Virar': {'lat': 19.4912, 'lng': 72.8054, 'state': 'Maharashtra'},
    'Varanasi': {'lat': 25.3176, 'lng': 82.9739, 'state': 'Uttar Pradesh'},
    'Srinagar': {'lat': 34.0837, 'lng': 74.7973, 'state': 'Jammu and Kashmir'},
    'Aurangabad': {'lat': 19.8762, 'lng': 75.3433, 'state': 'Maharashtra'},
    'Dhanbad': {'lat': 23.7957, 'lng': 86.4304, 'state': 'Jharkhand'},
    'Amritsar': {'lat': 31.6340, 'lng': 74.8723, 'state': 'Punjab'},
    'Navi Mumbai': {'lat': 19.0330, 'lng': 73.0297, 'state': 'Maharashtra'},
    'Allahabad': {'lat': 25.4358, 'lng': 81.8463, 'state': 'Uttar Pradesh'},
    'Ranchi': {'lat': 23.3441, 'lng': 85.3096, 'state': 'Jharkhand'},
    'Howrah': {'lat': 22.5958, 'lng': 88.2636, 'state': 'West Bengal'},
    'Coimbatore': {'lat': 11.0168, 'lng': 76.9558, 'state': 'Tamil Nadu'},
    'Jabalpur': {'lat': 23.1815, 'lng': 79.9864, 'state': 'Madhya Pradesh'},
    'Gwalior': {'lat': 26.2183, 'lng': 78.1828, 'state': 'Madhya Pradesh'},
    'Vijayawada': {'lat': 16.5062, 'lng': 80.6480, 'state': 'Andhra Pradesh'},
    'Jodhpur': {'lat': 26.2389, 'lng': 73.0243, 'state': 'Rajasthan'},
    'Madurai': {'lat': 9.9252, 'lng': 78.1198, 'state': 'Tamil Nadu'},
    'Raipur': {'lat': 21.2514, 'lng': 81.6296, 'state': 'Chhattisgarh'},
    'Kota': {'lat': 25.2138, 'lng': 75.8648, 'state': 'Rajasthan'},
    'Guwahati': {'lat': 26.1445, 'lng': 91.7362, 'state': 'Assam'},
    'Chandigarh': {'lat': 30.7333, 'lng': 76.7794, 'state': 'Chandigarh'},
    'Thiruvananthapuram': {'lat': 8.5241, 'lng': 76.9366, 'state': 'Kerala'},
    'Solapur': {'lat': 17.6599, 'lng': 75.9064, 'state': 'Maharashtra'},
    'Hubballi-Dharwad': {'lat': 15.3647, 'lng': 75.1240, 'state': 'Karnataka'},
    'Tiruchirappalli': {'lat': 10.7905, 'lng': 78.7047, 'state': 'Tamil Nadu'},
    'Bareilly': {'lat': 28.3670, 'lng': 79.4304, 'state': 'Uttar Pradesh'},
    'Mysore': {'lat': 12.2958, 'lng': 76.6394, 'state': 'Karnataka'},
    'Tiruppur': {'lat': 11.1085, 'lng': 77.3411, 'state': 'Tamil Nadu'},
    'Gurgaon': {'lat': 28.4595, 'lng': 77.0266, 'state': 'Haryana'},
    'Aligarh': {'lat': 27.8974, 'lng': 78.0880, 'state': 'Uttar Pradesh'},
    'Jalandhar': {'lat': 31.3260, 'lng': 75.5762, 'state': 'Punjab'},
    'Bhubaneswar': {'lat': 20.2961, 'lng': 85.8245, 'state': 'Odisha'},
    'Salem': {'lat': 11.6643, 'lng': 78.1460, 'state': 'Tamil Nadu'},
    'Warangal': {'lat': 17.9689, 'lng': 79.5941, 'state': 'Telangana'},
    'Mira-Bhayandar': {'lat': 19.2952, 'lng': 72.8544, 'state': 'Maharashtra'},
    'Guntur': {'lat': 16.3067, 'lng': 80.4365, 'state': 'Andhra Pradesh'},
    'Bhiwandi': {'lat': 19.3002, 'lng': 73.0693, 'state': 'Maharashtra'},
    'Saharanpur': {'lat': 29.9680, 'lng': 77.5552, 'state': 'Uttar Pradesh'},
    'Gorakhpur': {'lat': 26.7606, 'lng': 83.3732, 'state': 'Uttar Pradesh'},
    'Bikaner': {'lat': 28.0229, 'lng': 73.3119, 'state': 'Rajasthan'},
    'Amravati': {'lat': 20.9374, 'lng': 77.7796, 'state': 'Maharashtra'},
    'Noida': {'lat': 28.5355, 'lng': 77.3910, 'state': 'Uttar Pradesh'},
    'Jamshedpur': {'lat': 22.8046, 'lng': 86.2029, 'state': 'Jharkhand'},
    'Bhilai Nagar': {'lat': 21.1938, 'lng': 81.3509, 'state': 'Chhattisgarh'},
    'Cuttack': {'lat': 20.4625, 'lng': 85.8828, 'state': 'Odisha'},
    'Firozabad': {'lat': 27.1592, 'lng': 78.3957, 'state': 'Uttar Pradesh'},
    'Kochi': {'lat': 9.9312, 'lng': 76.2673, 'state': 'Kerala'},
    'Bhavnagar': {'lat': 21.7645, 'lng': 72.1519, 'state': 'Gujarat'},
    'Dehradun': {'lat': 30.3165, 'lng': 78.0322, 'state': 'Uttarakhand'},
    'Durgapur': {'lat': 23.4803, 'lng': 87.3119, 'state': 'West Bengal'},
    'Asansol': {'lat': 23.6739, 'lng': 86.9524, 'state': 'West Bengal'},
    'Nanded': {'lat': 19.1383, 'lng': 77.3210, 'state': 'Maharashtra'},
    'Kolhapur': {'lat': 16.7050, 'lng': 74.2433, 'state': 'Maharashtra'},
    'Ajmer': {'lat': 26.4499, 'lng': 74.6399, 'state': 'Rajasthan'},
    'Gulbarga': {'lat': 17.3297, 'lng': 76.8343, 'state': 'Karnataka'},
    'Jamnagar': {'lat': 22.4707, 'lng': 70.0577, 'state': 'Gujarat'},
    'Ujjain': {'lat': 23.1765, 'lng': 75.7885, 'state': 'Madhya Pradesh'},
    'Loni': {'lat': 28.7503, 'lng': 77.2905, 'state': 'Uttar Pradesh'},
    'Siliguri': {'lat': 26.7271, 'lng': 88.3953, 'state': 'West Bengal'},
    'Jhansi': {'lat': 25.4484, 'lng': 78.5685, 'state': 'Uttar Pradesh'},
    'Ulhasnagar': {'lat': 19.2215, 'lng': 73.1645, 'state': 'Maharashtra'},
    'Jammu': {'lat': 32.7266, 'lng': 74.8570, 'state': 'Jammu and Kashmir'},
    'Sangli-Miraj & Kupwad': {'lat': 16.8524, 'lng': 74.5815, 'state': 'Maharashtra'},
    'Mangalore': {'lat': 12.9141, 'lng': 74.8560, 'state': 'Karnataka'},
    'Erode': {'lat': 11.3410, 'lng': 77.7172, 'state': 'Tamil Nadu'},
    'Belgaum': {'lat': 15.8497, 'lng': 74.4977, 'state': 'Karnataka'},
    'Ambattur': {'lat': 13.1143, 'lng': 80.1548, 'state': 'Tamil Nadu'},
    'Tirunelveli': {'lat': 8.7139, 'lng': 77.7567, 'state': 'Tamil Nadu'},
    'Malegaon': {'lat': 20.5579, 'lng': 74.5287, 'state': 'Maharashtra'},
    'Gaya': {'lat': 24.7914, 'lng': 85.0002, 'state': 'Bihar'},
    'Jalgaon': {'lat': 21.0077, 'lng': 75.5626, 'state': 'Maharashtra'},
    'Udaipur': {'lat': 24.5854, 'lng': 73.7125, 'state': 'Rajasthan'},
    'Maheshtala': {'lat': 22.4851, 'lng': 88.2475, 'state': 'West Bengal'}
}

# Comprehensive procedure pricing ranges in INR
PROCEDURE_PRICE_RANGES = {
    'rhinoplasty': {'min': 80000, 'max': 300000, 'average': 180000},
    'breast_augmentation': {'min': 150000, 'max': 400000, 'average': 250000},
    'liposuction': {'min': 80000, 'max': 250000, 'average': 150000},
    'hair_transplant': {'min': 50000, 'max': 200000, 'average': 120000},
    'facelift': {'min': 200000, 'max': 500000, 'average': 300000},
    'tummy_tuck': {'min': 150000, 'max': 350000, 'average': 220000},
    'brazilian_butt_lift': {'min': 200000, 'max': 400000, 'average': 280000},
    'mommy_makeover': {'min': 300000, 'max': 600000, 'average': 450000},
    'brow_lift': {'min': 80000, 'max': 180000, 'average': 120000},
    'eyelid_surgery': {'min': 60000, 'max': 150000, 'average': 90000},
    'cheek_augmentation': {'min': 40000, 'max': 120000, 'average': 75000},
    'lip_enhancement': {'min': 15000, 'max': 60000, 'average': 35000},
    'chin_augmentation': {'min': 50000, 'max': 150000, 'average': 85000},
    'botox': {'min': 8000, 'max': 25000, 'average': 15000},
    'dermal_fillers': {'min': 15000, 'max': 50000, 'average': 28000},
    'laser_hair_removal': {'min': 5000, 'max': 25000, 'average': 12000},
    'chemical_peel': {'min': 3000, 'max': 15000, 'average': 8000},
    'microneedling': {'min': 2500, 'max': 12000, 'average': 6000},
    'coolsculpting': {'min': 20000, 'max': 80000, 'average': 45000},
    'thread_lift': {'min': 25000, 'max': 80000, 'average': 50000}
}

@enhanced_search_bp.route('/')
def advanced_search():
    """Advanced search page with all filters"""
    cities = list(INDIAN_CITIES.keys())
    specialties = db.session.query(Category).all()
    
    return render_template('advanced_search.html',
                         cities=cities,
                         specialties=specialties,
                         price_ranges=PROCEDURE_PRICE_RANGES)

@enhanced_search_bp.route('/api/search')
def api_search():
    """Advanced search API with multiple filters"""
    # Get search parameters
    city = request.args.get('city', '')
    specialty = request.args.get('specialty', '')
    min_price = request.args.get('min_price', type=int)
    max_price = request.args.get('max_price', type=int)
    amenities = request.args.getlist('amenities')
    rating_min = request.args.get('rating_min', type=float)
    distance = request.args.get('distance', type=int)  # km radius
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    
    # Start with base query
    query = db.session.query(Clinic)
    
    # Apply city filter
    if city:
        query = query.filter(Clinic.city.ilike(f'%{city}%'))
    
    # Apply specialty filter
    if specialty:
        query = query.join(ClinicSpecialty).join(Category).filter(
            Category.name.ilike(f'%{specialty}%')
        )
    
    # Apply rating filter
    if rating_min:
        query = query.filter(Clinic.overall_rating >= rating_min)
    
    # Apply distance filter (simplified calculation)
    if distance and user_lat and user_lng:
        # Use a simple bounding box calculation for performance
        lat_delta = distance / 111.0  # Approximate km per degree latitude
        lng_delta = distance / (111.0 * abs(user_lat))  # Adjust for longitude
        
        query = query.filter(
            and_(
                Clinic.latitude.between(user_lat - lat_delta, user_lat + lat_delta),
                Clinic.longitude.between(user_lng - lng_delta, user_lng + lng_delta)
            )
        )
    
    # Execute query
    clinics = query.all()
    
    # Convert to JSON-serializable format
    results = []
    for clinic in clinics:
        # Calculate distance if user location provided
        distance_km = None
        if user_lat and user_lng and clinic.latitude and clinic.longitude:
            distance_km = calculate_distance(user_lat, user_lng, clinic.latitude, clinic.longitude)
        
        clinic_data = {
            'id': clinic.id,
            'name': clinic.name,
            'city': clinic.city,
            'area': clinic.area,
            'rating': clinic.overall_rating,
            'total_reviews': clinic.total_reviews,
            'latitude': clinic.latitude,
            'longitude': clinic.longitude,
            'distance_km': distance_km,
            'phone': clinic.phone_number,
            'specialties': [s.category.name for s in clinic.specialties if s.category],
            'verified': clinic.is_verified,
            'featured': clinic.is_featured
        }
        results.append(clinic_data)
    
    # Sort by distance if available, otherwise by rating
    if user_lat and user_lng:
        results.sort(key=lambda x: x['distance_km'] if x['distance_km'] else float('inf'))
    else:
        results.sort(key=lambda x: x['rating'], reverse=True)
    
    return jsonify({
        'clinics': results,
        'total_count': len(results),
        'search_params': {
            'city': city,
            'specialty': specialty,
            'min_price': min_price,
            'max_price': max_price,
            'rating_min': rating_min,
            'distance': distance
        }
    })

@enhanced_search_bp.route('/api/price-range/<procedure>')
def get_price_range(procedure):
    """Get price range for a specific procedure"""
    procedure_key = procedure.lower().replace(' ', '_').replace('-', '_')
    price_range = PROCEDURE_PRICE_RANGES.get(procedure_key)
    
    if not price_range:
        return jsonify({'error': 'Procedure not found'})
    
    return jsonify(price_range)

@enhanced_search_bp.route('/api/nearby-clinics')
def nearby_clinics():
    """Find clinics near user location"""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 10, type=int)  # Default 10km
    
    if not lat or not lng:
        return jsonify({'error': 'Location coordinates required'})
    
    # Simple distance calculation for all clinics
    clinics = db.session.query(Clinic).filter(
        and_(Clinic.latitude.isnot(None), Clinic.longitude.isnot(None))
    ).all()
    
    nearby = []
    for clinic in clinics:
        distance = calculate_distance(lat, lng, clinic.latitude, clinic.longitude)
        if distance <= radius:
            nearby.append({
                'id': clinic.id,
                'name': clinic.name,
                'distance_km': round(distance, 1),
                'rating': clinic.overall_rating,
                'address': f"{clinic.area}, {clinic.city}",
                'specialties': [s.category.name for s in clinic.specialties[:3] if s.category]
            })
    
    # Sort by distance
    nearby.sort(key=lambda x: x['distance_km'])
    
    return jsonify({'nearby_clinics': nearby})

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r

@enhanced_search_bp.route('/api/cities/<state>')
def get_cities_by_state(state):
    """Get cities in a specific state"""
    cities_in_state = {city: data for city, data in INDIAN_CITIES.items() if data['state'] == state}
    return jsonify(list(cities_in_state.keys()))

@enhanced_search_bp.route('/api/coordinates/<city>')
def get_city_coordinates(city):
    """Get coordinates for a city"""
    city_data = INDIAN_CITIES.get(city)
    if not city_data:
        return jsonify({'error': 'City not found'})
    
    return jsonify({
        'city': city,
        'latitude': city_data['lat'],
        'longitude': city_data['lng'],
        'state': city_data['state']
    })