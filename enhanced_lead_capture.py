"""
Enhanced Lead Capture with Credit Processing
Integrates lead capture forms with automatic credit deduction and real-time notifications.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import text
from models import db
import logging

enhanced_lead_bp = Blueprint('enhanced_lead', __name__)
logger = logging.getLogger(__name__)

class LeadCreditService:
    """Service class for lead capture with credit processing."""
    
    @staticmethod
    def calculate_lead_cost(package_value):
        """Calculate credit cost based on package value using dynamic pricing."""
        from dynamic_lead_pricing import DynamicPricingService
        return DynamicPricingService.calculate_lead_cost(package_value)
    
    @staticmethod
    def check_clinic_credit_balance(clinic_id):
        """Check if clinic has sufficient credits."""
        try:
            result = db.session.execute(text("""
                SELECT credit_balance FROM clinics WHERE id = :clinic_id
            """), {"clinic_id": clinic_id}).fetchone()
            
            return result.credit_balance if result else 0
        except Exception as e:
            logger.error(f"Error checking credit balance: {e}")
            return 0
    
    @staticmethod
    def deduct_credits(clinic_id, credits, lead_id, description):
        """Deduct credits from clinic and record transaction."""
        try:
            # Update clinic balance
            db.session.execute(text("""
                UPDATE clinics 
                SET credit_balance = credit_balance - :credits,
                    total_credits_used = total_credits_used + :credits
                WHERE id = :clinic_id
            """), {"credits": credits, "clinic_id": clinic_id})
            
            # Record transaction
            db.session.execute(text("""
                INSERT INTO credit_transactions 
                (clinic_id, transaction_type, amount, description, lead_id, status, created_at)
                VALUES (:clinic_id, 'lead_deduction', :credits, :description, :lead_id, 'completed', :created_at)
            """), {
                "clinic_id": clinic_id,
                "credits": -credits,
                "description": description,
                "lead_id": lead_id,
                "created_at": datetime.utcnow()
            })
            
            return True
        except Exception as e:
            logger.error(f"Error deducting credits: {e}")
            return False
    
    @staticmethod
    def create_lead_with_billing(lead_data, clinic_id):
        """Create lead and process billing in one transaction."""
        try:
            package_value = lead_data.get('package_value', 0)
            credit_cost = LeadCreditService.calculate_lead_cost(package_value)
            
            # Allow negative credit balances - clinics can receive leads and go negative
            current_balance = LeadCreditService.check_clinic_credit_balance(clinic_id)
            # Removed credit balance validation to allow negative balances
            
            # Create lead
            lead_result = db.session.execute(text("""
                INSERT INTO leads 
                (clinic_id, user_id, patient_name, email, phone, mobile_number, procedure_name, 
                 lead_value, message, status, source_page, credit_cost, created_at)
                VALUES (:clinic_id, :user_id, :patient_name, :email, :phone, :mobile_number, :procedure_name,
                        :lead_value, :message, 'new', :source_page, :credit_cost, :created_at)
                RETURNING id
            """), {
                "clinic_id": clinic_id,
                "user_id": lead_data.get('user_id'),
                "patient_name": lead_data.get('user_name'),
                "email": lead_data.get('user_email'),
                "phone": lead_data.get('user_phone'),
                "mobile_number": lead_data.get('user_phone'),  # Store in both phone and mobile_number for compatibility
                "procedure_name": lead_data.get('procedure_name'),
                "lead_value": package_value,
                "message": lead_data.get('message', ''),
                "source_page": lead_data.get('source_page', 'website'),
                "credit_cost": credit_cost,
                "created_at": datetime.utcnow()
            })
            
            lead_row = lead_result.fetchone()
            if not lead_row:
                raise Exception("Failed to create lead")
            lead_id = lead_row[0]
            
            # Deduct credits
            success = LeadCreditService.deduct_credits(
                clinic_id, 
                credit_cost, 
                lead_id, 
                f"Lead generation - {lead_data.get('procedure_name')}"
            )
            
            if not success:
                raise Exception("Failed to deduct credits")
            
            # Commit the transaction
            db.session.commit()
            return True, lead_id
                
        except Exception as e:
            logger.error(f"Error creating lead with billing: {e}")
            db.session.rollback()
            return False, str(e)

@enhanced_lead_bp.route('/api/lead/cost-calculator', methods=['POST'])
def calculate_lead_cost():
    """Calculate lead cost in real-time."""
    try:
        data = request.get_json()
        package_value = data.get('package_value', 0)
        
        cost = LeadCreditService.calculate_lead_cost(package_value)
        
        return jsonify({
            'success': True,
            'credit_cost': cost,
            'package_value': package_value
        })
        
    except Exception as e:
        logger.error(f"Error calculating lead cost: {e}")
        return jsonify({'success': False, 'message': 'Error calculating cost'}), 500

@enhanced_lead_bp.route('/api/lead/submit', methods=['POST'])
def submit_lead():
    """Submit lead with automatic credit processing."""
    try:
        data = request.get_json() or request.form
        
        # Validate required fields
        required_fields = ['clinic_id', 'user_name', 'user_email', 'user_phone', 'procedure_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        clinic_id = data.get('clinic_id')
        
        # Prepare lead data
        lead_data = {
            'user_name': data.get('user_name'),
            'user_email': data.get('user_email'),
            'user_phone': data.get('user_phone'),
            'procedure_name': data.get('procedure_name'),
            'package_value': int(data.get('package_value', 0)),
            'message': data.get('message', ''),
            'source_page': data.get('source_page', 'website')
        }
        
        # Create lead with billing
        success, result = LeadCreditService.create_lead_with_billing(lead_data, clinic_id)
        
        if success:
            # Send notification to clinic (implement notification service)
            try:
                send_lead_notification(clinic_id, result, lead_data)
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")
            
            return jsonify({
                'success': True,
                'message': 'Lead submitted successfully',
                'lead_id': result
            })
        else:
            return jsonify({'success': False, 'message': result}), 400
            
    except Exception as e:
        logger.error(f"Error submitting lead: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@enhanced_lead_bp.route('/clinic/leads/dashboard')
@login_required
def lead_dashboard():
    """Enhanced lead dashboard for clinics."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            flash('Clinic profile not found.', 'danger')
            return redirect(url_for('web.index'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get leads with pagination and filtering
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        
        where_clause = "WHERE l.clinic_id = :clinic_id"
        params = {"clinic_id": clinic['id']}
        
        if status_filter != 'all':
            where_clause += " AND l.status = :status"
            params['status'] = status_filter
        
        # Get leads
        leads_result = db.session.execute(text(f"""
            SELECT l.*, p.title as package_title
            FROM leads l
            LEFT JOIN packages p ON l.package_id = p.id
            {where_clause}
            ORDER BY l.created_at DESC
            LIMIT 20 OFFSET :offset
        """), {**params, "offset": (page - 1) * 20})
        
        leads = [dict(row._mapping) for row in leads_result.fetchall()]
        
        # Get lead statistics
        stats_result = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN status = 'new' THEN 1 END) as new_leads,
                COUNT(CASE WHEN status = 'contacted' THEN 1 END) as contacted_leads,
                COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted_leads,
                COALESCE(SUM(credit_cost), 0) as total_credits_spent
            FROM leads
            WHERE clinic_id = :clinic_id
        """), {"clinic_id": clinic['id']}).fetchone()
        
        stats = dict(stats_result._mapping) if stats_result else {}
        
        return render_template('clinic/lead_dashboard.html',
                             clinic=clinic,
                             leads=leads,
                             stats=stats,
                             current_page=page,
                             status_filter=status_filter)
        
    except Exception as e:
        logger.error(f"Error loading lead dashboard: {e}")
        flash('Error loading lead dashboard.', 'danger')
        return redirect(url_for('web.index'))

@enhanced_lead_bp.route('/clinic/leads/<int:lead_id>')
@login_required
def lead_details(lead_id):
    """View detailed lead information."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            flash('Clinic profile not found.', 'danger')
            return redirect(url_for('web.index'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get lead details
        lead_result = db.session.execute(text("""
            SELECT l.*, p.title as package_title, p.description as package_description
            FROM leads l
            LEFT JOIN packages p ON l.package_id = p.id
            WHERE l.id = :lead_id AND l.clinic_id = :clinic_id
        """), {"lead_id": lead_id, "clinic_id": clinic['id']}).fetchone()
        
        if not lead_result:
            flash('Lead not found.', 'danger')
            return redirect(url_for('enhanced_lead.lead_dashboard'))
        
        lead = dict(lead_result._mapping)
        
        # Get related transaction
        transaction_result = db.session.execute(text("""
            SELECT * FROM credit_transactions
            WHERE lead_id = :lead_id AND clinic_id = :clinic_id
        """), {"lead_id": lead_id, "clinic_id": clinic['id']}).fetchone()
        
        transaction = dict(transaction_result._mapping) if transaction_result else None
        
        return render_template('clinic/lead_details.html',
                             clinic=clinic,
                             lead=lead,
                             transaction=transaction)
        
    except Exception as e:
        logger.error(f"Error loading lead details: {e}")
        flash('Error loading lead details.', 'danger')
        return redirect(url_for('enhanced_lead.lead_dashboard'))

@enhanced_lead_bp.route('/clinic/leads/<int:lead_id>/update-status', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    """Update lead status."""
    try:
        # Get clinic
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            return jsonify({'success': False, 'message': 'Clinic not found'}), 404
        
        clinic_id = clinic_result.id
        new_status = request.form.get('status')
        notes = request.form.get('notes', '')
        
        if new_status not in ['new', 'contacted', 'converted', 'lost']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        # Update lead status
        db.session.execute(text("""
            UPDATE leads 
            SET status = :status, 
                contacted_at = CASE WHEN :status = 'contacted' THEN :now ELSE contacted_at END,
                converted_at = CASE WHEN :status = 'converted' THEN :now ELSE converted_at END
            WHERE id = :lead_id AND clinic_id = :clinic_id
        """), {
            "status": new_status,
            "lead_id": lead_id,
            "clinic_id": clinic_id,
            "now": datetime.utcnow()
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Lead status updated to {new_status}'
        })
        
    except Exception as e:
        logger.error(f"Error updating lead status: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@enhanced_lead_bp.route('/instant-contact/<int:package_id>', methods=['POST'])
def instant_contact(package_id):
    """Simplified instant contact endpoint for authenticated users."""
    try:
        data = request.get_json() or {}
        contact_type = data.get('contact_type', 'whatsapp')  # 'whatsapp' or 'call'
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'requires_auth': True,
                'redirect_url': f'/auth?next=/packages/{package_id}',
                'message': 'Please sign in to get clinic contact details'
            }), 401
        
        # Get package details
        package_result = db.session.execute(text("""
            SELECT p.*, c.id as clinic_id, c.name as clinic_name, 
                   c.whatsapp_number, p.custom_phone_number,
                   p.price_discounted, p.price_actual
            FROM packages p
            JOIN clinics c ON p.clinic_id = c.id
            WHERE p.id = :package_id
        """), {"package_id": package_id}).fetchone()
        
        if not package_result:
            return jsonify({
                'success': False,
                'message': 'Package not found'
            }), 404
        
        package = dict(package_result._mapping)
        
        # Prepare lead data
        lead_data = {
            'user_id': current_user.id,
            'user_name': current_user.name,
            'user_email': getattr(current_user, 'email', ''),
            'user_phone': getattr(current_user, 'phone_number', ''),
            'procedure_name': package['title'],
            'package_value': package['price_discounted'] or package['price_actual'],
            'message': f'Interested in {package["title"]} via {contact_type}',
            'source_page': f'package_instant_{contact_type}'
        }
        
        # Create lead with billing (background process)
        success, result = LeadCreditService.create_lead_with_billing(lead_data, package['clinic_id'])
        
        if not success:
            return jsonify({
                'success': False,
                'message': f'Unable to process request: {result}'
            }), 400
        
        lead_id = result
        
        # Send notification to clinic (background)
        send_lead_notification(package['clinic_id'], lead_id, lead_data)
        
        # Return contact information immediately
        if contact_type == 'whatsapp':
            whatsapp_number = package['whatsapp_number']
            if not whatsapp_number:
                return jsonify({
                    'success': False,
                    'message': 'WhatsApp contact not available for this clinic'
                }), 400
            
            # Pre-filled message template
            message = f"Hi! I'm interested in the {package['title']} package from Antidote. Can we discuss this treatment?"
            
            return jsonify({
                'success': True,
                'contact_type': 'whatsapp',
                'whatsapp_number': whatsapp_number,
                'message_template': message,
                'whatsapp_url': f"https://wa.me/{whatsapp_number.replace('+', '').replace(' ', '')}?text={message}",
                'clinic_name': package['clinic_name'],
                'package_title': package['title']
            })
        
        elif contact_type == 'call':
            phone_number = package['custom_phone_number']
            if not phone_number:
                return jsonify({
                    'success': False,
                    'message': 'Phone contact not available for this clinic'
                }), 400
            
            return jsonify({
                'success': True,
                'contact_type': 'call',
                'phone_number': phone_number,
                'tel_url': f"tel:{phone_number}",
                'clinic_name': package['clinic_name'],
                'package_title': package['title']
            })
        
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid contact type'
            }), 400
            
    except Exception as e:
        logger.error(f"Error in instant contact: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500

@enhanced_lead_bp.route('/instant-contact/clinic/<int:clinic_id>', methods=['POST'])
def instant_contact_clinic(clinic_id):
    """Simplified instant contact endpoint for clinic pages."""
    try:
        data = request.get_json() or {}
        contact_type = data.get('contact_type', 'whatsapp')  # 'whatsapp' or 'call'
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'requires_auth': True,
                'redirect_url': f'/auth?next=/clinic/view/{clinic_id}',
                'message': 'Please sign in to get clinic contact details'
            }), 401
        
        # Get clinic details
        clinic_result = db.session.execute(text("""
            SELECT id, name, whatsapp_number, contact_number, city, address
            FROM clinics 
            WHERE id = :clinic_id
        """), {"clinic_id": clinic_id}).fetchone()
        
        if not clinic_result:
            return jsonify({
                'success': False,
                'message': 'Clinic not found'
            }), 404
        
        clinic = dict(clinic_result._mapping)
        
        # Prepare lead data for general clinic inquiry
        lead_data = {
            'user_id': current_user.id,
            'user_name': current_user.name,
            'user_email': getattr(current_user, 'email', ''),
            'user_phone': getattr(current_user, 'phone_number', ''),
            'procedure_name': 'General Inquiry',
            'package_value': 0,  # No specific package value for general inquiry
            'message': f'Interested in consulting at {clinic["name"]} via {contact_type}',
            'source_page': f'clinic_instant_{contact_type}'
        }
        
        # Create lead with billing (background process)
        success, result = LeadCreditService.create_lead_with_billing(lead_data, clinic_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': f'Unable to process request: {result}'
            }), 400
        
        lead_id = result
        
        # Send notification to clinic (background)
        send_lead_notification(clinic_id, lead_id, lead_data)
        
        # Return contact information immediately
        if contact_type == 'whatsapp':
            whatsapp_number = clinic['whatsapp_number']
            if not whatsapp_number:
                return jsonify({
                    'success': False,
                    'message': 'WhatsApp contact not available for this clinic'
                }), 400
            
            # Pre-filled message template
            message = f"Hi! I found {clinic['name']} on Antidote and would like to discuss treatment options. Can we schedule a consultation?"
            
            return jsonify({
                'success': True,
                'contact_type': 'whatsapp',
                'whatsapp_number': whatsapp_number,
                'message_template': message,
                'whatsapp_url': f"https://wa.me/{whatsapp_number.replace('+', '').replace(' ', '')}?text={message}",
                'clinic_name': clinic['name']
            })
        
        elif contact_type == 'call':
            phone_number = clinic['contact_number']
            if not phone_number:
                return jsonify({
                    'success': False,
                    'message': 'Phone contact not available for this clinic'
                }), 400
            
            return jsonify({
                'success': True,
                'contact_type': 'call',
                'phone_number': phone_number,
                'tel_url': f"tel:{phone_number}",
                'clinic_name': clinic['name']
            })
        
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid contact type'
            }), 400
            
    except Exception as e:
        logger.error(f"Error in clinic instant contact: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again.'
        }), 500

def send_lead_notification(clinic_id, lead_id, lead_data):
    """Send immediate notification to clinic about new lead."""
    try:
        # Get clinic notification preferences
        clinic_result = db.session.execute(text("""
            SELECT email, name FROM clinics WHERE id = :clinic_id
        """), {"clinic_id": clinic_id}).fetchone()
        
        if clinic_result:
            # Here you would implement email/SMS notification
            # For now, just log the notification
            logger.info(f"Lead notification sent to clinic {clinic_result.name} for lead {lead_id}")
            
    except Exception as e:
        logger.error(f"Error sending lead notification: {e}")