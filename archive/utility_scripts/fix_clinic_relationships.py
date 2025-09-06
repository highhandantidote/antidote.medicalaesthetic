#!/usr/bin/env python3
"""
Quick fix for clinic database relationship errors.
This script updates the existing clinic model to support the new marketplace features.
"""

import os
import sys
from sqlalchemy import text
from app import app, db

def fix_clinic_database():
    """Fix clinic database relationships and errors"""
    with app.app_context():
        try:
            # Create missing tables if they don't exist
            print("Creating missing database tables...")
            
            # Check if new tables exist, create if not
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'clinic_leads' not in existing_tables:
                print("Creating clinic_leads table...")
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS clinic_leads (
                        id SERIAL PRIMARY KEY,
                        clinic_id INTEGER REFERENCES clinics(id),
                        consultation_id INTEGER REFERENCES clinic_consultations(id),
                        lead_type VARCHAR(50),
                        value_score FLOAT DEFAULT 0.0,
                        conversion_likelihood FLOAT DEFAULT 0.5,
                        follow_up_date TIMESTAMP,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
            
            if 'clinic_billing' not in existing_tables:
                print("Creating clinic_billing table...")
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS clinic_billing (
                        id SERIAL PRIMARY KEY,
                        clinic_id INTEGER REFERENCES clinics(id),
                        lead_id INTEGER REFERENCES clinic_leads(id),
                        consultation_id INTEGER REFERENCES clinic_consultations(id),
                        billing_type VARCHAR(50),
                        amount DECIMAL(10,2) NOT NULL,
                        currency VARCHAR(3) DEFAULT 'INR',
                        status VARCHAR(30) DEFAULT 'pending',
                        payment_method VARCHAR(50),
                        payment_date TIMESTAMP,
                        payment_reference VARCHAR(100),
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
            
            if 'clinic_activities' not in existing_tables:
                print("Creating clinic_activities table...")
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS clinic_activities (
                        id SERIAL PRIMARY KEY,
                        clinic_id INTEGER REFERENCES clinics(id),
                        user_id INTEGER REFERENCES users(id),
                        activity_type VARCHAR(50),
                        source_page VARCHAR(100),
                        ip_address VARCHAR(45),
                        time_on_page INTEGER,
                        conversion_value FLOAT DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
            
            # Fix clinic consultation table if missing fields
            print("Checking clinic_consultations table...")
            consultation_columns = [col['name'] for col in inspector.get_columns('clinic_consultations')]
            
            if 'patient_name' not in consultation_columns:
                print("Adding missing fields to clinic_consultations...")
                db.session.execute(text("""
                    ALTER TABLE clinic_consultations 
                    ADD COLUMN IF NOT EXISTS patient_name VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS patient_phone VARCHAR(20),
                    ADD COLUMN IF NOT EXISTS patient_email VARCHAR(120),
                    ADD COLUMN IF NOT EXISTS procedure_interest VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS message TEXT,
                    ADD COLUMN IF NOT EXISTS source VARCHAR(100);
                """))
            
            db.session.commit()
            print("Database tables fixed successfully!")
            
            # Test that we can query clinics
            from models import Clinic
            clinic_count = db.session.query(Clinic).count()
            print(f"Found {clinic_count} clinics in database")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error fixing database: {e}")
            return False

if __name__ == "__main__":
    success = fix_clinic_database()
    if success:
        print("✓ Clinic database relationships fixed successfully")
    else:
        print("✗ Failed to fix clinic database relationships")
        sys.exit(1)