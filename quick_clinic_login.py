#!/usr/bin/env python3
"""
Quick login script for clinic owner testing.
This script creates a session for clinic owner testing.
"""

from app import create_app, db
from models import User
from flask_login import login_user
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def create_clinic_owner_session():
    """Create or update a clinic owner for testing."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if test clinic owner exists
            test_user = User.query.filter_by(email='test@clinic.com').first()
            
            if not test_user:
                # Create new clinic owner
                test_user = User(
                    name='Test Clinic Owner',
                    email='test@clinic.com',
                    username='testclinic',
                    role='clinic_owner',
                    password_hash=generate_password_hash('password123'),
                    phone_number='9876543210'
                )
                db.session.add(test_user)
                db.session.commit()
                print(f"Created new clinic owner: {test_user.email}")
            else:
                # Update existing user to clinic_owner role
                test_user.role = 'clinic_owner'
                if not test_user.password_hash:
                    test_user.password_hash = generate_password_hash('password123')
                db.session.commit()
                print(f"Updated existing user to clinic owner: {test_user.email}")
            
            # Check if user has a clinic
            clinic_result = db.session.execute(
                text("SELECT * FROM clinics WHERE owner_user_id = :user_id"),
                {'user_id': test_user.id}
            ).fetchone()
            
            if clinic_result:
                clinic = dict(clinic_result._mapping)
                print(f"User has clinic: {clinic['name']} (ID: {clinic['id']})")
            else:
                print("User doesn't have a clinic profile - will be redirected to create one")
            
            print("\nLogin credentials:")
            print(f"Email: {test_user.email}")
            print("Password: password123")
            print("\nYou can now log in at /login and then access /clinic/dashboard")
            
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    create_clinic_owner_session()