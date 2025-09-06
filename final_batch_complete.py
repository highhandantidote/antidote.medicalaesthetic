#!/usr/bin/env python3
import os, csv, requests, psycopg2

# Load CSV and process remaining categories
csv_data = {}
with open('attached_assets/new_category_images - Sheet1.csv', 'r') as f:
    for row in csv.DictReader(f):
        csv_data[row['category_name'].strip()] = row['image_url'].strip()

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
updated = 0

with conn.cursor() as cursor:
    cursor.execute("SELECT id, name FROM categories WHERE image_url = '/static/images/categories/default-procedure.jpg' OR image_url IS NULL ORDER BY name")
    
    for cat_id, cat_name in cursor.fetchall():
        image_url = csv_data.get(cat_name)
        if not image_url:
            for csv_name, csv_url in csv_data.items():
                if cat_name.lower() in csv_name.lower() or csv_name.lower() in cat_name.lower():
                    image_url = csv_url
                    break
        
        if image_url and '/file/d/' in image_url:
            file_id = image_url.split('/file/d/')[1].split('/')[0]
            try:
                response = requests.get(f'https://drive.google.com/uc?export=download&id={file_id}', timeout=6)
                if response.status_code == 200:
                    safe_name = cat_name.lower().replace(' ', '_').replace(',', '').replace('&', 'and').replace('-', '_').replace('(', '').replace(')', '')
                    filepath = f'static/images/categories/{safe_name}.jpg'
                    
                    os.makedirs('static/images/categories', exist_ok=True)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    cursor.execute('UPDATE categories SET image_url = %s WHERE id = %s', (f'/static/images/categories/{safe_name}.jpg', cat_id))
                    updated += 1
                    print(f'✅ {cat_name}')
            except:
                pass
    
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM categories WHERE image_url != '/static/images/categories/default-procedure.jpg' AND image_url IS NOT NULL")
    total = cursor.fetchone()[0]
    print(f'🎉 {total}/43 categories now have beautiful images!')

conn.close()