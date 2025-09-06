"""
OTP-Only Authentication System for Antidote
A unified phone-based authentication system that replaces traditional login/signup.
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CSRFError
from app import csrf
from models import User, db
from datetime import datetime, timedelta
import logging
import re
import json

# Profile completion workaround functions
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

def is_profile_completed_workaround(user):
    """Check if user has completed their profile using workaround"""
    # Check if they have a real name (not auto-generated temporary name)
    if not user.name or user.name.startswith("User "):
        return False
    
    # If they have a real name and no bio data, consider profile completed
    # This handles cases where users completed profile but bio wasn't set properly
    profile_data = get_profile_from_bio(user)
    if not profile_data and user.name and not user.name.startswith("User "):
        return True
    
    return profile_data.get('completed', False)

# Create blueprint for OTP authentication
otp_auth = Blueprint('otp_auth', __name__)
logger = logging.getLogger(__name__)

def normalize_phone_number(phone):
    """Normalize phone number to consistent format (+91XXXXXXXXXX)"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Handle different formats
    if digits_only.startswith('91') and len(digits_only) == 12:
        return f"+{digits_only}"
    elif len(digits_only) == 10:
        return f"+91{digits_only}"
    elif digits_only.startswith('0') and len(digits_only) == 11:
        return f"+91{digits_only[1:]}"
    else:
        return f"+91{digits_only}"

def is_valid_phone(phone):
    """Validate phone number format"""
    normalized = normalize_phone_number(phone)
    # Check if it's a valid Indian phone number format
    return re.match(r'^\+91[6-9]\d{9}$', normalized) is not None

@otp_auth.route('/auth')
def auth_entry():
    """
    Unified authentication entry point.
    Replaces separate login/signup pages.
    """
    # If user is already authenticated, redirect to appropriate dashboard
    if current_user.is_authenticated:
        return redirect_after_auth(current_user)
    
    # Get the page they were trying to access for redirect after auth
    next_page = request.args.get('next', '')
    context = request.args.get('context', '')  # e.g., 'contact_clinic', 'save_package'
    
    # Store next page in session to persist through profile completion
    if next_page:
        session['auth_next_page'] = next_page
    
    # Firebase configuration for simple template
    import os
    firebase_config = {
        'apiKey': os.environ.get('FIREBASE_API_KEY', ''),
        'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
        'projectId': os.environ.get('FIREBASE_PROJECT_ID', ''),
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
        'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
        'appId': os.environ.get('FIREBASE_APP_ID', '')
    }
    
    return render_template('auth/otp_auth_simple.html', 
                         next_page=next_page, 
                         context=context,
                         firebase_config=firebase_config,
                         title='Access Your Account')

@otp_auth.route('/auth/send-otp', methods=['POST'])
@csrf.exempt
def send_otp():
    """Send OTP to phone number - Development mode with test OTP"""
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        if not phone:
            return jsonify({'success': False, 'message': 'Phone number is required'})
        
        # Validate and normalize phone number
        if not is_valid_phone(phone):
            return jsonify({'success': False, 'message': 'Please enter a valid Indian phone number'})
        
        normalized_phone = normalize_phone_number(phone)
        
        # Generate test OTP for development (always use 123456 for easy testing)
        test_otp = "123456"
        
        # Store phone and OTP in session for verification
        session['pending_phone'] = normalized_phone
        session['pending_otp'] = test_otp  # Store for development verification
        session['otp_sent_at'] = datetime.utcnow().isoformat()
        
        # Check if user exists (for different UX messages)
        existing_user = User.query.filter_by(phone_number=normalized_phone).first()
        is_new_user = existing_user is None
        
        logger.info(f"Development OTP requested for {normalized_phone}, new user: {is_new_user}")
        logger.info(f"🔧 TEST OTP CODE: {test_otp} (for development testing)")
        
        return jsonify({
            'success': True, 
            'message': 'OTP sent successfully (development mode)',
            'masked_phone': f"{normalized_phone[:6]}XXXXX",
            'is_new_user': is_new_user,
            'dev_note': f'Development OTP: {test_otp}'
        })
        
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to send OTP. Please try again.'})

@otp_auth.route('/auth/firebase-login', methods=['POST'])
@csrf.exempt
def firebase_login():
    """Handle user login after successful Firebase OTP verification"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '').strip()
        firebase_uid = data.get('firebase_uid', '').strip()
        
        if not phone_number or not firebase_uid:
            return jsonify({'success': False, 'message': 'Missing phone number or Firebase UID'})
        
        # Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)
        
        # Find or create user - only query essential columns to avoid missing column errors
        try:
            user = User.query.filter_by(phone_number=normalized_phone).first()
            is_new_user = user is None
        except Exception as db_error:
            logger.error(f"Database query error: {str(db_error)}")
            # Fallback to basic query if there are column issues
            from sqlalchemy import text
            result = db.session.execute(
                text("SELECT id, phone_number, firebase_uid, name, email, role, is_verified, created_at, last_login_at FROM users WHERE phone_number = :phone"),
                {"phone": normalized_phone}
            ).fetchone()
            user = None
            if result:
                user = User.query.get(result[0])  # Get full object by ID
            is_new_user = user is None
        
        if is_new_user:
            # Create new user with Firebase authentication - profile incomplete initially
            # Use a temporary name to satisfy NOT NULL constraint, will be updated in profile completion
            temp_name = f"User {normalized_phone[-4:]}"  # Use last 4 digits for unique temp name
            user = User(
                phone_number=normalized_phone,
                name=temp_name,  # Temporary name to satisfy DB constraint
                role='user',
                is_verified=True,
                firebase_uid=firebase_uid,  # Store Firebase UID for future reference
                last_login_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            user.profile_completed = False  # Profile incomplete for new users
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user with Firebase UID {firebase_uid}")
        else:
            # Update existing user login time and Firebase UID
            user.last_login_at = datetime.utcnow()
            user.is_verified = True
            if not user.firebase_uid:
                user.firebase_uid = firebase_uid
            db.session.commit()
            logger.info(f"User {user.id} logged in with Firebase UID {firebase_uid}")
        
        # Log in the user
        login_user(user)
        
        # Determine redirect URL
        redirect_url = get_post_auth_redirect(user, is_new_user)
        
        return jsonify({
            'success': True, 
            'message': 'Login successful!',
            'is_new_user': is_new_user,
            'redirect_url': redirect_url
        })
        
    except Exception as e:
        logger.error(f"Error in Firebase login: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Login failed. Please try again.'})

@otp_auth.route('/auth/verify-otp', methods=['POST'])
@csrf.exempt
def verify_otp():
    """Verify OTP and authenticate user - Development mode with test verification"""
    try:
        data = request.get_json()
        otp_code = data.get('otp', '').strip()
        
        if not otp_code or len(otp_code) != 6:
            return jsonify({'success': False, 'message': 'Please enter a valid 6-digit OTP'})
        
        # Get phone from session
        pending_phone = session.get('pending_phone')
        if not pending_phone:
            return jsonify({'success': False, 'message': 'No OTP request found. Please request a new OTP.'})
        
        # Check OTP expiry (5 minutes)
        otp_sent_at = session.get('otp_sent_at')
        if otp_sent_at:
            sent_time = datetime.fromisoformat(otp_sent_at)
            if datetime.utcnow() - sent_time > timedelta(minutes=5):
                session.pop('pending_phone', None)
                session.pop('pending_otp', None)
                session.pop('otp_sent_at', None)
                return jsonify({'success': False, 'message': 'OTP has expired. Please request a new one.'})
        
        # Development mode: Check against stored test OTP
        pending_otp = session.get('pending_otp')
        if pending_otp and otp_code != pending_otp:
            return jsonify({'success': False, 'message': f'Invalid OTP. Development mode: Use {pending_otp}'})
        
        logger.info(f"Development OTP verification successful for {pending_phone}")
        
        # Find or create user - handle potential missing column errors
        try:
            user = User.query.filter_by(phone_number=pending_phone).first()
            is_new_user = user is None
        except Exception as db_error:
            logger.error(f"Database query error: {str(db_error)}")
            # Fallback to basic query if there are column issues
            from sqlalchemy import text
            result = db.session.execute(
                text("SELECT id, phone_number, firebase_uid, name, email, role, is_verified, created_at, last_login_at FROM users WHERE phone_number = :phone"),
                {"phone": pending_phone}
            ).fetchone()
            user = None
            if result:
                user = User.query.get(result[0])  # Get full object by ID
            is_new_user = user is None
        
        if is_new_user:
            # Create new user with phone-only authentication - profile incomplete initially
            # Use a temporary name to satisfy NOT NULL constraint, will be updated in profile completion
            temp_name = f"User {pending_phone[-4:]}"  # Use last 4 digits for unique temp name
            user = User(
                phone_number=pending_phone,
                name=temp_name,  # Temporary name to satisfy DB constraint
                role='user',
                is_verified=True,
                last_login_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            user.profile_completed = False  # Profile incomplete for new users
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user with phone {pending_phone}")
        else:
            # Update existing user login time
            user.last_login_at = datetime.utcnow()
            user.is_verified = True
            db.session.commit()
            logger.info(f"Existing user {user.id} logged in with phone {pending_phone}")
        
        # Log in the user
        login_user(user)
        
        # Clear session data
        session.pop('pending_phone', None)
        session.pop('pending_otp', None)
        session.pop('otp_sent_at', None)
        
        # Determine redirect URL
        redirect_url = get_post_auth_redirect(user, is_new_user)
        
        return jsonify({
            'success': True, 
            'message': 'Login successful!',
            'is_new_user': is_new_user,
            'redirect_url': redirect_url
        })
        
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Verification failed. Please try again.'})

@otp_auth.route('/auth/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    """Complete profile for new users - 2-step authentication"""
    # Check if profile is already completed using workaround
    if is_profile_completed_workaround(current_user) and current_user.name and current_user.name.strip():
        return redirect_after_auth(current_user)
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            age = data.get('age')
            gender = data.get('gender', '').strip()
            city = data.get('city', '').strip()
            interests = data.getlist('interests') if hasattr(data, 'getlist') else data.get('interests', [])
            
            # Name is required
            if not name:
                error_msg = 'Name is required'
                if request.is_json:
                    return jsonify({'success': False, 'message': error_msg})
                else:
                    flash(error_msg, 'error')
                    return render_template('auth/complete_profile.html', title='Complete Your Profile')
            
            # Validate email if provided
            if email:
                existing_email = User.query.filter_by(email=email).first()
                if existing_email and existing_email.id != current_user.id:
                    error_msg = 'Email already exists'
                    if request.is_json:
                        return jsonify({'success': False, 'message': error_msg})
                    else:
                        flash(error_msg, 'error')
                        return render_template('auth/complete_profile.html', title='Complete Your Profile')
            
            # Validate age if provided
            if age:
                try:
                    age = int(age)
                    if age < 18 or age > 100:
                        age = None
                except (ValueError, TypeError):
                    age = None
            
            # Update user profile
            current_user.name = name
            if email:
                current_user.email = email
            
            # Store profile data using workaround (in bio field as JSON)
            store_profile_in_bio(current_user, age, gender, city, interests)
            
            # Mark profile as completed in the stored data
            profile_data = get_profile_from_bio(current_user)
            profile_data['completed'] = True
            profile_json = json.dumps(profile_data)
            current_user.bio = f"PROFILE_DATA:{profile_json}"
            
            db.session.commit()
            logger.info(f"Profile completed for user {current_user.id} with name: {name}")
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Profile completed successfully!',
                    'redirect_url': get_post_auth_redirect(current_user, False)
                })
            else:
                flash('Welcome to Antidote! Your profile has been created.', 'success')
                return redirect_after_auth(current_user)
                
        except Exception as e:
            logger.error(f"Error completing profile: {str(e)}")
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'message': 'Profile completion failed. Please try again.'})
            else:
                flash('Profile completion failed. Please try again.', 'error')
    
    # Define interest options for the form
    interest_options = [
        'Facial treatments', 'Body contouring', 'Skin care',
        'Hair treatments', 'Anti-aging', 'Weight management'
    ]
    
    return render_template('auth/complete_profile.html', 
                         title='Complete Your Profile',
                         interest_options=interest_options)

@otp_auth.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    user_name = current_user.name if current_user.name else current_user.phone_number
    logout_user()
    flash(f'Goodbye {user_name}! You have been logged out.', 'info')
    return redirect(url_for('web.index'))

def redirect_after_auth(user):
    """Determine where to redirect user after authentication"""
    # Check if there's a next page specified
    next_page = session.get('auth_next_page') or request.args.get('next')
    if next_page and next_page.startswith('/'):
        session.pop('auth_next_page', None)
        return redirect(next_page)
    
    # Redirect based on user role
    if user.role == 'admin':
        return redirect(url_for('web.admin_dashboard'))
    elif user.role == 'clinic_admin':
        return redirect(url_for('clinic.clinic_dashboard'))
    elif user.role == 'doctor':
        from models import Doctor
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        if doctor:
            return redirect(url_for('web.doctor_dashboard', doctor_id=doctor.id))
    
    # Default redirect to homepage
    return redirect(url_for('web.index'))

def get_post_auth_redirect(user, is_new_user):
    """Get redirect URL after authentication"""
    # If user profile is not completed, redirect to complete profile (using workaround)
    if not is_profile_completed_workaround(user) or not user.name or not user.name.strip():
        return url_for('otp_auth.complete_profile')
    
    # Check if there's a next page specified (from URL parameter or session)
    next_page = session.get('auth_next_page') or request.args.get('next')
    if next_page and next_page.startswith('/'):
        session.pop('auth_next_page', None)
        return next_page
    
    # Check for context-specific redirects
    context = session.get('auth_context')
    if context == 'contact_clinic':
        # Continue with clinic contact flow
        package_id = session.get('auth_package_id')
        if package_id:
            return url_for('enhanced_lead_capture.create_lead', package_id=package_id)
    
    # Default redirects based on role
    if user.role == 'admin':
        return url_for('web.admin_dashboard')
    elif user.role == 'clinic_admin':
        return url_for('clinic.clinic_dashboard')
    elif user.role == 'doctor':
        from models import Doctor
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        if doctor:
            return url_for('web.doctor_dashboard', doctor_id=doctor.id)
    
    return url_for('web.index')

# Rate limiting helper
def check_rate_limit(phone):
    """Check if phone number has exceeded OTP request rate limit"""
    # This is a simple in-memory rate limiting
    # In production, you'd use Redis or database
    rate_limit_key = f"otp_rate_{phone}"
    current_requests = session.get(rate_limit_key, 0)
    
    if current_requests >= 3:  # Max 3 OTP requests per hour
        return False
    
    return True

def increment_rate_limit(phone):
    """Increment rate limit counter for phone number"""
    rate_limit_key = f"otp_rate_{phone}"
    current_requests = session.get(rate_limit_key, 0)
    session[rate_limit_key] = current_requests + 1

# Firebase configuration for OTP
def inject_firebase_config():
    """Inject Firebase configuration into templates"""
    import os
    return {
        'firebase_config': {
            'apiKey': os.environ.get('FIREBASE_API_KEY'),
            'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN'),
            'projectId': os.environ.get('FIREBASE_PROJECT_ID'),
            'storageBucket': f"{os.environ.get('FIREBASE_PROJECT_ID')}.appspot.com",
            'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
            'appId': os.environ.get('FIREBASE_APP_ID', '')
        }
    }

# Register context processor
@otp_auth.context_processor
def inject_firebase_config_processor():
    """Context processor to inject Firebase config into all OTP auth templates"""
    return inject_firebase_config()