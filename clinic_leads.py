"""
Clinic Lead Tracking and Billing System
Core Gangnam Unni-style marketplace features for clinic management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Clinic, ClinicConsultation, ClinicLead, ClinicBilling, User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

clinic_leads_bp = Blueprint('clinic_leads', __name__, url_prefix='/clinic-leads')

@clinic_leads_bp.route('/dashboard/<int:clinic_id>')
@login_required
def lead_dashboard(clinic_id):
    """Clinic lead management dashboard - core Gangnam Unni feature"""
    clinic = db.session.query(Clinic).get_or_404(clinic_id)
    
    # Get lead statistics for the current month
    current_month = datetime.now().replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    # Lead metrics
    total_leads = db.session.query(ClinicConsultation).filter_by(clinic_id=clinic_id).count()
    monthly_leads = db.session.query(ClinicConsultation).filter(
        ClinicConsultation.clinic_id == clinic_id,
        ClinicConsultation.created_at >= current_month,
        ClinicConsultation.created_at < next_month
    ).count()
    
    # Conversion rates
    contacted_leads = db.session.query(ClinicConsultation).filter(
        ClinicConsultation.clinic_id == clinic_id,
        ClinicConsultation.status.in_(['contacted', 'scheduled', 'completed'])
    ).count()
    
    conversion_rate = (contacted_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Recent leads
    recent_leads = db.session.query(ClinicConsultation).filter_by(
        clinic_id=clinic_id
    ).order_by(ClinicConsultation.created_at.desc()).limit(10).all()
    
    return render_template('clinic_leads_dashboard.html',
                         clinic=clinic,
                         total_leads=total_leads,
                         monthly_leads=monthly_leads,
                         conversion_rate=conversion_rate,
                         recent_leads=recent_leads)

@clinic_leads_bp.route('/api/leads/<int:clinic_id>')
@login_required
def get_leads_api(clinic_id):
    """API endpoint for lead data - for real-time updates"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = db.session.query(ClinicConsultation).filter_by(clinic_id=clinic_id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    leads = query.order_by(ClinicConsultation.created_at.desc()).offset(
        (page - 1) * 20
    ).limit(20).all()
    
    leads_data = []
    for lead in leads:
        leads_data.append({
            'id': lead.id,
            'patient_name': lead.patient_name,
            'patient_phone': lead.patient_phone,
            'procedure_interest': lead.procedure_interest,
            'status': lead.status,
            'source': lead.source,
            'created_at': lead.created_at.strftime('%Y-%m-%d %H:%M'),
            'message': lead.message[:100] + '...' if len(lead.message) > 100 else lead.message
        })
    
    return jsonify({
        'leads': leads_data,
        'total': query.count(),
        'page': page
    })

@clinic_leads_bp.route('/update-status', methods=['POST'])
@login_required
def update_lead_status():
    """Update lead status - key conversion tracking feature"""
    lead_id = request.form.get('lead_id')
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    lead = db.session.query(ClinicConsultation).get_or_404(lead_id)
    
    # Update status
    lead.status = new_status
    lead.updated_at = datetime.utcnow()
    
    # Track status change for billing
    if new_status == 'contacted' and lead.status != 'contacted':
        # Create billing entry for contacted lead
        billing = ClinicBilling(
            clinic_id=lead.clinic_id,
            lead_id=lead.id,
            billing_type='lead_contact',
            amount=50.00,  # Base contact fee
            status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(billing)
    
    elif new_status == 'completed':
        # Create billing entry for successful conversion
        billing = ClinicBilling(
            clinic_id=lead.clinic_id,
            lead_id=lead.id,
            billing_type='conversion',
            amount=500.00,  # Conversion fee
            status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(billing)
    
    try:
        db.session.commit()
        logger.info(f"Lead {lead_id} status updated to {new_status}")
        return jsonify({'success': True, 'message': 'Lead status updated successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating lead status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@clinic_leads_bp.route('/billing/<int:clinic_id>')
@login_required
def billing_dashboard(clinic_id):
    """Clinic billing dashboard - Gangnam Unni pricing model"""
    clinic = db.session.query(Clinic).get_or_404(clinic_id)
    
    # Current month billing
    current_month = datetime.now().replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    monthly_billing = db.session.query(ClinicBilling).filter(
        ClinicBilling.clinic_id == clinic_id,
        ClinicBilling.created_at >= current_month,
        ClinicBilling.created_at < next_month
    ).all()
    
    # Calculate totals
    total_amount = sum(bill.amount for bill in monthly_billing)
    paid_amount = sum(bill.amount for bill in monthly_billing if bill.status == 'paid')
    pending_amount = total_amount - paid_amount
    
    # Lead conversion stats
    total_leads = len([b for b in monthly_billing if b.billing_type == 'lead_contact'])
    conversions = len([b for b in monthly_billing if b.billing_type == 'conversion'])
    conversion_rate = (conversions / total_leads * 100) if total_leads > 0 else 0
    
    return render_template('clinic_billing_dashboard.html',
                         clinic=clinic,
                         monthly_billing=monthly_billing,
                         total_amount=total_amount,
                         paid_amount=paid_amount,
                         pending_amount=pending_amount,
                         total_leads=total_leads,
                         conversions=conversions,
                         conversion_rate=conversion_rate)

@clinic_leads_bp.route('/analytics/<int:clinic_id>')
@login_required
def analytics_dashboard(clinic_id):
    """Advanced analytics dashboard for clinic performance"""
    clinic = db.session.query(Clinic).get_or_404(clinic_id)
    
    # Get last 6 months of data
    months_data = []
    for i in range(6):
        month_start = (datetime.now().replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        month_leads = db.session.query(ClinicConsultation).filter(
            ClinicConsultation.clinic_id == clinic_id,
            ClinicConsultation.created_at >= month_start,
            ClinicConsultation.created_at < month_end
        ).count()
        
        month_conversions = db.session.query(ClinicConsultation).filter(
            ClinicConsultation.clinic_id == clinic_id,
            ClinicConsultation.status == 'completed',
            ClinicConsultation.created_at >= month_start,
            ClinicConsultation.created_at < month_end
        ).count()
        
        months_data.append({
            'month': month_start.strftime('%B %Y'),
            'leads': month_leads,
            'conversions': month_conversions,
            'conversion_rate': (month_conversions / month_leads * 100) if month_leads > 0 else 0
        })
    
    # Popular procedures
    procedure_stats = db.session.query(
        ClinicConsultation.procedure_interest,
        db.func.count(ClinicConsultation.id).label('count')
    ).filter_by(clinic_id=clinic_id).group_by(
        ClinicConsultation.procedure_interest
    ).order_by(db.desc('count')).limit(10).all()
    
    # Lead sources
    source_stats = db.session.query(
        ClinicConsultation.source,
        db.func.count(ClinicConsultation.id).label('count')
    ).filter_by(clinic_id=clinic_id).group_by(
        ClinicConsultation.source
    ).order_by(db.desc('count')).all()
    
    return render_template('clinic_analytics_dashboard.html',
                         clinic=clinic,
                         months_data=months_data,
                         procedure_stats=procedure_stats,
                         source_stats=source_stats)

@clinic_leads_bp.route('/export-leads/<int:clinic_id>')
@login_required
def export_leads(clinic_id):
    """Export leads data for clinic management"""
    clinic = db.session.query(Clinic).get_or_404(clinic_id)
    
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = db.session.query(ClinicConsultation).filter_by(clinic_id=clinic_id)
    
    if start_date:
        query = query.filter(ClinicConsultation.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(ClinicConsultation.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    leads = query.order_by(ClinicConsultation.created_at.desc()).all()
    
    # Generate CSV data
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Date', 'Patient Name', 'Phone', 'Email', 'Procedure', 'Status', 'Source', 'Message'])
    
    # Data rows
    for lead in leads:
        writer.writerow([
            lead.created_at.strftime('%Y-%m-%d %H:%M'),
            lead.patient_name,
            lead.patient_phone,
            lead.patient_email or '',
            lead.procedure_interest or '',
            lead.status,
            lead.source,
            lead.message or ''
        ])
    
    output.seek(0)
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={clinic.name}_leads_{datetime.now().strftime("%Y%m%d")}.csv'}
    )