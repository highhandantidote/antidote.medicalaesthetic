#!/usr/bin/env python3
"""
Complete import of all clinics from CSV with Google Places API data.
Processes all remaining clinics efficiently with rate limiting and error handling.
"""

import os
import csv
import requests
import psycopg2
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FullClinicImporter:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
        self.db_url = os.environ.get('DATABASE_URL')
        self.csv_file = 'attached_assets/hyderabad_filtered_clinics.csv - Sheet1_1750429116184.csv'
        self.imported_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        
    def get_db_connection(self):
        return psycopg2.connect(self.db_url)
    
    def clinic_exists(self, conn, place_id):
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clinics WHERE google_place_id = %s", (place_id,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    
    def fetch_google_data(self, place_id):
        """Fetch Google Places data with error handling."""
        url = 'https://maps.googleapis.com/maps/api/place/details/json'
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,reviews,opening_hours,geometry,business_status'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK':
                    return data.get('result', {})
                elif data.get('status') == 'OVER_QUERY_LIMIT':
                    logger.warning("API rate limit reached, waiting...")
                    time.sleep(10)
                    return None
        except Exception as e:
            logger.error(f"Error fetching Google data for {place_id}: {e}")
        return None
    
    def create_user(self, conn, clinic_name, email):
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
    
    def clean_email(self, clinic_name):
        """Generate clean email address."""
        clean_name = ''.join(c.lower() for c in clinic_name[:30] if c.isalnum())
        return f"{clean_name}@clinic.antidote.com"
    
    def import_reviews(self, conn, clinic_id, reviews):
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
    
    def import_single_clinic(self, conn, row):
        """Import a single clinic with comprehensive error handling."""
        clinic_name = row.get('name', '').strip()
        place_id = row.get('google_place_id', '').strip()
        
        if not clinic_name or not place_id:
            return False
        
        if self.clinic_exists(conn, place_id):
            self.skipped_count += 1
            return True
        
        # Fetch Google data
        google_data = self.fetch_google_data(place_id)
        if not google_data:
            logger.warning(f"No Google data for {clinic_name}")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Extract Google data
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
            
            # Use CSV specialties or generate from name
            specialties = row.get('specialties', '')
            if not specialties:
                name_lower = google_name.lower()
                if 'skin' in name_lower or 'derma' in name_lower:
                    specialties = 'Dermatology, Skin Care'
                elif 'plastic' in name_lower or 'cosmetic' in name_lower:
                    specialties = 'Plastic Surgery, Cosmetic Surgery'
                elif 'dental' in name_lower:
                    specialties = 'Dental Care, Orthodontics'
                elif 'hair' in name_lower:
                    specialties = 'Hair Transplant, Hair Care'
                else:
                    specialties = 'Medical Aesthetics, General Healthcare'
            
            # Generate clean email
            email = self.clean_email(google_name)
            
            # Create user
            user_id = self.create_user(conn, google_name, email)
            
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
                google_name.lower().replace(' ', '-').replace('&', 'and')[:50],
                f"{google_name} is a medical aesthetic clinic in Hyderabad with {rating}/5 rating based on {review_count} Google reviews.",
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
            review_count_imported = 0
            if google_data.get('reviews'):
                review_count_imported = self.import_reviews(conn, clinic_id, google_data['reviews'])
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Imported {google_name} (ID: {clinic_id}) with {review_count_imported} reviews")
            self.imported_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Error importing {clinic_name}: {e}")
            conn.rollback()
            self.failed_count += 1
            return False
    
    def import_all_clinics(self):
        """Import all clinics from CSV file."""
        logger.info("Starting complete clinic import...")
        
        if not os.path.exists(self.csv_file):
            logger.error(f"CSV file not found: {self.csv_file}")
            return
        
        conn = self.get_db_connection()
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for i, row in enumerate(csv_reader):
                    # Process clinic
                    self.import_single_clinic(conn, row)
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                    # Progress update every 25 clinics
                    if (i + 1) % 25 == 0:
                        logger.info(f"Processed {i + 1} clinics: {self.imported_count} imported, {self.skipped_count} skipped, {self.failed_count} failed")
                    
                    # Pause every 100 clinics to avoid rate limits
                    if (i + 1) % 100 == 0:
                        logger.info("Pausing for rate limit compliance...")
                        time.sleep(30)
        
        finally:
            conn.close()
        
        logger.info(f"Import completed: {self.imported_count} imported, {self.skipped_count} skipped, {self.failed_count} failed")

def main():
    importer = FullClinicImporter()
    importer.import_all_clinics()

if __name__ == "__main__":
    main()