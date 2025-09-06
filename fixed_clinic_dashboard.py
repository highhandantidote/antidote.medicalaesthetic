"""
Fixed Clinic Dashboard Implementation
Resolves authentication issues and provides complete dashboard functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Clinic, Lead, CreditTransaction, Package, User
from sqlalchemy import text, desc
import logging

logger = logging.getLogger(__name__)

# Create dedicated dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/clinic')

@dashboard_bp.route('/dashboard')
@login_required
def clinic_dashboard():
    """Comprehensive clinic dashboard with real data integration."""
    try:
        # Get clinic for current user with proper authentication
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE owner_user_id = :user_id 
            LIMIT 1
        """), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic profile found. Please create your clinic profile first.', 'warning')
            return redirect(url_for('web.index'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get comprehensive dashboard metrics
        metrics = get_dashboard_metrics(clinic['id'])
        
        # Get recent leads with proper joins
        recent_leads = get_recent_leads(clinic['id'])
        
        # Get recent credit transactions
        recent_transactions = get_recent_transactions(clinic['id'])
        
        # Get packages for this clinic
        packages = get_clinic_packages(clinic['id'])
        
        return render_template('clinic/dashboard.html',
                             clinic=clinic,
                             total_leads=metrics['total_leads'],
                             pending_leads=metrics['pending_leads'],
                             this_month_leads=metrics['monthly_leads'],
                             monthly_spending=metrics['monthly_spending'],
                             recent_leads=recent_leads,
                             recent_transactions=recent_transactions,
                             packages=packages)
                             
    except Exception as e:
        logger.error(f"Error loading clinic dashboard: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('web.index'))

def get_dashboard_metrics(clinic_id):
    """Get comprehensive dashboard metrics for a clinic."""
    try:
        # Total leads count
        total_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads WHERE clinic_id = :clinic_id
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Pending leads count
        pending_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id AND status = 'pending'
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # This month leads
        monthly_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id 
            AND created_at >= date_trunc('month', CURRENT_DATE)
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Monthly spending
        monthly_spending = db.session.execute(text("""
            SELECT COALESCE(ABS(SUM(amount)), 0) 
            FROM credit_transactions 
            WHERE clinic_id = :clinic_id 
            AND transaction_type = 'deduction'
            AND created_at >= date_trunc('month', CURRENT_DATE)
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        return {
            'total_leads': total_leads,
            'pending_leads': pending_leads,
            'monthly_leads': monthly_leads,
            'monthly_spending': monthly_spending
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return {
            'total_leads': 0,
            'pending_leads': 0,
            'monthly_leads': 0,
            'monthly_spending': 0
        }

def get_recent_leads(clinic_id, limit=10):
    """Get recent leads for a clinic with user information."""
    try:
        leads_result = db.session.execute(text("""
            SELECT l.*, u.name as user_name, u.email as user_email
            FROM leads l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE l.clinic_id = :clinic_id
            ORDER BY l.created_at DESC
            LIMIT :limit
        """), {'clinic_id': clinic_id, 'limit': limit}).fetchall()
        
        return [dict(row._mapping) for row in leads_result]
        
    except Exception as e:
        logger.error(f"Error getting recent leads: {e}")
        return []

def get_recent_transactions(clinic_id, limit=10):
    """Get recent credit transactions for a clinic."""
    try:
        transactions_result = db.session.execute(text("""
            SELECT * FROM credit_transactions 
            WHERE clinic_id = :clinic_id
            ORDER BY created_at DESC
            LIMIT :limit
        """), {'clinic_id': clinic_id, 'limit': limit}).fetchall()
        
        return [dict(row._mapping) for row in transactions_result]
        
    except Exception as e:
        logger.error(f"Error getting recent transactions: {e}")
        return []

def get_clinic_packages(clinic_id):
    """Get all packages for a clinic."""
    try:
        packages_result = db.session.execute(text("""
            SELECT * FROM packages 
            WHERE clinic_id = :clinic_id AND is_active = true
            ORDER BY created_at DESC
        """), {'clinic_id': clinic_id}).fetchall()
        
        return [dict(row._mapping) for row in packages_result]
        
    except Exception as e:
        logger.error(f"Error getting clinic packages: {e}")
        return []

@dashboard_bp.route('/profile/edit')
@login_required
def edit_profile():
    """Edit clinic profile page."""
    try:
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE owner_user_id = :user_id 
            LIMIT 1
        """), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic profile found.', 'error')
            return redirect(url_for('web.index'))
        
        clinic = dict(clinic_result._mapping)
        
        return render_template('clinic/edit_profile.html', clinic=clinic)
        
    except Exception as e:
        logger.error(f"Error loading edit profile: {e}")
        flash('Error loading profile editor.', 'error')
        return redirect(url_for('dashboard.clinic_dashboard'))

@dashboard_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update clinic profile information."""
    try:
        # Verify clinic ownership
        clinic_result = db.session.execute(text("""
            SELECT id FROM clinics 
            WHERE owner_user_id = :user_id 
            LIMIT 1
        """), {'user_id': current_user.id}).fetchone()
        
        if not clinic_result:
            flash('Unauthorized access.', 'error')
            return redirect(url_for('web.index'))
        
        clinic_id = clinic_result[0]
        
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')
        specialties = request.form.get('specialties')
        working_hours = request.form.get('working_hours')
        services_offered = request.form.get('services_offered')
        highlights = request.form.get('highlights')
        
        # Update clinic profile
        db.session.execute(text("""
            UPDATE clinics SET 
                name = :name,
                description = :description,
                specialties = :specialties,
                working_hours = :working_hours,
                services_offered = :services_offered,
                highlights = :highlights,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :clinic_id
        """), {
            'clinic_id': clinic_id,
            'name': name,
            'description': description,
            'specialties': specialties,
            'working_hours': working_hours,
            'services_offered': services_offered,
            'highlights': highlights
        })
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard.clinic_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating profile: {e}")
        flash('Error updating profile. Please try again.', 'error')
        return redirect(url_for('dashboard.edit_profile'))

@dashboard_bp.route('/leads/<int:lead_id>/status', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    """Update lead status with proper authorization."""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'contacted', 'completed', 'cancelled']:
            return jsonify({'success': False, 'message': 'Invalid status'})
        
        # Verify lead belongs to current user's clinic
        lead_result = db.session.execute(text("""
            SELECT l.id FROM leads l
            JOIN clinics c ON l.clinic_id = c.id
            WHERE l.id = :lead_id AND c.owner_user_id = :user_id
        """), {'lead_id': lead_id, 'user_id': current_user.id}).fetchone()
        
        if not lead_result:
            return jsonify({'success': False, 'message': 'Unauthorized access'})
        
        # Update lead status
        db.session.execute(text("""
            UPDATE leads SET 
                status = :status,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :lead_id
        """), {'lead_id': lead_id, 'status': new_status})
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lead status updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating lead status: {e}")
        return jsonify({'success': False, 'message': 'Error updating lead status'})

def register_dashboard_routes(app):
    """Register dashboard routes with the main app."""
    app.register_blueprint(dashboard_bp)
    logger.info("Fixed clinic dashboard routes registered successfully")