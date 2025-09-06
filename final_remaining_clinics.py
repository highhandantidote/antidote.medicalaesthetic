#!/usr/bin/env python3
"""
Handle the final remaining 59 clinics without images using advanced matching techniques.
"""

import csv
import os
import psycopg2
import logging
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def similarity(a, b):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def process_remaining_clinics():
    """Process remaining clinics using advanced matching."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all remaining clinics without images
    cursor.execute("""
        SELECT id, name, city, address FROM clinics 
        WHERE profile_image IS NULL OR profile_image = ''
    """)
    
    remaining_clinics = cursor.fetchall()
    logger.info(f"Found {len(remaining_clinics)} clinics without images")
    
    # Load all CSV data
    csv_data = []
    csv_files = ['mumbai_clinics.csv', 'delhi_clinics.csv', 'bengaluru_clinics.csv', 
                 'gurugram_clinics.csv', 'chennai_clinics.csv', 'ahmedabad_clinics.csv',
                 'hyderabad_clinics.csv', 'kolkata_clinics.csv', 'jaipur_clinics.csv',
                 'visakhapatnam_clinics.csv']
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get('name', '').strip()
                    image = row.get('profile_image', '').strip()
                    if name and image and 'googleusercontent.com' in image:
                        csv_data.append({
                            'name': name,
                            'image': image[:255],  # Truncate
                            'city': row.get('city', '').strip()
                        })
    
    logger.info(f"Loaded {len(csv_data)} clinic records from CSV files")
    
    updated_count = 0
    
    # Try advanced matching for each remaining clinic
    for clinic_id, clinic_name, clinic_city, clinic_address in remaining_clinics:
        best_match = None
        best_score = 0
        
        # Try to find best matching clinic in CSV data
        for csv_clinic in csv_data:
            # Calculate similarity scores
            name_score = similarity(clinic_name, csv_clinic['name'])
            city_score = similarity(clinic_city, csv_clinic['city'])
            
            # Combined score with name being more important
            combined_score = (name_score * 0.8) + (city_score * 0.2)
            
            # If we have a good match (>85% similarity)
            if combined_score > 0.85 and combined_score > best_score:
                best_score = combined_score
                best_match = csv_clinic
        
        # If we found a good match, update the clinic
        if best_match:
            cursor.execute("""
                UPDATE clinics 
                SET profile_image = %s 
                WHERE id = %s
            """, (best_match['image'], clinic_id))
            
            if cursor.rowcount > 0:
                updated_count += 1
                logger.info(f"Matched '{clinic_name}' with '{best_match['name']}' (score: {best_score:.2f})")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return updated_count

def main():
    """Main function."""
    logger.info("Starting final push to complete clinic image coverage")
    
    updated = process_remaining_clinics()
    logger.info(f"Successfully matched {updated} additional clinics")
    
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
    
    # Show final remaining count by city
    cursor.execute("""
        SELECT city, COUNT(*) as count
        FROM clinics 
        WHERE profile_image IS NULL OR profile_image = '' 
        GROUP BY city 
        ORDER BY count DESC
    """)
    
    remaining = cursor.fetchall()
    if remaining:
        logger.info("Final remaining clinics by city:")
        for city, count in remaining:
            logger.info(f"  {city}: {count} clinics")
    else:
        logger.info("🎉 ALL CLINICS NOW HAVE IMAGES! 100% COVERAGE ACHIEVED!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()