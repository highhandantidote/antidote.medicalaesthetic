#!/usr/bin/env python3
"""
Test using only the legacy Places API to bypass the New Places API requirement.
"""

import os
import requests
import logging

logging.basicConfig(level=logging.INFO)

def test_legacy_places_api(place_id):
    """Test the legacy Places API directly."""
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("No API key found")
        return False
    
    # Use only legacy Places API
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        'place_id': place_id,
        'key': api_key,
        'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,business_status,geometry,photos,reviews,types,opening_hours'
    }
    
    try:
        print(f"Testing legacy API with Place ID: {place_id}")
        response = requests.get(url, params=params)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API Status: {data.get('status')}")
            
            if data.get('status') == 'OK':
                result = data.get('result', {})
                print(f"✓ Success! Found: {result.get('name', 'Unknown')}")
                print(f"  Address: {result.get('formatted_address', 'N/A')}")
                print(f"  Rating: {result.get('rating', 'N/A')}")
                print(f"  Types: {result.get('types', [])}")
                return True
            else:
                print(f"API Error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                return False
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def main():
    """Test the legacy API with the provided Place ID."""
    place_id = "ChIJ-525K5mXyzsR5yUDZ9b8ROY"
    
    if test_legacy_places_api(place_id):
        print("\n✓ Legacy Places API is working!")
        print("We can proceed with clinic imports using the legacy API.")
    else:
        print("\n✗ Legacy Places API failed")
        print("Need to enable Places API in Google Cloud Console")

if __name__ == "__main__":
    main()