#!/usr/bin/env python3
"""
Add clinic using legacy Google Places API - working version.
"""

import os
import psycopg2
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    try:
        return psycopg2.connect(os.environ.get('DATABASE_URL'))
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
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
            logger.error(f"HTTP error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching place details: {e}")
        return None

def parse_address(formatted_address):
    """Parse formatted address into components."""
    if not formatted_address:
        return None, None, None
    
    parts = [part.strip() for part in formatted_address.split(',')]
    
    if len(parts) >= 3:
        city = parts[-3]
        state_postal = parts[-2]
        state = state_postal.split()[0] if state_postal else None
        return parts[0], city, state
    elif len(parts) >= 2:
        return parts[0], parts[-2], parts[-1]
    else:
        return formatted_address, None, None

def parse_opening_hours(opening_hours):
    """Parse opening hours into a formatted string."""
    if not opening_hours or 'weekday_text' not in opening_hours:
        return None
    
    weekday_text = opening_hours['weekday_text']
    return '; '.join(weekday_text)

def clinic_exists(conn, place_id):
    """Check if clinic already exists."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clinics WHERE google_place_id = %s", (place_id,))
    result = cursor.fetchone()
    cursor.close()
    return result is not None

def create_clinic_owner_user(conn, clinic_name, email=None):
    """Create clinic owner user account."""
    import random
    
    if not email:
        # Generate email from clinic name
        safe_name = ''.join(c.lower() for c in clinic_name if c.isalnum())[:20]
        email = f"{safe_name}@antidote-clinics.com"
    
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        return email
    
    # Generate unique phone number
    phone_number = f"+91-{random.randint(7000000000, 9999999999)}"
    
    # Create new user with existing table structure
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, role, created_at, phone_number, name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        email.split('@')[0],
        email,
        'placeholder_hash',  # Will be set when user first logs in
        'clinic_owner',
        datetime.now(),
        phone_number,
        clinic_name  # Use actual clinic name
    ))
    
    user_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    logger.info(f"Created clinic owner user: {email}")
    return email

def add_clinic_from_place_data(conn, place_data, place_id):
    """Add clinic to database from Google Places data."""
    cursor = conn.cursor()
    
    # Extract data
    name = place_data.get('name', 'Unknown Clinic')
    formatted_address = place_data.get('formatted_address', '')
    phone = place_data.get('formatted_phone_number', '')
    website = place_data.get('website', '')
    rating = place_data.get('rating', 0)
    user_ratings_total = place_data.get('user_ratings_total', 0)
    
    # Parse address
    address, city, state = parse_address(formatted_address)
    
    # Parse opening hours
    working_hours = parse_opening_hours(place_data.get('opening_hours'))
    
    # Extract coordinates
    geometry = place_data.get('geometry', {})
    location = geometry.get('location', {})
    latitude = location.get('lat', 0)
    longitude = location.get('lng', 0)
    
    # Extract types as services
    types = place_data.get('types', [])
    services_offered = ', '.join([t.replace('_', ' ').title() for t in types[:10]])
    
    # Create clinic owner user
    owner_email = create_clinic_owner_user(conn, name)
    
    # Insert clinic
    cursor.execute("""
        INSERT INTO clinics (
            name, address, city, state, phone_number, website, 
            google_rating, total_reviews, latitude, longitude,
            services_offered, working_hours, google_place_id,
            email, created_at, is_active, is_approved, is_verified
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
    """, (
        name, address, city, state, phone, website,
        rating, user_ratings_total, latitude, longitude,
        services_offered, working_hours, place_id,
        owner_email, datetime.now(), True, True, True
    ))
    
    clinic_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    logger.info(f"Added clinic: {name} (ID: {clinic_id})")
    return clinic_id

def import_reviews_for_clinic(conn, clinic_id, place_id, api_key):
    """Import reviews for a clinic from Google Places API."""
    try:
        # Fetch reviews using Places API
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'key': api_key,
            'fields': 'reviews'
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to fetch reviews: {response.status_code}")
            return 0
        
        data = response.json()
        if data.get('status') != 'OK':
            logger.error(f"API error fetching reviews: {data.get('status')}")
            return 0
        
        reviews = data.get('result', {}).get('reviews', [])
        if not reviews:
            logger.info("No reviews found for this clinic")
            return 0
        
        cursor = conn.cursor()
        imported_count = 0
        
        for review in reviews:
            try:
                # Extract review data
                author_name = review.get('author_name', 'Anonymous')
                author_photo_url = review.get('profile_photo_url', '')
                rating = review.get('rating', 0)
                text = review.get('text', '')
                time_created = review.get('time', 0)
                
                # Convert timestamp to datetime
                review_date = datetime.fromtimestamp(time_created) if time_created else datetime.now()
                
                # Check if review already exists
                cursor.execute("""
                    SELECT id FROM google_reviews 
                    WHERE clinic_id = %s AND author_name = %s AND text = %s
                """, (clinic_id, author_name, text))
                
                if cursor.fetchone():
                    continue  # Skip duplicate
                
                # Insert review with is_active = true
                cursor.execute("""
                    INSERT INTO google_reviews (
                        clinic_id, author_name, profile_photo_url, rating, 
                        text, time, created_at, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    clinic_id, author_name, author_photo_url, rating,
                    text, review_date, datetime.now(), True
                ))
                
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing review: {e}")
                continue
        
        conn.commit()
        cursor.close()
        
        logger.info(f"Successfully imported {imported_count} reviews for clinic {clinic_id}")
        return imported_count
        
    except Exception as e:
        logger.error(f"Error importing reviews for clinic {clinic_id}: {e}")
        return 0

def add_clinic_by_place_id(place_id):
    """Main function to add clinic by Place ID."""
    logger.info(f"Adding clinic with Place ID: {place_id}")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Check if clinic already exists
        if clinic_exists(conn, place_id):
            logger.info(f"Clinic with Place ID {place_id} already exists")
            return True
        
        # Get API key
        api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
        if not api_key:
            logger.error("GOOGLE_PLACES_API_KEY not found")
            return False
        
        # Fetch place details
        place_data = fetch_place_details_legacy(place_id, api_key)
        if not place_data:
            logger.error("Failed to fetch place details")
            return False
        
        # Add clinic
        clinic_id = add_clinic_from_place_data(conn, place_data, place_id)
        logger.info(f"Successfully added clinic with ID: {clinic_id}")
        
        # Import reviews for the clinic
        reviews_imported = import_reviews_for_clinic(conn, clinic_id, place_id, api_key)
        logger.info(f"Imported {reviews_imported} reviews for clinic {clinic_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding clinic: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main function for testing."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python add_clinic_legacy_api.py <place_id>")
        sys.exit(1)
    
    place_id = sys.argv[1]
    
    print(f"=== Adding Clinic with Legacy API ===")
    print(f"Place ID: {place_id}")
    
    success = add_clinic_by_place_id(place_id)
    
    if success:
        print("✅ Clinic added successfully")
    else:
        print("❌ Failed to add clinic")

if __name__ == "__main__":
    main()