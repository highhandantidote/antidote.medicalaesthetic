#!/usr/bin/env python3
"""
Quick test to identify and fix AI recommendations error
"""

import sys
import os
sys.path.append('.')

from app import app, db
from models import Clinic
import traceback

def test_clinic_attributes():
    """Test what attributes clinics actually have"""
    with app.app_context():
        try:
            clinic = Clinic.query.first()
            if clinic:
                print(f"Sample clinic found: {clinic.name}")
                print("Available attributes:")
                for attr in dir(clinic):
                    if not attr.startswith('_') and not callable(getattr(clinic, attr)):
                        try:
                            value = getattr(clinic, attr)
                            print(f"  {attr}: {type(value)} = {value}")
                        except Exception as e:
                            print(f"  {attr}: ERROR - {e}")
            else:
                print("No clinics found in database")
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    test_clinic_attributes()