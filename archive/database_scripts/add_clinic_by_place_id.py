"""
Add clinic to database using Google Place ID.
This script uses the Google Places API to fetch authentic clinic data.
"""
import os
import requests
import psycopg2
from werkzeug.security import generate_password_hash
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def get_google_api_key():
    """Get Google API key from environment."""
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        logger.error("GOOGLE_API_KEY not found in environment variables")
        return None
    return api_key

def fetch_place_details(place_id, api_key):
    """Fetch place details from Google Places API."""
    # Using Places API (New) format
    url = "https://places.googleapis.com/v1/places/{place_id}"
    
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'id,displayName,formattedAddress,phoneNumber,websiteUri,rating,userRatingCount,businessStatus,location,photos,reviews'
    }
    
    try:
        response = requests.get(url.format(place_id=place_id), headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            # Try legacy API as fallback
            return fetch_place_details_legacy(place_id, api_key)
            
    except Exception as e:
        logger.error(f"Error fetching place details: {e}")
        return None

def fetch_place_details_legacy(place_id, api_key):
    """Fetch place details using legacy Places API."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        'place_id': place_id,
        'key': api_key,
        'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,business_status,geometry,photos,reviews,types,opening_hours'
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result')
            else:
                logger.error(f"API error: {data.get('status')} - {data.get('error_message')}")
                return None
        else:
            logger.error(f"Legacy API request failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error with legacy API: {e}")
        return None

def parse_address(formatted_address):
    """Parse formatted address into components."""
    if not formatted_address:
        return None, None, None
    
    # Simple parsing - can be enhanced with geocoding API
    parts = formatted_address.split(', ')
    
    city = None
    state = None
    
    # Look for common Indian state patterns
    for part in reversed(parts):
        if any(keyword in part.lower() for keyword in ['india', 'delhi', 'mumbai', 'bangalore', 'chennai', 'hyderabad', 'pune', 'kolkata']):
            if 'india' not in part.lower():
                city = part.strip()
        elif len(part.strip()) <= 3 and part.strip().isupper():  # State codes
            state = part.strip()
        elif any(keyword in part.lower() for keyword in ['karnataka', 'maharashtra', 'tamil nadu', 'delhi', 'west bengal', 'telangana']):
            state = part.strip()
    
    return formatted_address, city, state

def clinic_exists(conn, place_id):
    """Check if clinic with this place_id already exists."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clinics WHERE google_place_id = %s", (place_id,))
    result = cursor.fetchone()
    cursor.close()
    return result is not None

def create_clinic_owner_user(conn, clinic_name, email=None):
    """Create a user account for the clinic owner."""
    if not email:
        # Generate email from clinic name
        clean_name = clinic_name.lower().replace(' ', '').replace('clinic', '').replace('hospital', '')[:20]
        email = f"{clean_name}@clinic.antidote.com"
    
    # Check if user already exists
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        return existing_user[0]
    
    # Create new user
    username = email.split('@')[0]
    password_hash = generate_password_hash('temppassword123')
    
    cursor.execute("""
        INSERT INTO users (email, username, password_hash, role, credits, is_active)
        VALUES (%s, %s, %s, 'clinic_owner', 100, true)
        RETURNING id
    """, (email, username, password_hash))
    
    user_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    logger.info(f"Created clinic owner user: {email}")
    return user_id

def add_clinic_from_place_data(conn, place_data, place_id):
    """Add clinic to database from Google Places data."""
    
    # Extract data from Google Places response
    # Handle both new and legacy API formats
    if 'displayName' in place_data:
        # New API format
        name = place_data.get('displayName', {}).get('text', 'Unknown Clinic')
        formatted_address = place_data.get('formattedAddress')
        phone = place_data.get('phoneNumber')
        website = place_data.get('websiteUri')
        rating = place_data.get('rating')
        review_count = place_data.get('userRatingCount')
    else:
        # Legacy API format
        name = place_data.get('name', 'Unknown Clinic')
        formatted_address = place_data.get('formatted_address')
        phone = place_data.get('formatted_phone_number')
        website = place_data.get('website')
        rating = place_data.get('rating')
        review_count = place_data.get('user_ratings_total')
    
    # Parse address
    address, city, state = parse_address(formatted_address)
    
    # Process services/types from Google Places
    services_offered = None
    if 'types' in place_data and place_data['types']:
        # Convert Google Place types to readable services
        type_mapping = {
            'doctor': 'Medical Doctor',
            'hospital': 'Hospital Services',
            'beauty_salon': 'Beauty Salon',
            'spa': 'Spa Services',
            'health': 'Healthcare Services',
            'dentist': 'Dental Services',
            'physiotherapist': 'Physiotherapy',
            'establishment': '',  # Skip generic types
            'point_of_interest': '',
            'premise': ''
        }
        
        readable_services = []
        for service_type in place_data['types']:
            if service_type in type_mapping:
                mapped_service = type_mapping[service_type]
                if mapped_service and mapped_service not in readable_services:
                    readable_services.append(mapped_service)
            else:
                # Convert snake_case to readable format
                readable_service = service_type.replace('_', ' ').title()
                if readable_service not in readable_services:
                    readable_services.append(readable_service)
        
        if readable_services:
            services_offered = ', '.join(readable_services)
    
    # Process opening hours from Google Places
    working_hours = None
    if 'opening_hours' in place_data and place_data['opening_hours']:
        opening_hours_data = place_data['opening_hours']
        if 'weekday_text' in opening_hours_data:
            # Join the weekday text into a readable format
            working_hours = '; '.join(opening_hours_data['weekday_text'])
        elif 'periods' in opening_hours_data:
            # Process periods data if weekday_text is not available
            periods = opening_hours_data['periods']
            if periods:
                # Convert periods to readable format
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                hours_list = []
                for period in periods:
                    if 'open' in period:
                        day = day_names[period['open']['day']]
                        open_time = period['open']['time']
                        close_time = period.get('close', {}).get('time', '2400') if 'close' in period else '2400'
                        
                        # Format times
                        open_formatted = f"{open_time[:2]}:{open_time[2:]}"
                        close_formatted = f"{close_time[:2]}:{close_time[2:]}"
                        
                        hours_list.append(f"{day}: {open_formatted} - {close_formatted}")
                
                if hours_list:
                    working_hours = '; '.join(hours_list)
    
    # Create clinic owner user
    owner_user_id = create_clinic_owner_user(conn, name)
    
    # Insert clinic
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clinics (
            name, address, city, state, contact_number, website_url,
            google_place_id, google_rating, google_review_count,
            google_sync_enabled, owner_user_id, is_verified, rating, total_reviews,
            services_offered, working_hours, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
    """, (
        name, address, city, state, phone, website,
        place_id, rating, review_count,
        True, owner_user_id, True, rating or 4.5, review_count or 0,
        services_offered, working_hours, datetime.now()
    ))
    
    clinic_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    logger.info(f"Added clinic: {name} (ID: {clinic_id})")
    return clinic_id

def add_clinic_by_place_id(place_id):
    """Main function to add clinic by Google Place ID."""
    logger.info(f"Adding clinic with Place ID: {place_id}")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        # Check if clinic already exists
        if clinic_exists(conn, place_id):
            logger.info(f"Clinic with Place ID {place_id} already exists")
            return True
        
        # Get Google API key
        api_key = get_google_api_key()
        if not api_key:
            logger.error("Google API key not available")
            return False
        
        # Fetch place details
        place_data = fetch_place_details(place_id, api_key)
        if not place_data:
            logger.error("Failed to fetch place details from Google")
            return False
        
        # Add clinic to database
        clinic_id = add_clinic_from_place_data(conn, place_data, place_id)
        
        logger.info(f"Successfully added clinic with ID: {clinic_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding clinic: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function for testing."""
    # Use the provided Place ID
    test_place_id = "ChIJhcOH4tyZyzsRN1AHrG8xZ5I"
    
    print("=== Add Clinic by Google Place ID ===")
    print(f"Creating clinic profile for Place ID: {test_place_id}")
    
    # Check if API key is available
    api_key = get_google_api_key()
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("Please set your Google API key to use this script")
        return
    
    print("✅ Google API key found")
    
    # Test adding clinic
    success = add_clinic_by_place_id(test_place_id)
    
    if success:
        print("✅ Clinic added successfully")
    else:
        print("❌ Failed to add clinic")

if __name__ == "__main__":
    main()