#!/usr/bin/env python3
"""
Complete all category image updates efficiently.
"""

import os
import csv
import requests
import psycopg2
import threading
import time

def process_single_category(cat_id, cat_name, image_url, results):
    """Process a single category image download."""
    try:
        # Extract file ID
        if '/file/d/' in image_url:
            file_id = image_url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in image_url:
            file_id = image_url.split('id=')[1].split('&')[0]
        else:
            return
        
        # Download
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
        response = requests.get(download_url, timeout=8)
        
        if response.status_code == 200:
            safe_name = cat_name.lower().replace(' ', '_').replace(',', '').replace('&', 'and').replace('-', '_').replace('(', '').replace(')', '')
            filepath = f"static/images/categories/{safe_name}.jpg"
            local_url = f"/static/images/categories/{safe_name}.jpg"
            
            os.makedirs('static/images/categories', exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            results.append((cat_id, local_url, cat_name))
            print(f"✅ Downloaded: {cat_name}")
    except Exception as e:
        print(f"❌ Failed: {cat_name} - {e}")

def main():
    # Load CSV
    csv_data = {}
    with open('attached_assets/new_category_images - Sheet1.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_data[row['category_name'].strip()] = row['image_url'].strip()
    
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    
    try:
        with conn.cursor() as cursor:
            # Get remaining categories
            cursor.execute("""
                SELECT id, name FROM categories 
                WHERE image_url = '/static/images/categories/default-procedure.jpg' 
                   OR image_url IS NULL
                ORDER BY name
            """)
            categories = cursor.fetchall()
            
            if not categories:
                print("🎉 All categories already have beautiful images!")
                return
            
            print(f"🎨 Processing {len(categories)} remaining categories...")
            
            # Process categories in small batches
            batch_size = 10
            for i in range(0, len(categories), batch_size):
                batch = categories[i:i+batch_size]
                results = []
                threads = []
                
                print(f"\n📦 Processing batch {i//batch_size + 1}/{(len(categories) + batch_size - 1)//batch_size}")
                
                for cat_id, cat_name in batch:
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
                        thread = threading.Thread(
                            target=process_single_category,
                            args=(cat_id, cat_name, image_url, results)
                        )
                        threads.append(thread)
                        thread.start()
                
                # Wait for all downloads to complete
                for thread in threads:
                    thread.join()
                
                # Update database with successful downloads
                if results:
                    for cat_id, local_url, cat_name in results:
                        cursor.execute(
                            "UPDATE categories SET image_url = %s WHERE id = %s",
                            (local_url, cat_id)
                        )
                    conn.commit()
                    print(f"✅ Updated {len(results)} categories in database")
                
                # Small delay between batches
                time.sleep(1)
            
            # Final status
            cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url != '/static/images/categories/default-procedure.jpg' AND image_url IS NOT NULL")
            with_images = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM categories")
            total = cursor.fetchone()[0]
            
            print(f"\n🎉 Complete! {with_images}/{total} categories now have beautiful images")
            print(f"📈 Success rate: {(with_images/total)*100:.1f}%")
            
    finally:
        conn.close()

if __name__ == "__main__":
    main()