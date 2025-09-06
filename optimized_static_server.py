"""
Optimized static file server with WebP support and compression
Serves WebP images when available and supported by browser
"""
from flask import Blueprint, request, send_from_directory, abort
import os
from pathlib import Path

optimized_static = Blueprint('optimized_static', __name__)

@optimized_static.route('/static/<path:filename>')
def optimized_static_files(filename):
    """Serve optimized static files with WebP support"""
    static_dir = Path('static')
    requested_file = static_dir / filename
    
    # Check for WebP version if client supports it
    if _supports_webp() and _is_image(filename):
        webp_file = _get_webp_version(requested_file)
        if webp_file and webp_file.exists():
            return send_from_directory(
                webp_file.parent, 
                webp_file.name,
                cache_timeout=31536000  # 1 year cache
            )
    
    # Serve original file if it exists
    if requested_file.exists():
        cache_timeout = 31536000 if 'optimized/' in filename else 86400
        return send_from_directory(
            static_dir, 
            filename,
            cache_timeout=cache_timeout
        )
    
    abort(404)

def _supports_webp():
    """Check if client supports WebP format"""
    accept = request.headers.get('Accept', '')
    return 'image/webp' in accept

def _is_image(filename):
    """Check if file is an image"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
    return Path(filename).suffix.lower() in image_extensions

def _get_webp_version(file_path):
    """Get WebP version of image file"""
    if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
        return file_path.with_suffix('.webp')
    return None

@optimized_static.route('/health-check')
def health_check():
    """Ultra-fast health check endpoint"""
    return {'status': 'ok'}, 200

def register_optimized_static(app):
    """Register optimized static file serving"""
    app.register_blueprint(optimized_static)
    return optimized_static