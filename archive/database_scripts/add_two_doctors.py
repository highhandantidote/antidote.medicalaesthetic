#!/usr/bin/env python3
"""
Add two specific doctors to the database.

This simplified script focuses on adding two specific doctors without complex error handling.
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging
import random
import hashlib
import string
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    conn.autocommit = True
    return conn

def add_doctors():
    """Add two specific doctors to the database."""
    conn = get_db_connection()
    
    # Define doctors to add
    doctors = [
        {
            'name': 'Dr. Raja Tiwari',
            'education': 'MBBS, MS',
            'specialty': 'Plastic Surgeon',
            'address': 'Cosmetic Surgery Clinic, Delhi',
            'experience': '12 years experience',
            'city': 'Delhi',
            'state': 'Delhi',
            'profile_image': 'https://cdn.plasticsurgery.org/images/profile/crop-default.jpg'
        },
        {
            'name': 'Dr. Madhu Kumar',
            'education': 'MBBS, MS',
            'specialty': 'Plastic Surgeon',
            'address': 'Kumar Aesthetic Center, Mumbai',
            'experience': '15 years experience',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'profile_image': 'https://cdn.plasticsurgery.org/images/profile/crop-default.jpg'
        }
    ]
    
    added_count = 0
    
    for doctor in doctors:
        try:
            # Create user account for doctor
            username = doctor['name'].replace('Dr. ', '').replace(' ', '').lower()
            email = f"{username}@example.com"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Check user table structure
            with conn.cursor() as cur:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
                columns = [col[0] for col in cur.fetchall()]
                logging.info(f"User table columns: {columns}")
            
            # Insert user with required fields
            with conn.cursor() as cur:
                # Check if the name field is required
                if 'name' in columns:
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, created_at, role, name)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (username, email, password_hash, datetime.now(), 'doctor', doctor['name']))
                else:
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, created_at, role)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (username, email, password_hash, datetime.now(), 'doctor'))
                
                user_id = cur.fetchone()[0]
            
            # Insert doctor
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO doctors (name, user_id, profile_image, education, specialty, address, experience, city, state, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    doctor['name'],
                    user_id,
                    doctor['profile_image'],
                    doctor['education'],
                    doctor['specialty'],
                    doctor['address'],
                    doctor['experience'],
                    doctor['city'],
                    doctor['state'],
                    datetime.now()
                ))
                
                doctor_id = cur.fetchone()[0]
                
                # Add a rating
                rating = round(random.uniform(3.5, 5.0), 1)
                cur.execute("""
                    INSERT INTO doctor_ratings (doctor_id, rating, created_at)
                    VALUES (%s, %s, %s)
                """, (doctor_id, rating, datetime.now()))
            
            logging.info(f"Added doctor: {doctor['name']} with rating {rating}")
            added_count += 1
            
        except Exception as e:
            logging.error(f"Error adding doctor {doctor['name']}: {e}")
    
    conn.close()
    logging.info(f"Added {added_count} doctors to the database")
    return added_count

def count_doctors():
    """Count doctors in the database."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM doctors")
        count = cur.fetchone()[0]
    conn.close()
    return count

def main():
    """Main function."""
    before_count = count_doctors()
    logging.info(f"Database has {before_count} doctors before import")
    
    add_doctors()
    
    after_count = count_doctors()
    logging.info(f"Database has {after_count} doctors after import")
    logging.info(f"Added {after_count - before_count} new doctors")

if __name__ == "__main__":
    main()