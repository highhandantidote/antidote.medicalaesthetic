"""
Banner caching system for instant hero banner loading.

This module provides memory-based caching for banner data to eliminate
database queries and provide instant banner loading.
"""

import os
import time
from flask import current_app
from models import Banner, BannerSlide


class BannerCache:
    """In-memory cache for banner data."""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.last_updated = {}
    
    def _is_cache_valid(self, key):
        """Check if cache entry is still valid."""
        if key not in self.cache or key not in self.last_updated:
            return False
        return time.time() - self.last_updated[key] < self.cache_timeout
    
    def get_hero_banner_data(self):
        """Get hero banner data from cache or database."""
        cache_key = 'hero_banner'
        
        # Return cached data if valid
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # Fetch from database and cache
        banner_data = self._fetch_hero_banner_from_db()
        if banner_data:
            self.cache[cache_key] = banner_data
            self.last_updated[cache_key] = time.time()
        
        return banner_data
    
    def _fetch_hero_banner_from_db(self):
        """Fetch hero banner data from database with optimized query."""
        try:
            # Single optimized query to get hero banner with active slides
            banner = Banner.query.filter_by(
                position='hero_banner', 
                is_active=True
            ).first()
            
            if not banner:
                return None
            
            # Get active slides
            active_slides = [slide for slide in banner.slides if slide.is_active]
            if not active_slides:
                return None
            
            # Process slides for optimal loading
            processed_slides = []
            for slide in active_slides:
                slide_data = {
                    'id': slide.id,
                    'title': slide.title,
                    'subtitle': slide.subtitle,
                    'redirect_url': slide.redirect_url,
                    'image_url': self._optimize_image_url(slide.image_url),
                    'mobile_image_url': self._optimize_image_url(slide.mobile_image_url),
                    'display_order': slide.display_order
                }
                processed_slides.append(slide_data)
            
            # Sort by display order
            processed_slides.sort(key=lambda x: x['display_order'])
            
            return {
                'id': banner.id,
                'name': banner.name,
                'position': banner.position,
                'slides': processed_slides
            }
            
        except Exception as e:
            current_app.logger.error(f"Error fetching hero banner: {e}")
            return None
    
    def _optimize_image_url(self, image_url):
        """Optimize image URL for WebP if available."""
        if not image_url:
            return None
        
        # Check for WebP version
        if image_url.endswith('.png') or image_url.endswith('.jpg'):
            webp_url = os.path.splitext(image_url)[0] + '.webp'
            webp_path = os.path.join(os.getcwd(), 'static', webp_url.lstrip('/static/'))
            
            if os.path.exists(webp_path):
                return webp_url
        
        return image_url
    
    def invalidate_cache(self, key=None):
        """Invalidate cache entries."""
        if key:
            self.cache.pop(key, None)
            self.last_updated.pop(key, None)
        else:
            self.cache.clear()
            self.last_updated.clear()
    
    def get_active_positions(self):
        """Get list of active banner positions (cached)."""
        cache_key = 'active_positions'
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # For now, just check if hero banner exists
        hero_data = self.get_hero_banner_data()
        positions = ['hero_banner'] if hero_data else []
        
        self.cache[cache_key] = positions
        self.last_updated[cache_key] = time.time()
        
        return positions


# Global cache instance
banner_cache = BannerCache()