#!/usr/bin/env python3
"""
Reset admin password to a known value.
"""

from app import create_app, db
from models import User
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """Reset admin password to 'admin123'."""
    app = create_app()
    
    with app.app_context():
        try:
            # Find admin user
            admin_user = User.query.filter_by(email='admin@antidote.com').first()
            
            if admin_user:
                # Set password to admin123
                admin_user.password_hash = generate_password_hash('admin123')
                db.session.commit()
                
                print("Admin password updated successfully!")
                print("Email: admin@antidote.com")
                print("Password: admin123")
            else:
                print("Admin user not found")
                
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    reset_admin_password()