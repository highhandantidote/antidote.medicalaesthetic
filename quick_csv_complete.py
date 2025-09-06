#!/usr/bin/env python3
"""
Quick completion of remaining category image updates.
"""

import os
import csv
import requests
import psycopg2

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def safe_filename(name):
    return name.lower().replace(' ', '_').replace(',', '').replace('&', 'and').replace('-', '_').replace('(', '').replace(')', '')

def extract_file_id(url):
    if '/file/d/' in url:
        return url.split('/file/d/')[1].split('/')[0]
    elif 'id=' in url:
        return url.split('id=')[1].split('&')[0]
    return None

def download_image_fast(url, filepath):
    try:
        file_id = extract_file_id(url)
        if not file_id:
            return False
        
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(download_url, timeout=8)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return True
    except:
        return False

def complete_remaining():
    # Load CSV
    csv_data = {}
    with open('attached_assets/new_category_images - Sheet1.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_data[row['category_name'].strip()] = row['image_url'].strip()
    
    conn = get_db_connection()
    updated = 0
    
    try:
        with conn.cursor() as cursor:
            # Get 5 categories that need updates
            cursor.execute("""
                SELECT id, name FROM categories 
                WHERE image_url = '/static/images/categories/default-procedure.jpg' 
                   OR image_url IS NULL
                ORDER BY name LIMIT 5
            """)
            categories = cursor.fetchall()
            
            for cat_id, cat_name in categories:
                # Find image
                image_url = None
                if cat_name in csv_data:
                    image_url = csv_data[cat_name]
                else:
                    for csv_name, csv_url in csv_data.items():
                        if cat_name.lower() in csv_name.lower() or csv_name.lower() in cat_name.lower():
                            image_url = csv_url
                            break
                
                if image_url:
                    safe_name = safe_filename(cat_name)
                    filepath = f"static/images/categories/{safe_name}.jpg"
                    local_url = f"/static/images/categories/{safe_name}.jpg"
                    
                    if download_image_fast(image_url, filepath):
                        cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", (local_url, cat_id))
                        updated += 1
                        print(f"✅ {cat_name}")
            
            conn.commit()
            
            # Show progress
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url != '/static/images/categories/default-procedure.jpg' AND image_url IS NOT NULL")
            with_images = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM categories")
            total = cursor.fetchone()[0]
            
            print(f"📊 {with_images}/{total} categories now have beautiful images")
            
    finally:
        conn.close()
    
    return updated

if __name__ == "__main__":
    updated = complete_remaining()
    print(f"Updated {updated} more categories with your beautiful CSV images!")