"""
Test the Lead model to verify the source field is properly implemented.

This script tests the Lead model directly by:
1. Creating a Lead object with source information
2. Saving it to the database
3. Retrieving it back to verify the source was saved correctly
"""

import os
import sys
import logging
from datetime import datetime
from app import app, db
from models import Lead

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_lead_model_with_source():
    """
    Test that the Lead model properly supports the source field.
    Creates a test lead with source information, saves it, and verifies it.
    """
    logger.info("Starting Lead model test with source field")
    
    # Create a test lead with source information
    test_sources = [
        "Doctor Page",
        "Procedure Page",
        "Doctors List Page"
    ]
    
    created_leads = []
    
    with app.app_context():
        try:
            # Test each source
            for i, source in enumerate(test_sources):
                # Create a test lead
                test_lead = Lead(
                    user_id=1,  # Assuming user with ID 1 exists for testing
                    doctor_id=1 if i != 1 else None,  # No doctor for procedure page
                    procedure_name=f"Test Procedure {i+1}",
                    message=f"Test message from {source}",
                    status='pending',
                    created_at=datetime.utcnow(),
                    patient_name=f"Test Patient {i+1}",
                    mobile_number="9876543210",
                    city="Mumbai",
                    preferred_date=datetime.utcnow(),
                    consent_given=True,
                    source=source
                )
                
                # Save to database
                db.session.add(test_lead)
                db.session.commit()
                
                logger.info(f"Created test lead ID {test_lead.id} with source: {source}")
                created_leads.append(test_lead.id)
                
                # Verify by retrieving the lead
                saved_lead = Lead.query.get(test_lead.id)
                
                if saved_lead.source == source:
                    logger.info(f"✓ Source field verification successful for '{source}'")
                else:
                    logger.error(f"✗ Source field verification failed for '{source}'")
                    logger.error(f"  Expected: '{source}', Got: '{saved_lead.source}'")
            
            # Clean up test data
            logger.info("Cleaning up test leads...")
            for lead_id in created_leads:
                lead_to_delete = Lead.query.get(lead_id)
                if lead_to_delete:
                    db.session.delete(lead_to_delete)
            
            db.session.commit()
            logger.info(f"Removed {len(created_leads)} test leads")
            
            logger.info("Lead model test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during Lead model test: {str(e)}")
            # Rollback transaction on error
            db.session.rollback()
            return False

if __name__ == "__main__":
    test_lead_model_with_source()