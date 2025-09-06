#!/usr/bin/env python3
"""
Final clinic image import - fast processing of remaining files.
"""

import csv
import os
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def quick_import(csv_file):
    """Quick import from a single CSV file."""
    if not os.path.exists(csv_file):
        return 0, 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    updated = 0
    processed = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                processed += 1
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
        logger.info(f"✓ {csv_file}: {updated} updated from {processed} records")
        
    except Exception as e:
        logger.error(f"Error with {csv_file}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return updated, processed

def main():
    """Process remaining CSV files quickly."""
    files = [
        './mumbai_clinics.csv',
        './delhi_clinics.csv', 
        './gurugram_clinics.csv',
        './kolkata_clinics.csv',
        './chennai_clinics.csv',
        './ahmedabad_clinics.csv',
        './jaipur_clinics.csv'
    ]
    
    total_updated = 0
    total_processed = 0
    
    for csv_file in files:
        updated, processed = quick_import(csv_file)
        total_updated += updated
        total_processed += processed
    
    logger.info(f"Total: {total_updated} clinics updated from {total_processed} records")
    
    # Check final status
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total, 
               COUNT(CASE WHEN profile_image IS NOT NULL AND profile_image != '' THEN 1 END) as with_images
        FROM clinics
    """)
    
    result = cursor.fetchone()
    logger.info(f"Final status: {result[1]} of {result[0]} clinics have images ({result[1]/result[0]*100:.1f}%)")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()