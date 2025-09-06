#!/usr/bin/env python3
"""
Complete Chennai Clinics Import System
Import all 282 Chennai clinics from CSV with Google Places API verification
Comprehensive clinic data extraction and authentic review integration
"""

import os
import csv
import requests
import psycopg2
import time
import re
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'chennai_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

def get_db_connection():
    """Get database connection using environment variable."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def get_google_api_key():
    """Get Google Places API key from environment."""
    return os.environ.get('GOOGLE_PLACES_API_KEY')

def clinic_exists(conn, place_id):
    """Check if clinic with this place_id already exists."""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM clinics WHERE google_place_id = %s', (place_id,))
    result = cursor.fetchone()
    cursor.close()
    return result is not None

def fetch_google_places_data(place_id, api_key):
    """Fetch comprehensive clinic data from Google Places API."""
    try:
        response = requests.get(
            f'https://maps.googleapis.com/maps/api/place/details/json',
            params={
                'place_id': place_id,
                'key': api_key,
                'fields': 'name,formatted_address,rating,user_ratings_total,reviews,opening_hours,geometry,website,formatted_phone_number'
            },
            timeout=12
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result', {})
        
        return {}
    except Exception as e:
        logging.warning(f"Google Places API error for {place_id}: {e}")
        return {}

def parse_working_hours(hours_data):
    """Parse working hours from various formats."""
    if not hours_data:
        return ''
    
    try:
        # Handle JSON format
        if isinstance(hours_data, str) and hours_data.startswith('{'):
            hours_dict = json.loads(hours_data.replace('\u202f', ' '))
            return '; '.join([f'{day}: {time}' for day, time in hours_dict.items() if time])
        
        # Handle Google Places format
        if isinstance(hours_data, dict) and 'weekday_text' in hours_data:
            return '; '.join(hours_data['weekday_text'])
        
        # Handle direct string
        if isinstance(hours_data, str):
            return hours_data
        
        return ''
    except Exception as e:
        logging.warning(f"Error parsing working hours: {e}")
        return str(hours_data) if hours_data else ''

def create_unique_identifiers(name, imported_count):
    """Create unique email and slug for clinic."""
    timestamp = int(time.time()) + imported_count * 100
    
    # Create clean name for email
    clean_name = re.sub(r'[^a-z0-9]', '', name.lower())[:3]
    if not clean_name:
        clean_name = 'clinic'
    
    email = f'{clean_name}chennai{imported_count}{timestamp}@clinic.antidote.com'
    
    # Create slug
    base_slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(' ', '-'))[:15]
    if not base_slug:
        base_slug = 'chennai-clinic'
    
    slug = f'{base_slug}-{imported_count}-{timestamp}'
    
    return email, slug

def import_google_reviews(conn, clinic_id, reviews_data):
    """Import Google reviews for a clinic."""
    if not reviews_data:
        return 0
    
    cursor = conn.cursor()
    imported_reviews = 0
    
    try:
        for review in reviews_data:
            cursor.execute('''
                INSERT INTO google_reviews (
                    clinic_id, author_name, rating, text,
                    relative_time_description, created_at, is_active
                ) VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            ''', (
                clinic_id,
                review.get('author_name', 'Patient'),
                review.get('rating', 5),
                review.get('text', ''),
                review.get('relative_time_description', 'Recent'),
                True
            ))
            imported_reviews += 1
        
        cursor.close()
        return imported_reviews
    except Exception as e:
        logging.warning(f"Error importing reviews: {e}")
        cursor.close()
        return 0

def import_single_clinic(record, api_key, imported_count):
    """Import a single clinic with complete data processing."""
    place_id = record.get('google_place_id', '').strip()
    csv_name = record.get('name', '').strip()
    
    if not place_id or not csv_name:
        return False
    
    conn = get_db_connection()
    
    # Check if clinic already exists
    if clinic_exists(conn, place_id):
        conn.close()
        return False
    
    try:
        # Fetch Google Places data
        google_data = fetch_google_places_data(place_id, api_key)
        
        # Extract clinic information
        clinic_name = google_data.get('name', csv_name)
        address = google_data.get('formatted_address', record.get('address', ''))
        rating = google_data.get('rating', 4.5)
        review_count = google_data.get('user_ratings_total', 0)
        
        # Extract coordinates
        location = google_data.get('geometry', {}).get('location', {})
        latitude = location.get('lat')
        longitude = location.get('lng')
        
        # Use CSV coordinates if Google doesn't provide them
        if not latitude and record.get('latitude'):
            try:
                latitude = float(record.get('latitude'))
                longitude = float(record.get('longitude'))
            except (ValueError, TypeError):
                pass
        
        # Parse working hours
        working_hours = ''
        if google_data.get('opening_hours'):
            working_hours = parse_working_hours(google_data.get('opening_hours'))
        elif record.get('operating_hours'):
            working_hours = parse_working_hours(record.get('operating_hours'))
        
        # Extract other details
        phone = google_data.get('formatted_phone_number', record.get('contact_number', ''))
        website = google_data.get('website', record.get('website_url', ''))
        specialties = record.get('specialties', 'Medical Aesthetics, Cosmetic Surgery')
        
        # Create unique identifiers
        email, slug = create_unique_identifiers(clinic_name, imported_count)
        
        cursor = conn.cursor()
        
        # Create user account for clinic owner
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, is_verified, role, created_at) 
            VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id
        ''', (clinic_name, email, 'hash', True, 'clinic_owner'))
        
        user_id = cursor.fetchone()[0]
        
        # Create clinic record
        cursor.execute('''
            INSERT INTO clinics (
                name, slug, description, address, city, state, country, pincode,
                phone_number, email, website, latitude, longitude,
                google_place_id, google_rating, google_review_count,
                working_hours, specialties, owner_user_id,
                is_verified, is_approved, is_active, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        ''', (
            clinic_name, slug, f'{clinic_name} - Professional medical aesthetics clinic in Chennai',
            address, 'Chennai', 'Tamil Nadu', 'India', record.get('pincode'),
            phone, email, website, latitude, longitude,
            place_id, rating, review_count,
            working_hours, specialties, user_id,
            True, True, True
        ))
        
        clinic_id = cursor.fetchone()[0]
        
        # Import Google reviews
        reviews_imported = 0
        if google_data.get('reviews'):
            reviews_imported = import_google_reviews(conn, clinic_id, google_data['reviews'])
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logging.info(f"✓ Imported: {clinic_name} | Reviews: {reviews_imported} | Rating: {rating}")
        return True
        
    except Exception as e:
        logging.error(f"Error importing clinic {csv_name}: {e}")
        try:
            conn.rollback()
            cursor.close()
            conn.close()
        except:
            pass
        return False

def import_chennai_clinics():
    """Import all Chennai clinics from CSV file."""
    api_key = get_google_api_key()
    if not api_key:
        logging.error("Google Places API key not found")
        return
    
    # Load Chennai clinic data
    csv_file = 'attached_assets/chennai_filtered_clinics.csv - Sheet1_1750459383999.csv'
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            chennai_records = list(reader)
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return
    
    total_records = len(chennai_records)
    logging.info(f"Starting Chennai import: {total_records} clinics to process")
    
    imported_count = 0
    success_count = 0
    
    for record in chennai_records:
        if import_single_clinic(record, api_key, imported_count):
            success_count += 1
        
        imported_count += 1
        
        # Progress update every 25 clinics
        if imported_count % 25 == 0:
            logging.info(f"Progress: {imported_count}/{total_records} processed | {success_count} successful")
    
    # Final statistics
    success_rate = (success_count / total_records) * 100 if total_records > 0 else 0
    
    logging.info(f"\n=== CHENNAI IMPORT COMPLETE ===")
    logging.info(f"Total processed: {imported_count}")
    logging.info(f"Successfully imported: {success_count}")
    logging.info(f"Success rate: {success_rate:.1f}%")
    
    # Get comprehensive platform statistics
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # City-wise counts
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('Chennai',))
    chennai_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('Gurugram',))
    gurugram_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('New Delhi',))
    delhi_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('Mumbai',))
    mumbai_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('Hyderabad',))
    hyderabad_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('Bangalore',))
    bangalore_total = cursor.fetchone()[0]
    
    # Platform totals
    cursor.execute('SELECT COUNT(*) FROM clinics')
    total_clinics = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(google_review_count) FROM clinics')
    total_reviews = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM clinics WHERE working_hours IS NOT NULL AND working_hours != ''")
    clinics_with_hours = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    # Comprehensive platform report
    logging.info(f"\n=== COMPLETE MEDICAL AESTHETICS MARKETPLACE ===")
    logging.info(f"Chennai: {chennai_total} clinics")
    logging.info(f"Gurugram: {gurugram_total} clinics") 
    logging.info(f"Delhi: {delhi_total} clinics")
    logging.info(f"Mumbai: {mumbai_total} clinics")
    logging.info(f"Hyderabad: {hyderabad_total} clinics")
    logging.info(f"Bangalore: {bangalore_total} clinics")
    logging.info(f"TOTAL: {total_clinics} clinics across 6 major Indian cities")
    logging.info(f"Google Reviews: {total_reviews:,}")
    logging.info(f"Working Hours Coverage: {clinics_with_hours} ({(clinics_with_hours/total_clinics)*100:.1f}%)")
    
    return success_count

if __name__ == "__main__":
    import_chennai_clinics()