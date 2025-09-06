#!/usr/bin/env python3
"""
Simplified lead submission test.

Directly tests database operations for lead submissions.
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
from app import create_app, db
from models import Lead, Doctor, User

# Create Flask app and set up application context
app = create_app()
app.app_context().push()

def test_lead_direct_insertion():
    """Test creating a lead record directly in the database."""
    
    # Get doctor ID for testing
    doctor = Doctor.query.first()
    doctor_id = doctor.id if doctor else None
    
    logger.info(f"Found doctor for testing: ID={doctor_id}, Name={doctor.name if doctor else 'None'}")
    
    # Create new lead record
    new_lead = Lead(
        user_id=1,  # Assuming test user ID 1 exists
        doctor_id=doctor_id,  # This might be None, which is now valid
        procedure_name='Rhinoplasty',
        message='This is a direct database test lead',
        status='pending',
        created_at=datetime.utcnow(),
        patient_name='Direct Test User',
        mobile_number='9876543210',
        city='Hyderabad',
        preferred_date=datetime.now() + timedelta(days=7),
        consent_given=True
    )
    
    logger.info("Creating test lead directly in database...")
    
    try:
        db.session.add(new_lead)
        db.session.commit()
        logger.info(f"Lead created successfully with ID: {new_lead.id}")
        return new_lead.id
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create lead: {str(e)}")
        return None

def main():
    """Run the test script."""
    print("\n===== Testing Direct Lead Database Operation =====\n")
    lead_id = test_lead_direct_insertion()
    
    if lead_id:
        print("\n✅ Lead direct database test completed successfully!")
        print(f"\nLead ID: {lead_id}")
    else:
        print("\n❌ Lead direct database test failed!")
    
if __name__ == "__main__":
    main()