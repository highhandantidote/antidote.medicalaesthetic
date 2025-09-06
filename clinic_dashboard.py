"""
Comprehensive clinic dashboard for lead management and business analytics.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Clinic, Lead, CreditTransaction, ClinicConsultation, Doctor, Package
from sqlalchemy import desc, func
import logging

clinic_dashboard_bp = Blueprint('clinic_dashboard', __name__)
logger = logging.getLogger(__name__)

@clinic_dashboard_bp.route('/clinic/dashboard')
@login_required
def dashboard():
    """Main clinic dashboard with overview and quick actions."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        flash('Clinic profile not found', 'error')
        return redirect(url_for('routes.index'))
    
    # Get dashboard metrics
    metrics = get_clinic_metrics(clinic.id)
    
    # Get recent leads
    recent_leads = Lead.query.filter_by(clinic_id=clinic.id).order_by(
        desc(Lead.created_at)
    ).limit(5).all()
    
    # Get recent consultations
    recent_consultations = ClinicConsultation.query.filter_by(
        clinic_id=clinic.id
    ).order_by(desc(ClinicConsultation.created_at)).limit(5).all()
    
    return render_template('clinic/dashboard.html',
                         clinic=clinic,
                         metrics=metrics,
                         recent_leads=recent_leads,
                         recent_consultations=recent_consultations)

@clinic_dashboard_bp.route('/clinic/leads')
@login_required
def leads_management():
    """Comprehensive lead management page."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        flash('Clinic profile not found', 'error')
        return redirect(url_for('routes.index'))
    
    # Get filters from request
    status_filter = request.args.get('status', 'all')
    date_filter = request.args.get('date', 'all')
    source_filter = request.args.get('source', 'all')
    
    # Build query
    query = Lead.query.filter_by(clinic_id=clinic.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if source_filter != 'all':
        query = query.filter_by(source_page=source_filter)
    
    if date_filter == 'today':
        today = datetime.now().date()
        query = query.filter(func.date(Lead.created_at) == today)
    elif date_filter == 'week':
        week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(Lead.created_at >= week_ago)
    elif date_filter == 'month':
        month_ago = datetime.now() - timedelta(days=30)
        query = query.filter(Lead.created_at >= month_ago)
    
    # Get paginated results
    page = request.args.get('page', 1, type=int)
    leads = query.order_by(desc(Lead.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get summary statistics
    total_leads = Lead.query.filter_by(clinic_id=clinic.id).count()
    new_leads = Lead.query.filter_by(clinic_id=clinic.id, status='new').count()
    contacted_leads = Lead.query.filter_by(clinic_id=clinic.id, status='contacted').count()
    converted_leads = Lead.query.filter_by(clinic_id=clinic.id, status='converted').count()
    
    return render_template('clinic/leads_management.html',
                         clinic=clinic,
                         leads=leads,
                         total_leads=total_leads,
                         new_leads=new_leads,
                         contacted_leads=contacted_leads,
                         converted_leads=converted_leads,
                         status_filter=status_filter,
                         date_filter=date_filter,
                         source_filter=source_filter)

@clinic_dashboard_bp.route('/clinic/lead/<int:lead_id>')
@login_required
def lead_detail(lead_id):
    """Detailed view of a specific lead."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        flash('Clinic profile not found', 'error')
        return redirect(url_for('routes.index'))
    
    lead = Lead.query.filter_by(id=lead_id, clinic_id=clinic.id).first_or_404()
    
    return render_template('clinic/lead_detail.html',
                         clinic=clinic,
                         lead=lead)

@clinic_dashboard_bp.route('/clinic/update-lead-status', methods=['POST'])
@login_required
def update_lead_status():
    """Update lead status and add notes."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        return jsonify({'error': 'Clinic not found'}), 404
    
    lead_id = request.form.get('lead_id')
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    lead = Lead.query.filter_by(id=lead_id, clinic_id=clinic.id).first()
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    
    # Update lead status
    lead.status = new_status
    if notes:
        lead.notes = notes
    lead.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Lead status updated successfully'})

@clinic_dashboard_bp.route('/clinic/analytics')
@login_required
def analytics():
    """Clinic analytics and performance dashboard."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        flash('Clinic profile not found', 'error')
        return redirect(url_for('routes.index'))
    
    # Get time period from request
    period = request.args.get('period', '30')  # Default to 30 days
    days = int(period)
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Lead analytics
    daily_leads = get_daily_lead_analytics(clinic.id, start_date)
    lead_sources = get_lead_source_analytics(clinic.id, start_date)
    conversion_funnel = get_conversion_funnel(clinic.id, start_date)
    
    # Revenue analytics
    credit_usage = get_credit_usage_analytics(clinic.id, start_date)
    
    # Top performing content
    top_procedures = get_top_performing_procedures(clinic.id, start_date)
    top_doctors = get_top_performing_doctors(clinic.id, start_date)
    
    return render_template('clinic/analytics.html',
                         clinic=clinic,
                         daily_leads=daily_leads,
                         lead_sources=lead_sources,
                         conversion_funnel=conversion_funnel,
                         credit_usage=credit_usage,
                         top_procedures=top_procedures,
                         top_doctors=top_doctors,
                         selected_period=period)

@clinic_dashboard_bp.route('/clinic/packages')
@login_required
def packages_management():
    """Manage clinic packages and pricing."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        flash('Clinic profile not found', 'error')
        return redirect(url_for('routes.index'))
    
    packages = Package.query.filter_by(clinic_id=clinic.id).all()
    
    return render_template('clinic/packages_management.html',
                         clinic=clinic,
                         packages=packages)

# Package creation is now handled by enhanced_package_routes.py
# This route redirects to the enhanced package creation system
@clinic_dashboard_bp.route('/clinic/packages/add', methods=['GET', 'POST'])
@login_required
def add_package():
    """Redirect to enhanced package creation system."""
    return redirect('/clinic/packages/add')

@clinic_dashboard_bp.route('/clinic/doctors')
@login_required
def doctors_management():
    """Manage clinic doctors and their profiles."""
    clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
    if not clinic:
        flash('Clinic profile not found', 'error')
        return redirect(url_for('routes.index'))
    
    doctors = Doctor.query.filter_by(clinic_id=clinic.id).all()
    
    return render_template('clinic/doctors_management.html',
                         clinic=clinic,
                         doctors=doctors)

def get_clinic_metrics(clinic_id):
    """Get key performance metrics for clinic dashboard."""
    # Time periods
    today = datetime.now().date()
    week_ago = datetime.now() - timedelta(days=7)
    month_ago = datetime.now() - timedelta(days=30)
    
    # Lead metrics
    total_leads = Lead.query.filter_by(clinic_id=clinic_id).count()
    weekly_leads = Lead.query.filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= week_ago
    ).count()
    monthly_leads = Lead.query.filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= month_ago
    ).count()
    
    # Conversion metrics
    converted_leads = Lead.query.filter_by(
        clinic_id=clinic_id, 
        status='converted'
    ).count()
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Credit metrics
    from billing_system import get_clinic_credits
    current_credits = get_clinic_credits(clinic_id)
    
    monthly_spend = sum([
        t.credits_used for t in CreditTransaction.query.filter(
            CreditTransaction.clinic_id == clinic_id,
            CreditTransaction.transaction_type == 'debit',
            CreditTransaction.created_at >= month_ago
        ).all()
    ])
    
    # Average cost per lead
    avg_cost_per_lead = (monthly_spend / monthly_leads) if monthly_leads > 0 else 0
    
    return {
        'total_leads': total_leads,
        'weekly_leads': weekly_leads,
        'monthly_leads': monthly_leads,
        'conversion_rate': round(conversion_rate, 1),
        'current_credits': current_credits,
        'monthly_spend': monthly_spend,
        'avg_cost_per_lead': round(avg_cost_per_lead, 0)
    }

def get_daily_lead_analytics(clinic_id, start_date):
    """Get daily lead count for analytics chart."""
    leads = db.session.query(
        func.date(Lead.created_at).label('date'),
        func.count(Lead.id).label('count')
    ).filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= start_date
    ).group_by(func.date(Lead.created_at)).all()
    
    return [{'date': str(lead.date), 'count': lead.count} for lead in leads]

def get_lead_source_analytics(clinic_id, start_date):
    """Get lead source breakdown."""
    sources = db.session.query(
        Lead.source_page,
        func.count(Lead.id).label('count')
    ).filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= start_date
    ).group_by(Lead.source_page).all()
    
    return [{'source': source.source_page, 'count': source.count} for source in sources]

def get_conversion_funnel(clinic_id, start_date):
    """Get conversion funnel data."""
    total = Lead.query.filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= start_date
    ).count()
    
    contacted = Lead.query.filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= start_date,
        Lead.status.in_(['contacted', 'scheduled', 'converted'])
    ).count()
    
    converted = Lead.query.filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= start_date,
        Lead.status == 'converted'
    ).count()
    
    return {
        'total': total,
        'contacted': contacted,
        'converted': converted
    }

def get_credit_usage_analytics(clinic_id, start_date):
    """Get credit usage over time."""
    usage = db.session.query(
        func.date(CreditTransaction.created_at).label('date'),
        func.sum(CreditTransaction.credits_used).label('credits')
    ).filter(
        CreditTransaction.clinic_id == clinic_id,
        CreditTransaction.transaction_type == 'debit',
        CreditTransaction.created_at >= start_date
    ).group_by(func.date(CreditTransaction.created_at)).all()
    
    return [{'date': str(u.date), 'credits': float(u.credits)} for u in usage]

def get_top_performing_procedures(clinic_id, start_date):
    """Get procedures that generate most leads."""
    procedures = db.session.query(
        Lead.procedure_id,
        func.count(Lead.id).label('lead_count')
    ).filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= start_date,
        Lead.procedure_id.isnot(None)
    ).group_by(Lead.procedure_id).order_by(desc('lead_count')).limit(5).all()
    
    return procedures

def get_top_performing_doctors(clinic_id, start_date):
    """Get doctors that generate most leads."""
    doctors = db.session.query(
        Lead.doctor_id,
        func.count(Lead.id).label('lead_count')
    ).filter(
        Lead.clinic_id == clinic_id,
        Lead.created_at >= start_date,
        Lead.doctor_id.isnot(None)
    ).group_by(Lead.doctor_id).order_by(desc('lead_count')).limit(5).all()
    
    return doctors