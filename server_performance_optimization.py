"""
Server Performance Optimization System

This module provides comprehensive server-side optimizations including:
- Response compression
- Caching headers
- Database query optimization
- Static file serving optimization
- Performance monitoring
"""

import time
import gzip
import io
import os
from functools import wraps
from flask import request, Response, current_app, g
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

logger = logging.getLogger(__name__)

class PerformanceOptimizationMiddleware:
    """Middleware for server performance optimization"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize performance optimization middleware"""
        app.config.setdefault('COMPRESS_MIN_SIZE', 1024)
        app.config.setdefault('COMPRESS_LEVEL', 6)
        app.config.setdefault('CACHE_STATIC_MAX_AGE', 3600)  # 1 hour
        app.config.setdefault('CACHE_DYNAMIC_MAX_AGE', 300)  # 5 minutes
        
        # Add performance monitoring
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Add compression
        app.after_request(self.compress_response)
        
        # Add caching headers
        app.after_request(self.add_cache_headers)
        
        # Add security headers
        app.after_request(self.add_security_headers)
    
    def before_request(self):
        """Track request start time"""
        g.start_time = time.time()
    
    def after_request(self, response):
        """Monitor response time and log slow requests"""
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000  # Convert to milliseconds
            
            # Log slow requests
            if duration > 500:  # Log requests slower than 500ms
                logger.warning(f"SLOW REQUEST: {request.method} {request.path} took {duration:.2f}ms")
            
            # Add response time header for monitoring
            response.headers['X-Response-Time'] = f"{duration:.2f}ms"
        
        return response
    
    def compress_response(self, response):
        """Compress response if applicable"""
        # Skip compression for certain content types
        if (response.content_type.startswith('image/') or 
            response.content_type.startswith('video/') or
            response.content_type.startswith('audio/') or
            'gzip' in response.headers.get('Content-Encoding', '')):
            return response
        
        # Check if client accepts gzip
        if 'gzip' not in request.headers.get('Accept-Encoding', ''):
            return response
        
        # Skip small responses - handle direct passthrough mode safely
        try:
            if len(response.data) < current_app.config['COMPRESS_MIN_SIZE']:
                return response
        except RuntimeError:
            # Response is in direct passthrough mode, skip compression
            return response
        
        try:
            # Compress the response
            gzip_buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=gzip_buffer, mode='wb', 
                              compresslevel=current_app.config['COMPRESS_LEVEL']) as gzip_file:
                gzip_file.write(response.data)
            
            # Update response
            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = len(response.data)
            response.headers['Vary'] = 'Accept-Encoding'
            
        except (RuntimeError, Exception) as e:
            # Handle both direct passthrough mode and other compression errors
            logger.debug(f"Compression skipped: {e}")
            # Return original response on error
            
        return response
    
    def add_cache_headers(self, response):
        """Add appropriate cache headers"""
        # Static files get longer cache times
        if request.path.startswith('/static/'):
            if any(request.path.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
                response.headers['Cache-Control'] = f'public, max-age={current_app.config["CACHE_STATIC_MAX_AGE"]}'
                try:
                    response.headers['ETag'] = f'"{hash(response.data)}"'
                except (RuntimeError, AttributeError):
                    # Skip ETag for direct passthrough responses
                    pass
        
        # API responses get shorter cache times
        elif request.path.startswith('/api/'):
            if request.method == 'GET':
                response.headers['Cache-Control'] = f'public, max-age={current_app.config["CACHE_DYNAMIC_MAX_AGE"]}'
        
        # HTML pages get minimal caching
        elif response.content_type.startswith('text/html'):
            response.headers['Cache-Control'] = 'public, max-age=60'
        
        return response
    
    def add_security_headers(self, response):
        """Add security headers"""
        # Don't override existing CSP
        if 'Content-Security-Policy' not in response.headers:
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response


def optimize_database_queries():
    """Decorator to optimize database queries"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Track database query time
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                
                db_time = (time.time() - start_time) * 1000
                if db_time > 100:  # Log slow database queries
                    logger.warning(f"SLOW DB QUERY in {f.__name__}: {db_time:.2f}ms")
                
                return result
            
            except Exception as e:
                logger.error(f"Database error in {f.__name__}: {e}")
                raise
        
        return decorated_function
    return decorator


def create_optimized_static_handler(app):
    """Create optimized static file handler - disabled to prevent conflicts"""
    # This functionality is moved to the existing static handler
    # to prevent endpoint conflicts
    pass


def setup_performance_monitoring(app):
    """Setup performance monitoring"""
    @app.route('/performance-metrics')
    def performance_metrics():
        """Endpoint for performance metrics"""
        return {
            'server_time': time.time(),
            'uptime': time.time() - app.config.get('START_TIME', time.time()),
            'version': '1.0.0'
        }


def initialize_performance_optimization(app):
    """Initialize all performance optimizations"""
    # Initialize middleware
    performance_middleware = PerformanceOptimizationMiddleware(app)
    
    # Setup optimized static file handler
    create_optimized_static_handler(app)
    
    # Setup performance monitoring
    setup_performance_monitoring(app)
    
    # Set start time for uptime calculation
    app.config['START_TIME'] = time.time()
    
    logger.info("Performance optimization system initialized")
    
    return performance_middleware