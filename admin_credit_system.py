"""
Admin Credit Management System - Core Foundation
Provides manual credit allocation and management without payment gateway dependency.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf
from datetime import datetime
from sqlalchemy import text
from models import db
import logging
from credit_notification_system import CreditNotificationService

admin_credit_bp = Blueprint('admin_credit', __name__)
logger = logging.getLogger(__name__)

class AdminCreditService:
    """Service class for admin credit operations."""
    
    @staticmethod
    def get_all_clinics_with_balances():
        """Get all clinics with their current credit balances."""
        try:
            result = db.session.execute(text("""
                SELECT c.id, c.name, c.email, c.credit_balance,
                       c.total_credits_purchased, c.total_credits_used,
                       u.username as owner_username
                FROM clinics c
                LEFT JOIN users u ON c.owner_user_id = u.id
                ORDER BY c.name
            """))
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching clinics with balances: {e}")
            return []
    
    @staticmethod
    def get_clinic_transaction_history(clinic_id, limit=50):
        """Get transaction history for a specific clinic."""
        try:
            result = db.session.execute(text("""
                SELECT ct.*, c.name as clinic_name
                FROM credit_transactions ct
                LEFT JOIN clinics c ON ct.clinic_id = c.id
                WHERE ct.clinic_id = :clinic_id
                ORDER BY ct.created_at DESC
                LIMIT :limit
            """), {"clinic_id": clinic_id, "limit": limit})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching transaction history: {e}")
            return []
    
    @staticmethod
    def get_all_leads_with_details():
        """Get all leads with clinic and source information for admin dashboard."""
        try:
            result = db.session.execute(text("""
                SELECT l.*, c.name as clinic_name, c.email as clinic_email,
                       u.username as clinic_owner
                FROM leads l
                LEFT JOIN clinics c ON l.clinic_id = c.id
                LEFT JOIN users u ON c.owner_user_id = u.id
                ORDER BY l.created_at DESC
            """))
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching all leads: {e}")
            return []
    
    @staticmethod
    def get_lead_source_analytics():
        """Get analytics on lead sources for admin dashboard."""
        try:
            result = db.session.execute(text("""
                SELECT source_page, COUNT(*) as lead_count,
                       AVG(credit_cost) as avg_credit_cost,
                       SUM(credit_cost) as total_credits_spent
                FROM leads
                WHERE source_page IS NOT NULL
                GROUP BY source_page
                ORDER BY lead_count DESC
            """))
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching lead source analytics: {e}")
            return []
    
    @staticmethod
    def get_lead_status_summary():
        """Get summary of lead statuses across all clinics."""
        try:
            result = db.session.execute(text("""
                SELECT status, COUNT(*) as count,
                       COUNT(DISTINCT clinic_id) as clinic_count
                FROM leads
                GROUP BY status
                ORDER BY count DESC
            """))
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching lead status summary: {e}")
            return []
    
    @staticmethod
    def allocate_credits(clinic_id, credits, description, admin_user_id):
        """Manually allocate credits to a clinic."""
        try:
            # Update clinic balance
            db.session.execute(text("""
                UPDATE clinics 
                SET credit_balance = credit_balance + :credits,
                    total_credits_purchased = total_credits_purchased + :credits
                WHERE id = :clinic_id
            """), {"credits": credits, "clinic_id": clinic_id})
            
            # Generate reference ID
            import uuid
            timestamp = datetime.now().strftime('%Y%m%d')
            short_uuid = str(uuid.uuid4()).replace('-', '').upper()[:8]
            reference_id = f"TXN-{timestamp}-{short_uuid}"
            
            # Record transaction
            db.session.execute(text("""
                INSERT INTO credit_transactions 
                (clinic_id, transaction_type, amount, description, status, created_at, created_by, reference_id)
                VALUES (:clinic_id, 'manual_allocation', :credits, :description, 'completed', :created_at, :admin_user_id, :reference_id)
            """), {
                "clinic_id": clinic_id,
                "credits": credits,
                "description": f"Admin allocation: {description} (by user {admin_user_id})",
                "created_at": datetime.utcnow(),
                "admin_user_id": admin_user_id,
                "reference_id": reference_id
            })
            
            # Commit the changes
            db.session.commit()
            
            # Create notification for the clinic
            try:
                # Get the transaction ID for the notification
                transaction_result = db.session.execute(text("""
                    SELECT id FROM credit_transactions 
                    WHERE clinic_id = :clinic_id 
                    AND transaction_type = 'manual_allocation' 
                    ORDER BY created_at DESC LIMIT 1
                """), {"clinic_id": clinic_id}).fetchone()
                
                if transaction_result:
                    CreditNotificationService.create_credit_notification(
                        transaction_id=transaction_result.id,
                        clinic_id=clinic_id,
                        transaction_type='manual_allocation',
                        amount=credits,
                        description=description
                    )
            except Exception as notif_error:
                logger.warning(f"Failed to create notification for credit allocation: {notif_error}")
            
            logger.info(f"Successfully allocated {credits} credits to clinic {clinic_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error allocating credits: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def debit_credits(clinic_id, credits, description, admin_user_id):
        """Debit credits from a clinic for refund situations."""
        try:
            # Check if clinic has enough credits
            result = db.session.execute(text("""
                SELECT credit_balance FROM clinics WHERE id = :clinic_id
            """), {"clinic_id": clinic_id}).fetchone()
            
            if not result:
                return False, "Clinic not found"
            
            current_balance = result.credit_balance or 0
            if current_balance < credits:
                return False, f"Insufficient credits. Current balance: {current_balance}, Requested debit: {credits}"
            
            # Generate reference ID
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d')
            short_uuid = str(uuid.uuid4()).replace('-', '').upper()[:8]
            reference_id = f"DEB-{timestamp}-{short_uuid}"
            
            # Deduct credits from clinic balance
            db.session.execute(text("""
                UPDATE clinics 
                SET credit_balance = credit_balance - :credits
                WHERE id = :clinic_id
            """), {"credits": credits, "clinic_id": clinic_id})
            
            # Record debit transaction
            db.session.execute(text("""
                INSERT INTO credit_transactions 
                (clinic_id, transaction_type, amount, description, status, created_at, created_by, reference_id)
                VALUES (:clinic_id, 'debit_adjustment', :credits, :description, 'completed', :created_at, :admin_user_id, :reference_id)
            """), {
                "clinic_id": clinic_id,
                "credits": -credits,  # Negative amount for debit
                "description": f"Admin debit: {description} (by user {admin_user_id})",
                "created_at": datetime.utcnow(),
                "admin_user_id": admin_user_id,
                "reference_id": reference_id
            })
            
            # Commit the changes
            db.session.commit()
            
            # Create notification for the clinic
            try:
                # Get the transaction ID for the notification
                transaction_result = db.session.execute(text("""
                    SELECT id FROM credit_transactions 
                    WHERE clinic_id = :clinic_id 
                    AND transaction_type = 'debit_adjustment' 
                    ORDER BY created_at DESC LIMIT 1
                """), {"clinic_id": clinic_id}).fetchone()
                
                if transaction_result:
                    CreditNotificationService.create_credit_notification(
                        transaction_id=transaction_result.id,
                        clinic_id=clinic_id,
                        transaction_type='debit_adjustment',
                        amount=-credits,  # Negative amount for debit
                        description=description
                    )
            except Exception as notif_error:
                logger.warning(f"Failed to create notification for credit debit: {notif_error}")
            
            logger.info(f"Successfully debited {credits} credits from clinic {clinic_id}")
            return True, f"Successfully debited {credits} credits. Reference: {reference_id}"
            
        except Exception as e:
            logger.error(f"Error debiting credits: {e}")
            db.session.rollback()
            return False, f"Debit failed: {str(e)}"
    
    @staticmethod
    def transfer_credits(from_clinic_id, to_clinic_id, credits, description, admin_user_id):
        """Transfer credits between clinics."""
        try:
            # Check if source clinic has enough credits
            result = db.session.execute(text("""
                SELECT credit_balance FROM clinics WHERE id = :clinic_id
            """), {"clinic_id": from_clinic_id}).fetchone()
            
            if not result or (result.credit_balance or 0) < credits:
                return False, "Insufficient credits in source clinic"
            
            # Deduct from source clinic
            db.session.execute(text("""
                UPDATE clinics 
                SET credit_balance = credit_balance - :credits
                WHERE id = :clinic_id
            """), {"credits": credits, "clinic_id": from_clinic_id})
            
            # Add to destination clinic
            db.session.execute(text("""
                UPDATE clinics 
                SET credit_balance = credit_balance + :credits
                WHERE id = :clinic_id
            """), {"credits": credits, "clinic_id": to_clinic_id})
            
            # Record transactions
            timestamp = datetime.utcnow()
            
            # Deduction transaction
            db.session.execute(text("""
                INSERT INTO credit_transactions 
                (clinic_id, transaction_type, amount, description, status, created_at)
                VALUES (:clinic_id, 'transfer_out', :credits, :description, 'completed', :created_at)
            """), {
                "clinic_id": from_clinic_id,
                "credits": -credits,
                "description": f"Transfer to clinic {to_clinic_id}: {description}",
                "created_at": timestamp
            })
            
            # Addition transaction
            db.session.execute(text("""
                INSERT INTO credit_transactions 
                (clinic_id, transaction_type, amount, description, status, created_at)
                VALUES (:clinic_id, 'transfer_in', :credits, :description, 'completed', :created_at)
            """), {
                "clinic_id": to_clinic_id,
                "credits": credits,
                "description": f"Transfer from clinic {from_clinic_id}: {description}",
                "created_at": timestamp
            })
            
            # Commit all changes
            db.session.commit()
            return True, "Transfer completed successfully"
            
        except Exception as e:
            logger.error(f"Error transferring credits: {e}")
            db.session.rollback()
            return False, f"Transfer failed: {str(e)}"
    
    @staticmethod
    def bulk_allocate_credits(allocations, admin_user_id):
        """Bulk allocate credits to multiple clinics."""
        try:
            successful = 0
            failed = 0
            
            for allocation in allocations:
                clinic_id = allocation.get('clinic_id')
                credits = allocation.get('credits')
                description = allocation.get('description', 'Bulk allocation')
                
                if AdminCreditService.allocate_credits(clinic_id, credits, description, admin_user_id):
                    successful += 1
                else:
                    failed += 1
            
            return successful, failed
            
        except Exception as e:
            logger.error(f"Error in bulk allocation: {e}")
            return 0, len(allocations)

@admin_credit_bp.route('/admin/credits')
@login_required
def credit_dashboard():
    """Comprehensive admin dashboard with credit and lead management."""
    # Check if user is admin
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('web.index'))
    
    # Get clinic data
    clinics = AdminCreditService.get_all_clinics_with_balances()
    
    # Get lead management data
    all_leads = AdminCreditService.get_all_leads_with_details()
    lead_source_analytics = AdminCreditService.get_lead_source_analytics()
    lead_status_summary = AdminCreditService.get_lead_status_summary()
    
    # Calculate summary statistics
    total_credits_in_system = sum(clinic['credit_balance'] or 0 for clinic in clinics)
    total_credits_purchased = sum(clinic['total_credits_purchased'] or 0 for clinic in clinics)
    total_credits_used = sum(clinic['total_credits_used'] or 0 for clinic in clinics)
    
    stats = {
        'total_clinics': len(clinics),
        'total_credits_in_system': total_credits_in_system,
        'total_credits_purchased': total_credits_purchased,
        'total_credits_used': total_credits_used,
        'low_balance_clinics': len([c for c in clinics if (c['credit_balance'] or 0) < 500]),
        'total_leads': len(all_leads),
        'leads_this_month': len([l for l in all_leads if l['created_at'] and l['created_at'].month == datetime.now().month]),
        'total_lead_revenue': sum(l['credit_cost'] or 0 for l in all_leads)
    }
    
    # Get recent transactions for the template
    try:
        recent_transactions_result = db.session.execute(text("""
            SELECT ct.*, c.name as clinic_name
            FROM credit_transactions ct
            LEFT JOIN clinics c ON ct.clinic_id = c.id
            ORDER BY ct.created_at DESC
            LIMIT 10
        """))
        recent_transactions = [dict(row._mapping) for row in recent_transactions_result.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching recent transactions: {e}")
        recent_transactions = []
    
    return render_template('admin/credit_dashboard.html', 
                         clinics=clinics, 
                         stats=stats,
                         all_leads=all_leads,
                         lead_source_analytics=lead_source_analytics,
                         lead_status_summary=lead_status_summary,
                         recent_transactions=recent_transactions)

@admin_credit_bp.route('/admin/credits/allocate', methods=['POST'])
@login_required
def allocate_credits():
    """Allocate credits to a clinic."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            logger.error(f"CSRF validation failed: {csrf_error}")
            return jsonify({'success': False, 'message': 'Security validation failed'}), 400
        
        clinic_id = request.form.get('clinic_id', type=int)
        credits = request.form.get('credits', type=int)
        description = request.form.get('description', '')
        
        if not clinic_id or not credits or credits <= 0:
            return jsonify({'success': False, 'message': 'Invalid input data'}), 400
        
        success = AdminCreditService.allocate_credits(
            clinic_id, credits, description, current_user.id
        )
        
        if success:
            return jsonify({'success': True, 'message': f'Successfully allocated {credits} credits'})
        else:
            return jsonify({'success': False, 'message': 'Failed to allocate credits'}), 500
            
    except Exception as e:
        logger.error(f"Error in credit allocation: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@admin_credit_bp.route('/admin/credits/debit', methods=['POST'])
@login_required
def debit_credits():
    """Debit credits from a clinic for refund situations."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            logger.error(f"CSRF validation failed: {csrf_error}")
            return jsonify({'success': False, 'message': 'Security validation failed'}), 400
        
        clinic_id = request.form.get('clinic_id', type=int)
        credits = request.form.get('credits', type=int)
        description = request.form.get('description', '')
        
        if not clinic_id or not credits or credits <= 0:
            return jsonify({'success': False, 'message': 'Invalid input data'}), 400
        
        success, message = AdminCreditService.debit_credits(
            clinic_id, credits, description, current_user.id
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        logger.error(f"Error in credit debit: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@admin_credit_bp.route('/admin/credits/transfer', methods=['POST'])
@login_required
def transfer_credits():
    """Transfer credits between clinics."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        from_clinic_id = request.form.get('from_clinic_id', type=int)
        to_clinic_id = request.form.get('to_clinic_id', type=int)
        credits = request.form.get('credits', type=int)
        description = request.form.get('description', '')
        
        if not all([from_clinic_id, to_clinic_id, credits]) or credits <= 0:
            return jsonify({'success': False, 'message': 'Invalid input data'}), 400
        
        if from_clinic_id == to_clinic_id:
            return jsonify({'success': False, 'message': 'Cannot transfer to the same clinic'}), 400
        
        success, message = AdminCreditService.transfer_credits(
            from_clinic_id, to_clinic_id, credits, description, current_user.id
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        logger.error(f"Error in credit transfer: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@admin_credit_bp.route('/admin/credits/clinic/<int:clinic_id>')
@login_required
def clinic_details(clinic_id):
    """View detailed credit information for a specific clinic."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('web.index'))
    
    # Get clinic information
    clinic_result = db.session.execute(text("""
        SELECT c.*, u.username as owner_username, u.email as owner_email
        FROM clinics c
        LEFT JOIN users u ON c.owner_user_id = u.id
        WHERE c.id = :clinic_id
    """), {"clinic_id": clinic_id}).fetchone()
    
    if not clinic_result:
        flash('Clinic not found.', 'danger')
        return redirect(url_for('admin_credit.credit_dashboard'))
    
    clinic = dict(clinic_result._mapping)
    transactions = AdminCreditService.get_clinic_transaction_history(clinic_id, 100)
    
    return render_template('admin/clinic_credit_details.html', 
                         clinic=clinic, 
                         transactions=transactions)

@admin_credit_bp.route('/admin/credits/bulk-allocate', methods=['POST'])
@login_required
def bulk_allocate():
    """Bulk allocate credits to multiple clinics."""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        json_data = request.get_json() or {}
        allocations_data = json_data.get('allocations', [])
        
        if not allocations_data:
            return jsonify({'success': False, 'message': 'No allocations provided'}), 400
        
        successful, failed = AdminCreditService.bulk_allocate_credits(
            allocations_data, current_user.id
        )
        
        return jsonify({
            'success': True,
            'message': f'Bulk allocation completed: {successful} successful, {failed} failed',
            'successful': successful,
            'failed': failed
        })
        
    except Exception as e:
        logger.error(f"Error in bulk allocation: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500