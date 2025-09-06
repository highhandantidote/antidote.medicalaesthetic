#!/usr/bin/env python3
"""
Admin Transaction History and Audit Trail System
Provides comprehensive tracking of all admin actions, credit allocations, and system changes.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import text, and_, or_, desc, asc
from datetime import datetime, timedelta
import logging
from app import db

logger = logging.getLogger(__name__)

# Create blueprint
admin_history_bp = Blueprint('admin_history', __name__, template_folder='templates')

def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('web.index'))
        return f(*args, **kwargs)
    return decorated_function

class AdminHistoryService:
    """Service class for admin transaction history and audit trail functionality."""
    
    @staticmethod
    def get_credit_allocation_history(clinic_id=None, start_date=None, end_date=None, limit=100):
        """Get comprehensive credit allocation history with admin details."""
        query = """
            SELECT 
                ct.id,
                ct.clinic_id,
                c.name as clinic_name,
                ct.amount,
                ct.transaction_type,
                ct.description,
                ct.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata' as created_at_ist,
                ct.reference_id,
                u_admin.username as admin_user,
                u_admin.email as admin_email,
                ct.transaction_metadata,
                ct.status,
                ct.monetary_value
            FROM credit_transactions ct
            JOIN clinics c ON ct.clinic_id = c.id
            LEFT JOIN users u_admin ON ct.created_by = u_admin.id
            WHERE 1=1
        """
        
        params = {}
        
        if clinic_id:
            query += " AND ct.clinic_id = :clinic_id"
            params['clinic_id'] = clinic_id
            
        if start_date:
            query += " AND DATE(ct.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') >= :start_date"
            params['start_date'] = start_date
            
        if end_date:
            query += " AND DATE(ct.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata') <= :end_date"
            params['end_date'] = end_date
            
        query += " ORDER BY ct.created_at DESC LIMIT :limit"
        params['limit'] = limit
        
        result = db.session.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in result]
    
    @staticmethod
    def get_lead_analytics_detailed(clinic_id=None, start_date=None, end_date=None):
        """Get detailed lead analytics with conversion tracking."""
        query = """
            SELECT 
                l.id,
                l.clinic_id,
                c.name as clinic_name,
                l.patient_name,
                l.mobile_number,
                l.procedure_name,
                l.status,
                l.credit_cost,
                l.source_page,
                l.created_at,
                l.contacted_at,
                l.converted_at,
                l.conversion_value,
                l.quality_score,
                l.is_qualified,
                CASE 
                    WHEN l.converted_at IS NOT NULL THEN 'converted'
                    WHEN l.contacted_at IS NOT NULL THEN 'contacted'
                    ELSE 'pending'
                END as lead_stage,
                CASE 
                    WHEN l.converted_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (l.converted_at - l.created_at))/3600
                    ELSE NULL
                END as hours_to_conversion
            FROM leads l
            JOIN clinics c ON l.clinic_id = c.id
            WHERE 1=1
        """
        
        params = {}
        
        if clinic_id:
            query += " AND l.clinic_id = :clinic_id"
            params['clinic_id'] = clinic_id
            
        if start_date:
            query += " AND l.created_at >= :start_date"
            params['start_date'] = start_date
            
        if end_date:
            query += " AND l.created_at <= :end_date"
            params['end_date'] = end_date
            
        query += " ORDER BY l.created_at DESC"
        
        result = db.session.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in result]
    
    @staticmethod
    def get_clinic_performance_metrics(clinic_id=None, days=30):
        """Get comprehensive clinic performance metrics."""
        query = """
            SELECT 
                c.id,
                c.name,
                c.credit_balance,
                
                -- Lead metrics
                COUNT(l.id) as total_leads,
                COUNT(CASE WHEN l.contacted_at IS NOT NULL THEN 1 END) as contacted_leads,
                COUNT(CASE WHEN l.converted_at IS NOT NULL THEN 1 END) as converted_leads,
                
                -- Financial metrics  
                SUM(l.credit_cost) as total_credits_spent,
                SUM(l.conversion_value) as total_revenue,
                
                -- Performance ratios
                CASE 
                    WHEN COUNT(l.id) > 0 THEN 
                        ROUND(COUNT(CASE WHEN l.contacted_at IS NOT NULL THEN 1 END) * 100.0 / COUNT(l.id), 2)
                    ELSE 0 
                END as contact_rate,
                
                CASE 
                    WHEN COUNT(l.id) > 0 THEN 
                        ROUND(COUNT(CASE WHEN l.converted_at IS NOT NULL THEN 1 END) * 100.0 / COUNT(l.id), 2)
                    ELSE 0 
                END as conversion_rate,
                
                -- ROI calculation
                CASE 
                    WHEN SUM(l.credit_cost) > 0 THEN 
                        ROUND((SUM(l.conversion_value) - SUM(l.credit_cost)) * 100.0 / SUM(l.credit_cost), 2)
                    ELSE 0 
                END as roi_percentage,
                
                -- Quality metrics
                AVG(l.quality_score) as avg_quality_score,
                AVG(CASE 
                    WHEN l.converted_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (l.converted_at - l.created_at))/3600
                    ELSE NULL
                END) as avg_hours_to_conversion
                
            FROM clinics c
            LEFT JOIN leads l ON c.id = l.clinic_id 
                AND l.created_at >= NOW() - INTERVAL '%s days'
            WHERE c.is_approved = true
        """ % days
        
        params = {}
        
        if clinic_id:
            query += " AND c.id = :clinic_id"
            params['clinic_id'] = clinic_id
            
        query += " GROUP BY c.id, c.name, c.credit_balance ORDER BY total_leads DESC"
        
        result = db.session.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in result]
    
    @staticmethod
    def get_dispute_analytics():
        """Get comprehensive dispute analytics."""
        query = """
            SELECT 
                d.id,
                d.lead_id,
                l.patient_name,
                l.procedure_name,
                c.name as clinic_name,
                d.reason,
                d.status,
                d.description,
                d.created_at,
                d.resolved_at,
                d.resolution_notes,
                d.refund_amount,
                u_admin.username as resolved_by_admin,
                CASE 
                    WHEN d.resolved_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (d.resolved_at - d.created_at))/3600
                    ELSE NULL
                END as hours_to_resolution
            FROM lead_disputes d
            JOIN leads l ON d.lead_id = l.id
            JOIN clinics c ON l.clinic_id = c.id
            LEFT JOIN users u_admin ON d.resolved_by = u_admin.id
            ORDER BY d.created_at DESC
        """
        
        result = db.session.execute(text(query)).fetchall()
        return [dict(row._mapping) for row in result]
    
    @staticmethod
    def log_admin_action(action_type, description, target_id=None, metadata=None):
        """Log admin actions for audit trail."""
        try:
            log_entry = {
                'admin_user_id': current_user.id,
                'action_type': action_type,
                'description': description,
                'target_id': target_id,
                'metadata': metadata,
                'created_at': datetime.utcnow(),
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.headers.get('User-Agent') if request else None
            }
            
            # Insert into admin_audit_log table (create if doesn't exist)
            db.session.execute(text("""
                INSERT INTO admin_audit_log 
                (admin_user_id, action_type, description, target_id, metadata, created_at, ip_address, user_agent)
                VALUES 
                (:admin_user_id, :action_type, :description, :target_id, :metadata, :created_at, :ip_address, :user_agent)
            """), log_entry)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {str(e)}")

@admin_history_bp.route('/admin/transaction-history')
@login_required
@admin_required
def transaction_history():
    """Admin transaction history dashboard."""
    
    # Get filter parameters
    clinic_id = request.args.get('clinic_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 100, type=int)
    
    # Parse dates if provided
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid start date format', 'warning')
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid end date format', 'warning')
    
    # Get transaction history
    credit_history = AdminHistoryService.get_credit_allocation_history(
        clinic_id=clinic_id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        limit=limit
    )
    
    # Get all clinics for filter dropdown
    clinics = db.session.execute(text("""
        SELECT id, name FROM clinics WHERE is_approved = true ORDER BY name
    """)).fetchall()
    
    # Calculate summary statistics
    total_allocated = sum(t['amount'] for t in credit_history if t['amount'] > 0)
    total_adjustments = sum(abs(t['amount']) for t in credit_history if t['amount'] < 0)
    unique_clinics = len(set(t['clinic_id'] for t in credit_history))
    
    stats = {
        'total_allocated': total_allocated,
        'total_adjustments': total_adjustments,
        'unique_clinics': unique_clinics,
        'transaction_count': len(credit_history)
    }
    
    return render_template('admin/transaction_history.html',
                          credit_history=credit_history,
                          clinics=clinics,
                          stats=stats,
                          selected_clinic=clinic_id,
                          start_date=start_date,
                          end_date=end_date,
                          limit=limit)

# Lead analytics route moved to main web blueprint to avoid conflicts

@admin_history_bp.route('/admin/clinic-performance')
@login_required
@admin_required
def clinic_performance():
    """Clinic performance comparison dashboard."""
    
    days = request.args.get('days', 30, type=int)
    sort_by = request.args.get('sort', 'total_leads')
    order = request.args.get('order', 'desc')
    
    # Get clinic performance data
    clinic_metrics = AdminHistoryService.get_clinic_performance_metrics(days=days)
    
    # Sort results
    reverse_sort = (order == 'desc')
    if sort_by in ['total_leads', 'contacted_leads', 'converted_leads', 'total_credits_spent', 
                   'total_revenue', 'contact_rate', 'conversion_rate', 'roi_percentage']:
        clinic_metrics.sort(key=lambda x: x[sort_by] or 0, reverse=reverse_sort)
    
    # Calculate platform totals
    platform_totals = {
        'total_clinics': len(clinic_metrics),
        'total_leads': sum(c['total_leads'] or 0 for c in clinic_metrics),
        'total_contacted': sum(c['contacted_leads'] or 0 for c in clinic_metrics),
        'total_converted': sum(c['converted_leads'] or 0 for c in clinic_metrics),
        'total_credits': sum(c['total_credits_spent'] or 0 for c in clinic_metrics),
        'total_revenue': sum(c['total_revenue'] or 0 for c in clinic_metrics)
    }
    
    # Add platform averages
    if platform_totals['total_clinics'] > 0:
        platform_totals['avg_contact_rate'] = round(
            platform_totals['total_contacted'] * 100 / platform_totals['total_leads'], 2
        ) if platform_totals['total_leads'] > 0 else 0
        
        platform_totals['avg_conversion_rate'] = round(
            platform_totals['total_converted'] * 100 / platform_totals['total_leads'], 2
        ) if platform_totals['total_leads'] > 0 else 0
        
        platform_totals['platform_roi'] = round(
            (platform_totals['total_revenue'] - platform_totals['total_credits']) * 100 / platform_totals['total_credits'], 2
        ) if platform_totals['total_credits'] > 0 else 0
    
    return render_template('admin/clinic_performance.html',
                          clinic_metrics=clinic_metrics,
                          platform_totals=platform_totals,
                          days=days,
                          sort_by=sort_by,
                          order=order)

# Create audit log table if it doesn't exist
def create_audit_log_table():
    """Create admin audit log table for tracking admin actions."""
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_audit_log (
                id SERIAL PRIMARY KEY,
                admin_user_id INTEGER REFERENCES users(id),
                action_type VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                target_id INTEGER,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                ip_address INET,
                user_agent TEXT
            )
        """))
        
        # Create indexes for better performance
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_admin_user ON admin_audit_log(admin_user_id);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON admin_audit_log(created_at);
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_action_type ON admin_audit_log(action_type);
        """))
        
        db.session.commit()
        logger.info("Admin audit log table created successfully")
        
    except Exception as e:
        logger.error(f"Error creating audit log table: {str(e)}")
        db.session.rollback()

# Initialize audit log table when module loads
try:
    create_audit_log_table()
except Exception as e:
    logger.warning(f"Could not create audit log table during module load: {str(e)}")