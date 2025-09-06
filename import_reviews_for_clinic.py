#!/usr/bin/env python3
"""
Import Google reviews for a specific clinic using Place ID.
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
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def fetch_reviews_from_places_api(place_id, api_key):
    """Fetch reviews using Google Places API."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        'place_id': place_id,
        'key': api_key,
        'fields': 'reviews'
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                result = data.get('result', {})
                return result.get('reviews', [])
            else:
                logger.error(f"API error: {data.get('status')}")
                return []
        else:
            logger.error(f"HTTP error: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        return []

def import_reviews_for_clinic(clinic_id, place_id):
    """Import reviews for a specific clinic."""
    logger.info(f"Importing reviews for clinic {clinic_id} with Place ID {place_id}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get API key
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        logger.error("Google API key not found")
        return False
    
    # Fetch reviews
    reviews = fetch_reviews_from_places_api(place_id, api_key)
    
    if not reviews:
        logger.warning("No reviews found for this clinic")
        return False
    
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
            
            # Insert review
            cursor.execute("""
                INSERT INTO google_reviews (
                    clinic_id, author_name, profile_photo_url, rating, 
                    text, time, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                clinic_id, author_name, author_photo_url, rating,
                text, review_date, datetime.now()
            ))
            
            imported_count += 1
            
        except Exception as e:
            logger.error(f"Error importing review: {e}")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"Successfully imported {imported_count} reviews for clinic {clinic_id}")
    return imported_count > 0

def main():
    """Import reviews for clinic 42."""
    clinic_id = 42
    place_id = "ChIJ-525K5mXyzsR5yUDZ9b8ROY"
    
    success = import_reviews_for_clinic(clinic_id, place_id)
    
    if success:
        print("✅ Reviews imported successfully")
    else:
        print("❌ Failed to import reviews")

if __name__ == "__main__":
    main()