#!/usr/bin/env python3
"""
Create missing database tables

This script ensures all required tables exist in the database.
"""

import os
import logging
from datetime import datetime
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    
    return psycopg2.connect(db_url)

def create_tables():
    """Create all necessary tables in the database."""
    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to database")
        return False

    try:
        with conn.cursor() as cur:
            # Create body_parts table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS body_parts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    icon_url VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create categories table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    body_part_id INTEGER REFERENCES body_parts(id),
                    popularity_score INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create procedures table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS procedures (
                    id SERIAL PRIMARY KEY,
                    procedure_name VARCHAR(100) NOT NULL,
                    alternative_names TEXT,
                    short_description TEXT,
                    overview TEXT,
                    procedure_details TEXT,
                    ideal_candidates TEXT,
                    recovery_process TEXT,
                    recovery_time VARCHAR(100),
                    procedure_duration VARCHAR(100),
                    hospital_stay_required VARCHAR(50),
                    results_duration VARCHAR(100),
                    min_cost INTEGER,
                    max_cost INTEGER,
                    benefits TEXT,
                    benefits_detailed TEXT,
                    risks TEXT,
                    procedure_types TEXT,
                    alternative_procedures TEXT,
                    category_id INTEGER REFERENCES categories(id),
                    popularity_score INTEGER DEFAULT 0,
                    avg_rating FLOAT DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    body_part VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create users table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    name VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'user',
                    role_type VARCHAR(20) DEFAULT 'user',
                    phone_number VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_verified BOOLEAN DEFAULT FALSE,
                    password_hash VARCHAR(256) DEFAULT 'pbkdf2:sha256:600000$default_password_hash'
                )
            """)
            
            # Create doctors table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS doctors (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    name VARCHAR(100) NOT NULL,
                    specialty VARCHAR(100),
                    experience INTEGER,
                    city VARCHAR(100),
                    consultation_fee INTEGER,
                    is_verified BOOLEAN DEFAULT FALSE,
                    rating FLOAT DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    bio TEXT,
                    certifications JSONB,
                    education JSONB,
                    verification_status VARCHAR(20) DEFAULT 'pending'
                )
            """)
            
            # Create banners table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS banners (
                    id SERIAL PRIMARY KEY,
                    position VARCHAR(100) UNIQUE NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create banner_slides table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS banner_slides (
                    id SERIAL PRIMARY KEY,
                    banner_id INTEGER REFERENCES banners(id),
                    title VARCHAR(100),
                    content TEXT,
                    button_text VARCHAR(100),
                    button_url VARCHAR(255),
                    image_url VARCHAR(255),
                    order_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create community_threads table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS community_threads (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    tags VARCHAR(255),
                    user_id INTEGER REFERENCES users(id),
                    upvotes INTEGER DEFAULT 0,
                    is_approved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create community_replies table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS community_replies (
                    id SERIAL PRIMARY KEY,
                    thread_id INTEGER REFERENCES community_threads(id),
                    user_id INTEGER REFERENCES users(id),
                    content TEXT,
                    upvotes INTEGER DEFAULT 0,
                    is_approved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create face_analysis table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS face_analysis (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    image_path VARCHAR(255),
                    analysis_data JSONB,
                    is_anonymous BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create face_scan_recommendations table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS face_scan_recommendations (
                    id SERIAL PRIMARY KEY,
                    face_analysis_id INTEGER REFERENCES face_analysis(id),
                    recommendation_type VARCHAR(50) DEFAULT 'procedure',
                    procedure_id INTEGER REFERENCES procedures(id),
                    description TEXT,
                    confidence FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("All tables created successfully")
            return True
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()