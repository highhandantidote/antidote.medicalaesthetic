"""
Update clinic 41 with authentic Google Places services data.
This script fetches services from Google Places API and updates the database.
"""

import os
import psycopg2
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not found")
            return None
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def get_google_api_key():
    """Get Google API key from environment."""
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        logger.error("GOOGLE_PLACES_API_KEY not found in environment")
    return api_key

def fetch_place_details(place_id, api_key):
    """Fetch place details from Google Places API."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        'place_id': place_id,
        'key': api_key,
        'fields': 'types,opening_hours'
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return data.get('result')
            else:
                logger.error(f"API error: {data.get('status')} - {data.get('error_message')}")
                return None
        else:
            logger.error(f"API request failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching place details: {e}")
        return None

def process_google_types(types_list):
    """Convert Google Place types to readable services."""
    if not types_list:
        return None
    
    # Mapping for common medical/aesthetic service types
    type_mapping = {
        'doctor': 'Medical Doctor',
        'hospital': 'Hospital Services',
        'beauty_salon': 'Beauty Salon',
        'spa': 'Spa Services',
        'health': 'Healthcare Services',
        'dentist': 'Dental Services',
        'physiotherapist': 'Physiotherapy',
        'dermatologist': 'Dermatologist',
        'plastic_surgeon': 'Plastic Surgeon',
        'cosmetic_surgeon': 'Cosmetic Surgeon',
        'hair_transplantation_clinic': 'Hair Transplantation Clinic',
        'laser_hair_removal_service': 'Laser Hair Removal Service',
        'permanent_make_up_clinic': 'Permanent Make-up Clinic',
        'plastic_surgery_clinic': 'Plastic Surgery Clinic',
        'skin_care_clinic': 'Skin Care Clinic',
        'tattoo_removal_service': 'Tattoo Removal Service',
        'obstetrician_gynecologist': 'Obstetrician-gynecologist',
        'establishment': '',  # Skip generic types
        'point_of_interest': '',
        'premise': ''
    }
    
    readable_services = []
    for service_type in types_list:
        if service_type in type_mapping:
            mapped_service = type_mapping[service_type]
            if mapped_service and mapped_service not in readable_services:
                readable_services.append(mapped_service)
        else:
            # Convert snake_case to readable format
            readable_service = service_type.replace('_', ' ').title()
            if readable_service not in readable_services and readable_service not in ['Establishment', 'Point Of Interest']:
                readable_services.append(readable_service)
    
    return ', '.join(readable_services) if readable_services else None

def update_clinic_services():
    """Update clinic 41 with Google Places services data."""
    logger.info("Starting clinic services update for clinic 41")
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False
    
    try:
        # Get clinic 41's Google Place ID
        cursor = conn.cursor()
        cursor.execute("SELECT google_place_id FROM clinics WHERE id = 41")
        result = cursor.fetchone()
        
        if not result or not result[0]:
            logger.error("Clinic 41 not found or no Google Place ID")
            return False
        
        place_id = result[0]
        logger.info(f"Found Place ID for clinic 41: {place_id}")
        
        # Get Google API key
        api_key = get_google_api_key()
        if not api_key:
            logger.error("Google API key not available")
            return False
        
        # Fetch place details from Google
        place_data = fetch_place_details(place_id, api_key)
        if not place_data:
            logger.error("Failed to fetch place details from Google")
            return False
        
        # Process the types data
        types_list = place_data.get('types', [])
        logger.info(f"Google Place types: {types_list}")
        
        services_offered = process_google_types(types_list)
        logger.info(f"Processed services: {services_offered}")
        
        # Process opening hours data
        working_hours = None
        if 'opening_hours' in place_data and place_data['opening_hours']:
            opening_hours_data = place_data['opening_hours']
            logger.info(f"Opening hours data: {opening_hours_data}")
            
            if 'weekday_text' in opening_hours_data:
                working_hours = '; '.join(opening_hours_data['weekday_text'])
            elif 'periods' in opening_hours_data:
                periods = opening_hours_data['periods']
                if periods:
                    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                    hours_list = []
                    for period in periods:
                        if 'open' in period:
                            day = day_names[period['open']['day']]
                            open_time = period['open']['time']
                            close_time = period.get('close', {}).get('time', '2400') if 'close' in period else '2400'
                            
                            open_formatted = f"{open_time[:2]}:{open_time[2:]}"
                            close_formatted = f"{close_time[:2]}:{close_time[2:]}"
                            
                            hours_list.append(f"{day}: {open_formatted} - {close_formatted}")
                    
                    if hours_list:
                        working_hours = '; '.join(hours_list)
        
        logger.info(f"Processed working hours: {working_hours}")
        
        # Update clinic with services and working hours data
        cursor.execute("""
            UPDATE clinics 
            SET services_offered = %s, working_hours = %s, updated_at = %s
            WHERE id = 41
        """, (services_offered, working_hours, datetime.now()))
        
        conn.commit()
        cursor.close()
        
        logger.info(f"Successfully updated clinic 41 with services: {services_offered}")
        logger.info(f"Successfully updated clinic 41 with working hours: {working_hours}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating clinic services: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Main function to update clinic services."""
    print("=== Update Clinic Services from Google Places ===")
    
    success = update_clinic_services()
    
    if success:
        print("✓ Successfully updated clinic 41 with Google Places services")
    else:
        print("✗ Failed to update clinic services")

if __name__ == "__main__":
    main()