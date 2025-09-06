#!/usr/bin/env python3
"""
Fix doctor email addresses in the database.
"""
import os
import sys
import logging
import random
import string
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a connection to the database."""
    import psycopg2
    
    # Get database connection info from environment variables
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)

def generate_valid_email(name, id):
    """Generate a valid email address from a doctor's name."""
    # Clean the name
    if not name or not isinstance(name, str):
        return f"doctor{id}@antidote.com"
    
    # Extract first name
    parts = name.split(' ')
    if len(parts) < 2:
        return f"doctor{id}@antidote.com"
    
    # Get the first name and last name
    first_name = parts[1].lower()  # Skip the "Dr." prefix
    
    # Remove non-alphanumeric characters
    first_name = ''.join(c for c in first_name if c.isalnum())
    
    # Generate email
    domain = "antidote.com"
    email = f"{first_name}{id}@{domain}"
    
    return email

def fix_doctor_emails():
    """Fix doctor email addresses in the database."""
    conn = get_db_connection()
    conn.autocommit = False
    cursor = conn.cursor()
    
    try:
        # Get all doctors with their current email addresses
        cursor.execute("""
            SELECT d.id, d.name, u.id as user_id, u.email 
            FROM doctors d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.id
        """)
        doctors = cursor.fetchall()
        
        if not doctors:
            logger.warning("No doctors found in the database")
            return
        
        print(f"Found {len(doctors)} doctors to fix")
        
        # Get all existing emails to avoid duplicates
        cursor.execute("SELECT email FROM users")
        existing_emails = set(row[0] for row in cursor.fetchall() if row[0])
        
        # Update each doctor's email
        fixed_count = 0
        for doctor in doctors:
            doctor_id, name, user_id, current_email = doctor
            
            # Skip if the email already looks valid
            if current_email and '@' in current_email:
                continue
            
            # Generate new email
            new_email = generate_valid_email(name, doctor_id)
            
            # Ensure email is unique
            while new_email in existing_emails:
                new_email = new_email.replace('@', f"{random.randint(1,999)}@")
            
            # Update the user's email
            cursor.execute(
                "UPDATE users SET email = %s WHERE id = %s",
                (new_email, user_id)
            )
            
            existing_emails.add(new_email)
            fixed_count += 1
            print(f"Updated {name} (ID: {doctor_id}): {current_email} -> {new_email}")
        
        if fixed_count > 0:
            conn.commit()
            print(f"Successfully fixed {fixed_count} doctor email addresses")
        else:
            print("No doctor email addresses needed fixing")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error fixing doctor emails: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_doctor_emails()