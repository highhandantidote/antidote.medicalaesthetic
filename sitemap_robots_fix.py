"""
Sitemap Robots Header Fix
Ensures sitemap.xml has proper search engine headers by overriding any global noindex headers
"""

from flask import request

def register_sitemap_robots_fix(app):
    """Register middleware to fix robots headers for sitemap"""
    
    # Store the original after_request handlers
    original_handlers = app.after_request_funcs.get(None, []).copy()
    
    def fix_sitemap_robots_headers(response):
        """Final middleware to clean robots headers for sitemap - runs last"""
        
        # Only apply to sitemap.xml
        if request.path == '/sitemap.xml':
            # Create new headers dict, filtering out all robots headers
            new_headers = {}
            for key, value in response.headers:
                if not key.lower().startswith('x-robots') and not key.lower().startswith('replit-x-robots'):
                    new_headers[key] = value
            
            # Clear response headers and set new ones
            response.headers.clear()
            for key, value in new_headers.items():
                response.headers[key] = value
            
            # Set the correct robots header for search engines
            response.headers['X-Robots-Tag'] = 'index, follow, all'
            
            # Ensure proper caching for SEO
            response.headers['Cache-Control'] = 'public, max-age=3600'
            
            # Add verification header
            response.headers['X-Sitemap-Fix'] = 'applied'
            
        return response
    
    # Register our handler to run AFTER all others
    app.after_request(fix_sitemap_robots_headers)
    
    app.logger.info("✅ Sitemap robots header fix registered (final priority)")

if __name__ == "__main__":
    print("Sitemap robots header fix ready")