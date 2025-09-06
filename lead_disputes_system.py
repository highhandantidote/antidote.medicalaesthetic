"""
Lead Disputes Management System
Allows clinics to dispute leads and admins to manage disputes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db
from sqlalchemy import text
import logging

disputes_bp = Blueprint('disputes', __name__)
logger = logging.getLogger(__name__)

class LeadDisputeService:
    """Service class for managing lead disputes."""
    
    DISPUTE_REASONS = [
        'Invalid contact information',
        'Duplicate lead',
        'Not interested in procedure',
        'Fake/spam inquiry',
        'Already contacted elsewhere',
        'Price inquiry only',
        'Outside service area',
        'Medical ineligibility',
        'Other'
    ]
    
    @staticmethod
    def create_dispute(lead_id, clinic_id, reason, description=None):
        """Create a new lead dispute."""
        try:
            # Check if dispute already exists
            existing = db.session.execute(text("""
                SELECT id FROM lead_disputes 
                WHERE lead_id = :lead_id AND clinic_id = :clinic_id
            """), {"lead_id": lead_id, "clinic_id": clinic_id}).fetchone()
            
            if existing:
                return {'success': False, 'error': 'Dispute already exists for this lead'}
            
            # Create dispute
            db.session.execute(text("""
                INSERT INTO lead_disputes (lead_id, clinic_id, reason, status, created_at)
                VALUES (:lead_id, :clinic_id, :reason, 'pending', CURRENT_TIMESTAMP)
            """), {
                "lead_id": lead_id,
                "clinic_id": clinic_id, 
                "reason": f"{reason}. {description}" if description else reason
            })
            
            # Update lead status
            db.session.execute(text("""
                UPDATE leads SET status = 'disputed', updated_at = CURRENT_TIMESTAMP
                WHERE id = :lead_id
            """), {"lead_id": lead_id})
            
            db.session.commit()
            
            logger.info(f"Dispute created for lead {lead_id} by clinic {clinic_id}")
            return {'success': True, 'message': 'Dispute submitted successfully'}
            
        except Exception as e:
            logger.error(f"Error creating dispute: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_clinic_disputes(clinic_id, status_filter=None):
        """Get disputes for a clinic."""
        try:
            base_query = """
                SELECT 
                    ld.*,
                    l.patient_name,
                    l.mobile_number,
                    l.procedure_name,
                    l.created_at as lead_created_at,
                    ct.amount as refund_amount
                FROM lead_disputes ld
                JOIN leads l ON ld.lead_id = l.id
                LEFT JOIN credit_transactions ct ON (ct.lead_id = l.id AND ct.transaction_type = 'refund')
                WHERE ld.clinic_id = :clinic_id
            """
            
            params = {"clinic_id": clinic_id}
            
            if status_filter and status_filter != 'all':
                base_query += " AND ld.status = :status"
                params["status"] = status_filter
                
            base_query += " ORDER BY ld.created_at DESC"
            
            disputes = db.session.execute(text(base_query), params).fetchall()
            return [dict(row._mapping) for row in disputes]
            
        except Exception as e:
            logger.error(f"Error getting clinic disputes: {e}")
            return []
    
    @staticmethod
    def get_admin_disputes(status_filter=None):
        """Get all disputes for admin review."""
        try:
            base_query = """
                SELECT 
                    ld.*,
                    l.patient_name,
                    l.mobile_number,
                    l.procedure_name,
                    l.created_at as lead_created_at,
                    c.name as clinic_name,
                    ct.amount as billed_amount
                FROM lead_disputes ld
                JOIN leads l ON ld.lead_id = l.id
                JOIN clinics c ON ld.clinic_id = c.id
                LEFT JOIN credit_transactions ct ON (ct.lead_id = l.id AND ct.transaction_type = 'deduction')
                WHERE 1=1
            """
            
            params = {}
            
            if status_filter and status_filter != 'all':
                base_query += " AND ld.status = :status"
                params["status"] = status_filter
                
            base_query += " ORDER BY ld.created_at DESC"
            
            disputes = db.session.execute(text(base_query), params).fetchall()
            return [dict(row._mapping) for row in disputes]
            
        except Exception as e:
            logger.error(f"Error getting admin disputes: {e}")
            return []
    
    @staticmethod
    def resolve_dispute(dispute_id, admin_id, action, admin_notes=None):
        """Resolve a dispute (approve/reject)."""
        try:
            # Get dispute details
            dispute = db.session.execute(text("""
                SELECT ld.*, ct.amount as billed_amount
                FROM lead_disputes ld
                LEFT JOIN credit_transactions ct ON (ct.lead_id = ld.lead_id AND ct.transaction_type = 'deduction')
                WHERE ld.id = :dispute_id
            """), {"dispute_id": dispute_id}).fetchone()
            
            if not dispute:
                return {'success': False, 'error': 'Dispute not found'}
            
            dispute_dict = dict(dispute._mapping)
            
            # Update dispute status
            status = 'approved' if action == 'approve' else 'rejected'
            db.session.execute(text("""
                UPDATE lead_disputes SET 
                    status = :status,
                    admin_notes = :admin_notes,
                    resolved_at = CURRENT_TIMESTAMP,
                    resolved_by = :admin_id,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :dispute_id
            """), {
                "status": status,
                "admin_notes": admin_notes,
                "admin_id": admin_id,
                "dispute_id": dispute_id
            })
            
            # If approved, issue refund
            if action == 'approve' and dispute_dict['billed_amount']:
                refund_amount = abs(dispute_dict['billed_amount'])
                
                # Add refund transaction
                db.session.execute(text("""
                    INSERT INTO credit_transactions (
                        clinic_id, transaction_type, amount, description, 
                        lead_id, status, created_at, processed_at
                    ) VALUES (
                        :clinic_id, 'refund', :amount, :description,
                        :lead_id, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """), {
                    "clinic_id": dispute_dict['clinic_id'],
                    "amount": refund_amount,
                    "description": f"Refund for disputed lead - {dispute_dict['reason']}",
                    "lead_id": dispute_dict['lead_id']
                })
                
                # Update clinic balance
                from enhanced_credit_billing import EnhancedCreditBillingService
                EnhancedCreditBillingService.get_clinic_credit_balance(dispute_dict['clinic_id'])
            
            # Update lead status
            new_lead_status = 'refunded' if action == 'approve' else 'active'
            db.session.execute(text("""
                UPDATE leads SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE id = :lead_id
            """), {"status": new_lead_status, "lead_id": dispute_dict['lead_id']})
            
            db.session.commit()
            
            logger.info(f"Dispute {dispute_id} resolved: {action} by admin {admin_id}")
            return {'success': True, 'action': action, 'refund_issued': action == 'approve'}
            
        except Exception as e:
            logger.error(f"Error resolving dispute: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

@disputes_bp.route('/clinic/disputes')
@login_required
def clinic_disputes():
    """Clinic disputes dashboard."""
    try:
        # Get clinic
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            flash('No clinic found for your account.', 'error')
            return redirect(url_for('web.index'))
        
        clinic_dict = dict(clinic._mapping)
        
        # Get filter
        status_filter = request.args.get('status', 'all')
        
        # Get disputes
        disputes = LeadDisputeService.get_clinic_disputes(clinic_dict['id'], status_filter)
        
        # Get dispute statistics
        stats = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_disputes,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_disputes,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_disputes,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_disputes
            FROM lead_disputes
            WHERE clinic_id = :clinic_id
        """), {"clinic_id": clinic_dict['id']}).fetchone()
        
        stats_dict = dict(stats._mapping) if stats else {
            'total_disputes': 0, 'pending_disputes': 0, 'approved_disputes': 0, 'rejected_disputes': 0
        }
        
        return render_template('clinic/disputes.html',
                             clinic=clinic_dict,
                             disputes=disputes,
                             stats=stats_dict,
                             status_filter=status_filter,
                             dispute_reasons=LeadDisputeService.DISPUTE_REASONS)
        
    except Exception as e:
        logger.error(f"Error in clinic disputes: {e}")
        flash('Error loading disputes. Please try again.', 'error')
        return redirect(url_for('enhanced_billing.billing_dashboard'))

@disputes_bp.route('/clinic/dispute-lead', methods=['POST'])
@login_required
def submit_dispute():
    """Submit a new lead dispute."""
    try:
        # Get clinic
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        clinic_dict = dict(clinic._mapping)
        
        # Get form data
        lead_id = int(request.form.get('lead_id'))
        reason = request.form.get('reason')
        description = request.form.get('description', '')
        
        # Validate lead belongs to clinic
        lead = db.session.execute(text("""
            SELECT * FROM leads WHERE id = :lead_id AND clinic_id = :clinic_id
        """), {"lead_id": lead_id, "clinic_id": clinic_dict['id']}).fetchone()
        
        if not lead:
            return jsonify({'success': False, 'error': 'Lead not found or not authorized'})
        
        # Create dispute
        result = LeadDisputeService.create_dispute(lead_id, clinic_dict['id'], reason, description)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error submitting dispute: {e}")
        return jsonify({'success': False, 'error': str(e)})

@disputes_bp.route('/admin/disputes')
@login_required
def admin_disputes():
    """Admin disputes management."""
    if not current_user.role == 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('web.index'))
    
    try:
        # Get filter
        status_filter = request.args.get('status', 'pending')
        
        # Get disputes
        disputes = LeadDisputeService.get_admin_disputes(status_filter)
        
        # Get dispute statistics
        stats = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_disputes,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_disputes,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_disputes,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_disputes,
                COALESCE(SUM(CASE WHEN status = 'approved' THEN ct.amount ELSE 0 END), 0) as total_refunds
            FROM lead_disputes ld
            LEFT JOIN credit_transactions ct ON (ct.lead_id = ld.lead_id AND ct.transaction_type = 'refund')
        """)).fetchone()
        
        stats_dict = dict(stats._mapping) if stats else {
            'total_disputes': 0, 'pending_disputes': 0, 'approved_disputes': 0, 
            'rejected_disputes': 0, 'total_refunds': 0
        }
        
        return render_template('admin/disputes.html',
                             disputes=disputes,
                             stats=stats_dict,
                             status_filter=status_filter)
        
    except Exception as e:
        logger.error(f"Error in admin disputes: {e}")
        flash('Error loading disputes. Please try again.', 'error')
        return redirect(url_for('web.admin_dashboard'))

@disputes_bp.route('/admin/resolve-dispute', methods=['POST'])
@login_required
def resolve_dispute():
    """Admin route to resolve disputes."""
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        dispute_id = int(request.form.get('dispute_id'))
        action = request.form.get('action')  # approve or reject
        admin_notes = request.form.get('admin_notes', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'success': False, 'error': 'Invalid action'})
        
        result = LeadDisputeService.resolve_dispute(dispute_id, current_user.id, action, admin_notes)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error resolving dispute: {e}")
        return jsonify({'success': False, 'error': str(e)})