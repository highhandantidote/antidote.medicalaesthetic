#!/usr/bin/env python3
"""
Add a specific set of procedures and doctors directly to the database.

This script uses minimal SQL commands to add exactly 25 procedures and 15 doctors.
"""
import os
import psycopg2
import json
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """Get a database connection."""
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def add_procedures():
    """Add a specific set of procedures."""
    procedures = [
        {
            "name": "Advanced Microdermabrasion",
            "description": "A non-invasive exfoliation treatment that removes dead skin cells."
        },
        {
            "name": "Crystal Clear Facial",
            "description": "A deep cleansing facial that uses crystal microparticles."
        },
        {
            "name": "DeepRenu Face Treatment",
            "description": "An intensive facial rejuvenation treatment for mature skin."
        },
        {
            "name": "EternalYouth Facial",
            "description": "Anti-aging treatment that reduces fine lines and wrinkles."
        },
        {
            "name": "Facial Contour Pro",
            "description": "Sculpting treatment that defines facial contours."
        },
        {
            "name": "Glow Factor Treatment",
            "description": "Brightening treatment for dull, tired skin."
        },
        {
            "name": "Harmony Lift",
            "description": "Non-surgical facelift using advanced techniques."
        },
        {
            "name": "Intensity Peel",
            "description": "Chemical peel that removes damaged layers of skin."
        },
        {
            "name": "Jewel Tone Facial",
            "description": "Luxury facial with gemstone-infused products."
        },
        {
            "name": "Kaya Deep Cleanse",
            "description": "Deep pore cleansing treatment for oily skin."
        },
        {
            "name": "Luminous Lift Pro",
            "description": "Lifting and firming treatment for sagging skin."
        },
        {
            "name": "Micro Touch Therapy",
            "description": "Microcurrent treatment that tones facial muscles."
        },
        {
            "name": "Natural Radiance Boost",
            "description": "Organic treatment that enhances skin's natural glow."
        },
        {
            "name": "Oxygen Infusion Facial",
            "description": "Treatment that infuses oxygen into the skin."
        },
        {
            "name": "Pristine Peel Treatment",
            "description": "Gentle peel that improves skin texture."
        },
        {
            "name": "Quantum Skin Renewal",
            "description": "Advanced treatment that accelerates skin renewal."
        },
        {
            "name": "Radiance Restore Pro",
            "description": "Restores radiance to dull, dehydrated skin."
        },
        {
            "name": "Silken Smooth Facial",
            "description": "Leaves skin with a silky smooth texture."
        },
        {
            "name": "Timeless Beauty Ritual",
            "description": "Anti-aging ritual with multiple steps."
        },
        {
            "name": "Ultra Glow Treatment",
            "description": "Instant glow-boosting treatment."
        },
        {
            "name": "Vital Rejuvenation",
            "description": "Comprehensive facial rejuvenation treatment."
        },
        {
            "name": "Wellness Facial Therapy",
            "description": "Holistic facial that promotes overall wellness."
        },
        {
            "name": "Xcelerate Skin Renew",
            "description": "Accelerates skin cell turnover."
        },
        {
            "name": "Youth Extend Facial",
            "description": "Anti-aging treatment that extends youthful appearance."
        },
        {
            "name": "Zenith Beauty Treatment",
            "description": "Ultimate luxury facial experience."
        }
    ]

    conn = get_connection()
    added_count = 0
    try:
        # Get or create Face body part
        body_part_id = None
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM body_parts WHERE name = 'Face'")
            result = cursor.fetchone()
            if result:
                body_part_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO body_parts (name, created_at) VALUES ('Face', %s) RETURNING id",
                    (datetime.utcnow(),)
                )
                body_part_id = cursor.fetchone()[0]
                conn.commit()
        
        # Get or create Facial Treatments category
        category_id = None
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM categories WHERE name = 'Facial Treatments'")
            result = cursor.fetchone()
            if result:
                category_id = result[0]
            else:
                cursor.execute(
                    "INSERT INTO categories (name, body_part_id, created_at) VALUES ('Facial Treatments', %s, %s) RETURNING id",
                    (body_part_id, datetime.utcnow())
                )
                category_id = cursor.fetchone()[0]
                conn.commit()
        
        # Add each procedure
        for procedure in procedures:
            with conn.cursor() as cursor:
                # Check if procedure exists
                cursor.execute(
                    "SELECT id FROM procedures WHERE procedure_name = %s",
                    (procedure["name"],)
                )
                if cursor.fetchone():
                    logger.info(f"Procedure {procedure['name']} already exists. Skipping.")
                    continue
                
                # Insert procedure
                cursor.execute("""
                    INSERT INTO procedures (
                        procedure_name, 
                        short_description, 
                        overview, 
                        procedure_details, 
                        ideal_candidates, 
                        recovery_time, 
                        min_cost, 
                        max_cost, 
                        risks, 
                        procedure_types, 
                        category_id, 
                        body_part, 
                        tags, 
                        body_area, 
                        category_type, 
                        created_at, 
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    procedure["name"],
                    procedure["description"],
                    f"A premium facial treatment for rejuvenation and beauty enhancement.",
                    f"The {procedure['name']} is performed by trained aestheticians.",
                    "Adults seeking facial rejuvenation",
                    "1-3 days",
                    10000,
                    30000,
                    "Minor redness or irritation (temporary)",
                    "Standard",
                    category_id,
                    "Face",
                    ["facial", "cosmetic", "rejuvenation"],
                    "Face",
                    "Facial Treatments",
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                conn.commit()
                added_count += 1
                logger.info(f"Added procedure: {procedure['name']}")
    
    except Exception as e:
        logger.error(f"Error adding procedures: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return added_count

def add_doctors():
    """Add a specific set of doctors."""
    doctors = [
        {"name": "Dr. Anand Sharma", "specialty": "Cosmetic Surgeon", "city": "Mumbai"},
        {"name": "Dr. Bhavna Patel", "specialty": "Plastic Surgeon", "city": "Delhi"},
        {"name": "Dr. Chetan Desai", "specialty": "Facial Plastic Surgeon", "city": "Bengaluru"},
        {"name": "Dr. Divya Agarwal", "specialty": "Aesthetic Surgeon", "city": "Chennai"},
        {"name": "Dr. Eshan Gupta", "specialty": "Plastic Surgeon", "city": "Hyderabad"},
        {"name": "Dr. Falguni Mehta", "specialty": "Cosmetic Dermatologist", "city": "Pune"},
        {"name": "Dr. Gaurav Singh", "specialty": "Plastic Surgeon", "city": "Kolkata"},
        {"name": "Dr. Hina Khan", "specialty": "Aesthetic Surgeon", "city": "Ahmedabad"},
        {"name": "Dr. Imran Ali", "specialty": "Plastic Surgeon", "city": "Jaipur"},
        {"name": "Dr. Jayshree Naidu", "specialty": "Facial Plastic Surgeon", "city": "Lucknow"},
        {"name": "Dr. Kunal Verma", "specialty": "Cosmetic Surgeon", "city": "Chandigarh"},
        {"name": "Dr. Leela Reddy", "specialty": "Plastic Surgeon", "city": "Bhopal"},
        {"name": "Dr. Manish Joshi", "specialty": "Aesthetic Surgeon", "city": "Indore"},
        {"name": "Dr. Neha Malhotra", "specialty": "Cosmetic Dermatologist", "city": "Nagpur"},
        {"name": "Dr. Omkar Kulkarni", "specialty": "Plastic Surgeon", "city": "Surat"}
    ]
    
    conn = get_connection()
    added_count = 0
    try:
        for doctor in doctors:
            with conn.cursor() as cursor:
                # Check if doctor exists
                cursor.execute(
                    "SELECT id FROM doctors WHERE name = %s",
                    (doctor["name"],)
                )
                if cursor.fetchone():
                    logger.info(f"Doctor {doctor['name']} already exists. Skipping.")
                    continue
                
                # Create user
                username = doctor["name"].lower().replace(' ', '_').replace('.', '')
                email = f"{username}@example.com"
                phone_number = f"+91{random.randint(7000000000, 9999999999)}"
                
                cursor.execute("""
                    INSERT INTO users (
                        username, email, name, role, role_type, phone_number,
                        created_at, is_verified, password_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    username,
                    email,
                    doctor["name"],
                    'doctor',
                    'doctor',
                    phone_number,
                    datetime.utcnow(),
                    True,
                    "pbkdf2:sha256:600000$default_password_hash"  # placeholder hash
                ))
                
                user_id = cursor.fetchone()[0]
                conn.commit()
                
                # Create doctor profile
                education = json.dumps([{"degree": "MBBS", "institution": "Medical College", "year": ""}])
                certifications = json.dumps([])
                
                cursor.execute("""
                    INSERT INTO doctors (
                        user_id, name, specialty, experience, city,
                        consultation_fee, is_verified, rating, review_count, created_at,
                        bio, certifications, education, verification_status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    user_id,
                    doctor["name"],
                    doctor["specialty"],
                    random.randint(5, 20),  # experience
                    doctor["city"],
                    1500,  # consultation_fee
                    False,  # is_verified
                    round(random.uniform(4.0, 5.0), 1),  # rating
                    random.randint(10, 50),  # review_count
                    datetime.utcnow(),
                    "Experienced healthcare professional specializing in cosmetic procedures.",  # bio
                    certifications,
                    education,
                    'pending'  # verification_status
                ))
                conn.commit()
                added_count += 1
                logger.info(f"Added doctor: {doctor['name']}")
    
    except Exception as e:
        logger.error(f"Error adding doctors: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return added_count

def main():
    """Run the import process."""
    # Add procedures
    procedure_count = add_procedures()
    logger.info(f"Added {procedure_count} procedures")
    
    # Add doctors
    doctor_count = add_doctors()
    logger.info(f"Added {doctor_count} doctors")
    
    # Get final counts
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            total_procedures = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM doctors")
            total_doctors = cursor.fetchone()[0]
            
            logger.info(f"Final procedure count: {total_procedures}")
            logger.info(f"Final doctor count: {total_doctors}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()