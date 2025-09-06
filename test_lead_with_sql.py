"""
Test lead source tracking using direct SQL execution.

This script tests the lead source tracking feature by:
1. Using direct SQL queries to create test leads with source information
2. Verifying the source is properly stored
3. Providing analytics on leads by source
"""

import os
import sys
import logging
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Get database connection string from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

def execute_sql(sql, params=None, fetch=False):
    """
    Execute SQL query with parameters.
    
    Args:
        sql (str): SQL query to execute
        params (tuple, optional): Parameters for the SQL query
        fetch (bool, optional): Whether to fetch results
        
    Returns:
        Various: Query results if fetch=True, otherwise None
    """
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        
        # Create a cursor
        cur = conn.cursor()
        
        # Execute the query
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        
        # Fetch results if requested
        result = None
        if fetch:
            result = cur.fetchall()
            
        # Commit changes
        conn.commit()
        
        # Get newly inserted row ID if this was an INSERT
        if cur.description is None and sql.strip().upper().startswith("INSERT"):
            try:
                return cur.fetchone()[0]  # Return the ID
            except:
                pass
                
        # Close cursor
        cur.close()
        
        return result
        
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error executing SQL: {error}")
        if conn:
            conn.rollback()
        return None
        
    finally:
        if conn:
            conn.close()

def insert_test_lead(source):
    """
    Insert a test lead with source tracking information.
    
    Args:
        source (str): Source of the lead
        
    Returns:
        int: ID of the newly inserted lead, or None on failure
    """
    try:
        # Current timestamp
        now = datetime.utcnow()
        
        # SQL to insert a test lead
        sql = """
            INSERT INTO leads (
                user_id, doctor_id, procedure_name, message, status, 
                created_at, patient_name, mobile_number, city, 
                preferred_date, consent_given, source
            ) VALUES (
                1, 3, %s, %s, 'pending',
                %s, %s, '9876543210', 'Mumbai',
                %s, TRUE, %s
            ) RETURNING id
        """
        
        # Parameters for the SQL query
        params = (
            f"Test Procedure ({source})",
            f"Test message from {source}",
            now,
            f"Test Patient ({source})",
            now,
            source
        )
        
        # Execute the query
        lead_id = execute_sql(sql, params)
        
        if lead_id:
            logger.info(f"Inserted test lead ID {lead_id} with source '{source}'")
            return lead_id
        else:
            logger.error(f"Failed to insert test lead with source '{source}'")
            return None
            
    except Exception as e:
        logger.error(f"Error inserting test lead: {str(e)}")
        return None
        
def verify_lead_source(lead_id, expected_source):
    """
    Verify that a lead has the expected source.
    
    Args:
        lead_id (int): ID of the lead to verify
        expected_source (str): Expected source value
        
    Returns:
        bool: True if source matches, False otherwise
    """
    try:
        # SQL to get lead source
        sql = "SELECT source FROM leads WHERE id = %s"
        
        # Execute the query
        result = execute_sql(sql, (lead_id,), fetch=True)
        
        if result and len(result) > 0:
            actual_source = result[0][0]
            
            if actual_source == expected_source:
                logger.info(f"✓ Source verification successful for lead ID {lead_id}")
                logger.info(f"  Expected: '{expected_source}', Got: '{actual_source}'")
                return True
            else:
                logger.error(f"✗ Source verification failed for lead ID {lead_id}")
                logger.error(f"  Expected: '{expected_source}', Got: '{actual_source}'")
                return False
        else:
            logger.error(f"Lead ID {lead_id} not found")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying lead source: {str(e)}")
        return False

def get_leads_by_source():
    """
    Get a summary of leads by source for analytics.
    
    Returns:
        list: List of (source, count) tuples
    """
    try:
        # SQL to count leads by source
        sql = """
            SELECT source, COUNT(*) as lead_count
            FROM leads
            WHERE source IS NOT NULL
            GROUP BY source
            ORDER BY lead_count DESC
        """
        
        # Execute the query
        result = execute_sql(sql, fetch=True)
        
        if result:
            # Log results
            logger.info("=== Leads by Source ===")
            for row in result:
                source, count = row
                logger.info(f"{source}: {count} leads")
                
            return result
        else:
            logger.info("No leads with source information found")
            return []
            
    except Exception as e:
        logger.error(f"Error getting leads by source: {str(e)}")
        return []

def delete_test_lead(lead_id):
    """
    Delete a test lead.
    
    Args:
        lead_id (int): ID of the lead to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # SQL to delete a lead
        sql = "DELETE FROM leads WHERE id = %s"
        
        # Execute the query
        execute_sql(sql, (lead_id,))
        
        logger.info(f"Deleted test lead ID {lead_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting test lead: {str(e)}")
        return False

def main():
    """Run the lead source tracking tests."""
    logger.info("Starting lead source tracking tests")
    
    # Test sources
    test_sources = [
        "Test - Doctor Page",
        "Test - Procedure Page",
        "Test - Doctors List Page"
    ]
    
    # Track created leads for cleanup
    created_leads = []
    
    # Insert and verify test leads for each source
    for source in test_sources:
        # Insert test lead
        lead_id = insert_test_lead(source)
        
        if lead_id:
            created_leads.append(lead_id)
            
            # Verify lead source
            verify_lead_source(lead_id, source)
    
    # Get analytics by source
    get_leads_by_source()
    
    # Clean up test leads (comment out to keep test data)
    logger.info("Cleaning up test leads...")
    for lead_id in created_leads:
        delete_test_lead(lead_id)
    
    logger.info("Lead source tracking tests completed")

if __name__ == "__main__":
    main()