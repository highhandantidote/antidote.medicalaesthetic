#!/usr/bin/env python3
"""
Test admin access by checking the current user's role and permissions.
"""

import os
import requests
from urllib.parse import urljoin

def test_admin_access():
    """Test admin access to the dashboard."""
    base_url = "http://0.0.0.0:5000"
    
    # Create a session to maintain login state
    session = requests.Session()
    
    # Step 1: Login as admin
    print("Testing admin login...")
    login_data = {
        'email': 'admin@antidote.com',
        'password': 'admin123'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    print(f"Login response status: {login_response.status_code}")
    print(f"Login response headers: {login_response.headers}")
    
    if login_response.status_code in [302, 303]:
        redirect_location = login_response.headers.get('Location', '')
        print(f"Login redirected to: {redirect_location}")
        
        # Follow the redirect to complete login
        if redirect_location:
            full_redirect_url = urljoin(base_url, redirect_location)
            login_complete_response = session.get(full_redirect_url)
            print(f"Post-login page status: {login_complete_response.status_code}")
    
    # Step 2: Try to access admin dashboard
    print("\nTesting admin dashboard access...")
    dashboard_response = session.get(f"{base_url}/dashboard/admin", allow_redirects=False)
    print(f"Dashboard response status: {dashboard_response.status_code}")
    print(f"Dashboard response headers: {dashboard_response.headers}")
    
    if dashboard_response.status_code in [302, 303]:
        redirect_location = dashboard_response.headers.get('Location', '')
        print(f"Dashboard redirected to: {redirect_location}")
        
        # Check if redirected to homepage (indicates access denied)
        if '/' in redirect_location and 'admin' not in redirect_location:
            print("❌ Admin access denied - redirected to homepage")
            return False
    elif dashboard_response.status_code == 200:
        print("✅ Admin dashboard accessed successfully")
        return True
    else:
        print(f"❌ Unexpected response status: {dashboard_response.status_code}")
        return False
    
    return False

if __name__ == "__main__":
    test_admin_access()