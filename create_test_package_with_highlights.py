#!/usr/bin/env python3
"""
Create a test package with proper key highlights and location data to verify the fixes.
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        conn = psycopg2.connect(
            os.environ.get('DATABASE_URL'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def create_test_package():
    """Create a test package with comprehensive key highlights and location data."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    try:
        # Get a verified clinic
        cursor.execute("SELECT id, name, city FROM clinics WHERE is_verified = true LIMIT 1")
        clinic = cursor.fetchone()
        
        if not clinic:
            logger.error("No verified clinic found")
            return
        
        # Create comprehensive key highlights
        key_highlights = {
            "Treatment Type": "Premium Korean Aesthetic Enhancement",
            "Procedure Duration": "45-60 minutes professional treatment",
            "Recovery Period": "2-3 days minimal downtime",
            "Results Timeline": "Immediate results, lasting 6-12 months",
            "Anesthesia": "Topical numbing cream included",
            "Follow-up": "Complimentary 2-week check-up included"
        }
        
        # Create detailed procedure breakdown
        procedure_breakdown = [
            {
                "name": "Primary Enhancement Procedure",
                "description": "Main aesthetic enhancement using premium Korean techniques",
                "price_actual": 45000,
                "price_discounted": 35000,
                "discount_percentage": 22
            },
            {
                "name": "Pre-Treatment Consultation",
                "description": "Comprehensive assessment and treatment planning",
                "price_actual": 8000,
                "price_discounted": 6000,
                "discount_percentage": 25
            },
            {
                "name": "Post-Treatment Care Package",
                "description": "Premium aftercare kit and follow-up consultation",
                "price_actual": 12000,
                "price_discounted": 9000,
                "discount_percentage": 25
            }
        ]
        
        # Create results gallery
        results_gallery = [
            {
                "title": "Natural Enhancement Results",
                "doctor_name": "Dr. Sarah Kim",
                "before_image": "/static/images/results/before_1.jpg",
                "after_image": "/static/images/results/after_1.jpg",
                "description": "Professional Korean-style enhancement with natural-looking results achieved through advanced techniques."
            },
            {
                "title": "Premium Treatment Outcome",
                "doctor_name": "Dr. Michael Park",
                "before_image": "/static/images/results/before_2.jpg", 
                "after_image": "/static/images/results/after_2.jpg",
                "description": "Exceptional results using premium materials and expert Korean aesthetic principles."
            }
        ]
        
        # Mumbai coordinates for testing map
        clinic_latitude = 19.0760
        clinic_longitude = 72.8777
        clinic_address = "Advanced Aesthetics Center, Bandra West, Mumbai, Maharashtra 400050"
        
        # Insert the test package
        package_sql = """
            INSERT INTO packages (
                clinic_id, title, slug, description, price_actual, price_discounted, 
                discount_percentage, category, about_procedure, key_highlights, 
                procedure_breakdown, vat_amount, anesthetic_type, aftercare_kit,
                recommended_for, downtime, duration, downtime_description, 
                precautions, results_gallery, whatsapp_number, custom_phone_number,
                chat_message_template, call_message_template, clinic_latitude,
                clinic_longitude, clinic_address, is_active, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        
        cursor.execute(package_sql, (
            clinic['id'],
            'Premium Korean-Style Aesthetic Enhancement',
            'premium-korean-aesthetic-enhancement',
            'Experience the finest in Korean aesthetic enhancement with our premium treatment package, designed for natural-looking results with minimal downtime.',
            65000,  # price_actual
            50000,  # price_discounted
            23,     # discount_percentage
            'Facial Enhancement',
            'Our premium Korean-style aesthetic enhancement combines advanced techniques with the highest quality materials to deliver exceptional, natural-looking results. This comprehensive treatment is performed by our expert practitioners who specialize in Korean aesthetic principles.',
            json.dumps(key_highlights),
            json.dumps(procedure_breakdown),
            7500,   # vat_amount
            'Topical numbing cream with optional local anesthesia',
            'Premium healing serum and aftercare instructions',
            'Individuals seeking natural enhancement with professional Korean aesthetic techniques. Perfect for those who want subtle, refined results with minimal downtime.',
            '2-3 days minimal swelling',
            '45-60 minutes',
            'Initial mild swelling for 24-48 hours. Avoid strenuous exercise for 24 hours. Return to normal activities within 2-3 days.',
            'Temporary swelling or minor bruising may occur. Avoid blood-thinning medications 1 week prior. Follow all pre and post-care instructions.',
            json.dumps(results_gallery),
            '+919876543210',
            '+919876543210',
            'Hi! I\'m interested in your Premium Korean-Style Aesthetic Enhancement package. Could you provide more details about the procedure and schedule a consultation?',
            'I would like to inquire about the Premium Korean-Style Aesthetic Enhancement package and discuss scheduling a consultation.',
            clinic_latitude,
            clinic_longitude,
            clinic_address,
            True,
            datetime.utcnow()
        ))
        
        result = cursor.fetchone()
        package_id = result['id'] if result else None
        
        conn.commit()
        
        if package_id:
            logger.info(f"✅ Test package created successfully with ID: {package_id}")
            logger.info(f"Package includes:")
            logger.info(f"- 6 key highlights with real data")
            logger.info(f"- 3 procedure breakdown items with pricing")
            logger.info(f"- 2 before/after result galleries")
            logger.info(f"- Real Mumbai coordinates for map testing")
            logger.info(f"Access URL: /packages/{package_id}")
        else:
            logger.error("Failed to create test package")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating test package: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Run the test package creation."""
    logger.info("Creating test package with enhanced features...")
    create_test_package()

if __name__ == "__main__":
    main()