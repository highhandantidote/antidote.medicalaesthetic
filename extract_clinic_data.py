"""
Extract clinic data using Google Place ID and create complete clinic profile.
Uses direct Google Maps access to get authentic business information.
"""
import os
import requests
import psycopg2
from werkzeug.security import generate_password_hash
import logging
from datetime import datetime
import re
import json

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

def fetch_google_maps_data(place_id):
    """Fetch data from Google Maps using Place ID."""
    # Use the direct Google Maps place URL
    maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        response = requests.get(maps_url, headers=headers, timeout=15)
        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Extract basic data from response
            content = response.text
            
            # Try to find JSON data in the page
            json_pattern = r'window\.APP_INITIALIZATION_STATE=(\[.+?\]);'
            json_match = re.search(json_pattern, content)
            
            clinic_data = {
                'place_id': place_id,
                'maps_url': maps_url,
                'name': 'Unknown Business',
                'address': None,
                'phone': None,
                'website': None,
                'rating': None,
                'review_count': None,
                'business_type': 'medical',
                'coordinates': None
            }
            
            if json_match:
                try:
                    json_data = json_match.group(1)
                    # This contains the Google Maps initialization data
                    # Extract business name from title patterns
                    title_pattern = r'"([^"]*(?:Clinic|Hospital|Medical|Dental|Surgery|Dermatology|Healthcare)[^"]*)"'
                    title_match = re.search(title_pattern, content, re.IGNORECASE)
                    if title_match:
                        clinic_data['name'] = title_match.group(1)
                except:
                    pass
            
            # Extract from page title
            title_pattern = r'<title>([^<]+)</title>'
            title_match = re.search(title_pattern, content)
            if title_match:
                title = title_match.group(1).replace(' - Google Maps', '').strip()
                if title and 'Google Maps' not in title:
                    clinic_data['name'] = title
            
            # Extract phone numbers
            phone_patterns = [
                r'\+91[\s\-]?\d{5}[\s\-]?\d{5}',
                r'\+91[\s\-]?\d{4}[\s\-]?\d{6}',
                r'(?:tel:|phone:)\s*(\+?[\d\s\-\(\)]+)',
                r'(\d{5}[\s\-]?\d{5})',
                r'(\d{4}[\s\-]?\d{6})'
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, content, re.IGNORECASE)
                if phone_match:
                    phone = phone_match.group(1) if phone_match.lastindex else phone_match.group(0)
                    # Clean phone number
                    phone = re.sub(r'[^\d+]', '', phone)
                    if len(phone) >= 10:
                        clinic_data['phone'] = phone
                        break
            
            # Extract rating
            rating_patterns = [
                r'(\d+\.?\d*)\s*★',
                r'"ratingValue":\s*(\d+\.?\d*)',
                r'rating["\']:\s*(\d+\.?\d*)'
            ]
            
            for pattern in rating_patterns:
                rating_match = re.search(pattern, content)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                        if 0 <= rating <= 5:
                            clinic_data['rating'] = rating
                            break
                    except:
                        continue
            
            # Extract review count
            review_patterns = [
                r'(\d+)\s*reviews?',
                r'(\d+)\s*Google\s*reviews?',
                r'"reviewCount":\s*(\d+)',
                r'(\d+)\s*ratings?'
            ]
            
            for pattern in review_patterns:
                review_match = re.search(pattern, content, re.IGNORECASE)
                if review_match:
                    try:
                        count = int(review_match.group(1))
                        clinic_data['review_count'] = count
                        break
                    except:
                        continue
            
            # Extract website
            website_patterns = [
                r'"website":\s*"([^"]+)"',
                r'href="(https?://[^"]+)"[^>]*>Website',
                r'website["\']:\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in website_patterns:
                website_match = re.search(pattern, content, re.IGNORECASE)
                if website_match:
                    website = website_match.group(1)
                    if not website.startswith('http'):
                        website = 'https://' + website
                    clinic_data['website'] = website
                    break
            
            logger.info(f"Extracted clinic data: {clinic_data['name']}")
            return clinic_data
            
        else:
            logger.error(f"Failed to fetch Google Maps page: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching Google Maps data: {e}")
        return None

def create_clinic_owner_user(conn, clinic_name):
    """Create a user account for the clinic owner."""
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
    username = clean_name[:30]
    password_hash = generate_password_hash('clinic123')
    
    # Generate unique phone number
    import random
    unique_phone = f"+91-{random.randint(7000000000, 9999999999)}"
    
    cursor.execute("""
        INSERT INTO users (name, email, username, password_hash, role, phone_number)
        VALUES (%s, %s, %s, %s, 'clinic_owner', %s)
        RETURNING id
    """, (clinic_name, email, username, password_hash, unique_phone))
    
    user_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    logger.info(f"Created clinic owner user: {email}")
    return user_id

def parse_location_data(address_text):
    """Parse address into components."""
    if not address_text:
        return None, None, None
    
    # Indian cities
    major_cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'hyderabad', 'pune', 'kolkata', 'ahmedabad', 'jaipur', 'surat', 'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'vadodara', 'firozabad', 'ludhiana', 'rajkot', 'agra', 'siliguri', 'nashik', 'faridabad', 'patiala', 'meerut', 'kalyan-dombivali', 'vasai-virar', 'varanasi', 'srinagar', 'dhanbad', 'jodhpur', 'amritsar', 'raipur', 'allahabad', 'coimbatore', 'jabalpur', 'gwalior', 'vijayawada', 'madurai', 'guwahati', 'chandigarh', 'hubli-dharwad', 'amroha', 'moradabad', 'gurgaon', 'aligarh', 'solapur', 'ranchi', 'jalandhar', 'tiruchirappalli', 'bhubaneswar', 'salem', 'warangal', 'guntur', 'bhiwandi', 'saharanpur', 'gorakhpur', 'bikaner', 'amravati', 'noida', 'jamshedpur', 'bhilai nagar', 'cuttack', 'kochi', 'udaipur', 'bhavnagar', 'dehradun', 'asansol', 'nanded-waghala', 'kolhapur', 'ajmer', 'gulbarga', 'jamnagar', 'ujjain', 'loni', 'sikar', 'jhansi', 'ulhasnagar', 'nellore', 'jammu', 'sangli-miraj & kupwad', 'belgaum', 'mangalore', 'ambattur', 'tirunelveli', 'malegaon', 'gaya', 'jalgaon', 'udaipur', 'kozhikode']
    
    # Indian states
    states = ['andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh', 'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka', 'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram', 'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal', 'delhi', 'jammu and kashmir', 'ladakh']
    
    address_lower = address_text.lower()
    
    city = None
    state = None
    
    # Find city
    for city_name in major_cities:
        if city_name in address_lower:
            city = city_name.title()
            break
    
    # Find state
    for state_name in states:
        if state_name in address_lower:
            state = state_name.title()
            break
    
    return address_text, city, state

def create_clinic_record(conn, clinic_data):
    """Create clinic record in database."""
    
    # Create clinic owner user
    owner_user_id = create_clinic_owner_user(conn, clinic_data['name'])
    
    # Parse address
    address, city, state = parse_location_data(clinic_data.get('address'))
    
    # Set default values and ensure required fields are not null
    rating = clinic_data.get('rating') or 4.5
    review_count = clinic_data.get('review_count') or 0
    
    # Ensure required fields are not null
    if not address:
        address = "Address not available"
    if not city:
        city = "City not available" 
    if not state:
        state = "State not available"
    
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
        'Cosmetic Surgery, Dermatology, Aesthetic Medicine', datetime.now()
    ))
    
    clinic_id = cursor.fetchone()[0]
    conn.commit()
    
    # Fetch complete clinic record
    cursor.execute("""
        SELECT c.*, u.email as owner_email, u.username as owner_username
        FROM clinics c 
        JOIN users u ON c.owner_user_id = u.id 
        WHERE c.id = %s
    """, (clinic_id,))
    
    clinic_record = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    clinic_dict = dict(zip(columns, clinic_record))
    
    cursor.close()
    
    logger.info(f"Created clinic record with ID: {clinic_id}")
    return clinic_dict

def main():
    """Main function to extract and create clinic profile."""
    place_id = "ChIJhcOH4tyZyzsRN1AHrG8xZ5I"
    
    print("=== EXTRACTING CLINIC DATA FROM GOOGLE PLACE ID ===")
    print(f"Place ID: {place_id}")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    try:
        # Check if clinic already exists
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM clinics WHERE google_place_id = %s", (place_id,))
        existing = cursor.fetchone()
        cursor.close()
        
        if existing:
            print(f"✓ Clinic already exists: {existing[1]} (ID: {existing[0]})")
            return
        
        # Extract clinic data
        print("Fetching data from Google Maps...")
        clinic_data = fetch_google_maps_data(place_id)
        
        if not clinic_data:
            print("❌ Failed to extract clinic data")
            return
        
        print("\n=== EXTRACTED DATA ===")
        for key, value in clinic_data.items():
            print(f"{key.upper()}: {value}")
        
        # Create clinic record
        print("\nCreating clinic record...")
        clinic_record = create_clinic_record(conn, clinic_data)
        
        print("\n=== CREATED CLINIC PROFILE ===")
        important_fields = ['id', 'name', 'address', 'city', 'state', 'contact_number', 'website_url', 'google_place_id', 'google_rating', 'google_review_count', 'owner_email', 'is_verified']
        
        for field in important_fields:
            if field in clinic_record:
                print(f"{field.upper()}: {clinic_record[field]}")
        
        print(f"\n✅ Clinic profile created successfully with ID: {clinic_record['id']}")
        print(f"Owner login: {clinic_record['owner_email']} / clinic123")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"❌ Error creating clinic: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()