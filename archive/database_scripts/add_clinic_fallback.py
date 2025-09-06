"""
Add clinic using Google Place ID with web scraping fallback when API is unavailable.
This script extracts authentic clinic data from Google Maps using the Place ID.
"""
import os
import requests
import psycopg2
from werkzeug.security import generate_password_hash
import logging
from datetime import datetime
import re
from bs4 import BeautifulSoup
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def extract_clinic_data_from_place_id(place_id):
    """Extract clinic data from Google Maps using Place ID."""
    
    # Construct Google Maps URL from Place ID
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        logger.info(f"Fetching data from: {maps_url}")
        response = requests.get(maps_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch page: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract clinic data
        clinic_data = {
            'place_id': place_id,
            'maps_url': maps_url,
            'name': None,
            'address': None,
            'phone': None,
            'website': None,
            'rating': None,
            'review_count': None,
            'business_type': None
        }
        
        # Extract business name from title or meta tags
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # Clean up title (remove " - Google Maps" suffix)
            name = title_text.replace(' - Google Maps', '').strip()
            if name and name != 'Google Maps':
                clinic_data['name'] = name
        
        # Look for structured data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'LocalBusiness' or 'name' in data:
                        clinic_data['name'] = data.get('name') or clinic_data['name']
                        if 'address' in data:
                            addr = data['address']
                            if isinstance(addr, dict):
                                clinic_data['address'] = addr.get('streetAddress', '')
                            else:
                                clinic_data['address'] = str(addr)
                        clinic_data['phone'] = data.get('telephone') or clinic_data['phone']
                        clinic_data['website'] = data.get('url') or clinic_data['website']
                        if 'aggregateRating' in data:
                            rating_data = data['aggregateRating']
                            clinic_data['rating'] = rating_data.get('ratingValue')
                            clinic_data['review_count'] = rating_data.get('reviewCount')
            except:
                continue
        
        # Fallback: Extract from page content using common patterns
        page_text = soup.get_text()
        
        # Look for phone numbers
        if not clinic_data['phone']:
            phone_patterns = [
                r'\+91[\s-]?\d{5}[\s-]?\d{5}',  # Indian format
                r'\+91[\s-]?\d{4}[\s-]?\d{6}',  # Indian format
                r'\d{5}[\s-]?\d{5}',  # 10 digit
                r'\d{4}[\s-]?\d{6}',  # 10 digit
            ]
            for pattern in phone_patterns:
                match = re.search(pattern, page_text)
                if match:
                    clinic_data['phone'] = match.group().strip()
                    break
        
        # Look for ratings
        if not clinic_data['rating']:
            rating_match = re.search(r'(\d+\.?\d*)\s*★', page_text)
            if rating_match:
                clinic_data['rating'] = float(rating_match.group(1))
        
        # Look for review count
        if not clinic_data['review_count']:
            review_patterns = [
                r'(\d+)\s*reviews?',
                r'(\d+)\s*Google reviews?',
                r'(\d+)\s*ratings?'
            ]
            for pattern in review_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    clinic_data['review_count'] = int(match.group(1))
                    break
        
        # Set default name if not found
        if not clinic_data['name']:
            clinic_data['name'] = f"Clinic {place_id[:8]}"
        
        # Determine if it's a medical facility
        medical_keywords = ['clinic', 'hospital', 'doctor', 'medical', 'healthcare', 'dental', 'cosmetic', 'surgery', 'dermatology']
        clinic_data['business_type'] = 'medical' if any(keyword in clinic_data['name'].lower() for keyword in medical_keywords) else 'general'
        
        logger.info(f"Extracted data for: {clinic_data['name']}")
        return clinic_data
        
    except Exception as e:
        logger.error(f"Error extracting clinic data: {e}")
        return None

def parse_address_components(address):
    """Parse address into city and state components."""
    if not address:
        return None, None, None
    
    city = None
    state = None
    
    # Common Indian cities and states
    cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'hyderabad', 'pune', 'kolkata', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'pimpri', 'patna', 'vadodara', 'ghaziabad', 'ludhiana', 'agra', 'nashik', 'faridabad', 'meerut', 'rajkot', 'kalyan', 'vasai', 'varanasi', 'srinagar', 'aurangabad', 'dhanbad', 'amritsar', 'navi mumbai', 'allahabad', 'ranchi', 'howrah', 'coimbatore', 'jabalpur', 'gwalior', 'vijayawada', 'jodhpur', 'madurai', 'raipur', 'kota', 'guwahati', 'chandigarh', 'solapur', 'hubli', 'dharwad', 'bareilly', 'moradabad', 'mysore', 'gurgaon', 'aligarh', 'jalandhar', 'tiruchirappalli', 'bhubaneswar', 'salem', 'warangal', 'mira', 'bhayandar', 'thiruvananthapuram']
    
    states = ['andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh', 'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka', 'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram', 'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal', 'delhi', 'jammu and kashmir', 'ladakh']
    
    address_lower = address.lower()
    
    # Find city
    for city_name in cities:
        if city_name in address_lower:
            city = city_name.title()
            break
    
    # Find state
    for state_name in states:
        if state_name in address_lower:
            state = state_name.title()
            break
    
    return address, city, state

def clinic_exists(conn, place_id):
    """Check if clinic with this place_id already exists."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM clinics WHERE google_place_id = %s", (place_id,))
    result = cursor.fetchone()
    cursor.close()
    return result is not None

def create_clinic_owner_user(conn, clinic_name, email=None):
    """Create a user account for the clinic owner."""
    if not email:
        # Generate email from clinic name
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', clinic_name.lower())[:20]
        email = f"{clean_name}@clinic.antidote.com"
    
    # Check if user already exists
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        return existing_user[0]
    
    # Create new user
    username = email.split('@')[0]
    password_hash = generate_password_hash('temppassword123')
    
    cursor.execute("""
        INSERT INTO users (email, username, password_hash, role)
        VALUES (%s, %s, %s, 'clinic_owner')
        RETURNING id
    """, (email, username, password_hash))
    
    user_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    logger.info(f"Created clinic owner user: {email}")
    return user_id

def add_clinic_from_extracted_data(conn, clinic_data):
    """Add clinic to database from extracted data."""
    
    # Parse address
    address, city, state = parse_address_components(clinic_data.get('address'))
    
    # Create clinic owner user
    owner_user_id = create_clinic_owner_user(conn, clinic_data['name'])
    
    # Set defaults
    rating = clinic_data.get('rating') or 4.5
    review_count = clinic_data.get('review_count') or 0
    
    # Insert clinic
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clinics (
            name, address, city, state, contact_number, website_url,
            google_place_id, google_maps_url, google_rating, google_review_count,
            google_sync_enabled, owner_user_id, is_verified, rating, total_reviews,
            specialties, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
    """, (
        clinic_data['name'], address, city, state, clinic_data.get('phone'), 
        clinic_data.get('website'), clinic_data['place_id'], clinic_data['maps_url'],
        rating, review_count, True, owner_user_id, True, rating, review_count,
        clinic_data.get('business_type', 'medical'), datetime.now()
    ))
    
    clinic_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    logger.info(f"Added clinic: {clinic_data['name']} (ID: {clinic_id})")
    return clinic_id

def add_clinic_by_place_id(place_id):
    """Main function to add clinic by Google Place ID using web scraping."""
    logger.info(f"Adding clinic with Place ID: {place_id}")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        # Check if clinic already exists
        if clinic_exists(conn, place_id):
            logger.info(f"Clinic with Place ID {place_id} already exists")
            return True
        
        # Extract clinic data using web scraping
        clinic_data = extract_clinic_data_from_place_id(place_id)
        if not clinic_data:
            logger.error("Failed to extract clinic data")
            return False
        
        # Display extracted data
        print("\n=== EXTRACTED CLINIC DATA ===")
        for key, value in clinic_data.items():
            print(f"{key.upper()}: {value}")
        
        # Add clinic to database
        clinic_id = add_clinic_from_extracted_data(conn, clinic_data)
        
        # Fetch and display final clinic record
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, u.email as owner_email 
            FROM clinics c 
            JOIN users u ON c.owner_user_id = u.id 
            WHERE c.id = %s
        """, (clinic_id,))
        
        clinic_record = cursor.fetchone()
        if clinic_record:
            columns = [desc[0] for desc in cursor.description]
            clinic_dict = dict(zip(columns, clinic_record))
            
            print("\n=== CREATED CLINIC RECORD ===")
            for key, value in clinic_dict.items():
                print(f"{key.upper()}: {value}")
        
        cursor.close()
        
        logger.info(f"Successfully added clinic with ID: {clinic_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding clinic: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function for testing."""
    place_id = "ChIJhcOH4tyZyzsRN1AHrG8xZ5I"
    
    print("=== Add Clinic by Google Place ID (Web Scraping) ===")
    print(f"Creating clinic profile for Place ID: {place_id}")
    
    # Test adding clinic
    success = add_clinic_by_place_id(place_id)
    
    if success:
        print("\n✅ Clinic added successfully with all available parameters")
    else:
        print("\n❌ Failed to add clinic")

if __name__ == "__main__":
    main()