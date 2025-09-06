#!/usr/bin/env python3
"""
Helper script to access admin functions for role changes and clinic verification.
"""

from app import create_app, db
from models import User, Clinic
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def setup_admin_access():
    """Set up admin access and show current system status."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check existing admin
            admin_user = User.query.filter_by(email='admin@antidote.com').first()
            if admin_user:
                print(f"Admin user exists: {admin_user.email}")
                print("Password: admin123")
                print("\nTo access admin functions:")
                print("1. Login at /login with admin@antidote.com / admin123")
                print("2. Go to /admin/users to change user roles")
                print("3. Go to /admin/clinic to verify clinics")
            
            # Show clinic admins that need role changes
            print("\n=== CLINIC ADMINS TO CHANGE TO CLINIC_OWNER ===")
            clinic_admins = User.query.filter_by(role='clinic_admin').all()
            for user in clinic_admins:
                print(f"ID: {user.id}, Email: {user.email}, Name: {user.name}")
            
            # Show clinics needing verification
            print("\n=== CLINICS NEEDING VERIFICATION ===")
            unverified_clinics = db.session.execute(text("""
                SELECT c.id, c.name, c.is_approved, c.is_verified, u.email as owner_email
                FROM clinics c
                LEFT JOIN users u ON c.owner_user_id = u.id
                WHERE c.is_approved = false OR c.is_verified = false
                ORDER BY c.created_at DESC
            """)).fetchall()
            
            for clinic in unverified_clinics:
                clinic_dict = dict(clinic._mapping)
                print(f"Clinic ID: {clinic_dict['id']}, Name: {clinic_dict['name']}")
                print(f"  Owner: {clinic_dict['owner_email']}")
                print(f"  Approved: {clinic_dict['is_approved']}, Verified: {clinic_dict['is_verified']}")
                print("---")
                
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    setup_admin_access()