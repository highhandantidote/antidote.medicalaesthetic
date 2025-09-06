#!/usr/bin/env python3
"""
Fix missing banners by adding the correct banner positions.
"""

import os
import psycopg2
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def main():
    print("Adding missing banners...")
    
    conn = get_db_connection()
    
    # Missing banner positions that the homepage is looking for
    missing_positions = [
        'between_treatment_categories',
        'between_popular_procedures', 
        'between_top_specialists',
        'between_community_posts'
    ]
    
    added = 0
    for position in missing_positions:
        try:
            with conn.cursor() as cursor:
                # Check if banner already exists
                cursor.execute("SELECT id FROM banners WHERE position = %s", (position,))
                if cursor.fetchone():
                    print(f"✅ Banner already exists for {position}")
                    continue
                
                # Create banner
                cursor.execute("""
                    INSERT INTO banners (name, position, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    f"Banner for {position}",
                    position,
                    True,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                
                banner_id = cursor.fetchone()[0]
                
                # Create a slide for this banner
                cursor.execute("""
                    INSERT INTO banner_slides (
                        banner_id, title, subtitle, image_url, redirect_url,
                        display_order, is_active, click_count, impression_count, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    banner_id,
                    f"Special Offers - {position.replace('_', ' ').title()}",
                    f"Discover amazing deals and treatments in our {position.replace('_', ' ')} section",
                    f"https://placehold.co/600x200/9053b8/ffffff?text=Banner+{position}",
                    "#",
                    1,
                    True,
                    0,
                    0,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                
                conn.commit()
                added += 1
                print(f"✅ Added banner for {position} (ID: {banner_id})")
                
        except Exception as e:
            print(f"❌ Error adding banner for {position}: {e}")
            conn.rollback()
    
    print(f"\n🎉 Added {added} missing banners!")
    print("Your homepage banners should now be working properly!")
    
    conn.close()

if __name__ == "__main__":
    main()