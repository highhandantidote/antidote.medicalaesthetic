#!/usr/bin/env python3
"""
Add banners for all defined positions to the database.

This script creates banners with slides for each position defined in the banner system.
Uses direct SQL connections for better performance.
"""
import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Define banner positions
BANNER_POSITIONS = [
    'between_hero_stats',
    'between_procedures_specialists', 
    'between_categories_community',
    'before_footer'
]

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    return psycopg2.connect(db_url)

def add_banner_for_position(conn, position, position_index):
    """Add a banner with a test slide for a specific position using raw SQL."""
    try:
        with conn.cursor() as cursor:
            # Check if a banner with this position already exists
            cursor.execute(
                "SELECT id, is_active FROM banners WHERE position = %s",
                (position,)
            )
            banner_row = cursor.fetchone()
            
            if banner_row:
                banner_id, is_active = banner_row
                logger.info(f"Banner already exists with position '{position}' (ID: {banner_id})")
                
                # Check if it has any active slides
                cursor.execute(
                    "SELECT id, is_active FROM banner_slides WHERE banner_id = %s AND is_active = true",
                    (banner_id,)
                )
                active_slides = cursor.fetchall()
                
                if not active_slides:
                    logger.info("No active slides found. Adding a new test slide.")
                    
                    # Create a test slide for the existing banner
                    cursor.execute(
                        """
                        INSERT INTO banner_slides 
                        (banner_id, title, subtitle, image_url, redirect_url, display_order, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            banner_id,
                            f'Test Slide for {position}',
                            f'This is a test slide for banner position {position}',
                            f'https://placehold.co/600x200/9053b8/ffffff?text=Banner+{position_index}',
                            '#',
                            1,
                            True,
                            datetime.utcnow(),
                            datetime.utcnow()
                        )
                    )
                    slide_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    logger.info(f"Created new slide with ID: {slide_id}")
                else:
                    logger.info(f"Banner has {len(active_slides)} active slides")
                    
                    # Update the first active slide's image URL to use placehold.co
                    slide_id = active_slides[0][0]
                    cursor.execute(
                        """
                        UPDATE banner_slides 
                        SET image_url = %s, is_active = true, updated_at = %s
                        WHERE id = %s
                        """,
                        (
                            f'https://placehold.co/600x200/9053b8/ffffff?text=Banner+{position_index}',
                            datetime.utcnow(),
                            slide_id
                        )
                    )
                    conn.commit()
                    
                    logger.info(f"Updated slide {slide_id} with placeholder image URL")
                
                # Ensure the banner itself is active
                if not is_active:
                    cursor.execute(
                        "UPDATE banners SET is_active = true, updated_at = %s WHERE id = %s",
                        (datetime.utcnow(), banner_id)
                    )
                    conn.commit()
                    logger.info(f"Activated banner ID: {banner_id}")
                
                return
            
            # Create a new banner
            cursor.execute(
                """
                INSERT INTO banners 
                (name, position, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    f'Banner for {position}',
                    position,
                    True,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            banner_id = cursor.fetchone()[0]
            
            # Create a test slide
            cursor.execute(
                """
                INSERT INTO banner_slides 
                (banner_id, title, subtitle, image_url, redirect_url, display_order, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    banner_id,
                    f'Test Slide for {position}',
                    f'This is a test slide for banner position {position}',
                    f'https://placehold.co/600x200/9053b8/ffffff?text=Banner+{position_index}',
                    '#',
                    1,
                    True,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            slide_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Created banner ID: {banner_id} with slide ID: {slide_id}")
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding banner for position {position}: {str(e)}")
        raise

def add_all_banners():
    """Add banners for all defined positions."""
    conn = get_db_connection()
    try:
        for i, position in enumerate(BANNER_POSITIONS, 1):
            logger.info(f"Adding banner for position: {position}")
            add_banner_for_position(conn, position, i)
    finally:
        conn.close()

def main():
    """Run the script to add banners for all positions."""
    add_all_banners()

if __name__ == '__main__':
    main()