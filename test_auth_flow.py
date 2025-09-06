#!/usr/bin/env python3
"""
Test authentication flow for admin and clinic users.
This script will test the complete login flow including CSRF tokens.
"""

import requests
from bs4 import BeautifulSoup
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_login_flow():
    """Test complete login flow with CSRF token handling"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    # Test admin login
    logger.info("=== Testing Admin Login ===")
    
    # Step 1: Get login page to retrieve CSRF token
    login_page = session.get(f"{base_url}/login")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    
    # Find CSRF token
    csrf_token = None
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        logger.info(f"Found CSRF token: {csrf_token[:20]}...")
    else:
        # Try to find in meta tag
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta:
            csrf_token = csrf_meta.get('content')
            logger.info(f"Found CSRF token in meta: {csrf_token[:20]}...")
        else:
            logger.error("No CSRF token found")
            return False
    
    # Step 2: Login with admin credentials
    login_data = {
        'email': 'admin@antidote.com',
        'password': 'admin123',
        'csrf_token': csrf_token,
        'submit': 'Log In'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
    logger.info(f"Admin login response status: {login_response.status_code}")
    
    if login_response.status_code in [302, 303]:
        redirect_location = login_response.headers.get('Location', '')
        logger.info(f"Admin login redirected to: {redirect_location}")
        
        # Follow redirect
        if redirect_location:
            follow_response = session.get(f"{base_url}{redirect_location}")
            logger.info(f"Follow redirect status: {follow_response.status_code}")
    
    # Step 3: Test admin dashboard access
    logger.info("Testing admin dashboard access...")
    dashboard_response = session.get(f"{base_url}/dashboard/admin", allow_redirects=False)
    logger.info(f"Admin dashboard response status: {dashboard_response.status_code}")
    
    if dashboard_response.status_code == 200:
        logger.info("✅ Admin dashboard accessible")
    elif dashboard_response.status_code in [302, 303]:
        redirect_location = dashboard_response.headers.get('Location', '')
        logger.error(f"❌ Admin dashboard redirected to: {redirect_location}")
    else:
        logger.error(f"❌ Unexpected admin dashboard status: {dashboard_response.status_code}")
    
    # Test clinic login
    logger.info("\n=== Testing Clinic Login ===")
    session2 = requests.Session()
    
    # Get fresh login page for clinic user
    login_page2 = session2.get(f"{base_url}/login")
    soup2 = BeautifulSoup(login_page2.text, 'html.parser')
    
    csrf_token2 = None
    csrf_input2 = soup2.find('input', {'name': 'csrf_token'})
    if csrf_input2:
        csrf_token2 = csrf_input2.get('value')
        logger.info(f"Found CSRF token for clinic: {csrf_token2[:20]}...")
    
    # Login with clinic credentials
    login_data2 = {
        'email': 'clinic.test@example.com',
        'password': 'clinic123',
        'csrf_token': csrf_token2,
        'submit': 'Log In'
    }
    
    login_response2 = session2.post(f"{base_url}/login", data=login_data2, allow_redirects=False)
    logger.info(f"Clinic login response status: {login_response2.status_code}")
    
    if login_response2.status_code in [302, 303]:
        redirect_location2 = login_response2.headers.get('Location', '')
        logger.info(f"Clinic login redirected to: {redirect_location2}")
        
        # Follow redirect
        if redirect_location2:
            follow_response2 = session2.get(f"{base_url}{redirect_location2}")
            logger.info(f"Clinic follow redirect status: {follow_response2.status_code}")
    
    # Test clinic dashboard access
    logger.info("Testing clinic dashboard access...")
    clinic_dashboard_response = session2.get(f"{base_url}/clinic/dashboard", allow_redirects=False)
    logger.info(f"Clinic dashboard response status: {clinic_dashboard_response.status_code}")
    
    if clinic_dashboard_response.status_code == 200:
        logger.info("✅ Clinic dashboard accessible")
    elif clinic_dashboard_response.status_code in [302, 303]:
        redirect_location3 = clinic_dashboard_response.headers.get('Location', '')
        logger.error(f"❌ Clinic dashboard redirected to: {redirect_location3}")
    else:
        logger.error(f"❌ Unexpected clinic dashboard status: {clinic_dashboard_response.status_code}")

if __name__ == "__main__":
    test_login_flow()