"""
Test script to manually add a mobile image to a banner slide for testing.
"""

import os
from app import app, db
from models import BannerSlide
from sqlalchemy import text

def test_mobile_banner_functionality():
    """Test the mobile banner functionality by adding a mobile image to an existing slide."""
    with app.app_context():
        print("Testing mobile banner functionality...")
        
        # Get the first banner slide
        slide = BannerSlide.query.first()
        if not slide:
            print("No banner slides found!")
            return False
            
        print(f"Found slide: {slide.title}")
        print(f"Current desktop image: {slide.image_url}")
        print(f"Current mobile image: {slide.mobile_image_url}")
        
        # Create a test mobile image URL
        test_mobile_url = "https://via.placeholder.com/600x400/ff6b6b/ffffff?text=Mobile+Test+Image"
        
        # Update the slide with a mobile image
        slide.mobile_image_url = test_mobile_url
        db.session.commit()
        
        print(f"Updated slide with mobile image: {test_mobile_url}")
        
        # Verify the update
        updated_slide = BannerSlide.query.get(slide.id)
        print(f"Verification - Mobile image URL: {updated_slide.mobile_image_url}")
        
        return True

if __name__ == "__main__":
    test_mobile_banner_functionality()