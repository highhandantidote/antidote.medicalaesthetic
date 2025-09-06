"""
Add sample promotional codes to the database for testing the simplified billing system.
"""

import os
import sys
from datetime import datetime, timedelta

# Setup Flask app context
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

# Create Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Import models after database setup
from models import PromoCode, User

def add_sample_promo_codes():
    """Add sample promotional codes to the database."""
    
    with app.app_context():
        try:
            # Find an admin user to assign as creator (or create a default admin)
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                admin_user = User.query.first()  # Use any user if no admin exists
                if not admin_user:
                    print("No users found in database. Please create a user first.")
                    return
            
            # Sample promotional codes
            promo_codes = [
                {
                    'code': 'WELCOME50',
                    'description': 'Welcome bonus - 50% off your first credit purchase',
                    'discount_percent': 50.0,
                    'max_discount': 5000.0,
                    'bonus_percent': 0.0,
                    'min_amount': 1000.0,
                    'usage_limit_per_user': 1,
                    'total_usage_limit': 100,
                    'start_date': datetime.utcnow(),
                    'end_date': datetime.utcnow() + timedelta(days=90)
                },
                {
                    'code': 'SAVE25',
                    'description': 'Save 25% on credit purchases - Limited time offer',
                    'discount_percent': 25.0,
                    'max_discount': 2500.0,
                    'bonus_percent': 0.0,
                    'min_amount': 2000.0,
                    'usage_limit_per_user': 3,
                    'total_usage_limit': 500,
                    'start_date': datetime.utcnow(),
                    'end_date': datetime.utcnow() + timedelta(days=30)
                },
                {
                    'code': 'BONUS20',
                    'description': 'Get 20% bonus credits on your purchase',
                    'discount_percent': 0.0,
                    'max_discount': None,
                    'bonus_percent': 20.0,
                    'min_amount': 5000.0,
                    'usage_limit_per_user': None,
                    'total_usage_limit': None,
                    'start_date': datetime.utcnow(),
                    'end_date': datetime.utcnow() + timedelta(days=60)
                },
                {
                    'code': 'MEGA15',
                    'description': '15% discount + 10% bonus credits - Best deal!',
                    'discount_percent': 15.0,
                    'max_discount': 10000.0,
                    'bonus_percent': 10.0,
                    'min_amount': 10000.0,
                    'usage_limit_per_user': 2,
                    'total_usage_limit': 200,
                    'start_date': datetime.utcnow(),
                    'end_date': datetime.utcnow() + timedelta(days=45)
                },
                {
                    'code': 'TOPUP10',
                    'description': '10% off on any credit top-up',
                    'discount_percent': 10.0,
                    'max_discount': 1000.0,
                    'bonus_percent': 0.0,
                    'min_amount': 500.0,
                    'usage_limit_per_user': None,
                    'total_usage_limit': 1000,
                    'start_date': datetime.utcnow(),
                    'end_date': datetime.utcnow() + timedelta(days=15)
                }
            ]
            
            added_count = 0
            
            for promo_data in promo_codes:
                # Check if promo code already exists
                existing_promo = PromoCode.query.filter_by(code=promo_data['code']).first()
                if existing_promo:
                    print(f"Promo code {promo_data['code']} already exists, skipping...")
                    continue
                
                # Create new promo code
                new_promo = PromoCode(
                    code=promo_data['code'],
                    description=promo_data['description'],
                    discount_percent=promo_data['discount_percent'],
                    max_discount=promo_data['max_discount'],
                    bonus_percent=promo_data['bonus_percent'],
                    min_amount=promo_data['min_amount'],
                    usage_limit_per_user=promo_data['usage_limit_per_user'],
                    total_usage_limit=promo_data['total_usage_limit'],
                    start_date=promo_data['start_date'],
                    end_date=promo_data['end_date'],
                    is_active=True,
                    created_by_admin_id=admin_user.id
                )
                
                db.session.add(new_promo)
                added_count += 1
                print(f"Added promo code: {promo_data['code']}")
            
            db.session.commit()
            print(f"\nSuccessfully added {added_count} promotional codes to the database!")
            
            # Display summary
            print("\nPromo Code Summary:")
            print("-" * 50)
            all_promos = PromoCode.query.filter_by(is_active=True).all()
            for promo in all_promos:
                print(f"Code: {promo.code}")
                print(f"  Description: {promo.description}")
                print(f"  Discount: {promo.discount_percent}%")
                if promo.bonus_percent > 0:
                    print(f"  Bonus: {promo.bonus_percent}%")
                print(f"  Min Amount: ₹{promo.min_amount:,.0f}")
                print(f"  Valid Until: {promo.end_date.strftime('%Y-%m-%d')}")
                print()
                
        except Exception as e:
            print(f"Error adding promo codes: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_sample_promo_codes()