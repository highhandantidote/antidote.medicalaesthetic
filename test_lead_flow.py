"""
Test script for the lead submission flow.

This script tests the lead submission flow for the India launch by:
1. Mocking a user login
2. Creating a lead
3. Checking if the lead was stored in the database
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up the path to allow imports from the main application
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the application
from app import create_app, db
from models import Lead, Doctor, User
from flask import session

# Create a test application
app = create_app()

def test_lead_creation():
    """Test creating a lead and checking if it's stored in the database."""
    with app.app_context():
        # Simplified test - use direct SQL for better performance
        print("Setting up test data...")
        
        # Check if test user exists
        from sqlalchemy import text
        user_exists = db.session.execute(text("SELECT id FROM users WHERE id = 1")).fetchone()
        
        if not user_exists:
            print("Creating test user...")
            db.session.execute(text("""
                INSERT INTO users (id, username, email, role)
                VALUES (1, 'test_user', 'test@example.com', 'user')
            """))
            db.session.commit()
            print("Test user created with ID: 1")
        
        # Check if any doctor exists
        doctor_exists = db.session.execute(text("SELECT id FROM doctors LIMIT 1")).fetchone()
        
        test_doctor = None
        if not doctor_exists:
            print("Creating test doctor...")
            result = db.session.execute(text("""
                INSERT INTO doctors (name, specialty, experience, city, hospital, is_verified, user_id)
                VALUES ('Dr. Test Doctor', 'General Surgery', 10, 'Mumbai', 'Test Hospital', true, 1)
                RETURNING id
            """))
            doctor_id = result.fetchone()[0]
            db.session.commit()
            print(f"Test doctor created with ID: {doctor_id}")
            
            # Get the test doctor for our lead
            test_doctor = Doctor.query.get(doctor_id)
        else:
            # Use existing doctor
            test_doctor = Doctor.query.first()
        
        # Create a test lead
        print("\nCreating test lead...")
        new_lead = Lead(
            user_id=1,
            doctor_id=test_doctor.id if test_doctor else None,
            procedure_name="Rhinoplasty",  # Using the correct field name
            message="Test lead submission for India launch",
            status="pending",
            created_at=datetime.utcnow(),
            patient_name="Test Patient",
            mobile_number="9876543210",
            city="Mumbai",
            preferred_date=datetime.now(),
            consent_given=True
        )
        
        db.session.add(new_lead)
        db.session.commit()
        print(f"Test lead created with ID: {new_lead.id}")
        
        # Verify the lead was created
        lead = Lead.query.get(new_lead.id)
        assert lead is not None, "Lead was not found in the database"
        print("\nLead attributes:")
        print(f"- Patient Name: {lead.patient_name}")
        print(f"- Mobile: {lead.mobile_number}")
        print(f"- City: {lead.city}")
        print(f"- Procedure: {lead.procedure_name}")
        print(f"- Preferred Date: {lead.preferred_date}")
        print(f"- Doctor ID: {lead.doctor_id}")
        
        print("\n✅ Lead creation test passed!")
        return lead.id

def main():
    """Run the test script."""
    print("Testing lead submission flow for India launch...")
    lead_id = test_lead_creation()
    print(f"\nTo view the confirmation page, visit: /lead-confirmation/{lead_id}")
    print("To test the full flow manually:")
    print("1. Visit: /mock_login (sets session['user_id'] = 1)")
    print("2. Navigate to a procedure or doctor page")
    print("3. Click 'Book Consultation'")
    print("4. Fill out the form and submit")
    
if __name__ == "__main__":
    main()