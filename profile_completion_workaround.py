"""
Profile Completion Workaround
This creates a temporary solution that works without the missing database columns
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models import User, db
import json
import logging

logger = logging.getLogger(__name__)

# Create a temporary profile completion system that stores data in existing fields
def store_profile_in_bio(user, age=None, gender=None, city=None, interests=None):
    """Store profile data in the bio field as JSON until DB columns are available"""
    profile_data = {}
    
    if age:
        profile_data['age'] = age
    if gender:
        profile_data['gender'] = gender
    if city:
        profile_data['city'] = city
    if interests:
        profile_data['interests'] = interests if isinstance(interests, list) else [interests]
    
    # Store as JSON in bio field with a prefix
    profile_json = json.dumps(profile_data)
    user.bio = f"PROFILE_DATA:{profile_json}"
    
    logger.info(f"Stored profile data for user {user.id}: {profile_data}")

def get_profile_from_bio(user):
    """Extract profile data from bio field"""
    if not user.bio or not user.bio.startswith("PROFILE_DATA:"):
        return {}
    
    try:
        profile_json = user.bio.replace("PROFILE_DATA:", "")
        return json.loads(profile_json)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error parsing profile data for user {user.id}: {e}")
        return {}

def is_profile_completed(user):
    """Check if user has completed their profile"""
    # Check if they have a real name (not auto-generated)
    if not user.name or user.name.startswith("User "):
        return False
    
    # Check if they have profile data stored
    profile_data = get_profile_from_bio(user)
    return len(profile_data) > 0

def mark_profile_completed(user):
    """Mark profile as completed by setting a flag in the bio"""
    profile_data = get_profile_from_bio(user)
    profile_data['completed'] = True
    profile_json = json.dumps(profile_data)
    user.bio = f"PROFILE_DATA:{profile_json}"

# This will be integrated into the main OTP auth system