#!/usr/bin/env python3
"""
Test script for logging in as admin and accessing admin dashboard.
This script uses requests to simulate a browser session.
"""

import os
import logging
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_admin_login():
    """Test admin login and admin dashboard access."""
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Define the base URL
    base_url = 'http://localhost:5000'
    
    # Step 1: Get the login page to obtain CSRF token
    logger.info("Accessing login page...")
    login_page = session.get(f"{base_url}/login")
    
    if login_page.status_code != 200:
        logger.error(f"Failed to access login page: Status code {login_page.status_code}")
        return
    
    # Parse the login page
    soup = BeautifulSoup(login_page.text, 'html.parser')
    
    # Find the CSRF token
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if not csrf_input:
        logger.error("CSRF token not found on login page")
        return
    
    csrf_token = csrf_input.get('value')
    logger.info(f"Found CSRF token: {csrf_token[:10]}...")
    
    # Step 2: Submit login form with admin credentials
    logger.info("Attempting to log in as admin...")
    login_data = {
        'csrf_token': csrf_token,
        'email': 'admin@antidote.com',
        'password': 'Admin1234',  # Standard test password (publicly visible in repo)
        'remember_me': 'y',
        'submit': 'Log In'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=True)
    
    # Check for successful login by looking for user-specific elements on the page
    soup = BeautifulSoup(login_response.text, 'html.parser')
    
    # Look for the navbar to see what elements are available after login
    nav_items = soup.select('nav .navbar-nav a, .dropdown-menu a')
    logger.info(f"Found {len(nav_items)} navigation items")
    
    nav_text = [item.text.strip() for item in nav_items if item.text.strip()]
    logger.info(f"Navigation items: {nav_text}")
    
    # Check for admin-specific navbar items or Dashboard link
    admin_indicators = [item for item in nav_text if 'Admin' in item or 'Dashboard' in item]
    logout_indicators = [item for item in nav_text if 'Logout' in item or 'Sign Out' in item]
    
    if admin_indicators or logout_indicators:
        logger.info(f"Login successful! Found indicators of being logged in: Admin/Dashboard={admin_indicators}, Logout={logout_indicators}")
    else:
        # Check for error messages
        error_msgs = soup.select('.alert-danger')
        
        if error_msgs:
            logger.error(f"Login failed: {error_msgs[0].text.strip()}")
        else:
            logger.error(f"Login status unclear. Current URL: {login_response.url}")
            logger.info("Response content preview: " + login_response.text[:200] + "...")
            return
    
    # Step 3: Try to access admin dashboard
    logger.info("Attempting to access admin dashboard...")
    dashboard_response = session.get(f"{base_url}/dashboard/admin")
    
    if dashboard_response.status_code != 200:
        logger.error(f"Failed to access admin dashboard: Status code {dashboard_response.status_code}")
        logger.info("Response content preview: " + dashboard_response.text[:200] + "...")
        return
    
    # Check if content looks like admin dashboard
    soup = BeautifulSoup(dashboard_response.text, 'html.parser')
    
    # Look for admin dashboard elements
    admin_elements = soup.select('.admin-dashboard, #admin-dashboard, h1:contains("Admin Dashboard"), h2:contains("Admin Dashboard")')
    
    if admin_elements:
        logger.info("Successfully accessed admin dashboard!")
        
        # Check for procedures section
        procedures_section = soup.select('#procedures, .procedures-section')
        
        if procedures_section:
            logger.info("Found procedures section in admin dashboard")
            
            # Count procedures
            procedure_rows = soup.select('#procedures table tbody tr')
            
            if not procedure_rows or len(procedure_rows) <= 1:  # Account for empty state row
                logger.warning("No procedure data found in admin dashboard table")
                
                # Look for empty state message
                empty_msg = soup.select('#procedures .alert-warning, #procedures .empty-state')
                if empty_msg:
                    logger.info(f"Empty state message found: {empty_msg[0].text.strip()}")
            else:
                logger.info(f"Found {len(procedure_rows)} procedure rows in admin dashboard")
                
                # Print first procedure details
                for i, row in enumerate(procedure_rows[:2]):
                    cells = row.select('td')
                    if cells:
                        logger.info(f"Procedure {i+1} data: ID={cells[0].text.strip()}, Name={cells[1].text.strip()}")
        else:
            logger.warning("Procedures section not found in admin dashboard")
    else:
        logger.error("Page doesn't appear to be admin dashboard")
        logger.info("Page title: " + soup.title.text if soup.title else "No title")
        logger.info("Headers: " + ', '.join([h.text for h in soup.select('h1, h2, h3')[:3]]))
        logger.info("Response content preview: " + dashboard_response.text[:200] + "...")

if __name__ == "__main__":
    test_admin_login()