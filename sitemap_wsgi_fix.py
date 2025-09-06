"""
WSGI Middleware for Sitemap Robots Headers Fix

This middleware operates at the WSGI level to ensure proper robots headers
for the sitemap.xml file, bypassing all Flask middleware conflicts.
"""

import re


class SitemapRobotsFixMiddleware:
    """WSGI middleware to fix robots headers specifically for sitemap.xml"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        """WSGI application entry point"""
        
        def new_start_response(status, response_headers, exc_info=None):
            """Intercept and modify response headers for sitemap.xml"""
            
            # Check if this is a request for sitemap.xml
            path_info = environ.get('PATH_INFO', '')
            if path_info == '/sitemap.xml':
                # Create completely new headers list, filtering ALL robots headers
                clean_headers = []
                
                # Find the intended robots header from the Flask route response first
                intended_robots_header = None
                for name, value in response_headers:
                    if name.lower() == 'x-robots-tag' and 'index, follow, all' in value:
                        intended_robots_header = ('X-Robots-Tag', 'index, follow, all')
                        break
                
                # Preserve only essential headers, completely removing all conflicting robots headers
                for name, value in response_headers:
                    name_lower = name.lower()
                    # Skip ALL robots headers from any source (they will all be conflicting)
                    if (name_lower.startswith('x-robots') or 
                        name_lower.startswith('replit-x-robots') or
                        'robots' in name_lower):
                        continue
                    
                    # Update cache control to proper SEO value
                    if name_lower == 'cache-control':
                        clean_headers.append(('Cache-Control', 'public, max-age=3600'))
                    else:
                        clean_headers.append((name, value))
                
                # Add the ONE correct robots header for search engines (from route or default)
                if intended_robots_header:
                    clean_headers.append(intended_robots_header)
                else:
                    clean_headers.append(('X-Robots-Tag', 'index, follow, all'))
                
                # Add verification header
                clean_headers.append(('X-Sitemap-WSGI-Fix', 'applied'))
                
                # Ensure cache control is set if it wasn't already
                if not any(h[0].lower() == 'cache-control' for h in clean_headers):
                    clean_headers.append(('Cache-Control', 'public, max-age=3600'))
                
                # Replace the entire headers list
                response_headers[:] = clean_headers
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, new_start_response)


def register_sitemap_wsgi_fix(app):
    """Register the WSGI middleware for sitemap robots fix"""
    app.wsgi_app = SitemapRobotsFixMiddleware(app.wsgi_app)
    app.logger.info("✅ Sitemap WSGI robots fix registered (lowest level)")