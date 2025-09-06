#!/usr/bin/env python3
"""
Process Visakhapatnam Google Places clinic data for database import.
This script cleans and transforms the scraped Visakhapatnam clinic data into the format needed for our clinic database.
"""

import csv
import json
import re
import os
from typing import Dict, List, Any

def clean_phone_number(phone: str) -> str:
    """Clean and format phone number."""
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # If it starts with +91, keep it
    if cleaned.startswith('+91'):
        return cleaned
    
    # If it's a 10-digit number, add +91
    if len(cleaned) == 10 and cleaned.isdigit():
        return f"+91{cleaned}"
    
    return cleaned

def extract_categories(row: Dict) -> str:
    """Extract and combine all categories into a comma-separated string."""
    categories = []
    
    # Extract from categories/0 through categories/9
    for i in range(10):
        cat_key = f"categories/{i}"
        if cat_key in row and row[cat_key]:
            categories.append(row[cat_key].strip())
    
    # Remove duplicates and return
    return ", ".join(list(dict.fromkeys(categories)))

def process_opening_hours(row: Dict) -> str:
    """Convert opening hours data to JSON format."""
    hours_data = {}
    
    for i in range(7):
        day_key = f"openingHours/{i}/day"
        hours_key = f"openingHours/{i}/hours"
        
        if day_key in row and hours_key in row and row[day_key] and row[hours_key]:
            day = row[day_key].strip()
            hours = row[hours_key].strip()
            if day and hours:
                hours_data[day] = hours
    
    return json.dumps(hours_data) if hours_data else ""

def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from clinic name."""
    if not name:
        return ""
    
    # Convert to lowercase, replace spaces and special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def generate_owner_email(name: str, index: int) -> str:
    """Generate a unique owner email for the clinic."""
    if not name:
        return f"visakhapatnam.clinic{index}@antidote-temp.com"
    
    # Create email from clinic name
    base_name = re.sub(r'[^\w\s]', '', name.lower())
    base_name = re.sub(r'\s+', '', base_name)[:20]  # Max 20 chars
    
    return f"vzg.{base_name}.{index}@antidote-temp.com"

def extract_amenities(row: Dict) -> List[str]:
    """Extract amenities and service options."""
    amenities = []
    
    # Check for accessibility features
    if row.get("additionalInfo/Accessibility/0/Wheelchair accessible entrance") == "true":
        amenities.append("Wheelchair Accessible")
    
    # Check for parking
    if row.get("additionalInfo/Parking/0/Free parking lot") == "true":
        amenities.append("Free Parking")
    elif row.get("additionalInfo/Parking/0/Paid parking lot") == "true":
        amenities.append("Parking Available")
    
    # Check for payment options
    if row.get("additionalInfo/Payments/0/Credit cards") == "true":
        amenities.append("Credit Cards Accepted")
    if row.get("additionalInfo/Payments/0/Google Pay") == "true":
        amenities.append("Digital Payments")
    
    # Check for appointments
    if row.get("additionalInfo/Planning/0/Appointment required") == "true":
        amenities.append("Appointment Required")
    elif row.get("additionalInfo/Planning/0/Accepts walk-ins") == "true":
        amenities.append("Walk-ins Welcome")
    
    return amenities

def clean_visakhapatnam_city_name(city: str) -> str:
    """Clean and standardize Visakhapatnam city name."""
    if not city:
        return "Visakhapatnam"
    
    city = city.strip()
    
    # Various forms of Visakhapatnam
    visakhapatnam_variants = ['visakhapatnam', 'vizag', 'viskapatanam', 'vishakhapatnam']
    
    for variant in visakhapatnam_variants:
        if variant in city.lower():
            return "Visakhapatnam"
    
    return "Visakhapatnam"

def process_visakhapatnam_clinic_data():
    """Process the Visakhapatnam clinic data CSV and create a cleaned version."""
    input_file = "attached_assets/dataset_crawler-google-places_2025-06-20_10-19-30-465_1750414845659.csv"
    output_file = "visakhapatnam_clinics.csv"
    
    # Define the output columns in the order they should appear
    output_columns = [
        'name', 'slug', 'description', 'address', 'city', 'state', 'country',
        'pincode', 'latitude', 'longitude', 'contact_number', 'email',
        'website_url', 'specialties', 'operating_hours', 'google_rating',
        'google_review_count', 'google_place_id', 'google_maps_url',
        'profile_image', 'amenities', 'owner_email', 'is_approved',
        'verification_status', 'claim_status'
    ]
    
    processed_clinics = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            for index, row in enumerate(reader, 1):
                # Skip if essential data is missing
                if not row.get('title') or not row.get('address'):
                    continue
                
                # Extract postal code from address
                postal_match = re.search(r'\b(\d{6})\b', row.get('address', ''))
                pincode = postal_match.group(1) if postal_match else ''
                
                # Clean city name
                city = clean_visakhapatnam_city_name(row.get('city', ''))
                
                # Process the clinic data
                clinic_data = {
                    'name': row.get('title', '').strip(),
                    'slug': generate_slug(row.get('title', '')),
                    'description': row.get('description', '').strip(),
                    'address': row.get('address', '').strip(),
                    'city': city,
                    'state': 'Andhra Pradesh',  # All Visakhapatnam clinics are in Andhra Pradesh
                    'country': 'India',
                    'pincode': pincode,
                    'latitude': row.get('location/lat', ''),
                    'longitude': row.get('location/lng', ''),
                    'contact_number': clean_phone_number(row.get('phone', '')),
                    'email': '',  # Will be filled with owner email
                    'website_url': row.get('website', '').strip(),
                    'specialties': extract_categories(row),
                    'operating_hours': process_opening_hours(row),
                    'google_rating': row.get('totalScore', ''),
                    'google_review_count': row.get('reviewsCount', ''),
                    'google_place_id': row.get('placeId', '').strip(),
                    'google_maps_url': row.get('url', '').strip(),
                    'profile_image': row.get('imageUrl', '').strip(),
                    'amenities': ', '.join(extract_amenities(row)),
                    'owner_email': generate_owner_email(row.get('title', ''), index),
                    'is_approved': 'false',  # All start as unapproved
                    'verification_status': 'pending',
                    'claim_status': 'unclaimed'
                }
                
                processed_clinics.append(clinic_data)
                
                # Progress indicator
                if index % 25 == 0:
                    print(f"Processed {index} Visakhapatnam clinics...")
    
        # Write the processed data to output CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_columns)
            writer.writeheader()
            writer.writerows(processed_clinics)
    
        print(f"\n✅ Successfully processed {len(processed_clinics)} Visakhapatnam clinics")
        print(f"📁 Output file: {output_file}")
        print(f"📊 Data ready for import into clinic database")
        
        # Show sample of processed data
        if processed_clinics:
            print(f"\n📋 Sample Visakhapatnam clinic data:")
            sample = processed_clinics[0]
            for key, value in sample.items():
                if value:  # Only show non-empty values
                    print(f"   {key}: {str(value)[:80]}{'...' if len(str(value)) > 80 else ''}")
        
        # Show some statistics
        total_with_phone = sum(1 for c in processed_clinics if c['contact_number'])
        total_with_website = sum(1 for c in processed_clinics if c['website_url'])
        total_with_rating = sum(1 for c in processed_clinics if c['google_rating'])
        
        print(f"\n📊 Statistics:")
        print(f"   Clinics with phone numbers: {total_with_phone}/{len(processed_clinics)}")
        print(f"   Clinics with websites: {total_with_website}/{len(processed_clinics)}")
        print(f"   Clinics with Google ratings: {total_with_rating}/{len(processed_clinics)}")
    
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found")
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_visakhapatnam_clinic_data()