
from flask import Flask, request, g
import time
import logging

class ServerResponseOptimizer:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        @app.before_request
        def before_request():
            g.start_time = time.time()
            
            # Skip processing for static files
            if request.path.startswith('/static/'):
                return
            
            # Add response timing
            g.request_start_time = time.time()
        
        @app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                total_time = time.time() - g.start_time
                response.headers['X-Response-Time'] = f"{total_time:.3f}s"
                
                # Log slow requests
                if total_time > 0.5:  # 500ms threshold
                    logging.warning(f"Slow request: {request.path} took {total_time:.3f}s")
            
            # Add performance headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            return response

# Global instance
server_optimizer = ServerResponseOptimizer()
