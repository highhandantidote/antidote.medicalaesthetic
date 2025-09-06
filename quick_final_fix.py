#!/usr/bin/env python3
"""
Quick final fix for both tasks.
"""

import os
import csv
import psycopg2
import re

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def main():
    print("Quick final doctor cleanup...")
    
    # Load CSV
    csv_doctors = {}
    with open("./attached_assets/Copy of Plastic surgeons india - Sheet1.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row.get('Name', '').strip()
            image = row.get('Profile Image', '').strip()
            if name:
                csv_doctors[name] = image
                # Add normalized version
                norm = re.sub(r'^Dr\.?\s*', '', name, flags=re.IGNORECASE).strip()
                if norm:
                    csv_doctors[norm] = image
    
    print(f"CSV: {len(csv_doctors)} entries")
    
    conn = get_db_connection()
    
    # Get DB doctors
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, name FROM doctors")
        db_doctors = cursor.fetchall()
    
    print(f"DB: {len(db_doctors)} doctors")
    
    updated = 0
    fixed = 0
    removed = 0
    
    for doc_id, doc_name in db_doctors:
        # Fix duplicate Dr.
        clean_name = re.sub(r'^(Dr\.?\s*){2,}', 'Dr. ', doc_name, flags=re.IGNORECASE).strip()
        
        # Find image
        image_url = None
        if clean_name in csv_doctors:
            image_url = csv_doctors[clean_name]
        else:
            norm_name = re.sub(r'^Dr\.?\s*', '', clean_name, flags=re.IGNORECASE).strip()
            if norm_name in csv_doctors:
                image_url = csv_doctors[norm_name]
        
        if image_url:
            # Update doctor
            with conn.cursor() as cursor:
                cursor.execute("SELECT profile_image FROM doctors WHERE id = %s", (doc_id,))
                current_img = cursor.fetchone()[0]
                
                updates = []
                params = []
                
                if clean_name != doc_name:
                    updates.append("name = %s")
                    params.append(clean_name)
                    fixed += 1
                
                if not current_img or current_img.strip() == '':
                    updates.append("profile_image = %s")
                    params.append(image_url)
                    updated += 1
                
                if updates:
                    params.append(doc_id)
                    query = f"UPDATE doctors SET {', '.join(updates)} WHERE id = %s"
                    cursor.execute(query, params)
                    conn.commit()
                    print(f"✅ {clean_name}")
        else:
            # Remove if not in CSV
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM doctors WHERE id = %s", (doc_id,))
                conn.commit()
                removed += 1
                print(f"❌ Removed: {doc_name}")
    
    # Final stats
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM doctors")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM doctors WHERE profile_image IS NOT NULL AND profile_image != ''")
        with_img = cursor.fetchone()[0]
    
    coverage = int((with_img / total) * 100) if total > 0 else 0
    
    print(f"\nSUMMARY:")
    print(f"✅ Updated {updated} images")
    print(f"✅ Fixed {fixed} names")
    print(f"❌ Removed {removed} doctors")
    print(f"📊 Final: {with_img}/{total} doctors with images ({coverage}%)")
    
    conn.close()

if __name__ == "__main__":
    main()