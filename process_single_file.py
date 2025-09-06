#!/usr/bin/env python3
"""
Process a single CSV file for clinic images.
"""

import csv
import os
import psycopg2
import sys

def process_file(csv_file):
    """Process a single CSV file."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()
    updated = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                name = row.get('name', '').strip()
                image = row.get('profile_image', '').strip()
                
                if name and image and 'googleusercontent.com' in image:
                    # Truncate long URLs
                    if len(image) > 255:
                        image = image[:255]
                    
                    cursor.execute("""
                        UPDATE clinics 
                        SET profile_image = %s 
                        WHERE name = %s AND (profile_image IS NULL OR profile_image = '')
                    """, (image, name))
                    
                    if cursor.rowcount > 0:
                        updated += 1
        
        conn.commit()
        print(f"✓ {csv_file}: {updated} clinics updated")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_file(sys.argv[1])
    else:
        print("Usage: python process_single_file.py <csv_file>")