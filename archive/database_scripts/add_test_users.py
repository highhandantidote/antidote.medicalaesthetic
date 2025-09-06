"""
Add test users to the database, including an admin user.
"""
import os
import psycopg2
import logging
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from datetime import datetime

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def add_test_users():
    """Add test users to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if admin user already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", ('admin@antidote.com',))
        if cursor.fetchone():
            logger.info("Admin user already exists, skipping creation.")
        else:
            # Create admin user
            admin_password_hash = generate_password_hash('Admin1234')
            cursor.execute("""
                INSERT INTO users 
                (phone_number, name, email, role, username, password_hash, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, ('9999999999', 'Admin User', 'admin@antidote.com', 'admin', 'admin', 
                  admin_password_hash, datetime.utcnow()))
            admin_id = cursor.fetchone()[0]
            logger.info(f"Created admin user with ID: {admin_id}")
        
        # Check if test user already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", ('testuser@example.com',))
        if cursor.fetchone():
            logger.info("Test user already exists, skipping creation.")
        else:
            # Create test user
            user_password_hash = generate_password_hash('Password123')
            cursor.execute("""
                INSERT INTO users 
                (phone_number, name, email, role, username, password_hash, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, ('8888888888', 'Test User', 'testuser@example.com', 'user', 'testuser', 
                  user_password_hash, datetime.utcnow()))
            user_id = cursor.fetchone()[0]
            logger.info(f"Created test user with ID: {user_id}")
            
        # Check if test doctor user already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", ('testdoctor@example.com',))
        if cursor.fetchone():
            logger.info("Test doctor user already exists, skipping creation.")
        else:
            # Create test doctor user
            doctor_password_hash = generate_password_hash('Password123')
            cursor.execute("""
                INSERT INTO users 
                (phone_number, name, email, role, username, password_hash, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, ('7777777777', 'Test Doctor', 'testdoctor@example.com', 'doctor', 'testdoctor', 
                  doctor_password_hash, datetime.utcnow()))
            doctor_user_id = cursor.fetchone()[0]
            logger.info(f"Created test doctor user with ID: {doctor_user_id}")
            
            # Add doctor profile for test doctor user
            cursor.execute("""
                INSERT INTO doctors
                (user_id, name, specialty, experience, city, created_at, qualification)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (doctor_user_id, 'Dr. Test Doctor', 'Plastic Surgery', 5, 'Mumbai', 
                  datetime.utcnow(), 'MD, Plastic Surgery'))
            doctor_id = cursor.fetchone()[0]
            logger.info(f"Created doctor profile with ID: {doctor_id}")
            
        conn.commit()
        logger.info("All test users added successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding test users: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the test user creation."""
    try:
        add_test_users()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())