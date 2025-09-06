#!/usr/bin/env python3
"""
Quick category image updater - direct SQL approach for speed.
"""

import os
import csv
import psycopg2
import re

def main():
    database_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(database_url)
    
    # Mapping of CSV categories to direct image URLs
    image_mappings = {}
    
    # Read CSV file
    with open('attached_assets/category_images - Sheet1.csv', 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            category_name = row['category_name'].strip()
            image_url = row['image_url'].strip()
            
            # Convert Google Drive URL to direct URL
            file_id = None
            if 'drive.google.com' in image_url:
                match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', image_url)
                if match:
                    file_id = match.group(1)
                elif 'id=' in image_url:
                    file_id = image_url.split('id=')[1].split('&')[0]
                
                if file_id:
                    direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                else:
                    direct_url = image_url
            else:
                direct_url = image_url
            
            # Clean category name (remove body part in parentheses)
            clean_name = re.sub(r'\s*\([^)]+\)$', '', category_name).strip()
            image_mappings[clean_name.lower()] = direct_url
    
    print(f"Loaded {len(image_mappings)} image mappings from CSV")
    
    cursor = conn.cursor()
    
    # Clear all existing images first
    cursor.execute("UPDATE categories SET image_url = NULL")
    print("Cleared all existing category images")
    
    # Get all categories
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    
    updated_count = 0
    
    # Update each category with matching image
    for cat_id, cat_name in categories:
        cat_name_lower = cat_name.lower()
        
        # Try exact match first
        if cat_name_lower in image_mappings:
            cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", 
                         (image_mappings[cat_name_lower], cat_id))
            print(f"✅ Updated '{cat_name}' with exact match")
            updated_count += 1
        else:
            # Try partial matches
            for csv_name, image_url in image_mappings.items():
                if (csv_name in cat_name_lower or cat_name_lower in csv_name or
                    any(word in cat_name_lower for word in csv_name.split() if len(word) > 3)):
                    cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", 
                                 (image_url, cat_id))
                    print(f"✅ Updated '{cat_name}' with partial match to '{csv_name}'")
                    updated_count += 1
                    break
    
    conn.commit()
    print(f"🎉 Successfully updated {updated_count} category images!")
    
    # Final verification
    cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url IS NOT NULL")
    total_with_images = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM categories")
    total_categories = cursor.fetchone()[0]
    print(f"📊 Final status: {total_with_images}/{total_categories} categories now have images")
    
    conn.close()

if __name__ == "__main__":
    main()