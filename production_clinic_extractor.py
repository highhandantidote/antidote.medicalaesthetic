"""
Production-ready clinic data extractor for Google Business URLs.
This is the main extraction engine for comprehensive clinic data processing.
"""

import os
import re
import time
import logging
import requests
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup, Tag
import psycopg2
from psycopg2.extras import RealDictCursor
import trafilatura
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClinicDataExtractor:
    """Production-ready clinic data extractor for Google Business URLs."""
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_db_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    def resolve_google_url(self, url: str) -> str:
        """Resolve Google Business URL to get the actual Maps URL."""
        try:
            # Handle different Google URL formats
            if 'g.co/kgs/' in url:
                # Knowledge Graph URLs - extract KG ID and convert to search
                kg_id = url.split('/')[-1]
                
                # Try different approaches to get business info
                search_urls = [
                    f"https://www.google.com/search?kgmid={kg_id}",
                    f"https://www.google.com/search?q={kg_id}",
                    url
                ]
                
                for search_url in search_urls:
                    try:
                        response = self.session.get(search_url, allow_redirects=True, timeout=15)
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for business information in the knowledge panel
                        # Try to find Maps links
                        maps_links = soup.find_all('a', href=re.compile(r'maps\.google\.com|google\.com/maps'))
                        for link in maps_links:
                            if hasattr(link, 'get'):
                                href = link.get('href', '')
                                if href and ('place' in href or 'search' in href):
                                    return href
                        
                        # If we found business info but no maps link, use the search URL
                        business_indicators = soup.find_all(text=re.compile(r'clinic|hospital|skin|hair|dermatology', re.IGNORECASE))
                        if business_indicators:
                            return search_url
                            
                    except Exception as e:
                        logger.warning(f"Failed to resolve {search_url}: {e}")
                        continue
            
            return url
            
        except Exception as e:
            logger.error(f"Error resolving URL {url}: {e}")
            return url
    
    def extract_place_id_from_url(self, url: str) -> Optional[str]:
        """Extract place ID from Google Maps URL."""
        try:
            # Try different place ID extraction methods
            patterns = [
                r'place_id:([A-Za-z0-9_-]+)',
                r'data=([^&]+)',
                r'cid=(\d+)',
                r'/place/([^/]+)/@'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting place ID from {url}: {e}")
            return None
    
    def extract_clinic_data_from_url(self, url: str) -> Dict:
        """Extract comprehensive clinic data from Google Business URL."""
        try:
            logger.info(f"Processing URL: {url}")
            
            # Resolve the URL first
            resolved_url = self.resolve_google_url(url)
            logger.info(f"Resolved URL: {resolved_url}")
            
            # Fetch the page content
            response = self.session.get(resolved_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialize clinic data
            clinic_data = {
                'name': None,
                'address': None,
                'phone_number': None,
                'website': None,
                'rating': None,
                'review_count': None,
                'business_hours': None,
                'latitude': None,
                'longitude': None,
                'place_id': None,
                'google_maps_url': resolved_url,
                'specialties': [],
                'description': None
            }
            
            # Extract place ID
            clinic_data['place_id'] = self.extract_place_id_from_url(resolved_url)
            
            # Extract business name
            name_selectors = [
                'h1[data-attrid="title"]',
                '.SPZz6b h1',
                '[data-attrid="title"]',
                'h1',
                '.x3AX1-LfntMc-header-title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    clinic_data['name'] = name_elem.get_text().strip()
                    break
            
            # Extract rating and review count
            rating_patterns = [
                r'(\d+\.?\d*)\s*★',
                r'(\d+\.?\d*)\s*stars?',
                r'Rating:\s*(\d+\.?\d*)'
            ]
            
            page_text = soup.get_text()
            for pattern in rating_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        clinic_data['rating'] = float(match.group(1))
                        break
                    except ValueError:
                        continue
            
            # Extract review count
            review_patterns = [
                r'(\d+(?:,\d+)*)\s*reviews?',
                r'(\d+(?:,\d+)*)\s*ratings?'
            ]
            
            for pattern in review_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        review_text = match.group(1).replace(',', '')
                        clinic_data['review_count'] = int(review_text)
                        break
                    except ValueError:
                        continue
            
            # Extract address
            address_selectors = [
                '[data-attrid="kc:/location/location:address"]',
                '.LrzXr',
                '[data-attrid="address"]'
            ]
            
            for selector in address_selectors:
                addr_elem = soup.select_one(selector)
                if addr_elem:
                    clinic_data['address'] = addr_elem.get_text().strip()
                    break
            
            # Extract phone number
            phone_patterns = [
                r'\+91[\s-]?[0-9]{5}[\s-]?[0-9]{5}',
                r'\+91[\s-]?[0-9]{10}',
                r'[0-9]{10}',
                r'\([0-9]{3}\)[\s-]?[0-9]{3}[\s-]?[0-9]{4}'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, page_text)
                if match:
                    clinic_data['phone_number'] = match.group(0).strip()
                    break
            
            # Extract website
            website_links = soup.find_all('a', href=re.compile(r'^https?://(?!.*google\.com|.*maps\.)'))
            for link in website_links:
                href = link.get('href', '')
                if href and not any(domain in href for domain in ['google.com', 'maps.', 'facebook.com', 'instagram.com']):
                    clinic_data['website'] = href
                    break
            
            # Extract coordinates from URL or script tags
            coord_patterns = [
                r'@(-?\d+\.?\d*),(-?\d+\.?\d*)',
                r'center=(-?\d+\.?\d*),(-?\d+\.?\d*)',
                r'lat.*?(-?\d+\.?\d*).*?lng.*?(-?\d+\.?\d*)'
            ]
            
            for pattern in coord_patterns:
                match = re.search(pattern, resolved_url + page_text)
                if match:
                    try:
                        clinic_data['latitude'] = float(match.group(1))
                        clinic_data['longitude'] = float(match.group(2))
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Extract specialties based on business name and content
            specialty_keywords = {
                'Dermatology': ['skin', 'dermatology', 'dermatologist'],
                'Hair Transplant': ['hair', 'transplant', 'restoration'],
                'Plastic Surgery': ['plastic', 'surgery', 'cosmetic'],
                'Laser Treatment': ['laser', 'treatment'],
                'Anti-Aging': ['anti-aging', 'botox', 'filler'],
                'Aesthetic Medicine': ['aesthetic', 'beauty', 'cosmetic']
            }
            
            content_lower = (clinic_data.get('name', '') + ' ' + page_text).lower()
            for specialty, keywords in specialty_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    clinic_data['specialties'].append(specialty)
            
            # Generate description
            if clinic_data['name']:
                desc_parts = [f"{clinic_data['name']} is a"]
                if clinic_data['specialties']:
                    desc_parts.append(f"specialized {', '.join(clinic_data['specialties']).lower()} clinic")
                else:
                    desc_parts.append("medical aesthetic clinic")
                
                if clinic_data['address']:
                    # Extract city from address
                    city_patterns = [
                        r'\b(Mumbai|Delhi|Bangalore|Hyderabad|Chennai|Kolkata|Pune|Ahmedabad|Jaipur|Lucknow)\b'
                    ]
                    for pattern in city_patterns:
                        match = re.search(pattern, clinic_data['address'], re.IGNORECASE)
                        if match:
                            desc_parts.append(f"located in {match.group(1)}")
                            break
                
                if clinic_data['rating'] and clinic_data['review_count']:
                    desc_parts.append(f"with a rating of {clinic_data['rating']}/5 based on {clinic_data['review_count']} reviews")
                
                clinic_data['description'] = ' '.join(desc_parts) + '.'
            
            logger.info(f"Extracted data for: {clinic_data.get('name', 'Unknown')}")
            return clinic_data
            
        except Exception as e:
            logger.error(f"Error extracting data from {url}: {e}")
            return {}
    
    def update_clinic_in_database(self, clinic_id: int, clinic_data: Dict) -> bool:
        """Update existing clinic with extracted data."""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Prepare update fields
            update_fields = []
            update_values = []
            
            field_mappings = {
                'name': 'name',
                'address': 'address', 
                'phone_number': 'contact_number',
                'website': 'website',
                'rating': 'google_rating',
                'review_count': 'google_review_count',
                'latitude': 'latitude',
                'longitude': 'longitude',
                'place_id': 'google_place_id',
                'google_maps_url': 'google_maps_url',
                'description': 'description'
            }
            
            for data_key, db_field in field_mappings.items():
                if clinic_data.get(data_key) is not None:
                    update_fields.append(f"{db_field} = %s")
                    update_values.append(clinic_data[data_key])
            
            # Handle specialties as array
            if clinic_data.get('specialties'):
                update_fields.append("specialties = %s")
                update_values.append(clinic_data['specialties'])
            
            # Add Google sync fields
            if clinic_data.get('rating') or clinic_data.get('review_count'):
                update_fields.append("google_sync_enabled = %s")
                update_values.append(True)
                update_fields.append("last_review_sync = NOW()")
            
            # Update timestamp
            update_fields.append("updated_at = NOW()")
            
            if update_fields:
                update_values.append(clinic_id)
                
                query = f"""
                UPDATE clinics 
                SET {', '.join(update_fields)}
                WHERE id = %s
                """
                
                cursor.execute(query, update_values)
                conn.commit()
                
                logger.info(f"Successfully updated clinic ID {clinic_id}")
                return True
            
        except Exception as e:
            logger.error(f"Error updating clinic {clinic_id}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def process_single_url(self, url: str, clinic_id: Optional[int] = None) -> Dict:
        """Process a single Google Business URL."""
        try:
            # Extract clinic data
            clinic_data = self.extract_clinic_data_from_url(url)
            
            if not clinic_data:
                return {'success': False, 'error': 'Failed to extract clinic data'}
            
            # Update existing clinic if clinic_id provided
            if clinic_id:
                success = self.update_clinic_in_database(clinic_id, clinic_data)
                return {
                    'success': success,
                    'clinic_id': clinic_id,
                    'data': clinic_data
                }
            
            return {
                'success': True,
                'data': clinic_data
            }
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_bulk_urls(self, urls: List[str], delay: float = 1.0) -> Dict:
        """Process multiple Google Business URLs in bulk."""
        results = {
            'total': len(urls),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Processing {i+1}/{len(urls)}: {url}")
                
                result = self.process_single_url(url)
                
                if result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"URL {url}: {result.get('error', 'Unknown error')}")
                
                # Rate limiting
                if delay > 0 and i < len(urls) - 1:
                    time.sleep(delay)
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"URL {url}: {str(e)}")
                logger.error(f"Error processing {url}: {e}")
        
        return results

def main():
    """Main function for testing the extractor."""
    extractor = ClinicDataExtractor()
    
    # Test URL
    test_url = "https://g.co/kgs/NjXr798"
    
    print(f"Testing clinic data extraction for: {test_url}")
    result = extractor.process_single_url(test_url, clinic_id=36)
    
    print(f"Result: {result}")

if __name__ == "__main__":
    main()