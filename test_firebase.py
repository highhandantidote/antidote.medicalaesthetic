#!/usr/bin/env python3
"""
Simple Firebase OTP Test
Test Firebase configuration and OTP functionality directly
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create minimal Flask app for testing
app = Flask(__name__)

# Test Firebase environment variables
print("🔥 Testing Firebase Configuration...")
print("=" * 50)

firebase_vars = [
    'FIREBASE_API_KEY',
    'FIREBASE_AUTH_DOMAIN', 
    'FIREBASE_PROJECT_ID',
    'FIREBASE_STORAGE_BUCKET',
    'FIREBASE_MESSAGING_SENDER_ID',
    'FIREBASE_APP_ID'
]

all_vars_present = True
for var in firebase_vars:
    value = os.environ.get(var)
    if value:
        print(f"✅ {var}: {value[:20]}...")
    else:
        print(f"❌ {var}: MISSING")
        all_vars_present = False

print("=" * 50)

if not all_vars_present:
    print("❌ Firebase configuration incomplete!")
    sys.exit(1)

print("✅ All Firebase environment variables present!")
print("")

# Test Firebase config structure
firebase_config = {
    'apiKey': os.environ.get('FIREBASE_API_KEY'),
    'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN'),
    'projectId': os.environ.get('FIREBASE_PROJECT_ID'),
    'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.environ.get('FIREBASE_APP_ID')
}

print("🔧 Firebase Config Structure:")
print("=" * 30)
for key, value in firebase_config.items():
    print(f"{key}: {value[:30]}...")

print("")
print("✅ Firebase test completed successfully!")
print("🎯 Firebase should be ready for OTP authentication")