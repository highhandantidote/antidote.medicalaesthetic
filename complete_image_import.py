#!/usr/bin/env python3
"""
Complete image import task:
1. Import all missing profile images from CSV
2. Remove duplicate "Dr." prefixes from doctor names
"""

import os
import csv
import psycopg2
import re

def get_db_connection():
    """Get a connection to the database."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def load_all_csv_doctors():
    """Load all doctors from CSV with their images."""
    csv_doctors = {}
    csv_path = "./attached_assets/Copy of Plastic surgeons india - Sheet1.csv"
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Name', '').strip()
            image = row.get('Profile Image', '').strip()
            if name and image:
                csv_doctors[name] = image
    
    return csv_doctors

def normalize_name_for_comparison(name):
    """Normalize name for comparison while preserving original structure."""
    if not name:
        return ""
    # Remove extra spaces and normalize
    name = ' '.join(name.split()).strip()
    return name

def fix_duplicate_dr_prefix(name):
    """Remove duplicate Dr. prefixes."""
    if not name:
        return name
    
    # Remove duplicate "Dr." prefixes
    # Match patterns like "Dr. Dr. Name" or "Dr.Dr. Name"
    name = re.sub(r'^(Dr\.?\s*){2,}', 'Dr. ', name, flags=re.IGNORECASE)
    return name.strip()

def find_matching_doctor(db_name, csv_doctors):
    """Find matching doctor in CSV data."""
    # Try exact match first
    if db_name in csv_doctors:
        return csv_doctors[db_name]
    
    # Try without Dr. prefix
    db_name_no_dr = re.sub(r'^Dr\.?\s*', '', db_name, flags=re.IGNORECASE).strip()
    
    for csv_name, image_url in csv_doctors.items():
        csv_name_no_dr = re.sub(r'^Dr\.?\s*', '', csv_name, flags=re.IGNORECASE).strip()
        
        # Compare without Dr. prefix
        if db_name_no_dr.lower() == csv_name_no_dr.lower():
            return image_url
        
        # Try partial matching
        if (db_name_no_dr.lower() in csv_name_no_dr.lower() and len(db_name_no_dr) > 5) or \
           (csv_name_no_dr.lower() in db_name_no_dr.lower() and len(csv_name_no_dr) > 5):
            return image_url
    
    return None

def main():
    print("Starting complete image import and name cleanup...")
    
    # Load CSV data
    print("Loading CSV doctors...")
    csv_doctors = load_all_csv_doctors()
    print(f"Loaded {len(csv_doctors)} doctors from CSV")
    
    # Get all doctors from database
    conn = get_db_connection()
    
    # First, fix duplicate Dr. prefixes
    print("\nFixing duplicate Dr. prefixes...")
    fixed_names = 0
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM doctors")
        all_doctors = cursor.fetchall()
        
        for doctor_id, name in all_doctors:
            fixed_name = fix_duplicate_dr_prefix(name)
            if fixed_name != name:
                cursor.execute("UPDATE doctors SET name = %s WHERE id = %s", (fixed_name, doctor_id))
                print(f"Fixed: '{name}' → '{fixed_name}'")
                fixed_names += 1
        
        conn.commit()
    
    print(f"Fixed {fixed_names} doctor names with duplicate Dr. prefixes")
    
    # Now handle missing images
    print("\nImporting missing profile images...")
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, name FROM doctors 
            WHERE profile_image IS NULL OR profile_image = ''
        """)
        doctors_without_images = cursor.fetchall()
    
    print(f"Found {len(doctors_without_images)} doctors without images")
    
    updated_images = 0
    not_found = 0
    
    for doctor_id, doctor_name in doctors_without_images:
        image_url = find_matching_doctor(doctor_name, csv_doctors)
        
        if image_url:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE doctors SET profile_image = %s WHERE id = %s
                """, (image_url, doctor_id))
                conn.commit()
                updated_images += 1
                print(f"✅ Updated image for: {doctor_name}")
        else:
            not_found += 1
            print(f"❌ No match found for: {doctor_name}")
    
    # Final statistics
    print("\n" + "="*50)
    print("COMPLETE IMPORT SUMMARY")
    print("="*50)
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE profile_image IS NOT NULL AND profile_image != ''")
        with_images = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors")
        total = cursor.fetchone()[0]
        
        coverage = int((with_images / total) * 100) if total > 0 else 0
    
    print(f"✅ Fixed {fixed_names} duplicate Dr. prefixes")
    print(f"✅ Updated {updated_images} doctor images")
    print(f"❌ Could not find {not_found} doctor images")
    print(f"📊 Total doctors with images: {with_images}/{total}")
    print(f"📈 Final coverage: {coverage}%")
    print("="*50)
    
    conn.close()

if __name__ == "__main__":
    main()