"""
Server-side compression middleware for Flask
Enables gzip compression for all static assets and responses
"""
from flask import Flask, request, g
import gzip
import os
from io import BytesIO

class CompressionMiddleware:
    """Middleware to enable gzip compression"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize compression middleware with Flask app"""
        app.config.setdefault('COMPRESS_MIMETYPES', [
            'text/html', 'text/css', 'text/xml', 'application/json',
            'application/javascript', 'text/javascript', 'application/xml',
            'text/plain', 'image/svg+xml'
        ])
        
        app.config.setdefault('COMPRESS_LEVEL', 6)
        app.config.setdefault('COMPRESS_MIN_SIZE', 500)
        
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Add cache headers for static files
        @app.after_request
        def add_cache_headers(response):
            """Add aggressive caching for static assets"""
            if request.endpoint == 'static':
                # Cache static files for 1 year
                response.cache_control.max_age = 31536000
                response.cache_control.public = True
                
                # Add immutable cache for CSS bundles
                if 'optimized/' in request.path:
                    response.cache_control.immutable = True
                    
            return response
    
    def should_compress(self, response):
        """Check if response should be compressed"""
        if not response:
            return False
            
        # Skip if response is in direct passthrough mode
        if response.direct_passthrough:
            return False
            
        # Don't compress if already compressed
        if response.headers.get('Content-Encoding'):
            return False
            
        # Check content type  
        content_type = response.headers.get('Content-Type', '')
        
        # Use Flask's current_app to get config if self.app is not available
        from flask import current_app
        app_config = self.app.config if self.app else current_app.config
        
        compress_mimetypes = app_config.get('COMPRESS_MIMETYPES', [
            'text/html', 'text/css', 'text/javascript', 'application/javascript',
            'application/json', 'text/plain', 'application/xml', 'text/xml'
        ])
        
        if not any(mt in content_type for mt in compress_mimetypes):
            return False
            
        # Check minimum size
        content_length = response.calculate_content_length()
        min_size = app_config.get('COMPRESS_MIN_SIZE', 500)
        if content_length and content_length < min_size:
            return False
            
        # Check if client accepts gzip
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' not in accept_encoding:
            return False
            
        return True
    
    def before_request(self):
        """Set up compression context before request"""
        g.compress_response = 'gzip' in request.headers.get('Accept-Encoding', '')
    
    def after_request(self, response):
        """Compress response if appropriate"""
        if not self.should_compress(response):
            return response
            
        # Skip if response is in direct passthrough mode
        if response.direct_passthrough:
            return response
            
        # Get response data
        data = response.get_data()
        
        # Compress data
        from flask import current_app
        app_config = self.app.config if self.app else current_app.config
        compress_level = app_config.get('COMPRESS_LEVEL', 6)
        
        gzip_buffer = BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode='wb', 
                          compresslevel=compress_level) as gz_file:
            gz_file.write(data)
        
        compressed_data = gzip_buffer.getvalue()
        
        # Update response
        response.set_data(compressed_data)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(compressed_data)
        response.headers['Vary'] = 'Accept-Encoding'
        
        return response

def enable_compression(app: Flask):
    """Enable compression for Flask app"""
    compression = CompressionMiddleware()
    compression.init_app(app)
    return compression