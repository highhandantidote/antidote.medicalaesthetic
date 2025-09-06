#!/usr/bin/env python3
"""
Comprehensive testing for Antidote platform functionality.

This script runs comprehensive tests for the Antidote platform, including:
1. Doctor verification workflow
2. Procedure listing
3. Community threads and replies
"""
import logging
import time
import psycopg2
import os
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=f'antidote_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    filemode='w'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using environment variables."""
    try:
        # Get database credentials from environment variables
        host = os.environ.get('PGHOST', 'localhost')
        port = os.environ.get('PGPORT', '5432')
        user = os.environ.get('PGUSER', 'postgres')
        password = os.environ.get('PGPASSWORD', 'postgres')
        dbname = os.environ.get('PGDATABASE', 'antidote')
        
        # Create connection string
        connection_string = f"host={host} port={port} user={user} password={password} dbname={dbname}"
        
        # Connect to the database
        conn = psycopg2.connect(connection_string)
        
        logger.info(f"Successfully connected to the database: {dbname}")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to the database: {str(e)}")
        return None

def execute_query(conn, query, params=None, fetch=True):
    """Execute a SQL query and return the results."""
    try:
        # Create a cursor
        cur = conn.cursor()
        
        # Execute the query
        start_time = time.time()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Query executed in {elapsed_time:.4f} seconds")
        
        # Fetch results if requested
        results = None
        if fetch:
            results = cur.fetchall()
        
        # Commit changes if needed
        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            conn.commit()
        
        # Close the cursor
        cur.close()
        
        return results
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(f"Query: {query}")
        if params:
            logger.error(f"Params: {params}")
        return None

def test_doctor_verification(conn):
    """Test the doctor verification workflow."""
    logger.info("=== Testing Doctor Verification Workflow ===")
    
    try:
        # 1. Check Doctor Test (ID 101) verification status
        query = "SELECT id, name, verification_status, is_verified FROM doctors WHERE id = 101"
        result = execute_query(conn, query)
        
        if result:
            doctor_id, name, status, is_verified = result[0]
            logger.info(f"Doctor Test (ID 101): status={status}, is_verified={is_verified}")
            
            # Verify status is correct
            if status == 'verified' and is_verified:
                logger.info("✓ Test Case 1: Doctor Test (ID 101) is verified correctly")
            else:
                logger.error("✗ Test Case 1: Doctor Test (ID 101) verification status is incorrect")
        else:
            logger.error("✗ Test Case 1: Could not find Doctor Test (ID 101)")
        
        # 2. Check if a doctor was rejected (e.g., ID 103)
        query = "SELECT id, name, verification_status, is_verified FROM doctors WHERE id = 103"
        result = execute_query(conn, query)
        
        if result:
            doctor_id, name, status, is_verified = result[0]
            logger.info(f"Doctor ID 103: status={status}, is_verified={is_verified}")
            
            # Verify status is correct
            if status == 'rejected' and not is_verified:
                logger.info("✓ Test Case 2: Doctor ID 103 was rejected correctly")
            else:
                logger.error("✗ Test Case 2: Doctor ID 103 rejection status is incorrect")
        else:
            logger.error("✗ Test Case 2: Could not find Doctor ID 103")
        
        # 3. Check notification for approved doctor
        query = """
            SELECT n.id, n.user_id, n.type, n.message 
            FROM notifications n 
            JOIN doctors d ON n.user_id = d.user_id 
            WHERE d.id = 101 AND n.type = 'verification_approved' 
            LIMIT 1
        """
        result = execute_query(conn, query)
        
        if result:
            logger.info("✓ Notification was created for approved doctor")
        else:
            logger.error("✗ No notification found for approved doctor")
        
        # 4. Check notification for rejected doctor
        query = """
            SELECT n.id, n.user_id, n.type, n.message 
            FROM notifications n 
            JOIN doctors d ON n.user_id = d.user_id 
            WHERE d.id = 103 AND n.type = 'verification_rejected' 
            LIMIT 1
        """
        result = execute_query(conn, query)
        
        if result:
            logger.info("✓ Notification was created for rejected doctor")
        else:
            logger.error("✗ No notification found for rejected doctor")
        
    except Exception as e:
        logger.error(f"Error in doctor verification test: {str(e)}")

def test_procedures(conn):
    """Test the procedures functionality."""
    logger.info("\n=== Testing Procedures ===")
    
    try:
        # 1. Check if we have all required procedures
        query = "SELECT id, procedure_name, short_description FROM procedures ORDER BY id"
        results = execute_query(conn, query)
        
        if results:
            procedures = [row[1] for row in results]
            logger.info(f"Found {len(results)} procedures: {', '.join(procedures)}")
            
            # Check if all required procedures exist
            required_procedures = ['Rhinoplasty', 'Facelift', 'Eyelid Surgery', 'Botox', 'Lip Fillers']
            missing_procedures = [p for p in required_procedures if p not in procedures]
            
            if not missing_procedures:
                logger.info("✓ Test Case 3: All required procedures exist")
            else:
                logger.error(f"✗ Test Case 3: Missing procedures: {', '.join(missing_procedures)}")
        else:
            logger.error("✗ Test Case 3: No procedures found")
            
        # 2. Check procedure details
        query = "SELECT min_cost, max_cost, benefits, risks FROM procedures WHERE procedure_name = 'Rhinoplasty'"
        result = execute_query(conn, query)
        
        if result:
            min_cost, max_cost, benefits, risks = result[0]
            logger.info(f"Rhinoplasty: Cost Range ${min_cost}-${max_cost}")
            logger.info(f"Benefits: {benefits[:50]}...")
            logger.info(f"Risks: {risks[:50]}...")
            
            if min_cost and max_cost and risks:
                logger.info("✓ Procedure details are complete")
            else:
                logger.error("✗ Procedure details are incomplete")
        else:
            logger.error("✗ Could not find Rhinoplasty procedure details")
        
    except Exception as e:
        logger.error(f"Error in procedures test: {str(e)}")

def test_community(conn):
    """Test the community functionality."""
    logger.info("\n=== Testing Community ===")
    
    try:
        # 1. Check if we have all required threads
        query = "SELECT id, title, content FROM community ORDER BY id"
        results = execute_query(conn, query)
        
        if results:
            thread_titles = [row[1] for row in results]
            logger.info(f"Found {len(results)} community threads")
            for i, (id, title, content) in enumerate(results, 1):
                logger.info(f"  {i}. {title}: {content[:50]}...")
            
            # Check if we have at least 5 threads
            if len(results) >= 5:
                logger.info("✓ Test Case 4: At least 5 community threads exist")
            else:
                logger.error(f"✗ Test Case 4: Only found {len(results)} community threads (need at least 5)")
        else:
            logger.error("✗ Test Case 4: No community threads found")
            
        # 2. Check thread replies
        query = """
            SELECT thread_id, COUNT(*) as reply_count 
            FROM community_replies 
            GROUP BY thread_id 
            ORDER BY thread_id
        """
        results = execute_query(conn, query)
        
        if results:
            reply_counts = {row[0]: row[1] for row in results}
            logger.info(f"Found replies for {len(results)} threads")
            for thread_id, count in reply_counts.items():
                logger.info(f"  Thread ID {thread_id}: {count} replies")
            
            # Check if each thread has at least one reply
            thread_ids = [row[0] for row in execute_query(conn, "SELECT id FROM community")]
            threads_without_replies = [tid for tid in thread_ids if tid not in reply_counts]
            
            if not threads_without_replies:
                logger.info("✓ All community threads have replies")
            else:
                logger.error(f"✗ {len(threads_without_replies)} threads have no replies: {threads_without_replies}")
        else:
            logger.error("✗ No community replies found")
        
    except Exception as e:
        logger.error(f"Error in community test: {str(e)}")

def run_comprehensive_tests():
    """Run all comprehensive tests."""
    logger.info("Starting comprehensive tests for Antidote platform...")
    
    # Connect to the database
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to the database. Tests aborted.")
        return
    
    try:
        # 1. Test doctor verification workflow
        test_doctor_verification(conn)
        
        # 2. Test procedures
        test_procedures(conn)
        
        # 3. Test community
        test_community(conn)
        
        # Log summary
        logger.info("\n=== Test Summary ===")
        logger.info("All tests completed. Please review the log for details.")
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
    finally:
        # Close the database connection
        conn.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    run_comprehensive_tests()