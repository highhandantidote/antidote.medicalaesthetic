"""
Phase 2: Static Asset Optimization
Implements compression and caching for static assets
"""

import os
import gzip
import mimetypes
from pathlib import Path
from flask import Flask, send_from_directory, request, make_response

class StaticAssetOptimizer:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize static asset optimization"""
        app.config.setdefault('STATIC_CACHE_TIMEOUT', 31536000)  # 1 year
        app.config.setdefault('COMPRESS_STATIC_FILES', True)
        
        # Register optimized static file handler
        app.add_url_rule(
            '/static/css/<path:filename>',
            'optimized_css',
            self.serve_optimized_css,
            methods=['GET']
        )
        
        app.add_url_rule(
            '/static/js/<path:filename>',
            'optimized_js', 
            self.serve_optimized_js,
            methods=['GET']
        )
    
    def serve_optimized_css(self, filename):
        """Serve optimized CSS files with compression and caching"""
        css_dir = Path('static/css')
        
        # Check for minified version first
        minified_path = css_dir / filename.replace('.css', '.min.css')
        if minified_path.exists():
            return self._serve_with_optimization(minified_path, 'text/css')
        
        # Fallback to original file
        original_path = css_dir / filename
        if original_path.exists():
            return self._serve_with_optimization(original_path, 'text/css')
        
        # Return 404 for missing files
        return '', 404
    
    def serve_optimized_js(self, filename):
        """Serve optimized JavaScript files with compression and caching"""
        js_dir = Path('static/js')
        
        # Check for minified version first
        minified_path = js_dir / filename.replace('.js', '.min.js')
        if minified_path.exists():
            return self._serve_with_optimization(minified_path, 'application/javascript')
        
        # Fallback to original file
        original_path = js_dir / filename
        if original_path.exists():
            return self._serve_with_optimization(original_path, 'application/javascript')
        
        return '', 404
    
    def _serve_with_optimization(self, file_path, content_type):
        """Serve file with compression and caching headers"""
        # Check if client accepts gzip
        accepts_gzip = 'gzip' in request.headers.get('Accept-Encoding', '')
        
        # Try to serve gzipped version if available
        gzipped_path = Path(str(file_path) + '.gz')
        if accepts_gzip and gzipped_path.exists():
            with open(gzipped_path, 'rb') as f:
                content = f.read()
            
            response = make_response(content)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Type'] = content_type
            response.headers['Vary'] = 'Accept-Encoding'
        else:
            # Serve regular file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            response = make_response(content)
            response.headers['Content-Type'] = content_type
        
        # Add aggressive caching headers
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        response.headers['Expires'] = 'Thu, 31 Dec 2037 23:55:55 GMT'
        
        # Add ETag for cache validation
        import hashlib
        etag = hashlib.md5(content if isinstance(content, bytes) else content.encode()).hexdigest()
        response.headers['ETag'] = f'"{etag}"'
        
        return response
    
    def precompress_static_files(self):
        """Pre-compress static files for faster serving"""
        static_dir = Path('static')
        
        # Compress CSS files
        css_dir = static_dir / 'css'
        for css_file in css_dir.glob('*.css'):
            if not css_file.name.endswith('.min.css'):
                continue
                
            gzipped_path = Path(str(css_file) + '.gz')
            if not gzipped_path.exists() or css_file.stat().st_mtime > gzipped_path.stat().st_mtime:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                with gzip.open(gzipped_path, 'wt', encoding='utf-8') as f:
                    f.write(content)
        
        # Compress JS files
        js_dir = static_dir / 'js'
        if js_dir.exists():
            for js_file in js_dir.glob('*.js'):
                if not js_file.name.endswith('.min.js'):
                    continue
                    
                gzipped_path = Path(str(js_file) + '.gz')
                if not gzipped_path.exists() or js_file.stat().st_mtime > gzipped_path.stat().st_mtime:
                    with open(js_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    with gzip.open(gzipped_path, 'wt', encoding='utf-8') as f:
                        f.write(content)

# Initialize static optimizer
static_optimizer = StaticAssetOptimizer()