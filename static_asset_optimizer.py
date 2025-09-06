
from flask import Flask, request, send_file, make_response
import os
import hashlib
from pathlib import Path
import mimetypes

class StaticAssetOptimizer:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize static asset optimization"""
        
        @app.route('/static/<path:filename>')
        def optimized_static_v2(filename):
            """Serve static files with optimized headers"""
            static_path = Path(app.static_folder) / filename
            
            if not static_path.exists():
                return '', 404
            
            # Create response
            response = make_response(send_file(static_path))
            
            # Get file info
            file_stat = static_path.stat()
            file_size = file_stat.st_size
            file_mtime = file_stat.st_mtime
            
            # Generate ETag
            etag = hashlib.md5(f"{filename}{file_mtime}{file_size}".encode()).hexdigest()
            
            # Set caching headers based on file type
            if any(filename.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico']):
                # Long-term caching for static assets
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                response.headers['Expires'] = 'Thu, 31 Dec 2037 23:55:55 GMT'
            else:
                # Short-term caching for other files
                response.headers['Cache-Control'] = 'public, max-age=3600'
            
            # Add ETag for cache validation
            response.headers['ETag'] = f'"{etag}"'
            
            # Check if client has cached version
            if request.headers.get('If-None-Match') == f'"{etag}"':
                return '', 304
            
            # Add compression hint
            response.headers['Vary'] = 'Accept-Encoding'
            
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            return response
        
        print("Static asset optimization initialized")

# Global optimizer instance
static_optimizer = StaticAssetOptimizer()
