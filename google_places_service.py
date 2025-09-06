"""
Google Places API service for fetching authentic clinic reviews.
Integrates with Google My Business to sync real reviews automatically.
"""
import requests
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from models import db, Clinic, GoogleReview
import logging

logger = logging.getLogger(__name__)

class GooglePlacesService:
    """Service for interacting with Google Places API."""
    
    def __init__(self):
        self.api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
        self.base_url = 'https://maps.googleapis.com/maps/api/place'
    
    def extract_place_id_from_url(self, google_url: str) -> Optional[str]:
        """
        Extract Place ID from various Google URL formats.
        Supports:
        - https://g.co/kgs/3mX75vm
        - https://maps.google.com/...
        - Direct Place ID input
        """
        if not google_url:
            return None
            
        # If it's already a Place ID (alphanumeric with underscores)
        if re.match(r'^[A-Za-z0-9_-]+$', google_url) and len(google_url) > 20:
            return google_url
            
        try:
            # Handle shortened g.co URLs by following redirects
            if 'g.co/kgs/' in google_url or 'goo.gl' in google_url:
                response = requests.get(google_url, allow_redirects=True, timeout=10)
                google_url = response.url
                
            # Extract from various Google Maps URL formats
            patterns = [
                r'place/[^/]+/([A-Za-z0-9_-]+)',
                r'data=.*!1s([A-Za-z0-9_-]+)',
                r'cid=(\d+)',
                r'!12m1!1s([A-Za-z0-9_-]+)',
                r'kgmid=([^&]+)',  # Handle Google Knowledge Graph IDs
                r'place_id=([A-Za-z0-9_-]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, google_url)
                if match:
                    extracted_id = match.group(1)
                    # If it's a kgmid, we need to use it directly with Places API
                    if pattern.startswith('kgmid'):
                        # Use the business name from the URL for text search
                        business_name_match = re.search(r'q=([^&]+)', google_url)
                        if business_name_match:
                            business_name = business_name_match.group(1).replace('+', ' ')
                            return self._find_place_id_by_query(business_name)
                    else:
                        return extracted_id
                    
            # Try to find Place ID using Find Place API with the full URL
            return self._find_place_id_by_query(google_url)
            
        except Exception as e:
            logger.error(f"Error extracting Place ID from URL {google_url}: {e}")
            return None
    
    def _find_place_id_by_query(self, query: str) -> Optional[str]:
        """Find Place ID using text search."""
        if not self.api_key:
            return None
            
        # Clean up the query - decode URL encoding and remove extra parameters
        import urllib.parse
        decoded_query = urllib.parse.unquote(query)
        
        # If it's a long URL, try to extract just the business name
        if 'google.com' in decoded_query:
            business_name_match = re.search(r'q=([^&]+)', decoded_query)
            if business_name_match:
                decoded_query = business_name_match.group(1).replace('+', ' ')
        
        url = f"{self.base_url}/findplacefromtext/json"
        params = {
            'input': decoded_query,
            'inputtype': 'textquery',
            'fields': 'place_id',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('candidates'):
                return data['candidates'][0]['place_id']
            elif data.get('status') == 'ZERO_RESULTS':
                logger.info(f"No place found for query: {decoded_query}")
                return None
            else:
                logger.error(f"Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error finding Place ID by query: {e}")
            
        return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Fetch place details including reviews from Google Places API.
        Returns place data with reviews, rating, and contact info.
        """
        if not self.api_key:
            logger.error("Google Places API key not configured")
            return None
            
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,rating,user_ratings_total,reviews,formatted_address,formatted_phone_number,website,opening_hours,geometry',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.error(f"Google Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                return None
                
            return data.get('result')
            
        except Exception as e:
            logger.error(f"Error fetching place details for {place_id}: {e}")
            return None
    
    def sync_clinic_reviews(self, clinic_id: int) -> Dict[str, any]:
        """
        Sync Google reviews for a specific clinic.
        Returns sync results with counts and status.
        """
        clinic = Clinic.query.get(clinic_id)
        if not clinic:
            return {'success': False, 'error': 'Clinic not found'}
            
        if not clinic.google_place_id:
            return {'success': False, 'error': 'Google Place ID not configured'}
            
        # Fetch place details from Google
        place_data = self.get_place_details(clinic.google_place_id)
        if not place_data:
            return {'success': False, 'error': 'Failed to fetch data from Google Places API'}
        
        try:
            # Update clinic's Google ratings
            clinic.google_rating = place_data.get('rating')
            clinic.google_review_count = place_data.get('user_ratings_total', 0)
            clinic.last_review_sync = datetime.utcnow()
            
            # Process reviews
            reviews = place_data.get('reviews', [])
            new_reviews = 0
            updated_reviews = 0
            
            for review_data in reviews:
                result = self._process_review(clinic_id, review_data)
                if result == 'new':
                    new_reviews += 1
                elif result == 'updated':
                    updated_reviews += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'new_reviews': new_reviews,
                'updated_reviews': updated_reviews,
                'total_reviews': len(reviews),
                'google_rating': clinic.google_rating,
                'google_review_count': clinic.google_review_count
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing reviews for clinic {clinic_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _process_review(self, clinic_id: int, review_data: Dict) -> str:
        """
        Process a single review from Google Places API.
        Returns 'new', 'updated', or 'skipped'.
        """
        # Generate unique review ID from Google data
        google_review_id = f"{review_data.get('author_name', 'unknown')}_{review_data.get('time', 0)}"
        
        # Check if review already exists
        existing_review = GoogleReview.query.filter_by(
            clinic_id=clinic_id,
            google_review_id=google_review_id
        ).first()
        
        # Convert Google timestamp to datetime
        review_time = datetime.fromtimestamp(review_data.get('time', 0), tz=timezone.utc)
        
        if existing_review:
            # Update existing review if content changed
            if (existing_review.text != review_data.get('text', '') or 
                existing_review.rating != review_data.get('rating', 0)):
                
                existing_review.text = review_data.get('text', '')
                existing_review.rating = review_data.get('rating', 0)
                existing_review.updated_at = datetime.utcnow()
                existing_review.original_data = review_data
                
                return 'updated'
            return 'skipped'
        
        # Create new review
        new_review = GoogleReview(
            clinic_id=clinic_id,
            google_review_id=google_review_id,
            author_name=review_data.get('author_name', 'Anonymous'),
            author_url=review_data.get('author_url'),
            profile_photo_url=review_data.get('profile_photo_url'),
            rating=review_data.get('rating', 0),
            text=review_data.get('text', ''),
            language=review_data.get('language'),
            time=review_time,
            relative_time_description=review_data.get('relative_time_description'),
            original_data=review_data
        )
        
        db.session.add(new_review)
        return 'new'
    
    def validate_google_url(self, url: str) -> Dict[str, any]:
        """
        Validate a Google Business URL and extract basic info.
        Returns validation result with place info if valid.
        """
        place_id = self.extract_place_id_from_url(url)
        if not place_id:
            return {'valid': False, 'error': 'Could not extract Place ID from URL'}
        
        # Test API connection with basic place info
        place_data = self.get_place_details(place_id)
        if not place_data:
            return {'valid': False, 'error': 'Could not fetch place data from Google'}
        
        # Extract location coordinates
        geometry = place_data.get('geometry', {})
        location = geometry.get('location', {})
        
        return {
            'valid': True,
            'place_id': place_id,
            'name': place_data.get('name'),
            'rating': place_data.get('rating'),
            'review_count': place_data.get('user_ratings_total', 0),
            'address': place_data.get('formatted_address'),
            'latitude': location.get('lat'),
            'longitude': location.get('lng')
        }
    
    def extract_location_from_url(self, url: str) -> Dict[str, any]:
        """
        Extract complete location information from Google My Business URL.
        Returns location data including coordinates for mapping.
        """
        place_id = self.extract_place_id_from_url(url)
        if not place_id:
            return {'success': False, 'error': 'Could not extract Place ID from URL'}
        
        # Get place details from Google
        place_data = self.get_place_details(place_id)
        if not place_data:
            return {'success': False, 'error': 'Could not fetch place data from Google Places API'}
        
        # Extract location coordinates
        geometry = place_data.get('geometry', {})
        location = geometry.get('location', {})
        
        if not location.get('lat') or not location.get('lng'):
            return {'success': False, 'error': 'Location coordinates not available for this place'}
        
        return {
            'success': True,
            'location': {
                'name': place_data.get('name'),
                'address': place_data.get('formatted_address'),
                'latitude': location.get('lat'),
                'longitude': location.get('lng'),
                'place_id': place_id,
                'rating': place_data.get('rating'),
                'phone': place_data.get('formatted_phone_number'),
                'website': place_data.get('website')
            }
        }

# Global service instance
google_places_service = GooglePlacesService()