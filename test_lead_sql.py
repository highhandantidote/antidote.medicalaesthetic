"""
Test lead submission and source tracking using direct SQL queries.

This script tests lead submissions by:
1. Creating a test lead directly via SQL
2. Verifying it can be retrieved with the source information
3. Displaying a summary of leads by source for analytics purposes
"""

import os
import sys
import logging
from datetime import datetime
from app import app, db
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def insert_test_lead_via_sql(source):
    """
    Insert a test lead directly using SQL to test the database structure.
    
    Args:
        source (str): The source value to set for the lead
        
    Returns:
        int: The ID of the inserted lead, or None on failure
    """
    with app.app_context():
        try:
            # Current timestamp for the test
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            # SQL to insert a test lead
            sql = text("""
                INSERT INTO leads (
                    user_id, doctor_id, procedure_name, message, status, 
                    created_at, patient_name, mobile_number, city, 
                    preferred_date, consent_given, source
                ) VALUES (
                    1, 1, 'Test Procedure', 'SQL Test Message', 'pending',
                    :created_at, 'SQL Test Patient', '9876543210', 'Delhi',
                    :preferred_date, TRUE, :source
                ) RETURNING id
            """)
            
            # Execute the SQL with parameters
            result = db.session.execute(
                sql, 
                {
                    'created_at': current_time,
                    'preferred_date': current_time,
                    'source': source
                }
            )
            
            # Get the ID of the inserted lead
            lead_id = result.scalar()
            db.session.commit()
            
            logger.info(f"Inserted test lead with ID {lead_id} and source '{source}' via SQL")
            return lead_id
            
        except Exception as e:
            logger.error(f"Error inserting test lead via SQL: {str(e)}")
            db.session.rollback()
            return None

def verify_lead_source_via_sql(lead_id, expected_source):
    """
    Verify that a lead has the expected source using SQL.
    
    Args:
        lead_id (int): The ID of the lead to verify
        expected_source (str): The expected source value
        
    Returns:
        bool: True if the source matches, False otherwise
    """
    with app.app_context():
        try:
            # SQL to retrieve a lead by ID
            sql = text("SELECT source FROM leads WHERE id = :lead_id")
            
            # Execute the SQL with parameters
            result = db.session.execute(sql, {'lead_id': lead_id})
            
            # Get the source value
            actual_source = result.scalar()
            
            if actual_source == expected_source:
                logger.info(f"✓ Source verification successful for lead ID {lead_id}")
                logger.info(f"  Expected: '{expected_source}', Got: '{actual_source}'")
                return True
            else:
                logger.error(f"✗ Source verification failed for lead ID {lead_id}")
                logger.error(f"  Expected: '{expected_source}', Got: '{actual_source}'")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying lead source via SQL: {str(e)}")
            return False

def get_leads_by_source():
    """
    Get a summary of leads by source for analytics purposes.
    
    Returns:
        list: A list of tuples containing (source, count) information
    """
    with app.app_context():
        try:
            # SQL to count leads by source
            sql = text("""
                SELECT source, COUNT(*) as lead_count
                FROM leads
                WHERE source IS NOT NULL
                GROUP BY source
                ORDER BY lead_count DESC
            """)
            
            # Execute the SQL
            result = db.session.execute(sql)
            
            # Get the results
            source_counts = [(row[0], row[1]) for row in result]
            
            # Log the results
            logger.info("=== Leads by Source ===")
            for source, count in source_counts:
                logger.info(f"{source}: {count} leads")
                
            return source_counts
                
        except Exception as e:
            logger.error(f"Error getting leads by source: {str(e)}")
            return []

def delete_test_lead(lead_id):
    """
    Delete a test lead after verification.
    
    Args:
        lead_id (int): The ID of the lead to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    with app.app_context():
        try:
            # SQL to delete a lead by ID
            sql = text("DELETE FROM leads WHERE id = :lead_id")
            
            # Execute the SQL with parameters
            db.session.execute(sql, {'lead_id': lead_id})
            db.session.commit()
            
            logger.info(f"Deleted test lead with ID {lead_id}")
            return True
                
        except Exception as e:
            logger.error(f"Error deleting test lead: {str(e)}")
            db.session.rollback()
            return False

def main():
    """Run the SQL-based lead source tracking tests."""
    logger.info("Starting SQL-based lead source tracking tests")
    
    # Test sources
    test_sources = [
        "SQL Test - Doctor Page",
        "SQL Test - Procedure Page",
        "SQL Test - Doctors List Page"
    ]
    
    # Track created leads for cleanup
    created_leads = []
    
    # Insert and verify test leads for each source
    for source in test_sources:
        # Insert test lead
        lead_id = insert_test_lead_via_sql(source)
        
        if lead_id:
            created_leads.append(lead_id)
            
            # Verify lead source
            verify_lead_source_via_sql(lead_id, source)
    
    # Get analytics by source
    get_leads_by_source()
    
    # Clean up test leads
    logger.info("Cleaning up test leads...")
    for lead_id in created_leads:
        delete_test_lead(lead_id)
    
    logger.info("SQL-based lead source tracking tests completed")

if __name__ == "__main__":
    main()