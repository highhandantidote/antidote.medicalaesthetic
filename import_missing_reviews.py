"""
Import missing Google reviews for clinics that have review counts but no actual reviews in the database.
This script will fetch and import Google reviews for clinics to populate the "What Our Patients Have to Say" section.
"""
import os
import requests
import psycopg2
import time
import json
from datetime import datetime

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def get_google_api_key():
    """Get Google API key from environment."""
    return os.environ.get('GOOGLE_PLACES_API_KEY')

def fetch_place_reviews(place_id, api_key):
    """Fetch reviews for a place from Google Places API."""
    try:
        response = requests.get(
            f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}&fields=reviews',
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result', {}).get('reviews', [])
        return []
    except Exception as e:
        print(f"Error fetching reviews for place {place_id}: {e}")
        return []

def import_reviews_for_clinic(conn, clinic_id, place_id, api_key):
    """Import reviews for a specific clinic."""
    reviews = fetch_place_reviews(place_id, api_key)
    
    if not reviews:
        return 0
    
    cursor = conn.cursor()
    imported_count = 0
    
    for review in reviews:
        try:
            # Extract review data
            author_name = review.get('author_name', 'Anonymous')
            rating = review.get('rating', 5)
            text = review.get('text', '')
            time_created = review.get('time', int(time.time()))
            
            # Convert timestamp to datetime
            review_date = datetime.fromtimestamp(time_created)
            
            # Check if review already exists
            cursor.execute(
                "SELECT id FROM google_reviews WHERE clinic_id = %s AND author_name = %s AND rating = %s AND text = %s",
                (clinic_id, author_name, rating, text)
            )
            
            if cursor.fetchone():
                continue  # Skip if review already exists
            
            # Insert review
            cursor.execute("""
                INSERT INTO google_reviews (
                    clinic_id, author_name, rating, text, 
                    time, created_at
                ) VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                clinic_id, author_name, rating, text,
                review_date
            ))
            
            imported_count += 1
            
        except Exception as e:
            print(f"Error importing review: {e}")
            continue
    
    conn.commit()
    cursor.close()
    return imported_count

def import_missing_reviews():
    """Import missing reviews for clinics that have review counts but no actual reviews."""
    api_key = get_google_api_key()
    if not api_key:
        print("Error: GOOGLE_PLACES_API_KEY not found in environment variables")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get clinics with review counts but no actual reviews in database
    cursor.execute("""
        SELECT c.id, c.name, c.google_place_id, c.google_review_count
        FROM clinics c
        LEFT JOIN google_reviews gr ON c.id = gr.clinic_id
        WHERE c.google_review_count > 0 
        AND c.google_place_id IS NOT NULL 
        AND c.google_place_id != ''
        AND gr.clinic_id IS NULL
        ORDER BY c.google_review_count DESC
        LIMIT 100
    """)
    
    clinics_missing_reviews = cursor.fetchall()
    cursor.close()
    
    print(f"Found {len(clinics_missing_reviews)} clinics missing reviews")
    
    total_imported = 0
    processed = 0
    
    for clinic_id, clinic_name, place_id, review_count in clinics_missing_reviews:
        try:
            print(f"Processing: {clinic_name} ({review_count} reviews claimed)")
            
            imported = import_reviews_for_clinic(conn, clinic_id, place_id, api_key)
            total_imported += imported
            processed += 1
            
            print(f"  → Imported {imported} reviews")
            
            # Pause to respect API limits
            time.sleep(0.1)
            
            if processed % 10 == 0:
                print(f"Progress: {processed}/{len(clinics_missing_reviews)} clinics processed, {total_imported} total reviews imported")
                
        except Exception as e:
            print(f"Error processing clinic {clinic_name}: {e}")
            continue
    
    conn.close()
    
    print(f"\n=== REVIEW IMPORT COMPLETED ===")
    print(f"Clinics processed: {processed}")
    print(f"Total reviews imported: {total_imported}")
    
    return total_imported

if __name__ == "__main__":
    import_missing_reviews()