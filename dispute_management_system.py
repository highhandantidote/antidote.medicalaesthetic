#!/usr/bin/env python3
"""
Comprehensive Dispute Management System
Handles lead disputes, resolution workflows, and clinic communication
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import text, and_, or_, desc
from datetime import datetime, timedelta
import logging
from app import db

logger = logging.getLogger(__name__)

# Create blueprint
dispute_bp = Blueprint('dispute', __name__, template_folder='templates')

def admin_required_dispute(f):
    """Decorator to require admin access for disputes"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('web.index'))
        return f(*args, **kwargs)
    return decorated_function

def clinic_required_dispute(f):
    """Decorator to require clinic access for disputes"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['clinic', 'admin']:
            flash('Access denied. Clinic access required.', 'danger')
            return redirect(url_for('web.index'))
        return f(*args, **kwargs)
    return decorated_function

class DisputeService:
    """Service class for dispute management functionality."""
    
    @staticmethod
    def create_dispute_tables():
        """Create dispute-related tables if they don't exist."""
        try:
            # Create lead_disputes table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS lead_disputes (
                    id SERIAL PRIMARY KEY,
                    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
                    clinic_id INTEGER REFERENCES clinics(id),
                    reason VARCHAR(100) NOT NULL,
                    description TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    priority VARCHAR(20) DEFAULT 'medium',
                    evidence_urls TEXT[],
                    created_at TIMESTAMP DEFAULT NOW(),
                    resolved_at TIMESTAMP,
                    resolved_by INTEGER REFERENCES users(id),
                    resolution_notes TEXT,
                    refund_amount INTEGER DEFAULT 0,
                    admin_notes TEXT,
                    escalation_level INTEGER DEFAULT 1,
                    last_updated TIMESTAMP DEFAULT NOW()
                )
            """))
            
            # Create dispute_messages table for communication
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS dispute_messages (
                    id SERIAL PRIMARY KEY,
                    dispute_id INTEGER REFERENCES lead_disputes(id) ON DELETE CASCADE,
                    sender_id INTEGER REFERENCES users(id),
                    sender_type VARCHAR(20) NOT NULL, -- 'admin', 'clinic'
                    message TEXT NOT NULL,
                    is_internal BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            
            # Create dispute_status_history table for audit trail
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS dispute_status_history (
                    id SERIAL PRIMARY KEY,
                    dispute_id INTEGER REFERENCES lead_disputes(id) ON DELETE CASCADE,
                    previous_status VARCHAR(50),
                    new_status VARCHAR(50) NOT NULL,
                    changed_by INTEGER REFERENCES users(id),
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            
            # Create indexes for better performance
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_disputes_clinic ON lead_disputes(clinic_id);
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_disputes_status ON lead_disputes(status);
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_disputes_created ON lead_disputes(created_at);
            """))
            
            db.session.commit()
            logger.info("Dispute management tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating dispute tables: {str(e)}")
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_clinic_disputes(clinic_id, status=None, limit=50):
        """Get disputes for a specific clinic."""
        query = """
            SELECT 
                d.id,
                d.lead_id,
                d.reason,
                d.description,
                d.status,
                d.priority,
                d.created_at,
                d.resolved_at,
                d.refund_amount,
                d.escalation_level,
                l.patient_name,
                l.procedure_name,
                l.credit_cost,
                l.mobile_number,
                u_resolved.username as resolved_by_admin
            FROM lead_disputes d
            JOIN leads l ON d.lead_id = l.id
            LEFT JOIN users u_resolved ON d.resolved_by = u_resolved.id
            WHERE d.clinic_id = :clinic_id
        """
        
        params = {'clinic_id': clinic_id}
        
        if status:
            query += " AND d.status = :status"
            params['status'] = status
            
        query += " ORDER BY d.created_at DESC LIMIT :limit"
        params['limit'] = limit
        
        result = db.session.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in result]
    
    @staticmethod
    def get_all_disputes(status=None, priority=None, limit=100):
        """Get all disputes for admin view."""
        query = """
            SELECT 
                d.id,
                d.lead_id,
                d.clinic_id,
                d.reason,
                d.description,
                d.status,
                d.priority,
                d.created_at,
                d.resolved_at,
                d.refund_amount,
                d.escalation_level,
                d.admin_notes,
                l.patient_name,
                l.procedure_name,
                l.credit_cost,
                l.mobile_number,
                c.name as clinic_name,
                u_resolved.username as resolved_by_admin
            FROM lead_disputes d
            JOIN leads l ON d.lead_id = l.id
            JOIN clinics c ON d.clinic_id = c.id
            LEFT JOIN users u_resolved ON d.resolved_by = u_resolved.id
            WHERE 1=1
        """
        
        params = {}
        
        if status:
            query += " AND d.status = :status"
            params['status'] = status
            
        if priority:
            query += " AND d.priority = :priority"
            params['priority'] = priority
            
        query += " ORDER BY d.escalation_level DESC, d.created_at DESC LIMIT :limit"
        params['limit'] = limit
        
        result = db.session.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in result]
    
    @staticmethod
    def create_dispute(lead_id, clinic_id, reason, description, priority='medium'):
        """Create a new dispute."""
        try:
            # Check if dispute already exists for this lead
            existing = db.session.execute(text("""
                SELECT id FROM lead_disputes WHERE lead_id = :lead_id AND status IN ('pending', 'under_review')
            """), {'lead_id': lead_id}).fetchone()
            
            if existing:
                return {'success': False, 'message': 'A dispute already exists for this lead'}
            
            # Create the dispute
            dispute_id = db.session.execute(text("""
                INSERT INTO lead_disputes (lead_id, clinic_id, reason, description, priority, created_at)
                VALUES (:lead_id, :clinic_id, :reason, :description, :priority, NOW())
                RETURNING id
            """), {
                'lead_id': lead_id,
                'clinic_id': clinic_id,
                'reason': reason,
                'description': description,
                'priority': priority
            }).fetchone()[0]
            
            # Add initial status history
            db.session.execute(text("""
                INSERT INTO dispute_status_history (dispute_id, new_status, changed_by, reason, created_at)
                VALUES (:dispute_id, 'pending', :user_id, 'Dispute created', NOW())
            """), {
                'dispute_id': dispute_id,
                'user_id': current_user.id
            })
            
            db.session.commit()
            return {'success': True, 'dispute_id': dispute_id}
            
        except Exception as e:
            logger.error(f"Error creating dispute: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def update_dispute_status(dispute_id, new_status, admin_notes=None, refund_amount=0):
        """Update dispute status."""
        try:
            # Get current status
            current_dispute = db.session.execute(text("""
                SELECT status FROM lead_disputes WHERE id = :dispute_id
            """), {'dispute_id': dispute_id}).fetchone()
            
            if not current_dispute:
                return {'success': False, 'message': 'Dispute not found'}
            
            previous_status = current_dispute[0]
            
            # Update dispute
            update_data = {
                'dispute_id': dispute_id,
                'new_status': new_status,
                'admin_notes': admin_notes,
                'refund_amount': refund_amount,
                'resolved_by': current_user.id if new_status in ['resolved', 'rejected'] else None
            }
            
            if new_status in ['resolved', 'rejected']:
                db.session.execute(text("""
                    UPDATE lead_disputes 
                    SET status = :new_status, admin_notes = :admin_notes, 
                        refund_amount = :refund_amount, resolved_by = :resolved_by, 
                        resolved_at = NOW(), last_updated = NOW()
                    WHERE id = :dispute_id
                """), update_data)
            else:
                db.session.execute(text("""
                    UPDATE lead_disputes 
                    SET status = :new_status, admin_notes = :admin_notes, last_updated = NOW()
                    WHERE id = :dispute_id
                """), update_data)
            
            # Add status history
            db.session.execute(text("""
                INSERT INTO dispute_status_history 
                (dispute_id, previous_status, new_status, changed_by, reason, created_at)
                VALUES (:dispute_id, :previous_status, :new_status, :user_id, :reason, NOW())
            """), {
                'dispute_id': dispute_id,
                'previous_status': previous_status,
                'new_status': new_status,
                'user_id': current_user.id,
                'reason': admin_notes or f'Status changed to {new_status}'
            })
            
            # Process refund if applicable
            if new_status == 'resolved' and refund_amount > 0:
                DisputeService.process_refund(dispute_id, refund_amount)
            
            db.session.commit()
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error updating dispute status: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def process_refund(dispute_id, refund_amount):
        """Process refund for resolved dispute."""
        try:
            # Get dispute and clinic info
            dispute_info = db.session.execute(text("""
                SELECT d.clinic_id, l.credit_cost, c.name as clinic_name
                FROM lead_disputes d
                JOIN leads l ON d.lead_id = l.id
                JOIN clinics c ON d.clinic_id = c.id
                WHERE d.id = :dispute_id
            """), {'dispute_id': dispute_id}).fetchone()
            
            if not dispute_info:
                return {'success': False, 'message': 'Dispute not found'}
            
            # Add credit back to clinic
            db.session.execute(text("""
                UPDATE clinics 
                SET credit_balance = credit_balance + :refund_amount 
                WHERE id = :clinic_id
            """), {
                'refund_amount': refund_amount,
                'clinic_id': dispute_info.clinic_id
            })
            
            # Record the transaction
            db.session.execute(text("""
                INSERT INTO credit_transactions 
                (clinic_id, amount, transaction_type, description, created_by, reference_id, created_at)
                VALUES 
                (:clinic_id, :amount, 'dispute_refund', :description, :admin_id, :reference_id, NOW())
            """), {
                'clinic_id': dispute_info.clinic_id,
                'amount': refund_amount,
                'description': f'Refund for dispute #{dispute_id}',
                'admin_id': current_user.id,
                'reference_id': f'dispute_{dispute_id}'
            })
            
            logger.info(f"Processed refund of {refund_amount} credits for dispute {dispute_id}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return {'success': False, 'message': str(e)}

# Routes for clinic dispute management
@dispute_bp.route('/clinic/disputes')
@login_required
@clinic_required_dispute
def clinic_disputes():
    """Clinic dispute dashboard."""
    try:
        # Get clinic ID from current user
        clinic = db.session.execute(text("""
            SELECT id FROM clinics WHERE user_id = :user_id
        """), {'user_id': current_user.id}).fetchone()
        
        if not clinic:
            flash('Clinic not found', 'danger')
            return redirect(url_for('web.index'))
        
        clinic_id = clinic[0]
        
        # Get filter parameters
        status_filter = request.args.get('status', 'all')
        
        # Get disputes
        disputes = DisputeService.get_clinic_disputes(
            clinic_id=clinic_id,
            status=status_filter if status_filter != 'all' else None
        )
        
        # Get dispute statistics
        stats = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_disputes,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_disputes,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_disputes,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_disputes,
                COALESCE(SUM(CASE WHEN status = 'resolved' THEN refund_amount END), 0) as total_refunds
            FROM lead_disputes 
            WHERE clinic_id = :clinic_id
        """), {'clinic_id': clinic_id}).fetchone()
        
        dispute_stats = dict(stats._mapping) if stats else {
            'total_disputes': 0, 'pending_disputes': 0, 
            'resolved_disputes': 0, 'rejected_disputes': 0, 'total_refunds': 0
        }
        
        return render_template('clinic/disputes.html',
                              disputes=disputes,
                              stats=dispute_stats,
                              status_filter=status_filter)
                              
    except Exception as e:
        logger.error(f"Error loading clinic disputes: {str(e)}")
        flash('Error loading disputes', 'danger')
        return redirect(url_for('web.index'))

@dispute_bp.route('/clinic/disputes/create', methods=['POST'])
@login_required
@clinic_required_dispute
def create_clinic_dispute():
    """Create a new dispute from clinic."""
    try:
        # Get clinic ID
        clinic = db.session.execute(text("""
            SELECT id FROM clinics WHERE user_id = :user_id
        """), {'user_id': current_user.id}).fetchone()
        
        if not clinic:
            return jsonify({'success': False, 'message': 'Clinic not found'})
        
        clinic_id = clinic[0]
        
        # Get form data
        lead_id = request.form.get('lead_id', type=int)
        reason = request.form.get('reason')
        description = request.form.get('description')
        priority = request.form.get('priority', 'medium')
        
        if not all([lead_id, reason, description]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Verify lead belongs to clinic
        lead_check = db.session.execute(text("""
            SELECT id FROM leads WHERE id = :lead_id AND clinic_id = :clinic_id
        """), {'lead_id': lead_id, 'clinic_id': clinic_id}).fetchone()
        
        if not lead_check:
            return jsonify({'success': False, 'message': 'Lead not found or access denied'})
        
        # Create dispute
        result = DisputeService.create_dispute(lead_id, clinic_id, reason, description, priority)
        
        if result['success']:
            flash('Dispute created successfully', 'success')
        else:
            flash(f'Error creating dispute: {result["message"]}', 'danger')
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating dispute: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

# Routes for admin dispute management
@dispute_bp.route('/admin/disputes')
@login_required
@admin_required_dispute
def admin_disputes():
    """Admin dispute management dashboard."""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', 'all')
        priority_filter = request.args.get('priority', 'all')
        
        # Get all disputes
        disputes = DisputeService.get_all_disputes(
            status=status_filter if status_filter != 'all' else None,
            priority=priority_filter if priority_filter != 'all' else None
        )
        
        # Get overall dispute statistics
        stats = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_disputes,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_disputes,
                COUNT(CASE WHEN status = 'under_review' THEN 1 END) as under_review_disputes,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_disputes,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_disputes,
                COALESCE(SUM(CASE WHEN status = 'resolved' THEN refund_amount END), 0) as total_refunds,
                COUNT(CASE WHEN priority = 'high' AND status IN ('pending', 'under_review') THEN 1 END) as high_priority_open
            FROM lead_disputes
        """)).fetchone()
        
        dispute_stats = dict(stats._mapping) if stats else {}
        
        return render_template('admin/disputes.html',
                              disputes=disputes,
                              stats=dispute_stats,
                              status_filter=status_filter,
                              priority_filter=priority_filter)
                              
    except Exception as e:
        logger.error(f"Error loading admin disputes: {str(e)}")
        flash('Error loading disputes', 'danger')
        return redirect(url_for('web.admin_dashboard'))

@dispute_bp.route('/admin/disputes/<int:dispute_id>/update', methods=['POST'])
@login_required
@admin_required_dispute
def update_dispute(dispute_id):
    """Update dispute status and resolution."""
    try:
        new_status = request.form.get('status')
        admin_notes = request.form.get('admin_notes')
        refund_amount = int(request.form.get('refund_amount', 0))
        
        if not new_status:
            return jsonify({'success': False, 'message': 'Status is required'})
        
        result = DisputeService.update_dispute_status(
            dispute_id, new_status, admin_notes, refund_amount
        )
        
        if result['success']:
            flash('Dispute updated successfully', 'success')
        else:
            flash(f'Error updating dispute: {result["message"]}', 'danger')
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error updating dispute: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

# Initialize dispute tables when module loads
try:
    DisputeService.create_dispute_tables()
except Exception as e:
    logger.warning(f"Could not create dispute tables during module load: {str(e)}")