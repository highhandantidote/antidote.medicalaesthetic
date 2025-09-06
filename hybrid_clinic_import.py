#!/usr/bin/env python3
"""
Hybrid clinic import system combining CSV data with Google Places API.
This system uses the comprehensive CSV data and enhances it with Google Places API data.
"""

import os
import csv
import psycopg2
import requests
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def get_google_api_key():
    """Get Google API key from environment."""
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_PLACES_API_KEY environment variable not set")
    return api_key

def fetch_google_places_data(place_id, api_key):
    """Fetch enhanced data from Google Places API."""
    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'key': api_key,
            'fields': 'name,formatted_address,geometry,rating,user_ratings_total,reviews,photos,formatted_phone_number,website,opening_hours,types,editorial_summary,business_status'
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logger.error(f"API request failed: {response.status_code}")
            return None
        
        data = response.json()
        if data.get('status') != 'OK':
            logger.error(f"Google Places API error: {data.get('status')}")
            return None
        
        return data.get('result', {})
        
    except Exception as e:
        logger.error(f"Error fetching Google Places data: {e}")
        return None

def create_clinic_owner_user(conn, clinic_name, email=None, phone=None):
    """Create a user account for the clinic owner."""
    try:
        cursor = conn.cursor()
        
        # Generate email if not provided
        if not email:
            clean_name = clinic_name.lower().replace(' ', '').replace(',', '').replace('|', '')[:20]
            email = f"{clean_name}@antidote-clinics.com"
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return email
        
        # Create user with phone number
        cursor.execute("""
            INSERT INTO users (name, email, phone_number, password_hash, is_clinic_owner, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (clinic_name, email, phone, 'temp_hash', True, datetime.now()))
        
        conn.commit()
        cursor.close()
        
        logger.info(f"Created clinic owner user: {email}")
        return email
        
    except Exception as e:
        logger.error(f"Error creating clinic owner user: {e}")
        return None

def import_reviews_for_clinic(conn, clinic_id, reviews_data):
    """Import reviews from Google Places API data."""
    try:
        if not reviews_data:
            return 0
        
        cursor = conn.cursor()
        imported_count = 0
        
        for review in reviews_data:
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

def clinic_exists(conn, google_place_id=None, name=None):
    """Check if clinic already exists."""
    try:
        cursor = conn.cursor()
        
        if google_place_id:
            cursor.execute("SELECT id FROM clinics WHERE google_place_id = %s", (google_place_id,))
        elif name:
            cursor.execute("SELECT id FROM clinics WHERE name = %s", (name,))
        else:
            return False
        
        result = cursor.fetchone()
        cursor.close()
        
        return result[0] if result else False
        
    except Exception as e:
        logger.error(f"Error checking clinic existence: {e}")
        return False

def import_hybrid_clinic(csv_row, google_data=None):
    """Import clinic combining CSV data with Google Places data."""
    try:
        conn = get_db_connection()
        
        # Extract CSV data
        name = csv_row['name']
        slug = csv_row['slug']
        description = csv_row['description']
        address = csv_row['address']
        city = csv_row['city']
        state = csv_row['state']
        country = csv_row['country']
        pincode = csv_row['pincode']
        latitude = float(csv_row['latitude']) if csv_row['latitude'] else None
        longitude = float(csv_row['longitude']) if csv_row['longitude'] else None
        contact_number = csv_row['contact_number']
        email = csv_row['email']
        website_url = csv_row['website_url']
        specialties = csv_row['specialties']
        operating_hours = csv_row['operating_hours']
        google_place_id = csv_row['google_place_id']
        amenities = csv_row['amenities']
        owner_email = csv_row['owner_email']
        
        # Check if clinic already exists
        existing_id = clinic_exists(conn, google_place_id, name)
        if existing_id:
            logger.info(f"Clinic already exists: {name} (ID: {existing_id})")
            conn.close()
            return existing_id
        
        # Use Google data if available, otherwise use CSV data
        if google_data:
            # Override with Google-verified data
            google_rating = google_data.get('rating')
            google_review_count = google_data.get('user_ratings_total')
            google_phone = google_data.get('formatted_phone_number')
            google_website = google_data.get('website')
            google_address = google_data.get('formatted_address')
            
            # Parse Google opening hours
            google_hours = None
            if google_data.get('opening_hours'):
                opening_hours_data = google_data['opening_hours']
                if opening_hours_data.get('weekday_text'):
                    # Convert Google's weekday_text to our format
                    weekday_hours = {}
                    for day_text in opening_hours_data['weekday_text']:
                        # Format: "Monday: 8:00 AM – 9:00 PM"
                        if ':' in day_text:
                            day_name, hours = day_text.split(':', 1)
                            weekday_hours[day_name.strip()] = hours.strip()
                    
                    if weekday_hours:
                        google_hours = '; '.join([f"{day}: {hours}" for day, hours in weekday_hours.items()])
            
            # Get Google description/summary
            google_description = None
            if google_data.get('editorial_summary'):
                google_description = google_data['editorial_summary'].get('overview', '')
            
            # If no editorial summary, create description from Google types and name
            if not google_description and google_data.get('types'):
                types = google_data.get('types', [])
                medical_types = [t for t in types if any(keyword in t.lower() for keyword in ['hospital', 'clinic', 'doctor', 'health', 'medical', 'beauty', 'spa'])]
                if medical_types:
                    primary_type = medical_types[0].replace('_', ' ').title()
                    google_description = f"Professional {primary_type.lower()} providing quality healthcare and aesthetic services."
            
            # Use Google coordinates if available
            if google_data.get('geometry'):
                google_location = google_data['geometry'].get('location', {})
                if google_location:
                    latitude = google_location.get('lat', latitude)
                    longitude = google_location.get('lng', longitude)
            
            # Use Google-verified contact info if available
            phone_number = google_phone or contact_number
            website = google_website or website_url
            verified_address = google_address or address
            working_hours = google_hours or operating_hours  # Prefer Google hours
            description = google_description or clinic_description  # Prefer Google description
            
        else:
            # Use CSV data only
            google_rating = None
            google_review_count = None
            phone_number = contact_number
            website = website_url
            verified_address = address
            working_hours = operating_hours
            description = description
        
        # Create clinic owner user
        owner_email_final = create_clinic_owner_user(conn, name, owner_email or email, contact_number)
        
        # Get owner user ID
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (owner_email_final,))
        result = cursor.fetchone()
        owner_user_id = result[0] if result else None
        
        # Insert clinic with hybrid data using correct schema
        cursor.execute("""
            INSERT INTO clinics (
                name, slug, description, address, city, state, pincode,
                latitude, longitude, phone_number, email, website, 
                services_offered, working_hours, google_place_id, google_rating, 
                google_review_count, owner_user_id, created_at, 
                is_active, is_approved, verification_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            name, slug, description, verified_address, city, state, pincode,
            latitude, longitude, phone_number, email, website,
            specialties, working_hours, google_place_id, google_rating,
            google_review_count, owner_user_id, datetime.now(),
            True, True, 'verified'  # Auto-approve clinics from CSV
        ))
        
        clinic_id = cursor.fetchone()[0]
        
        # Import reviews if available from Google data
        if google_data and google_data.get('reviews'):
            reviews_imported = import_reviews_for_clinic(conn, clinic_id, google_data['reviews'])
            logger.info(f"Imported {reviews_imported} reviews for {name}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully imported hybrid clinic: {name} (ID: {clinic_id})")
        return clinic_id
        
    except Exception as e:
        logger.error(f"Error importing hybrid clinic {name}: {e}")
        return None

def process_csv_file(csv_file_path, limit=None):
    """Process CSV file and import clinics with Google Places enhancement."""
    try:
        api_key = get_google_api_key()
        imported_count = 0
        error_count = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                
                try:
                    name = row['name']
                    place_id = row['google_place_id']
                    
                    logger.info(f"Processing clinic {i+1}: {name}")
                    
                    # Fetch Google Places data if place_id exists
                    google_data = None
                    if place_id:
                        google_data = fetch_google_places_data(place_id, api_key)
                        if google_data:
                            logger.info(f"Enhanced with Google data: rating {google_data.get('rating')}, reviews {google_data.get('user_ratings_total')}")
                    
                    # Import clinic
                    clinic_id = import_hybrid_clinic(row, google_data)
                    
                    if clinic_id:
                        imported_count += 1
                        logger.info(f"✅ Imported: {name} (ID: {clinic_id})")
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed: {name}")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing row {i+1}: {e}")
                    continue
        
        logger.info(f"Import complete: {imported_count} successful, {error_count} errors")
        return imported_count, error_count
        
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        return 0, 0

def main():
    """Test with a few clinics from the CSV."""
    csv_file = "attached_assets/hyderabad_filtered_clinics.csv - Sheet1_1750429116184.csv"
    
    # Test with first 5 clinics
    imported, errors = process_csv_file(csv_file, limit=5)
    
    print(f"\n🎯 Hybrid Import Test Results:")
    print(f"✅ Successfully imported: {imported} clinics")
    print(f"❌ Errors: {errors} clinics")
    
    if imported > 0:
        print(f"\n🚀 System ready for full bulk import of {imported} clinics!")

if __name__ == "__main__":
    main()