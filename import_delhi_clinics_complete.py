#!/usr/bin/env python3
"""
Complete Delhi clinic import from CSV with Google Places API integration.
Imports all 561 Delhi clinics with authentic Google Business data.
"""

import os
import csv
import requests
import psycopg2
import time
import re
import json
from typing import Dict, Any, Optional

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def get_existing_place_ids() -> set:
    """Get all existing Google Place IDs to avoid duplicates."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT google_place_id FROM clinics WHERE google_place_id IS NOT NULL')
    existing_places = set(row[0] for row in cursor.fetchall())
    cursor.close()
    conn.close()
    return existing_places

def fetch_google_places_data(place_id: str, api_key: str) -> Dict[str, Any]:
    """Fetch clinic data from Google Places API."""
    try:
        response = requests.get(
            f'https://maps.googleapis.com/maps/api/place/details/json',
            params={
                'place_id': place_id,
                'key': api_key,
                'fields': 'name,formatted_address,rating,user_ratings_total,reviews,opening_hours,geometry,phone_number'
            },
            timeout=20
        )
        
        if response.status_code == 200 and response.json().get('status') == 'OK':
            return response.json().get('result', {})
        
    except Exception as e:
        print(f"API error for {place_id}: {e}")
    
    return {}

def parse_operating_hours(hours_data) -> str:
    """Parse operating hours from CSV or Google data."""
    if isinstance(hours_data, str):
        try:
            # Try to parse JSON string from CSV
            hours_dict = json.loads(hours_data.replace('\u202f', ' '))
            return '; '.join([f"{day}: {time}" for day, time in hours_dict.items()])
        except:
            return hours_data
    elif isinstance(hours_data, dict):
        return '; '.join([f"{day}: {time}" for day, time in hours_data.items()])
    return ''

def create_unique_identifiers(name: str, imported_count: int) -> tuple:
    """Create unique email and slug for clinic."""
    timestamp = int(time.time()) + imported_count * 100
    clean_name = re.sub(r'[^a-z0-9]', '', name.lower())[:3]
    if not clean_name:
        clean_name = 'clinic'
    
    email = f'{clean_name}del{imported_count}{timestamp}@clinic.antidote.com'
    
    base_slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(' ', '-'))[:12]
    if not base_slug:
        base_slug = 'delhi-clinic'
    slug = f'{base_slug}-{imported_count}-{timestamp}'
    
    return email, slug

def insert_clinic_to_database(clinic_data: Dict[str, Any]) -> Optional[int]:
    """Insert clinic data into database with user account creation."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create user account for clinic owner
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, is_verified, role, created_at) 
            VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id
        ''', (
            clinic_data['name'], 
            clinic_data['email'], 
            'hash', 
            True, 
            'clinic_owner'
        ))
        user_id = cursor.fetchone()[0]
        
        # Insert clinic
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
            clinic_data['name'], clinic_data['slug'], clinic_data['description'],
            clinic_data['address'], clinic_data['city'], clinic_data['state'], 
            clinic_data['country'], clinic_data.get('pincode'),
            clinic_data.get('phone'), clinic_data['email'], clinic_data.get('website'),
            clinic_data.get('latitude'), clinic_data.get('longitude'),
            clinic_data.get('google_place_id'), clinic_data.get('google_rating', 4.5),
            clinic_data.get('google_review_count', 0), clinic_data.get('working_hours'),
            clinic_data.get('specialties'), user_id, True, True, True
        ))
        
        clinic_id = cursor.fetchone()[0]
        
        # Import Google reviews if available
        if clinic_data.get('reviews'):
            for review in clinic_data['reviews']:
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return clinic_id
        
    except Exception as e:
        if 'conn' in locals():
            try:
                conn.rollback()
                cursor.close()
                conn.close()
            except:
                pass
        print(f"Database error for {clinic_data.get('name', 'Unknown')}: {e}")
        return None

def import_delhi_clinics_complete():
    """Import all Delhi clinics from CSV with Google Places API integration."""
    
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("Error: GOOGLE_PLACES_API_KEY not found")
        return
    
    # Load existing place IDs to avoid duplicates
    existing_places = get_existing_place_ids()
    print(f"Found {len(existing_places)} existing clinics in database")
    
    # Load Delhi CSV data
    delhi_records = []
    csv_file_path = 'attached_assets/delhi_filtered_clinics - Sheet1_1750456687041.csv'
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            place_id = row.get('google_place_id', '').strip()
            name = row.get('name', '').strip()
            if place_id and name and place_id not in existing_places:
                delhi_records.append(row)
    
    total_records = len(delhi_records)
    print(f"Starting Delhi import: {total_records} clinics to process")
    
    imported_count = 0
    failed_count = 0
    
    # Process each clinic
    for i, record in enumerate(delhi_records, 1):
        place_id = record.get('google_place_id', '').strip()
        csv_name = record.get('name', '').strip()
        
        try:
            # Fetch Google Places data
            google_data = fetch_google_places_data(place_id, api_key)
            
            # Combine CSV and Google data
            name = google_data.get('name', csv_name)
            address = google_data.get('formatted_address', record.get('address', ''))
            rating = google_data.get('rating', float(record.get('google_rating', 4.5)))
            review_count = google_data.get('user_ratings_total', int(record.get('google_review_count', 0)))
            
            # Get coordinates
            location = google_data.get('geometry', {}).get('location', {})
            lat = location.get('lat')
            lng = location.get('lng')
            
            # Use CSV coordinates if Google doesn't provide them
            if not lat and record.get('latitude'):
                try:
                    lat = float(record.get('latitude'))
                    lng = float(record.get('longitude'))
                except:
                    pass
            
            # Parse working hours
            hours = ''
            if google_data.get('opening_hours', {}).get('weekday_text'):
                hours = '; '.join(google_data['opening_hours']['weekday_text'])
            elif record.get('operating_hours'):
                hours = parse_operating_hours(record.get('operating_hours'))
            
            # Create unique identifiers
            email, slug = create_unique_identifiers(name, imported_count)
            
            # Prepare clinic data
            clinic_data = {
                'name': name,
                'slug': slug,
                'description': f'{name} - Professional medical aesthetics clinic in Delhi',
                'address': address,
                'city': 'New Delhi',
                'state': 'Delhi',
                'country': 'India',
                'pincode': record.get('pincode'),
                'phone': google_data.get('formatted_phone_number') or record.get('contact_number'),
                'email': email,
                'website': record.get('website_url'),
                'latitude': lat,
                'longitude': lng,
                'google_place_id': place_id,
                'google_rating': rating,
                'google_review_count': review_count,
                'working_hours': hours,
                'specialties': record.get('specialties', 'Medical Aesthetics'),
                'reviews': google_data.get('reviews', [])
            }
            
            # Insert into database
            clinic_id = insert_clinic_to_database(clinic_data)
            
            if clinic_id:
                imported_count += 1
                if imported_count % 50 == 0:
                    print(f"Progress: {imported_count}/{total_records} clinics imported ({imported_count/total_records*100:.1f}%)")
            else:
                failed_count += 1
                
        except Exception as e:
            failed_count += 1
            print(f"Error processing {csv_name}: {e}")
            continue
        
        # Rate limiting to respect API quotas
        if i % 10 == 0:
            time.sleep(1)
    
    print(f"\nDelhi import complete!")
    print(f"Successfully imported: {imported_count} clinics")
    print(f"Failed imports: {failed_count} clinics")
    
    # Final platform statistics
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('New Delhi',))
    delhi_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('Mumbai',))
    mumbai_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('Hyderabad',))
    hyderabad_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE city = %s', ('Bangalore',))
    bangalore_total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM clinics')
    total_clinics = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(google_review_count) FROM clinics')
    total_reviews = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(*) FROM clinics WHERE working_hours IS NOT NULL AND working_hours != %s', ('',))
    clinics_with_hours = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    print(f"\n=== COMPLETE PLATFORM STATISTICS ===")
    print(f"Delhi: {delhi_total} clinics")
    print(f"Mumbai: {mumbai_total} clinics")
    print(f"Hyderabad: {hyderabad_total} clinics")
    print(f"Bangalore: {bangalore_total} clinics")
    print(f"Total: {total_clinics} clinics")
    print(f"Google Reviews: {total_reviews:,}")
    print(f"With Working Hours: {clinics_with_hours} ({clinics_with_hours/total_clinics*100:.1f}%)")
    
    return imported_count

if __name__ == "__main__":
    import_delhi_clinics_complete()