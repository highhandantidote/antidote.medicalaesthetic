#!/usr/bin/env python3
"""
Bulk import all clinics from hyderabad_filtered_clinics.csv using hybrid Google Places API system.
"""

import os
import csv
import psycopg2
import requests
import logging
import json
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def get_google_api_key():
    """Get Google API key from environment."""
    return os.environ.get('GOOGLE_PLACES_API_KEY')

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
    """Create clinic owner user account."""
    try:
        cursor = conn.cursor()
        
        # Generate email if not provided
        if not email:
            base_name = clinic_name.lower().replace(' ', '').replace('-', '').replace('.', '')[:20]
            email = f"{base_name}@antidote-temp.com"
        
        # Check if user exists
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return email
        
        # Create user
        cursor.execute("""
            INSERT INTO users (email, username, password_hash, is_active, created_at, is_clinic_owner, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (email, email.split('@')[0], 'temp_hash', True, datetime.now(), True, 'clinic_owner'))
        
        conn.commit()
        cursor.close()
        return email
    except Exception as e:
        logger.error(f"Error creating clinic owner: {e}")
        return None

def import_clinic_with_google_data(clinic_data, api_key):
    """Import single clinic with Google Places API enhancement."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if clinic already exists
        cursor.execute("SELECT id FROM clinics WHERE google_place_id = %s OR name = %s", 
                      (clinic_data.get('google_place_id'), clinic_data['name']))
        existing = cursor.fetchone()
        
        if existing:
            logger.info(f"Clinic already exists: {clinic_data['name']} (ID: {existing[0]})")
            cursor.close()
            conn.close()
            return existing[0]
        
        # Fetch Google Places data
        google_data = None
        if clinic_data.get('google_place_id'):
            google_data = fetch_google_places_data(clinic_data['google_place_id'], api_key)
            time.sleep(0.1)  # Rate limiting
        
        # Set default values
        description = clinic_data.get('description', '') or "Premier medical aesthetic clinic providing comprehensive cosmetic treatments and procedures with expert care."
        working_hours = clinic_data.get('operating_hours', '')
        google_rating = None
        google_review_count = None
        phone_number = clinic_data.get('contact_number', '')
        website = clinic_data.get('website_url', '')
        verified_address = clinic_data['address']
        latitude = float(clinic_data.get('latitude', 0))
        longitude = float(clinic_data.get('longitude', 0))
        
        # Use Google data if available
        if google_data:
            # Parse Google opening hours
            if google_data.get('opening_hours'):
                opening_hours_data = google_data['opening_hours']
                if opening_hours_data.get('weekday_text'):
                    weekday_hours = {}
                    for day_text in opening_hours_data['weekday_text']:
                        if ':' in day_text:
                            day_name, hours = day_text.split(':', 1)
                            weekday_hours[day_name.strip()] = hours.strip()
                    
                    if weekday_hours:
                        working_hours = '; '.join([f"{day}: {hours}" for day, hours in weekday_hours.items()])
            
            # Generate description from Google types
            if google_data.get('types'):
                types = google_data.get('types', [])
                medical_types = [t for t in types if any(keyword in t.lower() for keyword in ['hospital', 'clinic', 'doctor', 'health', 'medical', 'beauty', 'spa'])]
                if medical_types:
                    primary_type = medical_types[0].replace('_', ' ').title()
                    description = f"Professional {primary_type.lower()} providing quality healthcare and aesthetic services."
            
            # Use Google coordinates if available
            if google_data.get('geometry'):
                google_location = google_data['geometry'].get('location', {})
                if google_location:
                    latitude = google_location.get('lat', latitude)
                    longitude = google_location.get('lng', longitude)
            
            # Use Google-verified contact info
            phone_number = google_data.get('formatted_phone_number') or phone_number
            website = google_data.get('website') or website
            verified_address = google_data.get('formatted_address') or verified_address
            google_rating = google_data.get('rating')
            google_review_count = google_data.get('user_ratings_total')
        
        # Create clinic owner user
        owner_email = create_clinic_owner_user(conn, clinic_data['name'], clinic_data.get('owner_email'), phone_number)
        
        # Get owner user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (owner_email,))
        owner_user_id = cursor.fetchone()[0]
        
        # Create slug
        slug = clinic_data.get('slug') or clinic_data['name'].lower().replace(' ', '-').replace('.', '').replace(',', '')
        
        # Insert clinic
        cursor.execute("""
            INSERT INTO clinics (
                name, slug, description, address, city, state, pincode,
                latitude, longitude, phone_number, email, website,
                specialties, working_hours, google_place_id, google_rating,
                google_review_count, owner_user_id, created_at,
                is_active, is_approved, verification_status
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            ) RETURNING id
        """, (
            clinic_data['name'], slug, description, verified_address, 
            clinic_data['city'], clinic_data['state'], clinic_data.get('pincode'),
            latitude, longitude, phone_number, 
            clinic_data.get('email', ''), website,
            clinic_data.get('specialties', ''), working_hours, clinic_data.get('google_place_id'),
            google_rating, google_review_count, owner_user_id, datetime.now(),
            True, True, 'verified'  # Auto-approve clinics
        ))
        
        clinic_id = cursor.fetchone()[0]
        conn.commit()
        
        logger.info(f"Successfully imported clinic: {clinic_data['name']} (ID: {clinic_id})")
        
        cursor.close()
        conn.close()
        return clinic_id
        
    except Exception as e:
        logger.error(f"Error importing clinic {clinic_data['name']}: {e}")
        if conn:
            conn.rollback()
            cursor.close()
            conn.close()
        return None

def bulk_import_from_csv():
    """Import all clinics from CSV file."""
    csv_file_path = "attached_assets/hyderabad_filtered_clinics.csv - Sheet1_1750429116184.csv"
    api_key = get_google_api_key()
    
    if not api_key:
        logger.error("Google Places API key not found")
        return
    
    imported_count = 0
    failed_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):  # Start from 2 because row 1 is headers
                try:
                    # Clean and prepare clinic data
                    clinic_data = {
                        'name': row['name'].strip(),
                        'slug': row['slug'].strip() if row['slug'] else None,
                        'description': row['description'].strip() if row['description'] else '',
                        'address': row['address'].strip(),
                        'city': row['city'].strip(),
                        'state': row['state'].strip(),
                        'pincode': row['pincode'].strip() if row['pincode'] else None,
                        'latitude': row['latitude'].strip() if row['latitude'] else '0',
                        'longitude': row['longitude'].strip() if row['longitude'] else '0',
                        'contact_number': row['contact_number'].strip() if row['contact_number'] else '',
                        'email': row['email'].strip() if row['email'] else '',
                        'website_url': row['website_url'].strip() if row['website_url'] else '',
                        'specialties': row['specialties'].strip() if row['specialties'] else '',
                        'operating_hours': row['operating_hours'].strip() if row['operating_hours'] else '',
                        'google_place_id': row['google_place_id'].strip() if row['google_place_id'] else None,
                        'owner_email': row['owner_email'].strip() if row['owner_email'] else None
                    }
                    
                    # Skip empty clinic names
                    if not clinic_data['name']:
                        logger.warning(f"Skipping row {row_num}: No clinic name")
                        continue
                    
                    # Import clinic
                    clinic_id = import_clinic_with_google_data(clinic_data, api_key)
                    
                    if clinic_id:
                        imported_count += 1
                        logger.info(f"Progress: {imported_count} clinics imported (Row {row_num})")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to import clinic from row {row_num}")
                    
                    # Rate limiting for Google API
                    time.sleep(0.2)
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing row {row_num}: {e}")
                    continue
                    
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file_path}")
        return
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return
    
    logger.info(f"Bulk import completed: {imported_count} imported, {failed_count} failed")
    return imported_count, failed_count

if __name__ == "__main__":
    logger.info("Starting bulk clinic import from CSV...")
    bulk_import_from_csv()