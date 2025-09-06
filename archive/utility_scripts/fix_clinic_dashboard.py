"""
Fix clinic dashboard implementation and integrate with main routes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Clinic, Lead, Doctor, Package, User
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

clinic_dashboard_bp = Blueprint('clinic_dashboard', __name__, url_prefix='/clinic')

@clinic_dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Main clinic dashboard with overview and quick actions."""
    try:
        # Get clinic for current user
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            flash('No clinic found for your account. Please contact support.', 'error')
            return redirect(url_for('web.index'))
        
        # Get basic metrics using raw SQL to avoid transaction issues
        total_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads WHERE clinic_id = :clinic_id
        """), {"clinic_id": clinic.id}).scalar() or 0
        
        # Get this month's leads
        current_month_start = datetime.now().replace(day=1)
        monthly_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id 
            AND created_at >= :start_date
        """), {
            "clinic_id": clinic.id,
            "start_date": current_month_start
        }).scalar() or 0
        
        # Get current credit balance
        credit_balance = db.session.execute(text("""
            SELECT COALESCE(
                (SELECT SUM(amount) FROM credit_transactions 
                 WHERE clinic_id = :clinic_id AND transaction_type = 'credit') -
                (SELECT SUM(amount) FROM credit_transactions 
                 WHERE clinic_id = :clinic_id AND transaction_type = 'deduction'), 
                0
            ) as balance
        """), {"clinic_id": clinic.id}).scalar() or 0
        
        # Get recent leads
        recent_leads = db.session.execute(text("""
            SELECT l.*, u.name as user_name 
            FROM leads l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE l.clinic_id = :clinic_id
            ORDER BY l.created_at DESC
            LIMIT 5
        """), {"clinic_id": clinic.id}).fetchall()
        
        # Get doctor count
        doctor_count = db.session.execute(text("""
            SELECT COUNT(*) FROM doctors WHERE clinic_id = :clinic_id
        """), {"clinic_id": clinic.id}).scalar() or 0
        
        # Get package count
        package_count = db.session.execute(text("""
            SELECT COUNT(*) FROM packages WHERE clinic_id = :clinic_id AND is_active = true
        """), {"clinic_id": clinic.id}).scalar() or 0
        
        metrics = {
            'total_leads': total_leads,
            'monthly_leads': monthly_leads,
            'credit_balance': credit_balance,
            'doctor_count': doctor_count,
            'package_count': package_count,
            'conversion_rate': 15.5  # Placeholder for now
        }
        
        return render_template('clinic_dashboard.html',
                             clinic=clinic,
                             metrics=metrics,
                             recent_leads=recent_leads)
        
    except Exception as e:
        logger.error(f"Error in clinic dashboard: {e}")
        db.session.rollback()
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('web.index'))

@clinic_dashboard_bp.route('/leads')
@login_required
def leads():
    """Clinic leads management page."""
    try:
        # Get clinic for current user
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            flash('No clinic found for your account.', 'error')
            return redirect(url_for('web.index'))
        
        # Get all leads for this clinic
        leads = db.session.execute(text("""
            SELECT l.*, u.name as user_name, u.phone_number as user_phone
            FROM leads l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE l.clinic_id = :clinic_id
            ORDER BY l.created_at DESC
        """), {"clinic_id": clinic.id}).fetchall()
        
        return render_template('clinic_leads.html',
                             clinic=clinic,
                             leads=leads)
        
    except Exception as e:
        logger.error(f"Error in clinic leads: {e}")
        db.session.rollback()
        flash('Error loading leads. Please try again.', 'error')
        return redirect(url_for('clinic_dashboard.dashboard'))

@clinic_dashboard_bp.route('/billing')
@login_required
def billing():
    """Clinic billing and credit management."""
    try:
        # Get clinic for current user
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            flash('No clinic found for your account.', 'error')
            return redirect(url_for('web.index'))
        
        # Get current credit balance
        credit_balance = db.session.execute(text("""
            SELECT COALESCE(
                (SELECT SUM(amount) FROM credit_transactions 
                 WHERE clinic_id = :clinic_id AND transaction_type = 'credit') -
                (SELECT SUM(amount) FROM credit_transactions 
                 WHERE clinic_id = :clinic_id AND transaction_type = 'deduction'), 
                0
            ) as balance
        """), {"clinic_id": clinic.id}).scalar() or 0
        
        # Get recent transactions
        transactions = db.session.execute(text("""
            SELECT * FROM credit_transactions 
            WHERE clinic_id = :clinic_id
            ORDER BY created_at DESC
            LIMIT 20
        """), {"clinic_id": clinic.id}).fetchall()
        
        # Credit packages
        credit_packages = [
            {'credits': 1000, 'price': 5000, 'bonus': 0, 'popular': False},
            {'credits': 2500, 'price': 12000, 'bonus': 100, 'popular': True},
            {'credits': 5000, 'price': 22500, 'bonus': 500, 'popular': False},
            {'credits': 10000, 'price': 42000, 'bonus': 1500, 'popular': False},
        ]
        
        return render_template('clinic_billing.html',
                             clinic=clinic,
                             credit_balance=credit_balance,
                             transactions=transactions,
                             credit_packages=credit_packages)
        
    except Exception as e:
        logger.error(f"Error in clinic billing: {e}")
        db.session.rollback()
        flash('Error loading billing information. Please try again.', 'error')
        return redirect(url_for('clinic_dashboard.dashboard'))

def register_clinic_dashboard_routes(app):
    """Register clinic dashboard routes with the main app."""
    app.register_blueprint(clinic_dashboard_bp)
    logger.info("Clinic dashboard routes registered successfully")