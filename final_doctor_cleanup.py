#!/usr/bin/env python3
"""
Final comprehensive doctor cleanup:
1. Import ALL missing profile images from CSV 
2. Remove doctors not in CSV
3. Fix duplicate "Dr." prefixes
4. Ensure only CSV doctors exist
"""

import os
import csv
import psycopg2
import re

def get_db_connection():
    """Get a connection to the database."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def load_csv_data():
    """Load all doctor data from CSV."""
    csv_data = {}
    csv_path = "./attached_assets/Copy of Plastic surgeons india - Sheet1.csv"
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Name', '').strip()
            image = row.get('Profile Image', '').strip()
            if name:
                # Store with original name as key
                csv_data[name] = {
                    'image': image,
                    'original_name': name
                }
                
                # Also store normalized versions for matching
                normalized = normalize_name(name)
                if normalized and normalized != name:
                    csv_data[normalized] = {
                        'image': image,
                        'original_name': name
                    }
    
    return csv_data

def normalize_name(name):
    """Normalize name for matching."""
    if not name:
        return ""
    # Remove Dr. prefix, medical degrees, extra spaces
    name = re.sub(r'^Dr\.?\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*(M\.?S\.?|M\.?Ch\.?|M\.?D\.?|Ph\.?D\.?|MBBS|MS|MCh|MD|PhD|DNB).*$', '', name, flags=re.IGNORECASE)
    return ' '.join(name.split()).strip()

def fix_duplicate_dr(name):
    """Fix duplicate Dr. prefixes."""
    if not name:
        return name
    # Remove multiple Dr. prefixes and normalize
    name = re.sub(r'^(Dr\.?\s*){2,}', 'Dr. ', name, flags=re.IGNORECASE)
    return name.strip()

def find_best_match(db_name, csv_data):
    """Find best match in CSV data."""
    # Try exact match first
    if db_name in csv_data:
        return csv_data[db_name]
    
    # Try normalized match
    normalized_db = normalize_name(db_name)
    if normalized_db in csv_data:
        return csv_data[normalized_db]
    
    # Try fuzzy matching
    normalized_db_lower = normalized_db.lower()
    
    for csv_key, csv_info in csv_data.items():
        csv_normalized = normalize_name(csv_key).lower()
        
        # Check if names match closely
        if normalized_db_lower == csv_normalized:
            return csv_info
        
        # Check partial matches for longer names
        if len(normalized_db_lower) > 8:
            if normalized_db_lower in csv_normalized or csv_normalized in normalized_db_lower:
                return csv_info
    
    return None

def main():
    print("Starting final comprehensive doctor cleanup...")
    
    # Load CSV data
    csv_data = load_csv_data()
    print(f"Loaded {len(csv_data)} entries from CSV")
    
    conn = get_db_connection()
    
    # Get all doctors from database
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM doctors ORDER BY name")
        all_doctors = cursor.fetchall()
    
    print(f"Found {len(all_doctors)} doctors in database")
    
    # Track changes
    updated_images = 0
    fixed_names = 0
    removed_doctors = 0
    kept_doctors = 0
    
    for doctor_id, doctor_name in all_doctors:
        # Fix duplicate Dr. prefix
        fixed_name = fix_duplicate_dr(doctor_name)
        
        # Find match in CSV
        match = find_best_match(fixed_name, csv_data)
        
        if match:
            # Keep this doctor - update name and image if needed
            name_changed = fixed_name != doctor_name
            image_url = match['image']
            
            # Check current image status
            with conn.cursor() as cursor:
                cursor.execute("SELECT profile_image FROM doctors WHERE id = %s", (doctor_id,))
                current_image = cursor.fetchone()[0]
            
            # Update if needed
            if name_changed or not current_image or current_image.strip() == '':
                update_parts = []
                params = []
                
                if name_changed:
                    update_parts.append("name = %s")
                    params.append(fixed_name)
                
                if image_url and (not current_image or current_image.strip() == ''):
                    update_parts.append("profile_image = %s")
                    params.append(image_url)
                
                if update_parts:
                    params.append(doctor_id)
                    query = f"UPDATE doctors SET {', '.join(update_parts)} WHERE id = %s"
                    
                    with conn.cursor() as cursor:
                        cursor.execute(query, params)
                        conn.commit()
                    
                    if name_changed:
                        print(f"✅ Fixed name: '{doctor_name}' → '{fixed_name}'")
                        fixed_names += 1
                    
                    if image_url and (not current_image or current_image.strip() == ''):
                        print(f"✅ Added image: {fixed_name}")
                        updated_images += 1
            
            kept_doctors += 1
            
        else:
            # Remove doctor not in CSV
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
                conn.commit()
            print(f"❌ Removed: {doctor_name} (not in CSV)")
            removed_doctors += 1
    
    # Final statistics
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM doctors")
        final_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE profile_image IS NOT NULL AND profile_image != ''")
        with_images = cursor.fetchone()[0]
        
        coverage = int((with_images / final_count) * 100) if final_count > 0 else 0
    
    print("\n" + "="*60)
    print("FINAL COMPREHENSIVE CLEANUP SUMMARY")
    print("="*60)
    print(f"✅ Updated {updated_images} doctor images")
    print(f"✅ Fixed {fixed_names} duplicate Dr. prefixes")
    print(f"✅ Kept {kept_doctors} doctors from CSV")
    print(f"❌ Removed {removed_doctors} doctors not in CSV")
    print(f"📊 Final doctor count: {final_count}")
    print(f"📈 Doctors with images: {with_images}/{final_count} ({coverage}%)")
    print("="*60)
    
    # Show remaining doctors without images
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM doctors 
            WHERE profile_image IS NULL OR profile_image = ''
            ORDER BY name
        """)
        remaining = cursor.fetchall()
        
        if remaining:
            print(f"\nRemaining {len(remaining)} doctors without images:")
            for name, in remaining:
                print(f"  - {name}")
    
    conn.close()

if __name__ == "__main__":
    main()