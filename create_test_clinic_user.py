#!/usr/bin/env python3
"""
Create a test clinic user with proper password hashing
"""

import os
import sys
sys.path.insert(0, '.')

from werkzeug.security import generate_password_hash
from sqlalchemy import text
from app import app, db

def create_test_clinic_user():
    """Create a test clinic user with proper password hashing."""
    with app.app_context():
        try:
            # Generate proper password hash for "test123"
            password_hash = generate_password_hash("test123")
            
            # Create or update the test user
            db.session.execute(text("""
                INSERT INTO users (username, email, password_hash, phone_number, name, role, created_at)
                VALUES ('clinic_test', 'clinic@test.demo', :password_hash, '+919876543210', 'Test Clinic Owner', 'clinic_owner', NOW())
                ON CONFLICT (email) DO UPDATE SET 
                    password_hash = :password_hash,
                    username = 'clinic_test',
                    name = 'Test Clinic Owner',
                    role = 'clinic_owner'
                RETURNING id
            """), {'password_hash': password_hash})
            
            result = db.session.execute(text("SELECT id FROM users WHERE email = 'clinic@test.demo'")).fetchone()
            user_id = result[0]
            
            # Create clinic for the test user
            db.session.execute(text("""
                INSERT INTO clinics (
                    name, address, city, state, contact_number, whatsapp_number, email,
                    owner_user_id, is_verified, is_active, created_at, updated_at
                ) VALUES (
                    'Demo Test Clinic',
                    '456 Demo Street, Test Area',
                    'Delhi',
                    'Delhi', 
                    '+919876543210',
                    '+919876543210',
                    'clinic@test.demo',
                    :user_id,
                    true,
                    true,
                    NOW(),
                    NOW()
                ) ON CONFLICT (email) DO UPDATE SET
                    name = 'Demo Test Clinic',
                    city = 'Delhi',
                    is_verified = true,
                    is_active = true
            """), {'user_id': user_id})
            
            db.session.commit()
            
            print("✓ Test clinic user created successfully!")
            print("Email: clinic@test.demo")
            print("Password: test123")
            print("Clinic: Demo Test Clinic (Delhi)")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test user: {e}")

if __name__ == "__main__":
    create_test_clinic_user()