#!/usr/bin/env python3
"""
Final update of all remaining categories with your beautiful CSV images.
"""

import os
import csv
import requests
import psycopg2

def update_remaining_categories():
    # Load your CSV data
    csv_data = {}
    with open('attached_assets/new_category_images - Sheet1.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_data[row['category_name'].strip()] = row['image_url'].strip()
    
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    updated = 0
    
    try:
        with conn.cursor() as cursor:
            # Get all categories still needing updates
            cursor.execute("""
                SELECT id, name FROM categories 
                WHERE image_url = '/static/images/categories/default-procedure.jpg' 
                   OR image_url IS NULL
                ORDER BY name
            """)
            categories = cursor.fetchall()
            
            print(f"Updating {len(categories)} remaining categories...")
            
            for cat_id, cat_name in categories:
                # Find matching image
                image_url = None
                if cat_name in csv_data:
                    image_url = csv_data[cat_name]
                else:
                    for csv_name, csv_url in csv_data.items():
                        if cat_name.lower() in csv_name.lower() or csv_name.lower() in cat_name.lower():
                            image_url = csv_url
                            break
                
                if image_url:
                    # Extract file ID and download
                    if '/file/d/' in image_url:
                        file_id = image_url.split('/file/d/')[1].split('/')[0]
                    elif 'id=' in image_url:
                        file_id = image_url.split('id=')[1].split('&')[0]
                    else:
                        continue
                    
                    try:
                        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
                        response = requests.get(download_url, timeout=5)
                        
                        if response.status_code == 200:
                            safe_name = cat_name.lower().replace(' ', '_').replace(',', '').replace('&', 'and').replace('-', '_').replace('(', '').replace(')', '')
                            filepath = f"static/images/categories/{safe_name}.jpg"
                            local_url = f"/static/images/categories/{safe_name}.jpg"
                            
                            os.makedirs('static/images/categories', exist_ok=True)
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            
                            cursor.execute("UPDATE categories SET image_url = %s WHERE id = %s", (local_url, cat_id))
                            updated += 1
                            print(f"✅ {cat_name}")
                        
                    except:
                        continue
            
            conn.commit()
            
            # Final count
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url != '/static/images/categories/default-procedure.jpg' AND image_url IS NOT NULL")
            total_with_images = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]
            
            print(f"\n🎉 Update Complete!")
            print(f"📊 {total_with_images}/{total_categories} categories now have beautiful images")
            
    finally:
        conn.close()
    
    return updated

if __name__ == "__main__":
    update_remaining_categories()