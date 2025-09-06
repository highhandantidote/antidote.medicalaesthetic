#!/usr/bin/env python3
"""
Verify doctor count in index query.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def verify_doctor_count():
    """Verify doctor count in the index query."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Get database connection info from environment variables
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query all doctors
        cursor.execute("SELECT COUNT(*) as total FROM doctors")
        total_count = cursor.fetchone()['total']
        print(f"Total doctors in database: {total_count}")
        
        # Query doctors with ratings (not null)
        cursor.execute("SELECT COUNT(*) as rated FROM doctors WHERE rating IS NOT NULL")
        rated_count = cursor.fetchone()['rated']
        print(f"Doctors with ratings: {rated_count}")
        
        # Query doctors without ratings (null)
        cursor.execute("SELECT COUNT(*) as unrated FROM doctors WHERE rating IS NULL")
        unrated_count = cursor.fetchone()['unrated']
        print(f"Doctors without ratings: {unrated_count}")
        
        # Get sample of doctors with ratings
        cursor.execute("""
            SELECT id, name, city, rating 
            FROM doctors 
            WHERE rating IS NOT NULL 
            ORDER BY rating DESC 
            LIMIT 5
        """)
        print("\nTop rated doctors:")
        for doc in cursor.fetchall():
            print(f"ID: {doc['id']}, Name: {doc['name']}, City: {doc['city']}, Rating: {doc['rating']}")
        
        # Get sample of doctors without ratings
        cursor.execute("""
            SELECT id, name, city, rating 
            FROM doctors 
            WHERE rating IS NULL 
            LIMIT 5
        """)
        print("\nDoctors without ratings:")
        for doc in cursor.fetchall():
            print(f"ID: {doc['id']}, Name: {doc['name']}, City: {doc['city']}, Rating: {doc['rating']}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error verifying doctor count: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_doctor_count()