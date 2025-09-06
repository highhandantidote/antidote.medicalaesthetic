"""
Fix clinic dashboard routing by adding a direct route to the main routes.py
"""

from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import text
from app import db
import logging

logger = logging.getLogger(__name__)

def get_clinic_for_user(user_id):
    """Get clinic owned by the current user"""
    try:
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics 
            WHERE owner_user_id = :user_id 
            LIMIT 1
        """), {'user_id': user_id}).fetchone()
        
        return dict(clinic_result._mapping) if clinic_result else None
    except Exception as e:
        logger.error(f"Error getting clinic for user {user_id}: {e}")
        return None

def get_dashboard_metrics(clinic_id):
    """Get comprehensive dashboard metrics"""
    try:
        # Total leads
        total_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads WHERE clinic_id = :clinic_id
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Pending leads
        pending_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id AND status = 'new'
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Monthly leads
        monthly_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE clinic_id = :clinic_id 
            AND created_at >= date_trunc('month', CURRENT_DATE)
        """), {'clinic_id': clinic_id}).scalar() or 0
        
        # Credit balance (if billing system exists)
        try:
            credit_balance = db.session.execute(text("""
                SELECT COALESCE(
                    (SELECT SUM(amount) FROM credit_transactions 
                     WHERE clinic_id = :clinic_id AND transaction_type = 'credit') -
                    (SELECT ABS(SUM(amount)) FROM credit_transactions 
                     WHERE clinic_id = :clinic_id AND transaction_type = 'deduction'),
                    0
                ) as balance
            """), {'clinic_id': clinic_id}).scalar() or 0
        except:
            credit_balance = 0
        
        return {
            'total_leads': total_leads,
            'pending_leads': pending_leads,
            'monthly_leads': monthly_leads,
            'credit_balance': credit_balance,
            'package_count': 0,
            'doctor_count': 0
        }
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return {
            'total_leads': 0,
            'pending_leads': 0,
            'monthly_leads': 0,
            'credit_balance': 0,
            'package_count': 0,
            'doctor_count': 0
        }

def clinic_dashboard_view():
    """Direct clinic dashboard view function"""
    try:
        clinic = get_clinic_for_user(current_user.id)
        
        if not clinic:
            flash('No clinic profile found. Please contact support to set up your clinic profile.', 'warning')
            return redirect(url_for('web.index'))
        
        # Get dashboard metrics
        metrics = get_dashboard_metrics(clinic['id'])
        
        # Get recent leads
        try:
            recent_leads_result = db.session.execute(text("""
                SELECT l.*, u.name as user_name, u.phone_number as user_phone
                FROM leads l
                LEFT JOIN users u ON l.user_id = u.id
                WHERE l.clinic_id = :clinic_id
                ORDER BY l.created_at DESC
                LIMIT 5
            """), {'clinic_id': clinic['id']}).fetchall()
            
            recent_leads = [dict(row._mapping) for row in recent_leads_result]
        except:
            recent_leads = []
        
        # Get clinic packages
        try:
            packages_result = db.session.execute(text("""
                SELECT * FROM packages 
                WHERE clinic_id = :clinic_id AND is_active = true
                ORDER BY created_at DESC
                LIMIT 10
            """), {'clinic_id': clinic['id']}).fetchall()
            
            packages = [dict(row._mapping) for row in packages_result]
        except:
            packages = []
        
        # Get clinic doctors
        try:
            doctors_result = db.session.execute(text("""
                SELECT d.*, cd.role, cd.is_primary 
                FROM doctors d
                JOIN clinic_doctors cd ON d.id = cd.doctor_id
                WHERE cd.clinic_id = :clinic_id AND cd.is_active = true
                ORDER BY cd.is_primary DESC
                LIMIT 10
            """), {'clinic_id': clinic['id']}).fetchall()
            
            doctors = [dict(row._mapping) for row in doctors_result]
        except:
            doctors = []
        
        # Get all categories
        try:
            categories_result = db.session.execute(text("""
                SELECT id, name, category_type FROM categories ORDER BY name
            """)).fetchall()
            
            categories = [dict(row._mapping) for row in categories_result]
        except:
            categories = []
        
        # Get all procedures
        try:
            procedures_result = db.session.execute(text("""
                SELECT id, procedure_name, min_cost, max_cost FROM procedures 
                ORDER BY procedure_name LIMIT 100
            """)).fetchall()
            
            procedures = [dict(row._mapping) for row in procedures_result]
        except:
            procedures = []
        
        return render_template('clinic/unified_dashboard.html',
                             clinic=clinic,
                             metrics=metrics,
                             recent_leads=recent_leads,
                             packages=packages,
                             doctors=doctors,
                             categories=categories,
                             procedures=procedures)
                             
    except Exception as e:
        logger.error(f"Error loading clinic dashboard: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('web.index'))