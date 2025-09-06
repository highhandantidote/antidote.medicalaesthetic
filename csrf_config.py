"""
CSRF Configuration for OTP Authentication
Disables CSRF for specific OTP endpoints
"""

from flask_wtf.csrf import CSRFProtect

def configure_csrf_exemptions(csrf, app):
    """Configure CSRF exemptions for OTP endpoints"""
    
    @app.before_request
    def handle_otp_csrf():
        from flask import request
        # Exempt OTP authentication endpoints from CSRF
        if request.endpoint in ['otp_auth.send_otp', 'otp_auth.verify_otp']:
            return
    
    return csrf