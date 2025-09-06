#!/usr/bin/env python3
"""
Add a test banner to the database.

This script creates a test banner with a test slide to help diagnose banner display issues.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import Flask app and models
from app import create_app, db
from models import Banner, BannerSlide

def add_test_banner():
    """Add a test banner with a test slide."""
    try:
        # Check if a banner with this position already exists
        existing_banner = Banner.query.filter_by(position='between_hero_stats').first()
        
        if existing_banner:
            logger.info(f"Banner already exists with position 'between_hero_stats' (ID: {existing_banner.id})")
            
            # Check if it has any active slides
            active_slides = [s for s in existing_banner.slides if s.is_active]
            
            if not active_slides:
                logger.info("No active slides found. Adding a new test slide.")
                
                # Create a test slide for the existing banner
                slide = BannerSlide(
                    banner_id=existing_banner.id,
                    title='Test Slide',
                    subtitle='This is a test slide',
                    image_url='https://placehold.co/600x400',
                    redirect_url='#',
                    display_order=1,
                    is_active=True
                )
                db.session.add(slide)
                db.session.commit()
                
                logger.info(f"Created new slide with ID: {slide.id}")
            else:
                logger.info(f"Banner has {len(active_slides)} active slides")
                
                # Update the first active slide's image URL to use placehold.co 
                active_slides[0].image_url = 'https://placehold.co/600x400'
                db.session.commit()
                
                logger.info(f"Updated slide {active_slides[0].id} with placeholder image URL")
            
            return
        
        # Create a new test banner
        banner = Banner(
            name='Test Banner',
            position='between_hero_stats',
            is_active=True
        )
        db.session.add(banner)
        db.session.flush()  # Get the banner ID
        
        # Create a test slide
        slide = BannerSlide(
            banner_id=banner.id,
            title='Test Slide',
            subtitle='This is a test slide',
            image_url='https://placehold.co/600x400',
            redirect_url='#',
            display_order=1,
            is_active=True
        )
        db.session.add(slide)
        db.session.commit()
        
        logger.info(f"Created banner ID: {banner.id} with slide ID: {slide.id}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding test banner: {str(e)}")
        raise

def main():
    """Run the script to add a test banner."""
    app = create_app()
    with app.app_context():
        add_test_banner()

if __name__ == '__main__':
    main()