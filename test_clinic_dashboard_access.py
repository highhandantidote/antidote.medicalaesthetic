"""
Test clinic dashboard access by programmatically logging in and checking authentication.
"""

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_clinic_dashboard_access():
    """Test the complete authentication flow and clinic dashboard access."""
    
    # Use session to maintain cookies
    session = requests.Session()
    base_url = "http://localhost:5000"
    
    try:
        # Step 1: Get login page and extract CSRF token
        logger.info("Getting login page...")
        login_page = session.get(f"{base_url}/login")
        logger.info(f"Login page status: {login_page.status_code}")
        
        if login_page.status_code != 200:
            logger.error(f"Failed to get login page: {login_page.status_code}")
            return False
            
        # Parse CSRF token from meta tag
        soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        
        if not csrf_meta:
            logger.error("CSRF token not found in login page")
            return False
            
        csrf_token = csrf_meta.get('content')
        logger.info(f"CSRF token extracted: {csrf_token[:20]}...")
        
        # Step 2: Submit login form
        logger.info("Submitting login credentials...")
        login_data = {
            'email': 'clinic.test@example.com',
            'password': 'clinic123',
            'csrf_token': csrf_token,
            'submit': 'Log In'
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        logger.info(f"Login response status: {login_response.status_code}")
        logger.info(f"Login response headers: {dict(login_response.headers)}")
        
        # Check if login was successful (should redirect)
        if login_response.status_code in [302, 303]:
            redirect_location = login_response.headers.get('Location', '')
            logger.info(f"Login redirected to: {redirect_location}")
            
            # Follow the redirect
            if redirect_location:
                if redirect_location.startswith('/'):
                    redirect_url = f"{base_url}{redirect_location}"
                else:
                    redirect_url = redirect_location
                    
                redirect_response = session.get(redirect_url)
                logger.info(f"Redirect response status: {redirect_response.status_code}")
        else:
            logger.error(f"Login failed with status: {login_response.status_code}")
            logger.error(f"Response text: {login_response.text[:500]}")
            return False
        
        # Step 3: Try to access clinic dashboard
        logger.info("Attempting to access clinic dashboard...")
        dashboard_response = session.get(f"{base_url}/clinic/dashboard", allow_redirects=False)
        logger.info(f"Dashboard response status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            logger.info("✅ Successfully accessed clinic dashboard!")
            # Check if the page contains expected content
            if "clinic" in dashboard_response.text.lower() and "dashboard" in dashboard_response.text.lower():
                logger.info("✅ Dashboard contains expected content")
                return True
            else:
                logger.warning("Dashboard accessible but may not contain expected content")
                return True
        elif dashboard_response.status_code in [302, 303]:
            redirect_location = dashboard_response.headers.get('Location', '')
            logger.error(f"❌ Dashboard still redirecting to: {redirect_location}")
            return False
        else:
            logger.error(f"❌ Dashboard access failed with status: {dashboard_response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing clinic dashboard access: {e}")
        return False

def main():
    """Main function to run the test."""
    logger.info("Starting clinic dashboard access test...")
    success = test_clinic_dashboard_access()
    
    if success:
        logger.info("✅ Clinic dashboard access test PASSED")
    else:
        logger.info("❌ Clinic dashboard access test FAILED")
        
    return success

if __name__ == "__main__":
    main()