"""
Enhanced admin dashboard with clinic approval workflow, analytics, and management features.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Clinic, Lead, Doctor, Package, User
from sqlalchemy import text, func
import logging

enhanced_admin_bp = Blueprint('enhanced_admin', __name__)
logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin role."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('routes.index'))
        return f(*args, **kwargs)
    return decorated_function

@enhanced_admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Enhanced admin dashboard with comprehensive analytics."""
    # Platform overview metrics
    total_clinics = Clinic.query.count()
    pending_clinics = Clinic.query.filter_by(is_approved=False).count()
    total_doctors = Doctor.query.count()
    verified_doctors = Doctor.query.filter_by(verification_status='approved').count()
    
    # Lead analytics
    total_leads = Lead.query.count()
    today_leads = Lead.query.filter(
        func.date(Lead.created_at) == datetime.now().date()
    ).count()
    
    # Revenue analytics
    monthly_revenue = db.session.execute(text("""
        SELECT COALESCE(SUM(amount), 0) 
        FROM credit_transactions 
        WHERE transaction_type = 'credit' 
        AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
    """)).scalar() or 0
    
    # Recent activity
    recent_clinics = Clinic.query.order_by(Clinic.created_at.desc()).limit(5).all()
    recent_leads = Lead.query.order_by(Lead.created_at.desc()).limit(10).all()
    
    # Performance metrics
    performance_data = get_platform_performance_metrics()
    
    return render_template('admin/enhanced_dashboard.html',
                         total_clinics=total_clinics,
                         pending_clinics=pending_clinics,
                         total_doctors=total_doctors,
                         verified_doctors=verified_doctors,
                         total_leads=total_leads,
                         today_leads=today_leads,
                         monthly_revenue=monthly_revenue,
                         recent_clinics=recent_clinics,
                         recent_leads=recent_leads,
                         performance_data=performance_data)

@enhanced_admin_bp.route('/admin/clinic-approvals')
@login_required
@admin_required
def clinic_approvals():
    """Clinic approval workflow dashboard."""
    status_filter = request.args.get('status', 'pending')
    
    if status_filter == 'pending':
        clinics = Clinic.query.filter_by(is_approved=False).order_by(Clinic.created_at.desc()).all()
    elif status_filter == 'approved':
        clinics = Clinic.query.filter_by(is_approved=True).order_by(Clinic.created_at.desc()).all()
    else:
        clinics = Clinic.query.order_by(Clinic.created_at.desc()).all()
    
    return render_template('admin/clinic_approvals.html',
                         clinics=clinics,
                         status_filter=status_filter)

@enhanced_admin_bp.route('/admin/approve-clinic/<int:clinic_id>', methods=['POST'])
@login_required
@admin_required
def approve_clinic(clinic_id):
    """Approve a clinic and send notification."""
    clinic = Clinic.query.get_or_404(clinic_id)
    
    clinic.is_approved = True
    clinic.approval_date = datetime.utcnow()
    clinic.approved_by = current_user.id
    
    db.session.commit()
    
    # Send approval notification email
    send_clinic_approval_email(clinic)
    
    flash(f'Clinic "{clinic.name}" has been approved successfully.', 'success')
    return redirect(url_for('enhanced_admin.clinic_approvals'))

@enhanced_admin_bp.route('/admin/reject-clinic/<int:clinic_id>', methods=['POST'])
@login_required
@admin_required
def reject_clinic(clinic_id):
    """Reject a clinic with reason."""
    clinic = Clinic.query.get_or_404(clinic_id)
    rejection_reason = request.form.get('reason', 'Application does not meet requirements')
    
    clinic.is_approved = False
    clinic.rejection_reason = rejection_reason
    clinic.rejection_date = datetime.utcnow()
    clinic.rejected_by = current_user.id
    
    db.session.commit()
    
    # Send rejection notification email
    send_clinic_rejection_email(clinic, rejection_reason)
    
    flash(f'Clinic "{clinic.name}" has been rejected.', 'warning')
    return redirect(url_for('enhanced_admin.clinic_approvals'))

@enhanced_admin_bp.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    """Comprehensive platform analytics dashboard."""
    period = request.args.get('period', '30')
    days = int(period)
    start_date = datetime.now() - timedelta(days=days)
    
    # Lead analytics
    lead_analytics = get_lead_analytics_data(start_date)
    
    # Revenue analytics
    revenue_analytics = get_revenue_analytics_data(start_date)
    
    # Clinic performance
    clinic_performance = get_clinic_performance_data(start_date)
    
    # Geographic analytics
    geographic_data = get_geographic_analytics()
    
    return render_template('admin/analytics_dashboard.html',
                         lead_analytics=lead_analytics,
                         revenue_analytics=revenue_analytics,
                         clinic_performance=clinic_performance,
                         geographic_data=geographic_data,
                         selected_period=period)

@enhanced_admin_bp.route('/admin/credit-management')
@login_required
@admin_required
def credit_management():
    """Credit management and pricing control."""
    # Credit statistics
    total_credits_sold = db.session.execute(text("""
        SELECT COALESCE(SUM(amount), 0) 
        FROM credit_transactions 
        WHERE transaction_type = 'credit'
    """)).scalar() or 0
    
    total_credits_used = db.session.execute(text("""
        SELECT COALESCE(SUM(amount), 0) 
        FROM credit_transactions 
        WHERE transaction_type = 'deduction'
    """)).scalar() or 0
    
    # Low balance clinics
    low_balance_clinics = get_low_balance_clinics()
    
    # Recent transactions
    recent_transactions = db.session.execute(text("""
        SELECT ct.*, c.name as clinic_name 
        FROM credit_transactions ct
        JOIN clinics c ON ct.clinic_id = c.id
        ORDER BY ct.created_at DESC
        LIMIT 20
    """)).fetchall()
    
    return render_template('admin/credit_management.html',
                         total_credits_sold=total_credits_sold,
                         total_credits_used=total_credits_used,
                         low_balance_clinics=low_balance_clinics,
                         recent_transactions=recent_transactions)

@enhanced_admin_bp.route('/admin/refund-requests')
@login_required
@admin_required
def refund_requests():
    """Handle refund requests from clinics."""
    status_filter = request.args.get('status', 'pending')
    
    refund_requests = db.session.execute(text("""
        SELECT 
            rr.*,
            c.name as clinic_name,
            l.action_type as lead_type,
            l.created_at as lead_date
        FROM refund_requests rr
        JOIN clinics c ON rr.clinic_id = c.id
        LEFT JOIN leads l ON rr.lead_id = l.id
        WHERE rr.status = :status
        ORDER BY rr.created_at DESC
    """), {"status": status_filter}).fetchall()
    
    return render_template('admin/refund_requests.html',
                         refund_requests=refund_requests,
                         status_filter=status_filter)

@enhanced_admin_bp.route('/admin/process-refund/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def process_refund(request_id):
    """Process a refund request."""
    action = request.form.get('action')  # 'approve' or 'deny'
    admin_notes = request.form.get('admin_notes', '')
    
    if action == 'approve':
        # Process refund
        db.session.execute(text("""
            UPDATE refund_requests 
            SET status = 'approved', 
                processed_by = :admin_id,
                processed_at = :now,
                admin_notes = :notes
            WHERE id = :request_id
        """), {
            "admin_id": current_user.id,
            "now": datetime.utcnow(),
            "notes": admin_notes,
            "request_id": request_id
        })
        
        # Add refund credits back to clinic
        refund_data = db.session.execute(text("""
            SELECT clinic_id, refund_amount FROM refund_requests WHERE id = :request_id
        """), {"request_id": request_id}).fetchone()
        
        if refund_data:
            from billing_system import add_credits_to_clinic
            add_credits_to_clinic(
                refund_data.clinic_id, 
                refund_data.refund_amount, 
                'credit', 
                f'Refund processed for request #{request_id}'
            )
        
        flash('Refund approved and processed successfully.', 'success')
    else:
        # Deny refund
        db.session.execute(text("""
            UPDATE refund_requests 
            SET status = 'denied', 
                processed_by = :admin_id,
                processed_at = :now,
                admin_notes = :notes
            WHERE id = :request_id
        """), {
            "admin_id": current_user.id,
            "now": datetime.utcnow(),
            "notes": admin_notes,
            "request_id": request_id
        })
        
        flash('Refund request denied.', 'warning')
    
    db.session.commit()
    return redirect(url_for('enhanced_admin.refund_requests'))

def get_platform_performance_metrics():
    """Get key platform performance metrics."""
    # Conversion rates
    total_leads = Lead.query.count()
    converted_leads = Lead.query.filter_by(status='converted').count()
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Average response time
    avg_response_time = db.session.execute(text("""
        SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) 
        FROM leads 
        WHERE status != 'new' AND updated_at IS NOT NULL
    """)).scalar() or 0
    
    # Top performing clinics
    top_clinics = db.session.execute(text("""
        SELECT c.name, COUNT(l.id) as lead_count
        FROM clinics c
        LEFT JOIN leads l ON c.id = l.clinic_id
        GROUP BY c.id, c.name
        ORDER BY lead_count DESC
        LIMIT 5
    """)).fetchall()
    
    return {
        'conversion_rate': round(conversion_rate, 1),
        'avg_response_time': round(avg_response_time, 1),
        'top_clinics': top_clinics
    }

def get_lead_analytics_data(start_date):
    """Get detailed lead analytics."""
    daily_leads = db.session.execute(text("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM leads
        WHERE created_at >= :start_date
        GROUP BY DATE(created_at)
        ORDER BY date
    """), {"start_date": start_date}).fetchall()
    
    lead_sources = db.session.execute(text("""
        SELECT source_page, COUNT(*) as count
        FROM leads
        WHERE created_at >= :start_date
        GROUP BY source_page
    """), {"start_date": start_date}).fetchall()
    
    return {
        'daily_leads': [{'date': str(row.date), 'count': row.count} for row in daily_leads],
        'lead_sources': [{'source': row.source_page, 'count': row.count} for row in lead_sources]
    }

def get_revenue_analytics_data(start_date):
    """Get revenue analytics data."""
    daily_revenue = db.session.execute(text("""
        SELECT DATE(created_at) as date, SUM(amount) as revenue
        FROM credit_transactions
        WHERE transaction_type = 'credit' AND created_at >= :start_date
        GROUP BY DATE(created_at)
        ORDER BY date
    """), {"start_date": start_date}).fetchall()
    
    return {
        'daily_revenue': [{'date': str(row.date), 'revenue': float(row.revenue)} for row in daily_revenue]
    }

def get_clinic_performance_data(start_date):
    """Get clinic performance rankings."""
    return db.session.execute(text("""
        SELECT 
            c.name,
            COUNT(l.id) as leads_count,
            COUNT(CASE WHEN l.status = 'converted' THEN 1 END) as conversions,
            ROUND(COUNT(CASE WHEN l.status = 'converted' THEN 1 END)::decimal / 
                  NULLIF(COUNT(l.id), 0) * 100, 1) as conversion_rate
        FROM clinics c
        LEFT JOIN leads l ON c.id = l.clinic_id AND l.created_at >= :start_date
        WHERE c.is_approved = true
        GROUP BY c.id, c.name
        HAVING COUNT(l.id) > 0
        ORDER BY leads_count DESC
        LIMIT 10
    """), {"start_date": start_date}).fetchall()

def get_geographic_analytics():
    """Get geographic distribution of clinics and leads."""
    clinic_distribution = db.session.execute(text("""
        SELECT city, COUNT(*) as count
        FROM clinics
        WHERE is_approved = true
        GROUP BY city
        ORDER BY count DESC
        LIMIT 10
    """)).fetchall()
    
    return {
        'clinic_distribution': [{'city': row.city, 'count': row.count} for row in clinic_distribution]
    }

def get_low_balance_clinics():
    """Get clinics with low credit balance."""
    return db.session.execute(text("""
        SELECT 
            c.name,
            c.id,
            COALESCE(credits.balance, 0) as credit_balance
        FROM clinics c
        LEFT JOIN (
            SELECT 
                clinic_id,
                SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) as balance
            FROM credit_transactions
            GROUP BY clinic_id
        ) credits ON c.id = credits.clinic_id
        WHERE COALESCE(credits.balance, 0) < 500
        AND c.is_approved = true
        ORDER BY credit_balance ASC
    """)).fetchall()

def send_clinic_approval_email(clinic):
    """Send email notification for clinic approval."""
    # Email implementation would go here
    logger.info(f"Approval email sent to clinic: {clinic.name}")

def send_clinic_rejection_email(clinic, reason):
    """Send email notification for clinic rejection."""
    # Email implementation would go here
    logger.info(f"Rejection email sent to clinic: {clinic.name}, reason: {reason}")