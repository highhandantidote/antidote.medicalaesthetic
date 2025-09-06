"""
Security Headers Middleware
Implements comprehensive security headers to ensure browser security
"""

from flask import g
import secrets

def add_security_headers(response):
    """Add comprehensive security headers to all responses."""
    
    # Generate nonce for inline scripts if not already set
    if not hasattr(g, 'nonce'):
        g.nonce = secrets.token_urlsafe(16)
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Allow camera access for face analysis, restrict others
    response.headers['Permissions-Policy'] = 'camera=*, microphone=(), geolocation=()'
    
    # Strict Transport Security (HSTS)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Temporarily disable CSP to test Firebase functionality
    # TODO: Re-enable with proper configuration once Firebase works
    # response.headers['Content-Security-Policy'] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    
    return response

def register_security_middleware(app):
    """Register security middleware with Flask app."""
    
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)
    
    # Add template context for nonce
    @app.context_processor
    def inject_security_context():
        if not hasattr(g, 'nonce'):
            g.nonce = secrets.token_urlsafe(16)
        return {
            'csp_nonce': g.nonce
        }
    
    app.logger.info("✅ Security headers middleware registered")