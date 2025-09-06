#!/usr/bin/env python3
"""
Task 2: Clean up doctors list
- Remove doctors not in CSV
- Fix duplicate "Dr." prefixes
"""

import os
import csv
import psycopg2
import re

def get_db_connection():
    """Get a connection to the database."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def load_csv_doctor_names():
    """Load all doctor names from CSV."""
    csv_names = set()
    csv_path = "./attached_assets/Copy of Plastic surgeons india - Sheet1.csv"
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Name', '').strip()
            if name:
                csv_names.add(name)
                # Also add normalized version
                normalized = re.sub(r'^Dr\.?\s*', '', name, flags=re.IGNORECASE).strip()
                if normalized:
                    csv_names.add(normalized)
    
    return csv_names

def normalize_for_comparison(name):
    """Normalize name for comparison."""
    if not name:
        return ""
    return re.sub(r'^Dr\.?\s*', '', name, flags=re.IGNORECASE).strip().lower()

def fix_duplicate_dr(name):
    """Fix duplicate Dr. prefixes."""
    if not name:
        return name
    # Remove multiple Dr. prefixes
    name = re.sub(r'^(Dr\.?\s*){2,}', 'Dr. ', name, flags=re.IGNORECASE)
    return name.strip()

def main():
    print("Starting doctor list cleanup...")
    
    # Load CSV names
    csv_names = load_csv_doctor_names()
    print(f"Loaded {len(csv_names)} names from CSV")
    
    conn = get_db_connection()
    
    # Get all doctors from database
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM doctors ORDER BY name")
        db_doctors = cursor.fetchall()
    
    print(f"Found {len(db_doctors)} doctors in database")
    
    # Track changes
    fixed_names = 0
    removed_doctors = 0
    
    for doctor_id, doctor_name in db_doctors:
        # Fix duplicate Dr. prefix first
        fixed_name = fix_duplicate_dr(doctor_name)
        name_was_fixed = fixed_name != doctor_name
        
        # Check if doctor should exist
        normalized_fixed = normalize_for_comparison(fixed_name)
        normalized_csv_names = [normalize_for_comparison(csv_name) for csv_name in csv_names]
        
        should_keep = False
        for csv_norm in normalized_csv_names:
            if normalized_fixed == csv_norm or (len(normalized_fixed) > 5 and normalized_fixed in csv_norm):
                should_keep = True
                break
        
        if should_keep:
            if name_was_fixed:
                # Update the name
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE doctors SET name = %s WHERE id = %s", (fixed_name, doctor_id))
                    conn.commit()
                    print(f"✅ Fixed name: '{doctor_name}' → '{fixed_name}'")
                    fixed_names += 1
        else:
            # Remove doctor not in CSV
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
                conn.commit()
                print(f"❌ Removed: {doctor_name} (not in CSV)")
                removed_doctors += 1
    
    # Final check
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM doctors")
        final_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE profile_image IS NOT NULL AND profile_image != ''")
        with_images = cursor.fetchone()[0]
        
        coverage = int((with_images / final_count) * 100) if final_count > 0 else 0
    
    print("\n" + "="*50)
    print("DOCTOR LIST CLEANUP SUMMARY")
    print("="*50)
    print(f"✅ Fixed {fixed_names} duplicate Dr. prefixes")
    print(f"❌ Removed {removed_doctors} doctors not in CSV")
    print(f"📊 Final doctor count: {final_count}")
    print(f"📈 Doctors with images: {with_images} ({coverage}%)")
    print("="*50)
    
    conn.close()

if __name__ == "__main__":
    main()