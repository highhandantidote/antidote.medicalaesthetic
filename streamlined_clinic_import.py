#!/usr/bin/env python3
"""
Streamlined clinic import with Google Places API integration.
Processes remaining clinics efficiently with authentic data.
"""

import os
import csv
import requests
import psycopg2
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def fetch_google_data(place_id, api_key):
    """Fetch essential Google Places data."""
    url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {
        'place_id': place_id,
        'key': api_key,
        'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,reviews,opening_hours,geometry'
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result', {})
    except Exception as e:
        logger.error(f"Error fetching Google data: {e}")
    return None

def clinic_exists(conn, place_id):
    """Check if clinic exists."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clinics WHERE google_place_id = %s", (place_id,))
    result = cursor.fetchone()
    cursor.close()
    return result is not None

def create_user(conn, clinic_name, email):
    """Create clinic owner user."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing = cursor.fetchone()
    
    if existing:
        user_id = existing[0]
    else:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, is_verified, role, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id
        """, (clinic_name, email, 'temp_hash', True, 'clinic_owner'))
        user_id = cursor.fetchone()[0]
    
    cursor.close()
    return user_id

def import_reviews(conn, clinic_id, reviews):
    """Import Google reviews."""
    if not reviews:
        return 0
    
    cursor = conn.cursor()
    cursor.execute("DELETE FROM google_reviews WHERE clinic_id = %s", (clinic_id,))
    
    count = 0
    for review in reviews:
        try:
            cursor.execute("""
                INSERT INTO google_reviews (clinic_id, author_name, rating, text, 
                relative_time_description, created_at, is_active)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            """, (
                clinic_id,
                review.get('author_name', 'Anonymous'),
                review.get('rating', 5),
                review.get('text', ''),
                review.get('relative_time_description', 'Recently'),
                True
            ))
            count += 1
        except Exception as e:
            logger.error(f"Error importing review: {e}")
    
    cursor.close()
    return count

def import_clinic(conn, row, api_key):
    """Import single clinic with Google data."""
    clinic_name = row.get('name', '').strip()
    place_id = row.get('google_place_id', '').strip()
    
    if not clinic_name or not place_id:
        return False
    
    if clinic_exists(conn, place_id):
        logger.info(f"Clinic {clinic_name} already exists")
        return True
    
    # Fetch Google data
    google_data = fetch_google_data(place_id, api_key)
    if not google_data:
        logger.warning(f"No Google data for {clinic_name}")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Extract data
        google_name = google_data.get('name', clinic_name)
        address = google_data.get('formatted_address', '')
        phone = google_data.get('formatted_phone_number', '')
        website = google_data.get('website', '')
        rating = google_data.get('rating', 0)
        review_count = google_data.get('user_ratings_total', 0)
        
        # Location
        location = google_data.get('geometry', {}).get('location', {})
        latitude = location.get('lat')
        longitude = location.get('lng')
        
        # Working hours
        working_hours = ''
        if google_data.get('opening_hours', {}).get('weekday_text'):
            working_hours = '; '.join(google_data['opening_hours']['weekday_text'])
        
        # Specialties from CSV
        specialties = row.get('specialties', '')
        
        # Create user
        email = f"{google_name.lower().replace(' ', '').replace('&', '')}@clinic.antidote.com"
        user_id = create_user(conn, google_name, email)
        
        # Insert clinic
        cursor.execute("""
            INSERT INTO clinics (
                name, slug, description, address, city, state, country,
                phone_number, email, website, latitude, longitude,
                google_place_id, google_rating, google_review_count,
                working_hours, specialties, owner_user_id,
                is_verified, is_approved, is_active, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            google_name,
            google_name.lower().replace(' ', '-').replace('&', 'and'),
            f"{google_name} is a medical aesthetic clinic in Hyderabad with {rating}/5 rating.",
            address,
            'Hyderabad',
            'Telangana', 
            'India',
            phone,
            email,
            website,
            latitude,
            longitude,
            place_id,
            rating,
            review_count,
            working_hours,
            specialties,
            user_id,
            True,
            True,
            True
        ))
        
        clinic_id = cursor.fetchone()[0]
        
        # Import reviews
        review_count = 0
        if google_data.get('reviews'):
            review_count = import_reviews(conn, clinic_id, google_data['reviews'])
        
        conn.commit()
        cursor.close()
        
        logger.info(f"Imported {google_name} (ID: {clinic_id}) with {review_count} reviews")
        return True
        
    except Exception as e:
        logger.error(f"Error importing {clinic_name}: {e}")
        conn.rollback()
        return False

def main():
    """Main import function."""
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    csv_file = 'attached_assets/hyderabad_filtered_clinics.csv - Sheet1_1750429116184.csv'
    
    conn = get_db_connection()
    imported = 0
    failed = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for i, row in enumerate(reader):
                if i >= 50:  # Process first 50 clinics
                    break
                    
                if import_clinic(conn, row, api_key):
                    imported += 1
                else:
                    failed += 1
                
                # Rate limiting
                time.sleep(1)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1} clinics: {imported} imported, {failed} failed")
    
    finally:
        conn.close()
    
    logger.info(f"Import completed: {imported} imported, {failed} failed")

if __name__ == "__main__":
    main()