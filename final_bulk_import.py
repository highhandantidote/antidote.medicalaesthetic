#!/usr/bin/env python3
"""
Final bulk import with proper error handling and transaction management.
"""

import os
import csv
import psycopg2
import requests
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_google_data(place_id, api_key):
    """Fetch Google Places data with error handling."""
    if not place_id or not api_key:
        return None
        
    try:
        url = 'https://maps.googleapis.com/maps/api/place/details/json'
        params = {
            'place_id': place_id,
            'key': api_key,
            'fields': 'name,formatted_address,geometry,rating,user_ratings_total,opening_hours,types'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result', {})
        return None
    except Exception as e:
        logger.error(f"Google API error for {place_id}: {e}")
        return None

def import_single_clinic(row, api_key):
    """Import a single clinic with complete error handling."""
    conn = None
    try:
        clinic_name = row['name'].strip()
        if not clinic_name:
            return False, "No clinic name"
            
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Check if clinic exists
        cursor.execute('SELECT id FROM clinics WHERE name = %s', (clinic_name,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Clinic already exists"
        
        # Prepare basic data
        description = "Professional medical clinic providing quality healthcare and aesthetic services."
        working_hours = ""
        google_rating = None
        google_review_count = None
        
        # Fetch Google data if Place ID available
        if row.get('google_place_id'):
            google_data = fetch_google_data(row['google_place_id'], api_key)
            
            if google_data:
                # Extract working hours
                if google_data.get('opening_hours', {}).get('weekday_text'):
                    weekday_hours = {}
                    for day_text in google_data['opening_hours']['weekday_text']:
                        if ':' in day_text:
                            day_name, hours = day_text.split(':', 1)
                            weekday_hours[day_name.strip()] = hours.strip()
                    if weekday_hours:
                        working_hours = '; '.join([f"{day}: {hours}" for day, hours in weekday_hours.items()])
                
                # Generate description from types
                if google_data.get('types'):
                    types = google_data.get('types', [])
                    medical_types = [t for t in types if any(keyword in t.lower() for keyword in ['hospital', 'clinic', 'doctor', 'health', 'medical', 'beauty', 'spa'])]
                    if medical_types:
                        primary_type = medical_types[0].replace('_', ' ').title()
                        description = f"Professional {primary_type.lower()} providing quality healthcare and aesthetic services."
                
                google_rating = google_data.get('rating')
                google_review_count = google_data.get('user_ratings_total')
        
        # Create or get user
        owner_email = row.get('owner_email') or f"{clinic_name.lower().replace(' ', '').replace('-', '').replace('.', '')[:20]}@antidote-temp.com"
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email = %s', (owner_email,))
        user_result = cursor.fetchone()
        
        if user_result:
            owner_user_id = user_result[0]
        else:
            # Create new user
            cursor.execute('''
                INSERT INTO users (email, username, password_hash, created_at, is_active, is_clinic_owner, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (owner_email, owner_email.split('@')[0], 'temp_hash', datetime.now(), True, True, 'clinic_owner'))
            owner_user_id = cursor.fetchone()[0]
        
        # Create slug
        slug = row.get('slug') or clinic_name.lower().replace(' ', '-').replace('.', '').replace(',', '').replace('(', '').replace(')', '').replace('&', 'and')[:50]
        
        # Insert clinic
        cursor.execute('''
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
        ''', (
            clinic_name, slug, description, row.get('address', ''), 
            row.get('city', ''), row.get('state', ''), row.get('pincode'),
            float(row.get('latitude', 0)), float(row.get('longitude', 0)), 
            row.get('contact_number', ''), row.get('email', ''), row.get('website_url', ''),
            row.get('specialties', ''), working_hours, row.get('google_place_id'),
            google_rating, google_review_count, owner_user_id, datetime.now(),
            True, True, 'verified'
        ))
        
        clinic_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, clinic_id
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, str(e)

def main():
    """Main bulk import function."""
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    csv_file = 'attached_assets/hyderabad_filtered_clinics.csv - Sheet1_1750429116184.csv'
    
    imported = 0
    failed = 0
    
    logger.info("Starting bulk clinic import...")
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                success, result = import_single_clinic(row, api_key)
                
                if success:
                    imported += 1
                    logger.info(f"Imported: {row['name']} (ID: {result}) - Total: {imported}")
                else:
                    failed += 1
                    if "already exists" not in str(result):
                        logger.error(f"Failed {row['name']}: {result}")
                
                # Rate limiting for Google API
                if row.get('google_place_id'):
                    time.sleep(0.2)
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error processing row {row_num}: {e}")
                continue
    
    logger.info(f"Bulk import completed: {imported} imported, {failed} failed")

if __name__ == "__main__":
    main()