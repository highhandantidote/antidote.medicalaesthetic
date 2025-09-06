#!/usr/bin/env python3
"""
Complete Clinic Data Import System with Google Places API Integration

This script imports all clinic data from the CSV file with authentic Google Places API data
including reviews, ratings, hours, descriptions, and contact information.
"""

import os
import csv
import json
import time
import requests
import psycopg2
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompletClinicImporter:
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
        self.db_url = os.environ.get('DATABASE_URL')
        self.csv_file = 'attached_assets/hyderabad_filtered_clinics.csv - Sheet1_1750429116184.csv'
        self.imported_count = 0
        self.failed_count = 0
        self.batch_size = 10
        
    def get_db_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.db_url)
    
    def clinic_exists(self, conn, place_id):
        """Check if clinic already exists."""
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clinics WHERE google_place_id = %s", (place_id,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    
    def fetch_google_places_data(self, place_id):
        """Fetch comprehensive data from Google Places API."""
        if not self.api_key or not place_id:
            return None
            
        url = 'https://maps.googleapis.com/maps/api/place/details/json'
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,reviews,opening_hours,business_status,types,geometry,photos'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK':
                    return data.get('result', {})
                else:
                    logger.warning(f"Google API error for {place_id}: {data.get('status')}")
            else:
                logger.error(f"HTTP error for {place_id}: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching Google data for {place_id}: {e}")
        
        return None
    
    def parse_opening_hours(self, opening_hours):
        """Parse Google opening hours into readable format."""
        if not opening_hours or not opening_hours.get('weekday_text'):
            return None
        
        # Join weekday text with semicolons
        return '; '.join(opening_hours['weekday_text'])
    
    def extract_specialties_from_types(self, types, clinic_name):
        """Extract medical specialties from Google types and clinic name."""
        specialties = []
        
        # Medical type mappings
        type_mappings = {
            'doctor': 'General Medicine',
            'health': 'Healthcare Services',
            'beauty_salon': 'Aesthetic Services',
            'spa': 'Wellness & Spa Services',
            'hospital': 'Hospital Services',
            'dentist': 'Dental Care',
            'pharmacy': 'Pharmaceutical Services',
            'physiotherapist': 'Physiotherapy'
        }
        
        # Add specialties based on Google types
        for gtype in types:
            if gtype in type_mappings:
                specialties.append(type_mappings[gtype])
        
        # Add specialties based on clinic name keywords
        name_lower = clinic_name.lower()
        specialty_keywords = {
            'Dermatology': ['skin', 'derma', 'dermatology'],
            'Cosmetic Surgery': ['cosmetic', 'plastic', 'aesthetic'],
            'Hair Transplant': ['hair', 'transplant'],
            'Laser Treatment': ['laser'],
            'Anti-aging': ['anti-aging', 'botox', 'filler'],
            'Dental Care': ['dental', 'dentist', 'orthodontic'],
            'Eye Care': ['eye', 'vision', 'ophthalmology'],
            'Weight Management': ['weight', 'obesity', 'bariatric']
        }
        
        for specialty, keywords in specialty_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                specialties.append(specialty)
        
        # Remove duplicates and return
        return list(set(specialties))
    
    def create_clinic_owner_user(self, conn, clinic_name, email=None, phone=None):
        """Create a user account for the clinic owner."""
        cursor = conn.cursor()
        
        # Generate email if not provided
        if not email:
            clean_name = ''.join(c.lower() for c in clinic_name if c.isalnum())
            email = f"{clean_name}@clinic.antidote.com"
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            user_id = existing_user[0]
        else:
            # Create new user
            cursor.execute("""
                INSERT INTO users (name, email, phone_number, password_hash, is_verified, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (
                clinic_name,
                email,
                phone,
                'pbkdf2:sha256:600000$temp$temp',  # Temporary password hash
                True,
                'clinic_owner'
            ))
            user_id = cursor.fetchone()[0]
        
        cursor.close()
        return user_id
    
    def import_google_reviews(self, conn, clinic_id, reviews):
        """Import Google reviews for a clinic."""
        if not reviews:
            return 0
        
        cursor = conn.cursor()
        
        # Delete existing reviews
        cursor.execute("DELETE FROM google_reviews WHERE clinic_id = %s", (clinic_id,))
        
        # Insert new reviews
        imported_reviews = 0
        for review in reviews:
            try:
                cursor.execute("""
                    INSERT INTO google_reviews (
                        clinic_id, author_name, rating, text, 
                        relative_time_description, created_at, is_active
                    ) VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                """, (
                    clinic_id,
                    review.get('author_name', 'Anonymous'),
                    review.get('rating', 5),
                    review.get('text', ''),
                    review.get('relative_time_description', 'Recently'),
                    True
                ))
                imported_reviews += 1
            except Exception as e:
                logger.error(f"Error importing review for clinic {clinic_id}: {e}")
        
        cursor.close()
        return imported_reviews
    
    def import_single_clinic(self, conn, row):
        """Import a single clinic with Google Places data."""
        try:
            # Extract data from CSV row
            clinic_name = row.get('name', '').strip()
            place_id = row.get('google_place_id', '').strip()
            
            if not clinic_name or not place_id:
                logger.warning(f"Missing required data for clinic: {clinic_name}")
                return False
            
            # Check if clinic already exists
            if self.clinic_exists(conn, place_id):
                logger.info(f"Clinic {clinic_name} already exists, skipping")
                return True
            
            # Fetch Google Places data
            google_data = self.fetch_google_places_data(place_id)
            
            cursor = conn.cursor()
            
            # Prepare clinic data with Google Places info
            google_name = google_data.get('name', clinic_name) if google_data else clinic_name
            google_address = google_data.get('formatted_address', '') if google_data else ''
            google_phone = google_data.get('formatted_phone_number', '') if google_data else ''
            google_website = google_data.get('website', '') if google_data else ''
            google_rating = google_data.get('rating', 0) if google_data else 0
            google_review_count = google_data.get('user_ratings_total', 0) if google_data else 0
            
            # Parse location data
            latitude = longitude = None
            if google_data and google_data.get('geometry', {}).get('location'):
                location = google_data['geometry']['location']
                latitude = location.get('lat')
                longitude = location.get('lng')
            
            # Parse opening hours
            working_hours = ''
            if google_data and google_data.get('opening_hours'):
                working_hours = self.parse_opening_hours(google_data['opening_hours'])
            
            # Extract specialties
            specialties = []
            if google_data and google_data.get('types'):
                specialties = self.extract_specialties_from_types(google_data['types'], google_name)
            
            # Generate description
            description = f"{google_name} is a medical aesthetic clinic"
            if specialties:
                description += f" specializing in {', '.join(specialties[:3]).lower()}"
            if google_address:
                # Extract city from address
                if 'Hyderabad' in google_address:
                    description += " located in Hyderabad"
            if google_rating and google_review_count:
                description += f" with a {google_rating}/5 rating based on {google_review_count} Google reviews"
            description += "."
            
            # Create clinic owner user
            owner_user_id = self.create_clinic_owner_user(conn, google_name, phone=google_phone)
            
            # Insert clinic
            cursor.execute("""
                INSERT INTO clinics (
                    name, slug, description, address, city, state, country,
                    phone_number, email, website, latitude, longitude,
                    google_place_id, google_rating, google_review_count,
                    working_hours, specialties, owner_user_id,
                    is_verified, is_approved, is_active, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                ) RETURNING id
            """, (
                google_name,
                google_name.lower().replace(' ', '-').replace('&', 'and'),
                description,
                google_address,
                'Hyderabad',
                'Telangana',
                'India',
                google_phone,
                f"{google_name.lower().replace(' ', '')}@clinic.antidote.com",
                google_website,
                latitude,
                longitude,
                place_id,
                google_rating,
                google_review_count,
                working_hours,
                ', '.join(specialties) if specialties else None,
                owner_user_id,
                True,
                True,
                True
            ))
            
            clinic_id = cursor.fetchone()[0]
            
            # Import Google reviews
            reviews_imported = 0
            if google_data and google_data.get('reviews'):
                reviews_imported = self.import_google_reviews(conn, clinic_id, google_data['reviews'])
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Successfully imported {google_name} (ID: {clinic_id}) with {reviews_imported} reviews")
            return True
            
        except Exception as e:
            logger.error(f"Error importing clinic {clinic_name}: {e}")
            conn.rollback()
            return False
    
    def import_all_clinics(self):
        """Import all clinics from CSV file."""
        logger.info("Starting complete clinic data import...")
        
        if not os.path.exists(self.csv_file):
            logger.error(f"CSV file not found: {self.csv_file}")
            return
        
        conn = self.get_db_connection()
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                batch = []
                for row in csv_reader:
                    batch.append(row)
                    
                    # Process in batches to avoid rate limiting
                    if len(batch) >= self.batch_size:
                        self.process_batch(conn, batch)
                        batch = []
                        
                        # Rate limiting - wait between batches
                        time.sleep(2)
                
                # Process remaining clinics
                if batch:
                    self.process_batch(conn, batch)
        
        finally:
            conn.close()
        
        logger.info(f"Import completed: {self.imported_count} succeeded, {self.failed_count} failed")
    
    def process_batch(self, conn, batch):
        """Process a batch of clinics."""
        logger.info(f"Processing batch of {len(batch)} clinics...")
        
        for row in batch:
            if self.import_single_clinic(conn, row):
                self.imported_count += 1
            else:
                self.failed_count += 1
        
        logger.info(f"Batch completed. Total: {self.imported_count} imported, {self.failed_count} failed")

def main():
    """Main function to run the complete clinic import."""
    importer = CompletClinicImporter()
    importer.import_all_clinics()

if __name__ == "__main__":
    main()