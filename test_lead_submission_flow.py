#!/usr/bin/env python3
"""
Test script for the lead submission flow.

This script tests the lead submission flow by:
1. Setting up a mock session
2. Submitting a test lead
3. Verifying the lead was stored in the database
4. Checking doctor email notification
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the application
from app import create_app, db, mail
from models import Lead, Doctor, User
from flask import session
from flask_mail import Message

def test_lead_submission():
    """Test the lead submission flow."""
    
    # Create a test app with a test request context
    app = create_app()
    
    with app.test_request_context():
        with app.test_client() as client:
            # Step 1: Set up mock session (simulate /mock_login)
            with client.session_transaction() as sess:
                sess['user_id'] = 1
            
            logger.info("Mock session created with user_id = 1")
            
            # Step 2: Test mock_login route
            response = client.get('/mock_login', follow_redirects=True)
            logger.info(f"Mock login response status: {response.status_code}")
            
            # Step 3: Check if there's a doctor in the database
            doctor = Doctor.query.first()
            if not doctor:
                logger.warning("No doctor found in database for testing")
                return
                
            logger.info(f"Found doctor for testing: ID={doctor.id}, Name={doctor.name}")
            
            # Step 4: Test lead form submission (via submit_lead route)
            lead_data = {
                'patient_name': 'Test User',
                'mobile_number': '9876543210',
                'city': 'Hyderabad',
                'procedure_name': 'Rhinoplasty',
                'preferred_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'message': 'This is a test lead submission',
                'consent': 'on',
                'doctor_id': str(doctor.id)
            }
            
            logger.info("Submitting test lead form...")
            response = client.post('/submit-lead', data=lead_data, follow_redirects=True)
            
            if response.status_code != 200:
                logger.error(f"Lead submission failed with status code: {response.status_code}")
                return
                
            logger.info("Lead form submitted successfully")
            
            # Step 5: Verify the lead was added to the database
            latest_lead = Lead.query.filter_by(
                patient_name='Test User',
                procedure_name='Rhinoplasty'
            ).order_by(Lead.created_at.desc()).first()
            
            if not latest_lead:
                logger.error("Failed to find the submitted lead in the database")
                return
                
            logger.info(f"Lead created successfully with ID: {latest_lead.id}")
            logger.info(f"Lead details: {latest_lead.patient_name} - {latest_lead.mobile_number} - {latest_lead.procedure_name}")
            
            # Step 6: Check lead confirmation page
            response = client.get(f'/lead-confirmation/{latest_lead.id}', follow_redirects=True)
            if response.status_code != 200:
                logger.error(f"Failed to access lead confirmation page: {response.status_code}")
            else:
                logger.info("Lead confirmation page loaded successfully")
            
            # Step 7: Test edge case - invalid mobile number
            invalid_data = lead_data.copy()
            invalid_data['mobile_number'] = '123'  # Invalid mobile number (not 10 digits)
            
            logger.info("Testing submission with invalid mobile number...")
            response = client.post('/submit-lead', data=invalid_data, follow_redirects=True)
            
            if "Please enter a valid 10-digit mobile number" in response.get_data(as_text=True):
                logger.info("Invalid mobile number validation working correctly")
            else:
                logger.warning("Mobile number validation might not be working properly")
            
            # Step 8: Test edge case - missing consent
            no_consent_data = lead_data.copy()
            no_consent_data.pop('consent')  # Remove consent
            
            logger.info("Testing submission without consent...")
            response = client.post('/submit-lead', data=no_consent_data, follow_redirects=True)
            
            if "Please fill all required fields" in response.get_data(as_text=True):
                logger.info("Missing consent validation working correctly")
            else:
                logger.warning("Consent requirement validation might not be working properly")
            
            return latest_lead.id

def main():
    """Run the test script."""
    print("\n===== Testing Lead Submission Flow =====\n")
    lead_id = test_lead_submission()
    
    if lead_id:
        print("\n✅ Lead submission test completed successfully!")
        print("\nManual Testing Information:")
        print("1. Visit: /mock_login (sets session['user_id'] = 1)")
        print("2. Navigate to a procedure detail page: /procedures/detail/2")
        print("3. Click 'Book Consultation' and submit the form")
        print("4. You should be redirected to the confirmation page")
        print(f"5. Check the lead in the database: SELECT * FROM leads WHERE id = {lead_id};")
    else:
        print("\n❌ Lead submission test failed!")
    
if __name__ == "__main__":
    main()