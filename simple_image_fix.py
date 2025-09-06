#!/usr/bin/env python3
"""
Simple script to fix remaining doctor profile images.
"""

import os
import csv
import psycopg2
import re

def get_db_connection():
    """Get a connection to the database."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def normalize_name(name):
    """Normalize doctor name for matching."""
    if not name:
        return ""
    # Remove Dr. prefix and medical degrees
    name = re.sub(r'^(Dr\.?|Doctor)\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*(M\.?S\.?|M\.?Ch\.?|M\.?D\.?|MBBS|MS|MCh|MD).*$', '', name, flags=re.IGNORECASE)
    return ' '.join(name.split()).strip()

def main():
    # Load CSV data
    csv_images = {}
    csv_path = "./attached_assets/Copy of Plastic surgeons india - Sheet1.csv"
    
    print("Loading CSV data...")
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Name', '').strip()
            image = row.get('Profile Image', '').strip()
            if name and image:
                csv_images[name] = image
                # Also store normalized version
                norm_name = normalize_name(name)
                if norm_name:
                    csv_images[norm_name] = image
    
    print(f"Loaded {len(csv_images)} image entries")
    
    # Get doctors without images
    conn = get_db_connection()
    doctors_to_fix = []
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, name FROM doctors 
            WHERE profile_image IS NULL OR profile_image = ''
        """)
        doctors_to_fix = cursor.fetchall()
    
    print(f"Found {len(doctors_to_fix)} doctors without images")
    
    # Try to match and update
    updated = 0
    for doctor_id, doctor_name in doctors_to_fix:
        image_url = None
        
        # Try exact match first
        if doctor_name in csv_images:
            image_url = csv_images[doctor_name]
        else:
            # Try normalized match
            norm_doctor = normalize_name(doctor_name)
            if norm_doctor in csv_images:
                image_url = csv_images[norm_doctor]
            else:
                # Try partial matching
                for csv_name, csv_image in csv_images.items():
                    if norm_doctor.lower() in csv_name.lower() or csv_name.lower() in norm_doctor.lower():
                        image_url = csv_image
                        break
        
        # Update if match found
        if image_url:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE doctors SET profile_image = %s WHERE id = %s
                """, (image_url, doctor_id))
                conn.commit()
                updated += 1
                print(f"✅ Updated: {doctor_name}")
        else:
            print(f"❌ No match: {doctor_name}")
    
    # Final stats
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE profile_image IS NOT NULL AND profile_image != ''")
        with_images = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM doctors")
        total = cursor.fetchone()[0]
        coverage = int((with_images / total) * 100) if total > 0 else 0
    
    print(f"\n🎉 Results:")
    print(f"✅ Updated {updated} doctors")
    print(f"📊 Total doctors with images: {with_images}/{total}")
    print(f"📈 Coverage: {coverage}%")
    
    conn.close()

if __name__ == "__main__":
    main()