"""
Enhanced Lead Generation System with Firebase OTP Verification
Handles verified lead creation from package and clinic contact forms
"""

import os
import logging
import urllib.parse
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, session
from flask_login import current_user
from app import db
from models import Lead, Clinic, Package, User
from sqlalchemy import and_, or_, text

# Create Blueprint
lead_bp = Blueprint('enhanced_leads', __name__)

logger = logging.getLogger(__name__)

@lead_bp.route('/api/leads/check-verification', methods=['POST'])
def check_phone_verification():
    """
    Check if a phone number is already verified in the current session
    """
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        if not phone:
            return jsonify({
                'success': False,
                'message': 'Phone number is required'
            }), 400
        
        # Clean phone number for comparison
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Check if phone is verified in session
        verified_phones = session.get('verified_phones', {})
        
        # Check if this phone number is verified and still within time limit (60 minutes)
        phone_verification = verified_phones.get(clean_phone)
        if phone_verification:
            verification_time = datetime.fromisoformat(phone_verification['verified_at'])
            if datetime.now() - verification_time <= timedelta(minutes=60):
                return jsonify({
                    'success': True,
                    'verified': True,
                    'message': 'Phone number already verified',
                    'verification_time': phone_verification['verified_at'],
                    'user_data': {
                        'name': phone_verification.get('name', ''),
                        'phone': phone_verification.get('phone', ''),
                        'email': phone_verification.get('email', '')
                    }
                })
        
        return jsonify({
            'success': True,
            'verified': False,
            'message': 'Phone number not verified or verification expired'
        })
        
    except Exception as e:
        logger.error(f"Error checking phone verification: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@lead_bp.route('/api/leads/create-verified-lead', methods=['POST'])
def create_verified_lead():
    """
    Create a lead using already verified phone number from session
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['phone', 'source_type', 'source_id', 'contact_intent']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Clean phone number
        clean_phone = ''.join(filter(str.isdigit, data['phone']))
        
        # Check if phone is verified in session
        verified_phones = session.get('verified_phones', {})
        phone_verification = verified_phones.get(clean_phone)
        
        if not phone_verification:
            return jsonify({
                'success': False,
                'message': 'Phone number not verified. Please verify first.'
            }), 400
        
        # Check verification time (60 minutes)
        verification_time = datetime.fromisoformat(phone_verification['verified_at'])
        if datetime.now() - verification_time > timedelta(minutes=60):
            return jsonify({
                'success': False,
                'message': 'Phone verification expired. Please verify again.'
            }), 400
        
        # Use verified user data
        verified_data = {
            'name': phone_verification.get('name', ''),
            'phone': phone_verification.get('phone', ''),
            'email': data.get('email', phone_verification.get('email', '')),
            'message': data.get('message', ''),
            'source_type': data['source_type'],
            'source_id': data['source_id'],
            'contact_intent': data['contact_intent'],
            'firebase_uid': phone_verification.get('firebase_uid', 'session_verified')
        }
        
        # Create the lead using the same logic as verify_phone_lead
        return create_lead_from_verified_data(verified_data, skip_session_storage=True)
        
    except Exception as e:
        logger.error(f"Error creating verified lead: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@lead_bp.route('/api/leads/create-authenticated-lead', methods=['POST'])
def create_authenticated_lead():
    """
    Create a lead for logged-in users - no OTP verification required
    """
    try:
        from flask_login import current_user
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': 'User must be logged in to use this endpoint'
            }), 401
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['source_type', 'source_id', 'contact_intent']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Use logged-in user data
        verified_data = {
            'name': current_user.name or 'User',
            'phone': current_user.phone_number,
            'email': data.get('email', current_user.email or ''),
            'message': data.get('message', ''),
            'source_type': data['source_type'],
            'source_id': data['source_id'],
            'contact_intent': data['contact_intent'],
            'firebase_uid': current_user.firebase_uid or 'authenticated_user'
        }
        
        # Create the lead using logged-in user data
        result = create_lead_from_verified_data(verified_data, skip_session_storage=True)
        
        # If successful, associate with current user
        if result.status_code == 200:
            result_data = result.get_json()
            if result_data.get('success') and result_data.get('lead_id'):
                try:
                    # Update the lead to associate with logged-in user
                    lead = Lead.query.get(result_data['lead_id'])
                    if lead:
                        lead.user_id = current_user.id
                        db.session.commit()
                except Exception as e:
                    logger.error(f"Error associating lead with user: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating authenticated lead: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@lead_bp.route('/api/leads/verify-phone', methods=['POST'])
def verify_phone_lead():
    """
    Create a verified lead after Firebase OTP verification
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'phone', 'source_type', 'source_id', 'contact_intent', 'firebase_uid']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Validate source type
        if data['source_type'] not in ['package', 'clinic']:
            return jsonify({
                'success': False,
                'message': 'Invalid source type. Must be package or clinic'
            }), 400
        
        # Validate contact intent
        if data['contact_intent'] not in ['whatsapp', 'call', 'inquiry']:
            return jsonify({
                'success': False,
                'message': 'Invalid contact intent'
            }), 400
        
        # Get clinic information based on source
        clinic = None
        source_name = ""
        
        if data['source_type'] == 'package':
            package = Package.query.get(data['source_id'])
            if not package:
                return jsonify({
                    'success': False,
                    'message': 'Package not found'
                }), 404
            
            # Get clinic through the relationship
            clinic = package.clinic
            source_name = package.title or package.package_name
            
        elif data['source_type'] == 'clinic':
            clinic = Clinic.query.get(data['source_id'])
            if not clinic:
                return jsonify({
                    'success': False,
                    'message': 'Clinic not found'
                }), 404
            
            source_name = clinic.name
        
        if not clinic:
            return jsonify({
                'success': False,
                'message': 'Associated clinic not found'
            }), 404
        
        # Use the helper function to create the lead and handle all the contact logic
        return create_lead_from_verified_data(data)
        
    except Exception as e:
        logger.error(f"Error creating verified lead: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

def calculate_lead_cost(clinic, contact_intent):
    """
    Calculate lead cost based on clinic tier and contact intent
    """
    base_costs = {
        'inquiry': 50,
        'whatsapp': 75,
        'call': 100
    }
    
    base_cost = base_costs.get(contact_intent, 75)
    
    # Premium clinics pay 25% more for higher quality leads
    if hasattr(clinic, 'is_premium') and clinic.is_premium:
        return int(base_cost * 1.25)
    
    return base_cost

def send_lead_notification_email(clinic, lead, source_name, data=None, lead_cost=0):
    """
    Send email notification to clinic about new verified lead
    """
    try:
        from flask_mail import Message
        from app import mail
        
        subject = f"New Verified Lead: {lead.patient_name} interested in {source_name}"
        
        body = f"""
        New Verified Lead Notification
        
        Lead Details:
        - Name: {lead.patient_name}
        - Phone: {lead.mobile_number}
        - Contact Intent: {data['contact_intent'].title() if data else 'Unknown'}
        - Source: {source_name}
        - Message: {lead.message}
        - Verification: Phone verified via OTP
        
        This lead has been verified with phone OTP and {lead_cost} credits have been deducted from your account.
        
        Please contact the patient as soon as possible for best conversion rates.
        
        Best regards,
        Antidote Team
        """
        
        msg = Message(
            subject=subject,
            recipients=[clinic.email],
            body=body
        )
        
        mail.send(msg)
        logger.info(f"Lead notification email sent to {clinic.email}")
        
    except Exception as e:
        logger.error(f"Failed to send lead notification email: {e}")

@lead_bp.route('/api/leads/analytics', methods=['GET'])
def lead_analytics():
    """
    Get lead analytics for admin dashboard
    """
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Get date range from query params (default last 30 days)
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic lead statistics
        total_leads = Lead.query.filter(Lead.created_at >= start_date).count()
        verified_leads = Lead.query.filter(
            and_(Lead.created_at >= start_date, Lead.status == 'verified')
        ).count()
        
        paid_leads = Lead.query.filter(
            and_(Lead.created_at >= start_date, Lead.status == 'verified')
        ).count()
        
        total_revenue = 0  # Lead cost not tracked in current model
        
        # Lead sources breakdown
        source_stats = db.session.query(
            Lead.source,
            func.count(Lead.id).label('count')
        ).filter(
            Lead.created_at >= start_date
        ).group_by(Lead.source).all()
        
        # Daily lead trend
        daily_stats = db.session.query(
            func.date(Lead.created_at).label('date'),
            func.count(Lead.id).label('leads'),
            func.count(func.nullif(Lead.status != 'verified', False)).label('verified')
        ).filter(
            Lead.created_at >= start_date
        ).group_by(func.date(Lead.created_at)).order_by('date').all()
        
        # Top performing clinics
        top_clinics = db.session.query(
            Clinic.name,
            func.count(Lead.id).label('lead_count')
        ).join(Lead).filter(
            Lead.created_at >= start_date
        ).group_by(Clinic.id, Clinic.name).order_by('lead_count desc').limit(10).all()
        
        return jsonify({
            'success': True,
            'analytics': {
                'overview': {
                    'total_leads': total_leads,
                    'verified_leads': verified_leads,
                    'verification_rate': round((verified_leads / total_leads * 100) if total_leads > 0 else 0, 2),
                    'paid_leads': paid_leads,
                    'total_revenue': total_revenue,
                    'avg_lead_value': round(total_revenue / paid_leads if paid_leads > 0 else 0, 2)
                },
                'source_breakdown': [
                    {
                        'source': stat.source,
                        'count': stat.count
                    } for stat in source_stats
                ],
                'daily_trend': [
                    {
                        'date': stat.date.strftime('%Y-%m-%d'),
                        'leads': stat.leads,
                        'verified': stat.verified or 0
                    } for stat in daily_stats
                ],
                'top_clinics': [
                    {
                        'clinic_name': clinic.name,
                        'lead_count': clinic.lead_count
                    } for clinic in top_clinics
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting lead analytics: {e}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving analytics'
        }), 500

def create_lead_from_verified_data(data, skip_session_storage=False):
    """
    Helper function to create a lead from verified data
    Used by both Firebase OTP verification and session-based verification
    """
    try:
        # Get clinic information based on source
        clinic = None
        source_name = ""
        
        if data['source_type'] == 'package':
            package = Package.query.get(data['source_id'])
            if not package:
                return jsonify({
                    'success': False,
                    'message': 'Package not found'
                }), 404
            
            # Get clinic through the relationship
            clinic = package.clinic
            source_name = package.title or package.package_name
            
        elif data['source_type'] == 'clinic':
            clinic = Clinic.query.get(data['source_id'])
            if not clinic:
                return jsonify({
                    'success': False,
                    'message': 'Clinic not found'
                }), 404
            
            source_name = clinic.name
        
        if not clinic:
            return jsonify({
                'success': False,
                'message': 'Associated clinic not found'
            }), 404
        
        # Calculate lead cost based on clinic tier and contact intent
        lead_cost = calculate_lead_cost(clinic, data['contact_intent'])
        
        # Check clinic credit balance
        if clinic.credit_balance < lead_cost:
            # Create lead but mark as insufficient credits
            payment_status = 'insufficient_credits'
            logger.warning(f"Clinic {clinic.id} has insufficient credits for lead. Required: {lead_cost}, Available: {clinic.credit_balance}")
        else:
            # Deduct credits from clinic
            clinic.credit_balance -= lead_cost
            payment_status = 'paid'
            logger.info(f"Deducted {lead_cost} credits from clinic {clinic.id}. New balance: {clinic.credit_balance}")
        
        # Create the verified lead using only valid Lead model fields
        lead = Lead(
            patient_name=data['name'],
            mobile_number=data['phone'],
            message=data.get('message', ''),
            clinic_id=clinic.id,
            package_id=data['source_id'] if data['source_type'] == 'package' else None,
            status='verified',
            source=f"{data['source_type']}_{data['contact_intent']}",
            consent_given=True,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        db.session.add(lead)
        db.session.commit()
        
        logger.info(f"Created verified lead {lead.id} for clinic {clinic.id}")
        
        # Store verification in session for future use (only if not already using session data)
        if not skip_session_storage:
            if 'verified_phones' not in session:
                session['verified_phones'] = {}
            
            clean_user_phone = ''.join(filter(str.isdigit, data['phone']))
            session['verified_phones'][clean_user_phone] = {
                'name': data['name'],
                'phone': data['phone'],
                'email': data.get('email', ''),
                'verified_at': datetime.now().isoformat(),
                'firebase_uid': data.get('firebase_uid', 'verified')
            }
            session.permanent = True
            
            logger.info(f"Stored phone verification in session for {clean_user_phone}")
        
        # Prepare response with contact information
        contact_info = {
            'whatsapp_number': clinic.contact_number,
            'phone_number': clinic.contact_number,
            'email': clinic.email
        }
        
        # Send notification email to clinic (if configured)
        try:
            send_lead_notification_email(clinic, lead, source_name, data, lead_cost)
        except Exception as e:
            logger.error(f"Failed to send lead notification email: {e}")
        
        # Prepare contact execution data for frontend
        if data['contact_intent'] == 'whatsapp':
            # Get WhatsApp number - prioritize package specific number, then clinic number
            whatsapp_number = None
            if data['source_type'] == 'package':
                # Try to get package-specific WhatsApp number
                package_result = db.session.execute(text("SELECT whatsapp_number FROM packages WHERE id = :package_id"), {'package_id': data['source_id']}).fetchone()
                if package_result and package_result[0]:
                    whatsapp_number = package_result[0]
            
            # Fallback to clinic contact number
            if not whatsapp_number:
                whatsapp_number = clinic.contact_number
            
            if whatsapp_number:
                # Clean and format phone number for WhatsApp
                # Remove all non-digit characters first
                clean_phone = ''.join(filter(str.isdigit, str(whatsapp_number)))
                
                # Ensure it starts with country code (91 for India)
                if clean_phone.startswith('91') and len(clean_phone) == 12:
                    # Already has country code
                    formatted_phone = clean_phone
                elif len(clean_phone) == 10:
                    # Add India country code
                    formatted_phone = '91' + clean_phone
                else:
                    # Use as is if it's a different format
                    formatted_phone = clean_phone
                
                # Create personalized message
                message = f"Hi! I'm interested in {source_name}. My name is {data['name']}. Could you please provide more information and help me schedule a consultation?"
                
                # Proper URL encoding for WhatsApp
                encoded_message = urllib.parse.quote(message)
                
                # WhatsApp URL format: https://wa.me/[country_code][phone_number]?text=[encoded_message]
                contact_url = f"https://wa.me/{formatted_phone}?text={encoded_message}"
                
                logger.info(f"WhatsApp URL generated: https://wa.me/{formatted_phone}?text=[message]")
            else:
                logger.error(f"No WhatsApp number found for clinic {clinic.id}")
                contact_url = None
        elif data['contact_intent'] == 'call':
            contact_url = f"tel:{contact_info['phone_number']}"
        else:
            contact_url = None
        
        return jsonify({
            'success': True,
            'message': 'Lead created successfully',
            'lead_id': lead.id,
            'clinic_name': clinic.name,
            'contact_intent': data['contact_intent'],
            'contact_url': contact_url,
            'contact_info': contact_info,
            'lead_cost': lead_cost,
            'payment_status': payment_status
        })
        
    except Exception as e:
        logger.error(f"Error creating lead from verified data: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# Template context processor to inject Firebase configuration
def inject_firebase_config():
    """Inject Firebase configuration into all templates"""
    return dict(
        firebase_api_key=os.environ.get('FIREBASE_API_KEY', ''),
        firebase_auth_domain=os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
        firebase_project_id=os.environ.get('FIREBASE_PROJECT_ID', ''),
        firebase_storage_bucket=os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
        firebase_messaging_sender_id=os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
        firebase_app_id=os.environ.get('FIREBASE_APP_ID', '')
    )