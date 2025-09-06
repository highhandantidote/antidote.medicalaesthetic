#!/usr/bin/env python3
"""
Test import of Revera Clinic using the hybrid import system.
"""

import os
import sys
sys.path.append('.')

from hybrid_clinic_import import import_single_clinic

def test_revera_clinic():
    """Import Revera Clinic from CSV data with Google Places integration."""
    
    # Revera Clinic data from CSV
    clinic_data = {
        'name': 'Revera Clinic',
        'description': '',  # Will be generated from Google data
        'address': '#Prime plaza-304,Besides "West Side",HimayatNagar,Main Road, Hyderabad, Telangana 500029, India',
        'city': 'Hyderabad',
        'state': 'Telangana',
        'pincode': '500029',
        'latitude': 17.4015388,
        'longitude': 78.4848302,
        'contact_number': '918341057464',
        'email': '',
        'website_url': 'http://www.revera.in/',
        'specialties': 'Plastic surgeon, Cosmetic surgeon, Dermatologist, Obstetrician-gynecologist, Hair transplantation clinic, Laser hair removal service, Permanent make-up clinic, Plastic surgery clinic, Skin care clinic, Tattoo removal service',
        'operating_hours': '{"Monday": "10 AM to 8 PM", "Tuesday": "10 AM to 8 PM", "Wednesday": "10 AM to 8 PM", "Thursday": "10 AM to 8 PM", "Friday": "10 AM to 8 PM", "Saturday": "10 AM to 8 PM", "Sunday": "10 AM to 8 PM"}',
        'google_place_id': 'ChIJhcOH4tyZyzsRN1AHrG8xZ5I',
        'owner_email': 'reveraclinic.48@antidote-temp.com'
    }
    
    try:
        clinic_id = import_single_clinic(clinic_data)
        if clinic_id:
            print(f"Successfully imported Revera Clinic with ID: {clinic_id}")
            print(f"Clinic URL: /clinic/view/{clinic_id}")
            return clinic_id
        else:
            print("Failed to import Revera Clinic")
            return None
    except Exception as e:
        print(f"Error importing Revera Clinic: {e}")
        return None

if __name__ == "__main__":
    test_revera_clinic()