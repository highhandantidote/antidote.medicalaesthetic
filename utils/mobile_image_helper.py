"""
Mobile Image Helper
Provides responsive image URLs based on device type and browser capabilities
"""

import os
from flask import request
from pathlib import Path

def get_responsive_image_url(image_path, default_fallback=None):
    """
    Returns appropriate image URL based on device type and WebP support
    
    Args:
        image_path: Original image path
        default_fallback: Fallback URL if optimized versions don't exist
    
    Returns:
        Optimized image URL based on device and browser capabilities
    """
    if not image_path:
        return default_fallback or ''
    
    # Check if it's a mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile_device = any(mobile in user_agent for mobile in [
        'mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'
    ])
    
    # Check WebP support
    accept_header = request.headers.get('Accept', '').lower()
    supports_webp = 'image/webp' in accept_header
    
    # For banner images, use specific optimized versions
    if '20250714081643_YouTube_Banner' in image_path:
        if is_mobile_device:
            return '/static/images/mobile-optimized/main_banner_mobile.webp'
        else:
            return '/static/images/optimized/main_banner_desktop.webp'
    
    # For hero bottom image
    if 'hero_bottom_image' in image_path:
        if is_mobile_device:
            return '/static/images/mobile-optimized/hero_bottom_image_mobile.webp'
        else:
            return '/static/images/optimized/hero_bottom_image_desktop.webp'
    
    # For general images, try to find optimized versions
    if supports_webp:
        # Try mobile-optimized first for mobile devices
        if is_mobile_device:
            mobile_path = image_path.replace('/static/images/', '/static/images/mobile-optimized/')
            mobile_path = mobile_path.replace('/static/uploads/', '/static/uploads/mobile-optimized/')
            mobile_path = mobile_path.rsplit('.', 1)[0] + '.webp'
            
            # Check if mobile-optimized file exists
            if os.path.exists(mobile_path.replace('/static/', 'static/')):
                return mobile_path
        
        # Try desktop optimized version
        desktop_path = image_path.replace('/static/images/', '/static/images/optimized/')
        desktop_path = desktop_path.replace('/static/uploads/', '/static/uploads/optimized/')
        desktop_path = desktop_path.rsplit('.', 1)[0] + '.webp'
        
        if os.path.exists(desktop_path.replace('/static/', 'static/')):
            return desktop_path
    
    # Return original if no optimized version exists
    return image_path

def create_responsive_image_srcset(image_path, sizes=None):
    """
    Creates responsive image srcset for different screen sizes
    
    Args:
        image_path: Base image path
        sizes: List of sizes to generate srcset for
    
    Returns:
        Dictionary with srcset and sizes attributes
    """
    if not image_path:
        return {'src': '', 'srcset': '', 'sizes': ''}
    
    # Default sizes for responsive images
    if sizes is None:
        sizes = ['mobile', 'desktop']
    
    srcset_parts = []
    
    # Mobile version
    if 'mobile' in sizes:
        mobile_url = get_responsive_image_url(image_path)
        if 'mobile-optimized' in mobile_url:
            srcset_parts.append(f"{mobile_url} 800w")
    
    # Desktop version
    if 'desktop' in sizes:
        desktop_url = get_responsive_image_url(image_path)
        if 'optimized' in desktop_url and 'mobile-optimized' not in desktop_url:
            srcset_parts.append(f"{desktop_url} 1200w")
    
    # Fallback to original
    if not srcset_parts:
        srcset_parts.append(f"{image_path} 1200w")
    
    return {
        'src': get_responsive_image_url(image_path),
        'srcset': ', '.join(srcset_parts) if srcset_parts else '',
        'sizes': '(max-width: 768px) 800px, 1200px'
    }

def optimize_image_loading(image_path, is_critical=False, loading='lazy'):
    """
    Returns optimized image attributes for performance
    
    Args:
        image_path: Image path
        is_critical: Whether this is a critical image (above fold)
        loading: Loading strategy ('lazy', 'eager', 'auto')
    
    Returns:
        Dictionary with optimized image attributes
    """
    responsive_data = create_responsive_image_srcset(image_path)
    
    attributes = {
        'src': responsive_data['src'],
        'loading': 'eager' if is_critical else loading,
        'decoding': 'async'
    }
    
    # Add srcset for responsive images
    if responsive_data['srcset']:
        attributes['srcset'] = responsive_data['srcset']
        attributes['sizes'] = responsive_data['sizes']
    
    # Add fetchpriority for critical images
    if is_critical:
        attributes['fetchpriority'] = 'high'
    
    return attributes

# Template helper functions
def register_mobile_image_helpers(app):
    """Register mobile image helpers with Flask app"""
    
    @app.template_global()
    def mobile_image_url(image_path, default_fallback=None):
        """Template helper for responsive image URLs"""
        return get_responsive_image_url(image_path, default_fallback)
    
    @app.template_global()
    def responsive_image_attrs(image_path, is_critical=False, loading='lazy'):
        """Template helper for responsive image attributes"""
        return optimize_image_loading(image_path, is_critical, loading)
    
    @app.template_global()
    def image_srcset(image_path, sizes=None):
        """Template helper for responsive image srcset"""
        return create_responsive_image_srcset(image_path, sizes)