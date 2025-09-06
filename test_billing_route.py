#!/usr/bin/env python3
"""
Test script to verify the simplified billing system route works correctly.
"""

import os
import sys
import requests
from models import db, User, Clinic
from app import create_app

def test_billing_route():
    """Test the simplified billing route directly."""
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Check if any clinics exist
        clinics = Clinic.query.all()
        print(f"Found {len(clinics)} clinics in database")
        
        if clinics:
            clinic = clinics[0]
            print(f"Testing with clinic: {clinic.name} (ID: {clinic.id})")
            print(f"Owner user ID: {clinic.owner_user_id}")
            
            # Check if owner user exists
            user = User.query.get(clinic.owner_user_id)
            if user:
                print(f"Owner user: {user.username} ({user.email})")
            else:
                print("Owner user not found!")
        
        # Test the route directly
        print("\nTesting route registration...")
        for rule in app.url_map.iter_rules():
            if 'credit' in str(rule) or 'billing' in str(rule):
                print(f"Route: {rule} -> {rule.endpoint}")

if __name__ == "__main__":
    test_billing_route()