"""
Initialize banners for the Antidote platform.

This script creates initial banners for the homepage with sample slides.
"""

import os
from app import create_app, db
from datetime import datetime
from models import Banner, BannerSlide

app = create_app()

def create_banners():
    """Create initial banners for the homepage."""
    
    # Check if banners already exist
    existing_banners = Banner.query.all()
    if existing_banners:
        print("Banners already exist. Skipping initialization.")
        return
    
    # Create banners for each position
    banners = [
        {
            'name': 'Hero-Stats Banner',
            'position': 'between_hero_stats',
            'slides': [
                {
                    'title': 'Find Your Perfect Doctor',
                    'subtitle': 'Connect with top plastic surgeons and cosmetic specialists in India',
                    'image_url': 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800&auto=format&fit=crop',
                    'redirect_url': '/doctors',
                    'display_order': 0
                },
                {
                    'title': 'Expert Consultations',
                    'subtitle': 'Schedule a consultation with verified specialists',
                    'image_url': 'https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800&auto=format&fit=crop',
                    'redirect_url': '/doctors',
                    'display_order': 1
                }
            ]
        },
        {
            'name': 'Popular-Top Banner',
            'position': 'between_popular_top',
            'slides': [
                {
                    'title': 'Discover Procedures',
                    'subtitle': 'Explore popular cosmetic and plastic surgery procedures',
                    'image_url': 'https://images.unsplash.com/photo-1588776813677-77aaf5595b83?w=800&auto=format&fit=crop',
                    'redirect_url': '/procedures',
                    'display_order': 0
                },
                {
                    'title': 'Latest Innovations',
                    'subtitle': 'Learn about cutting-edge techniques and technologies',
                    'image_url': 'https://images.unsplash.com/photo-1583911860205-72f8ac8ddcbe?w=800&auto=format&fit=crop',
                    'redirect_url': '/procedures',
                    'display_order': 1
                }
            ]
        },
        {
            'name': 'Explore-Community Banner',
            'position': 'between_explore_community',
            'slides': [
                {
                    'title': 'Join Our Community',
                    'subtitle': 'Connect with others and share your experiences',
                    'image_url': 'https://images.unsplash.com/photo-1573497620053-ea5300f94f21?w=800&auto=format&fit=crop',
                    'redirect_url': '/community',
                    'display_order': 0
                },
                {
                    'title': 'Ask Questions, Get Answers',
                    'subtitle': 'Get advice from real patients and healthcare professionals',
                    'image_url': 'https://images.unsplash.com/photo-1576089172869-4f5f6f315620?w=800&auto=format&fit=crop',
                    'redirect_url': '/community',
                    'display_order': 1
                }
            ]
        },
        {
            'name': 'Before-Footer Banner',
            'position': 'before_footer',
            'slides': [
                {
                    'title': 'Download Our App',
                    'subtitle': 'Access Antidote on the go with our mobile app',
                    'image_url': 'https://images.unsplash.com/photo-1616593918824-4fef16054381?w=800&auto=format&fit=crop',
                    'redirect_url': '#',
                    'display_order': 0
                },
                {
                    'title': 'Subscribe to Our Newsletter',
                    'subtitle': 'Stay updated with the latest procedures and medical advancements',
                    'image_url': 'https://images.unsplash.com/photo-1586769852044-692d6e3703f2?w=800&auto=format&fit=crop',
                    'redirect_url': '/newsletter',
                    'display_order': 1
                }
            ]
        }
    ]
    
    # Create the banners and slides
    for banner_data in banners:
        banner = Banner(
            name=banner_data['name'],
            position=banner_data['position']
        )
        db.session.add(banner)
        db.session.flush()  # Flush to get the banner ID
        
        for slide_data in banner_data['slides']:
            slide = BannerSlide(
                banner_id=banner.id,
                title=slide_data['title'],
                subtitle=slide_data['subtitle'],
                image_url=slide_data['image_url'],
                redirect_url=slide_data['redirect_url'],
                display_order=slide_data['display_order']
            )
            db.session.add(slide)
    
    db.session.commit()
    print(f"Created {len(banners)} banners with {sum(len(b['slides']) for b in banners)} slides.")

if __name__ == '__main__':
    with app.app_context():
        create_banners()