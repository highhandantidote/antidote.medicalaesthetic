#!/usr/bin/env python3
"""
Fix remaining clinics without images - handle city name variations and missing matches.
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

def fix_bangalore_clinics():
    """Fix Bangalore clinics with city name variation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    updated = 0
    
    try:
        # Update Bangalore to Bengaluru in database for consistency
        cursor.execute("""
            UPDATE clinics SET city = 'Bengaluru' WHERE city = 'Bangalore'
        """)
        bangalore_updated = cursor.rowcount
        logger.info(f"Updated {bangalore_updated} clinics from Bangalore to Bengaluru")
        
        # Now process bengaluru_clinics.csv again
        with open('bengaluru_clinics.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                name = row.get('name', '').strip()
                image = row.get('profile_image', '').strip()
                
                if name and image and 'googleusercontent.com' in image:
                    # Truncate long URLs
                    if len(image) > 255:
                        image = image[:255]
                    
                    # Try exact match first
                    cursor.execute("""
                        UPDATE clinics 
                        SET profile_image = %s 
                        WHERE name = %s AND city = 'Bengaluru' AND (profile_image IS NULL OR profile_image = '')
                    """, (image, name))
                    
                    if cursor.rowcount > 0:
                        updated += 1
                    else:
                        # Try fuzzy match for slight variations
                        cursor.execute("""
                            UPDATE clinics 
                            SET profile_image = %s 
                            WHERE LOWER(name) = LOWER(%s) AND city = 'Bengaluru' AND (profile_image IS NULL OR profile_image = '')
                        """, (image, name))
                        
                        if cursor.rowcount > 0:
                            updated += 1
        
        conn.commit()
        logger.info(f"Fixed {updated} Bengaluru clinics with images")
        
    except Exception as e:
        logger.error(f"Error fixing Bangalore clinics: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return updated

def try_alternative_matching():
    """Try alternative matching methods for remaining clinics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    total_updated = 0
    
    csv_files = [
        'mumbai_clinics.csv',
        'delhi_clinics.csv',
        'gurugram_clinics.csv',
        'chennai_clinics.csv',
        'ahmedabad_clinics.csv',
        'hyderabad_clinics.csv',
        'kolkata_clinics.csv',
        'jaipur_clinics.csv',
        'visakhapatnam_clinics.csv'
    ]
    
    try:
        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                continue
                
            logger.info(f"Trying alternative matching for {csv_file}")
            updated = 0
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    name = row.get('name', '').strip()
                    image = row.get('profile_image', '').strip()
                    
                    if name and image and 'googleusercontent.com' in image:
                        # Truncate long URLs
                        if len(image) > 255:
                            image = image[:255]
                        
                        # Try partial matching for remaining clinics
                        cursor.execute("""
                            UPDATE clinics 
                            SET profile_image = %s 
                            WHERE name ILIKE %s AND (profile_image IS NULL OR profile_image = '')
                        """, (image, f"%{name}%"))
                        
                        if cursor.rowcount > 0:
                            updated += 1
            
            logger.info(f"Alternative matching for {csv_file}: {updated} clinics updated")
            total_updated += updated
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error in alternative matching: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    return total_updated

def main():
    """Main function to fix remaining clinics."""
    logger.info("Starting fix for remaining clinics without images")
    
    # Fix Bangalore/Bengaluru city name issue
    bengaluru_fixed = fix_bangalore_clinics()
    
    # Try alternative matching methods
    alternative_fixed = try_alternative_matching()
    
    logger.info(f"Total clinics fixed: {bengaluru_fixed + alternative_fixed}")
    
    # Check final status
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as total, 
               COUNT(CASE WHEN profile_image IS NOT NULL AND profile_image != '' THEN 1 END) as with_images
        FROM clinics
    """)
    
    result = cursor.fetchone()
    total, with_images = result
    coverage = (with_images / total * 100) if total > 0 else 0
    
    logger.info(f"Final status: {with_images} of {total} clinics have images ({coverage:.1f}%)")
    
    # Show remaining clinics by city
    cursor.execute("""
        SELECT city, COUNT(*) as missing_count
        FROM clinics 
        WHERE profile_image IS NULL OR profile_image = '' 
        GROUP BY city 
        ORDER BY missing_count DESC
    """)
    
    remaining = cursor.fetchall()
    logger.info("Remaining clinics without images by city:")
    for city, count in remaining:
        logger.info(f"  {city}: {count} clinics")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()