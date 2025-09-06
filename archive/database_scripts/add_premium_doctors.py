#!/usr/bin/env python3
"""
Add premium doctors to the Antidote platform.

This script adds specialized doctors with premium credentials to enhance 
the marketplace's medical professional offerings.
"""

import os
import time
import logging
import psycopg2
import random
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = False  # We'll manage transactions manually
    return conn

def create_user_for_doctor(conn, doctor_name, email=None):
    """Create a user account for a doctor."""
    # Generate clean name, username, and phone number
    clean_name = doctor_name.replace("Dr. ", "").replace("Dr.", "").strip()
    username = clean_name.lower()
    username = ''.join(c for c in username if c.isalnum() or c.isspace()).replace(" ", ".")
    
    # Generate email if not provided
    if not email:
        email = f"{username}@example.com"
    
    # Generate phone number (using a consistent format for test data)
    phone_number = f"+91987{random.randint(1000000, 9999999)}"
    
    # Generate a random password
    password = f"Doctor{random.randint(10000, 99999)}"
    
    # Check if user already exists with this email
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            return existing_user[0]
        
        # Check if user exists with this phone number
        cursor.execute(
            "SELECT id FROM users WHERE phone_number = %s",
            (phone_number,)
        )
        if cursor.fetchone():
            # Generate a different phone number if this one exists
            phone_number = f"+91986{random.randint(1000000, 9999999)}"
        
        # Create new user
        cursor.execute(
            """
            INSERT INTO users (
                name, username, email, password_hash, phone_number, 
                role, role_type, is_verified, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """,
            (
                clean_name,
                username,
                email,
                generate_password_hash(password),
                phone_number,
                'doctor',  # Set role as doctor
                'doctor',  # Set role_type as doctor
                True,      # Set is_verified to true
                datetime.now()
            )
        )
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            logger.info(f"Created user account for doctor: {doctor_name} (ID: {user_id}, Email: {email})")
            return user_id
        else:
            logger.error(f"Failed to create user for doctor: {doctor_name}")
            return None

def add_premium_doctors():
    """Add premium doctors with specialized credentials."""
    conn = get_db_connection()
    doctors_added = 0
    
    try:
        # Premium doctor profiles with detailed information
        premium_doctors = [
            {
                "name": "Dr. Nandini Sharma",
                "specialty": "Advanced Facial Plastic Surgery",
                "education": "MBBS, MS (Plastic Surgery), Fellowship in Facial Plastic Surgery (London)",
                "experience": "15 years experience",
                "bio": "Dr. Sharma is a renowned facial plastic surgeon specializing in rhinoplasty and facial rejuvenation procedures. With extensive training in London and New York, she brings international expertise to her practice in Delhi.",
                "address": "Harmony Aesthetics Clinic, Defence Colony",
                "city": "New Delhi",
                "state": "Delhi",
                "consultation_fee": 3500,
                "ratings": 4.9,
                "ratings_count": 156
            },
            {
                "name": "Dr. Vikram Malhotra",
                "specialty": "Hair Restoration Specialist",
                "education": "MBBS, MD (Dermatology), Certification in Advanced Hair Transplantation (USA)",
                "experience": "12 years experience",
                "bio": "Dr. Malhotra is a leader in hair restoration techniques, pioneering several advanced methods now used throughout India. His clinic specializes in FUE and DHI hair transplantation with minimal downtime.",
                "address": "Mane Clinic, Bandra West",
                "city": "Mumbai",
                "state": "Maharashtra",
                "consultation_fee": 3000,
                "ratings": 4.8,
                "ratings_count": 212
            },
            {
                "name": "Dr. Priya Agarwal",
                "specialty": "Non-Surgical Facial Rejuvenation",
                "education": "MBBS, MD (Dermatology), Fellowship in Cosmetic Dermatology (Singapore)",
                "experience": "10 years experience",
                "bio": "Dr. Agarwal specializes in comprehensive non-surgical facial rejuvenation using the latest injectables, lasers, and energy devices. Her approach focuses on natural-looking results with minimal downtime.",
                "address": "Revive Aesthetics, Indiranagar",
                "city": "Bangalore",
                "state": "Karnataka",
                "consultation_fee": 2800,
                "ratings": 4.7,
                "ratings_count": 189
            },
            {
                "name": "Dr. Rajiv Menon",
                "specialty": "Body Contouring Surgeon",
                "education": "MBBS, MS (General Surgery), Fellowship in Cosmetic Surgery (Brazil)",
                "experience": "14 years experience",
                "bio": "Dr. Menon is a body contouring expert who trained in Brazil, the world capital of aesthetic surgery. He specializes in advanced liposculpture techniques that define and enhance the body's natural contours.",
                "address": "Contour Clinic, Anna Nagar",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "consultation_fee": 3200,
                "ratings": 4.8,
                "ratings_count": 147
            },
            {
                "name": "Dr. Sanjana Mehta",
                "specialty": "Aesthetic Dentistry",
                "education": "BDS, MDS (Prosthodontics), Certification in Smile Design (USA)",
                "experience": "9 years experience",
                "bio": "Dr. Mehta is a sought-after aesthetic dentist who combines technical precision with an artistic eye. Her practice focuses on comprehensive smile makeovers using veneers, bonding, and teeth whitening techniques.",
                "address": "Pristine Smiles, Jubilee Hills",
                "city": "Hyderabad",
                "state": "Telangana",
                "consultation_fee": 2500,
                "ratings": 4.9,
                "ratings_count": 178
            },
            {
                "name": "Dr. Arjun Kapoor",
                "specialty": "Reconstructive and Aesthetic Surgery",
                "education": "MBBS, MS (Plastic Surgery), DNB (Plastic Surgery), Fellowship in Microsurgery (Japan)",
                "experience": "16 years experience",
                "bio": "Dr. Kapoor combines reconstructive expertise with aesthetic principles to deliver exceptional results. His specialties include post-traumatic reconstruction and aesthetic enhancement procedures.",
                "address": "Renaissance Plastic Surgery, Civil Lines",
                "city": "Jaipur",
                "state": "Rajasthan",
                "consultation_fee": 3000,
                "ratings": 4.7,
                "ratings_count": 134
            },
            {
                "name": "Dr. Leela Krishnan",
                "specialty": "Advanced Laser Dermatology",
                "education": "MBBS, MD (Dermatology), Fellowship in Laser Medicine (Germany)",
                "experience": "11 years experience",
                "bio": "Dr. Krishnan is an expert in laser-based treatments for skin conditions and aesthetic concerns. Her German training gives her unique expertise in the latest laser technologies for rejuvenation and skin disorders.",
                "address": "Luminous Skin Clinic, Alwarpet",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "consultation_fee": 2700,
                "ratings": 4.8,
                "ratings_count": 165
            }
        ]
        
        # Process each doctor
        for doc in premium_doctors:
            try:
                # Check if doctor already exists
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM doctors WHERE name = %s",
                        (doc["name"],)
                    )
                    if cursor.fetchone():
                        logger.info(f"Doctor already exists: {doc['name']}")
                        continue
                
                # Create user account for doctor
                user_id = create_user_for_doctor(conn, doc["name"])
                
                if not user_id:
                    logger.error(f"Cannot add doctor without valid user_id: {doc['name']}")
                    continue
                
                # Convert experience string to integer years
                try:
                    exp_years = int(''.join(filter(str.isdigit, doc["experience"])))
                except (ValueError, TypeError):
                    exp_years = 10  # Default to 10 years if parsing fails
                
                # Insert doctor
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO doctors (
                            name, user_id, specialty,
                            experience, bio, city, state,
                            consultation_fee, is_verified, rating, review_count,
                            created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            doc["name"],
                            user_id,
                            doc["specialty"],
                            exp_years,  # Experience as integer
                            doc["bio"],
                            doc["city"],
                            doc["state"],
                            doc["consultation_fee"],
                            True,  # Set verified to true by default
                            doc.get("ratings", 4.5),  # Default rating if not specified
                            doc.get("ratings_count", 100),  # Default rating count if not specified
                            datetime.now()
                        )
                    )
                    result = cursor.fetchone()
                    if result:
                        doctor_id = result[0]
                        logger.info(f"Added premium doctor: {doc['name']} (ID: {doctor_id})")
                        doctors_added += 1
                        
                        # Commit each doctor individually
                        conn.commit()
                        
                        # Brief pause to avoid timeouts
                        time.sleep(0.2)
                    else:
                        logger.error(f"Failed to add doctor: {doc['name']}")
                        conn.rollback()
                
            except Exception as e:
                logger.error(f"Error adding doctor {doc['name']}: {str(e)}")
                conn.rollback()
        
        return doctors_added
        
    except Exception as e:
        logger.error(f"Error in add_premium_doctors: {str(e)}")
        return 0
    finally:
        conn.close()

def check_database_status():
    """Check the current status of the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check doctors
            cursor.execute("SELECT COUNT(*) FROM doctors")
            result = cursor.fetchone()
            doctor_count = result[0] if result else 0
            
            # Print summary
            logger.info("=" * 80)
            logger.info("PREMIUM DOCTORS IMPORT STATUS")
            logger.info("=" * 80)
            logger.info(f"Total Doctors in database: {doctor_count}")
            logger.info("=" * 80)
            
            # Get recently added doctors
            cursor.execute(
                """
                SELECT name, specialty, city, created_at
                FROM doctors
                ORDER BY created_at DESC
                LIMIT 5
                """
            )
            recent_doctors = cursor.fetchall()
            
            logger.info("RECENTLY ADDED DOCTORS:")
            for doc in recent_doctors:
                logger.info(f"  {doc[0]} - {doc[1]} in {doc[2]}")
            
            logger.info("=" * 80)
            
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
    finally:
        if conn:
            conn.close()

def main():
    """Run the premium doctors addition script."""
    start_time = time.time()
    
    # Add premium doctors
    doctors_added = add_premium_doctors()
    
    elapsed = time.time() - start_time
    logger.info(f"Added {doctors_added} premium doctors in {elapsed:.2f} seconds")
    
    # Check final database status
    check_database_status()
    
    logger.info("Premium doctors import complete!")

if __name__ == "__main__":
    main()