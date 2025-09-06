"""
Responsive Image Serving Routes
Serves optimized images based on device type and browser support
"""

import os
from pathlib import Path
from flask import Blueprint, request, send_file, abort
from werkzeug.utils import secure_filename

# Create blueprint for responsive images
responsive_images = Blueprint('responsive_images', __name__)

def get_optimized_image_path(image_name, is_mobile=False):
    """Get the best optimized image path based on device and browser support"""
    
    # Check if WebP is supported
    accepts_webp = 'image/webp' in request.headers.get('Accept', '')
    
    # Base paths
    optimized_dir = Path("static/optimized")
    original_dir = Path("static/uploads/banners")
    
    # Get base name without extension
    base_name = Path(image_name).stem
    
    # Priority order: WebP mobile > WebP desktop > original
    if is_mobile and accepts_webp:
        mobile_webp = optimized_dir / f"{base_name}_mobile.webp"
        if mobile_webp.exists():
            return mobile_webp
    
    if accepts_webp:
        webp_path = optimized_dir / f"{base_name}.webp"
        if webp_path.exists():
            return webp_path
    
    # Fallback to original
    original_path = original_dir / image_name
    if original_path.exists():
        return original_path
    
    # Check in images directory
    images_path = Path("static/images") / image_name
    if images_path.exists():
        return images_path
    
    return None

@responsive_images.route('/optimized-image/<path:image_name>')
def serve_optimized_image(image_name):
    """Serve optimized image based on device and browser capabilities"""
    
    # Sanitize filename
    image_name = secure_filename(image_name)
    
    # Detect mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipad'])
    
    # Get optimized image path
    image_path = get_optimized_image_path(image_name, is_mobile)
    
    if not image_path:
        abort(404)
    
    # Set appropriate cache headers
    def add_cache_headers(response):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        response.headers['Expires'] = 'Thu, 31 Dec 2037 23:55:55 GMT'
        
        # Add format info
        if image_path.suffix.lower() == '.webp':
            response.headers['Content-Type'] = 'image/webp'
            response.headers['Vary'] = 'Accept'
        
        return response
    
    try:
        response = send_file(image_path)
        return add_cache_headers(response)
    except Exception as e:
        print(f"Error serving image {image_name}: {e}")
        abort(404)

@responsive_images.route('/banner/<path:image_name>')
def serve_banner_image(image_name):
    """Serve banner images with optimization"""
    return serve_optimized_image(image_name)

@responsive_images.route('/hero/<path:image_name>')
def serve_hero_image(image_name):
    """Serve hero images with optimization"""
    return serve_optimized_image(image_name)

# Template helper functions
def optimized_image_url(image_path, is_mobile=False):
    """Template helper to get optimized image URL"""
    from flask import url_for
    
    # Extract filename from path
    filename = Path(image_path).name
    
    # Check if optimized version exists
    optimized_path = get_optimized_image_path(filename, is_mobile)
    
    if optimized_path and optimized_path.exists():
        return url_for('responsive_images.serve_optimized_image', image_name=filename)
    
    # Fallback to original
    return f"/{image_path}"

def register_image_helpers(app):
    """Register template helpers for optimized images"""
    app.jinja_env.globals.update(
        optimized_image_url=optimized_image_url
    )