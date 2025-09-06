#!/usr/bin/env python3
"""Test homepage data retrieval to identify the issue."""

from app import app, db
from models import BodyPart, Category, Procedure, Doctor, Community

with app.app_context():
    try:
        # Test each query individually to see which one fails
        print("Testing body parts...")
        body_parts = BodyPart.query.limit(4).all()
        print(f"Body parts: {len(body_parts)} found")
        
        print("Testing categories...")
        categories = Category.query.limit(6).all()
        print(f"Categories: {len(categories)} found")
        
        print("Testing procedures...")
        procedures = Procedure.query.limit(6).all()
        print(f"Procedures: {len(procedures)} found")
        
        print("Testing doctors...")
        doctors = Doctor.query.limit(9).all()
        print(f"Doctors: {len(doctors)} found")
        
        print("Testing community posts...")
        community = Community.query.limit(3).all()
        print(f"Community posts: {len(community)} found")
        
        print("All queries successful!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()