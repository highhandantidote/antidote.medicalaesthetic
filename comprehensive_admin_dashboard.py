"""
Comprehensive Admin Dashboard for Lead Management
Shows all CTA submissions and lead conversions from all sources
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import text, func
from datetime import datetime, timedelta
import json
import logging
from app import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
comprehensive_admin_bp = Blueprint('comprehensive_admin', __name__, url_prefix='/admin/comprehensive')

@comprehensive_admin_bp.route('/leads')
@login_required
def detailed_leads():
    """Detailed lead management with full contact information."""
    try:
        # Get filters
        days = request.args.get('days', 30)
        if isinstance(days, str):
            days = int(days) if days.isdigit() else 30
        
        status_filter = request.args.get('status', '')
        source_filter = request.args.get('source', '')
        min_score = request.args.get('min_score', '')
        page = request.args.get('page', 1, type=int)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Build query conditions
        where_conditions = ["created_at >= :start_date", "created_at <= :end_date"]
        params = {'start_date': start_date, 'end_date': end_date}
        
        if status_filter:
            where_conditions.append("status = :status")
            params['status'] = status_filter
            
        if source_filter:
            where_conditions.append("source = :source")
            params['source'] = source_filter
            
        if min_score:
            where_conditions.append("COALESCE(lead_score, 0) >= :min_score")
            params['min_score'] = int(min_score)
        
        where_clause = " AND ".join(where_conditions)
        
        # Get total count for pagination
        total_count = db.session.execute(text(f"""
            SELECT COUNT(*) FROM leads WHERE {where_clause}
        """), params).scalar()
        
        # Calculate pagination
        per_page = 20
        total_pages = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # Get leads with pagination
        leads_result = db.session.execute(text(f"""
            SELECT * FROM leads 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """), {**params, 'limit': per_page, 'offset': offset}).fetchall()
        
        leads = [dict(row._mapping) for row in leads_result]
        
        # Get summary statistics
        stats = db.session.execute(text(f"""
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN status = 'new' THEN 1 END) as new_leads,
                COUNT(CASE WHEN status = 'contacted' THEN 1 END) as contacted_leads,
                COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted_leads
            FROM leads WHERE {where_clause}
        """), params).fetchone()
        
        stats_data = dict(stats._mapping) if stats else {
            'total_leads': 0, 'new_leads': 0, 'contacted_leads': 0, 'converted_leads': 0
        }
        
        # Get available sources for filter
        sources_result = db.session.execute(text("""
            SELECT DISTINCT source FROM leads 
            WHERE source IS NOT NULL AND source != ''
            ORDER BY source
        """)).fetchall()
        
        available_sources = [row[0] for row in sources_result]
        
        # Add default sources if none exist
        if not available_sources:
            available_sources = [
                'Doctor Detail Page',
                'Procedure Detail Page', 
                'AI Recommendation Form',
                'Face Analysis Form',
                'Cost Calculator',
                'Website Contact Form',
                'Search Results Page',
                'Homepage Banner',
                'Google Ads Landing',
                'Social Media Link'
            ]
        
        return render_template('admin/detailed_leads_table.html',
                             leads=leads,
                             total_leads=stats_data['total_leads'],
                             new_leads=stats_data['new_leads'],
                             contacted_leads=stats_data['contacted_leads'],
                             converted_leads=stats_data['converted_leads'],
                             available_sources=available_sources,
                             days=days,
                             status_filter=status_filter,
                             source_filter=source_filter,
                             min_score=int(min_score) if min_score else '',
                             current_page=page,
                             total_pages=total_pages)
    
    except Exception as e:
        logger.error(f"Error loading detailed leads: {e}")
        flash('Error loading lead details', 'danger')
        return redirect(url_for('comprehensive_admin.comprehensive_dashboard'))

@comprehensive_admin_bp.route('/dashboard')
@login_required
def comprehensive_dashboard():
    """Comprehensive admin dashboard showing all lead sources and interactions."""
    try:
        # Get date range filters
        days = request.args.get('days', 30, type=int)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get basic analytics using existing data
        analytics = get_basic_analytics(start_date, end_date)
        
        # Get simplified data
        interaction_breakdown = get_lead_source_breakdown(start_date, end_date)
        conversion_funnel = get_simple_funnel(start_date, end_date)
        recent_leads = get_recent_leads(limit=10)
        source_performance = get_lead_sources(start_date, end_date)
        
        return render_template('admin/comprehensive_dashboard.html',
                             analytics=analytics,
                             interaction_breakdown=interaction_breakdown,
                             conversion_funnel=conversion_funnel,
                             recent_leads=recent_leads,
                             source_performance=source_performance,
                             days=days)
    
    except Exception as e:
        logger.error(f"Error loading comprehensive dashboard: {e}")
        flash('Error loading dashboard analytics', 'danger')
        return redirect(url_for('web.admin_dashboard'))

@comprehensive_admin_bp.route('/interactions')
@login_required
def interaction_analytics():
    """Detailed interaction analytics view."""
    try:
        # Get filters
        interaction_type = request.args.get('type', 'all')
        days = request.args.get('days', '7', type=int)
        page = request.args.get('page', 1, type=int)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Build query conditions
        where_conditions = ["created_at >= :start_date", "created_at <= :end_date"]
        params = {'start_date': start_date, 'end_date': end_date}
        
        if interaction_type != 'all':
            where_conditions.append("interaction_type = :interaction_type")
            params['interaction_type'] = interaction_type
        
        where_clause = " AND ".join(where_conditions)
        
        # Get interactions with pagination
        offset = (page - 1) * 50
        interactions_result = db.session.execute(text(f"""
            SELECT ui.*, u.name as user_name, u.email as user_email,
                   l.id as lead_id, l.patient_name, l.mobile_number, l.lead_score
            FROM user_interactions ui
            LEFT JOIN users u ON ui.user_id = u.id
            LEFT JOIN leads l ON ui.lead_id = l.id
            WHERE {where_clause}
            ORDER BY ui.created_at DESC
            LIMIT 50 OFFSET :offset
        """), {**params, 'offset': offset}).fetchall()
        
        interactions = [dict(row._mapping) for row in interactions_result]
        
        # Parse JSON data for each interaction
        for interaction in interactions:
            try:
                interaction['parsed_data'] = json.loads(interaction['data']) if interaction['data'] else {}
            except:
                interaction['parsed_data'] = {}
        
        # Get total count
        total_count = db.session.execute(text(f"""
            SELECT COUNT(*) FROM user_interactions WHERE {where_clause}
        """), params).scalar()
        
        # Get interaction types for filter
        interaction_types = db.session.execute(text("""
            SELECT interaction_type, COUNT(*) as count
            FROM user_interactions
            WHERE created_at >= :start_date
            GROUP BY interaction_type
            ORDER BY count DESC
        """), {'start_date': start_date}).fetchall()
        
        interaction_types = [{'type': row[0], 'count': row[1]} for row in interaction_types]
        
        return render_template('admin/interaction_analytics.html',
                             interactions=interactions,
                             interaction_types=interaction_types,
                             current_type=interaction_type,
                             days=days,
                             page=page,
                             total_count=total_count,
                             has_next=total_count > page * 50)
    
    except Exception as e:
        logger.error(f"Error loading interaction analytics: {e}")
        flash('Error loading interaction analytics', 'danger')
        return redirect(url_for('comprehensive_admin.comprehensive_dashboard'))

@comprehensive_admin_bp.route('/lead-scoring')
@login_required
def lead_scoring_management():
    """Manage lead scoring rules and view scoring performance."""
    try:
        # Get all scoring rules
        rules_result = db.session.execute(text("""
            SELECT * FROM lead_scoring_rules ORDER BY interaction_type, points DESC
        """)).fetchall()
        
        scoring_rules = [dict(row._mapping) for row in rules_result]
        
        # Get scoring performance statistics
        scoring_stats = db.session.execute(text("""
            SELECT 
                l.lead_score,
                l.engagement_level,
                l.status,
                COUNT(*) as count,
                AVG(CASE WHEN l.converted_at IS NOT NULL THEN 1.0 ELSE 0.0 END) as conversion_rate
            FROM leads l
            WHERE l.lead_score IS NOT NULL
            GROUP BY l.lead_score, l.engagement_level, l.status
            ORDER BY l.lead_score DESC
        """)).fetchall()
        
        scoring_performance = [dict(row._mapping) for row in scoring_stats]
        
        return render_template('admin/lead_scoring_management.html',
                             scoring_rules=scoring_rules,
                             scoring_performance=scoring_performance)
    
    except Exception as e:
        logger.error(f"Error loading lead scoring management: {e}")
        flash('Error loading lead scoring management', 'danger')
        return redirect(url_for('comprehensive_admin.comprehensive_dashboard'))

@comprehensive_admin_bp.route('/update-lead-status/<int:lead_id>', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    """Update lead status via AJAX."""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['new', 'contacted', 'converted', 'closed']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        db.session.execute(text("""
            UPDATE leads 
            SET status = :status, updated_at = CURRENT_TIMESTAMP
            WHERE id = :lead_id
        """), {'status': new_status, 'lead_id': lead_id})
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating lead status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@comprehensive_admin_bp.route('/export-leads')
@login_required
def export_leads():
    """Export leads to CSV."""
    try:
        # Get same filters as the main view
        days = request.args.get('days', 30, type=int)
        status_filter = request.args.get('status', '')
        source_filter = request.args.get('source', '')
        min_score = request.args.get('min_score', '')
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        where_conditions = ["created_at >= :start_date", "created_at <= :end_date"]
        params = {'start_date': start_date, 'end_date': end_date}
        
        if status_filter:
            where_conditions.append("status = :status")
            params['status'] = status_filter
            
        if source_filter:
            where_conditions.append("source = :source")
            params['source'] = source_filter
            
        if min_score:
            where_conditions.append("COALESCE(lead_score, 0) >= :min_score")
            params['min_score'] = int(min_score)
        
        where_clause = " AND ".join(where_conditions)
        
        # Get leads data
        leads_result = db.session.execute(text(f"""
            SELECT patient_name, mobile_number, email, city, procedure_name, 
                   source, status, lead_score, created_at, preferred_date
            FROM leads 
            WHERE {where_clause}
            ORDER BY created_at DESC
        """), params).fetchall()
        
        # Create CSV response
        from flask import Response
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Name', 'Phone', 'Email', 'City', 'Procedure', 'Source', 'Status', 'Score', 'Created', 'Preferred Date'])
        
        # Data rows
        for lead in leads_result:
            writer.writerow([
                lead[0] or '',  # name
                lead[1] or '',  # phone
                lead[2] or '',  # email
                lead[3] or '',  # city
                lead[4] or '',  # procedure
                lead[5] or '',  # source
                lead[6] or '',  # status
                lead[7] or '',  # score
                lead[8].strftime('%Y-%m-%d %H:%M') if lead[8] else '',  # created
                lead[9].strftime('%Y-%m-%d') if lead[9] else ''  # preferred_date
            ])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=leads_export_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        flash('Error exporting leads', 'danger')
        return redirect(url_for('comprehensive_admin.detailed_leads'))

@comprehensive_admin_bp.route('/update-scoring-rule/<int:rule_id>', methods=['POST'])
@login_required
def update_scoring_rule(rule_id):
    """Update a lead scoring rule."""
    try:
        points = request.form.get('points', type=int)
        is_active = request.form.get('is_active') == 'true'
        description = request.form.get('description', '').strip()
        
        db.session.execute(text("""
            UPDATE lead_scoring_rules 
            SET points = :points, is_active = :is_active, description = :description,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :rule_id
        """), {
            'rule_id': rule_id,
            'points': points,
            'is_active': is_active,
            'description': description
        })
        
        db.session.commit()
        flash('Scoring rule updated successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error updating scoring rule: {e}")
        flash('Error updating scoring rule', 'danger')
    
    return redirect(url_for('comprehensive_admin.lead_scoring_management'))

def get_basic_analytics(start_date, end_date):
    """Get basic analytics using existing database structure."""
    try:
        # Get lead analytics from leads table
        lead_result = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_leads_created,
                AVG(COALESCE(lead_score, 50)) as avg_lead_score,
                COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted_leads,
                COUNT(CASE WHEN source LIKE '%ai%' OR source LIKE '%recommendation%' THEN 1 END) as ai_recommendations,
                COUNT(CASE WHEN source LIKE '%face%' OR source LIKE '%analysis%' THEN 1 END) as face_analyses,
                COUNT(CASE WHEN source LIKE '%cost%' OR source LIKE '%calculator%' THEN 1 END) as cost_calculations,
                COUNT(CASE WHEN source LIKE '%appointment%' OR source LIKE '%booking%' THEN 1 END) as appointment_bookings
            FROM leads 
            WHERE created_at >= :start_date AND created_at <= :end_date
        """), {'start_date': start_date, 'end_date': end_date}).fetchone()
        
        # Get interaction data
        interaction_result = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_interactions,
                COUNT(DISTINCT session_id) as unique_sessions
            FROM user_interactions 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
        """), {'start_date': start_date, 'end_date': end_date}).fetchone()
        
        data = {}
        if lead_result:
            lead_data = dict(lead_result._mapping)
            data.update(lead_data)
        
        if interaction_result:
            interaction_data = dict(interaction_result._mapping)
            data.update(interaction_data)
        
        # Calculate conversion rates
        data['interaction_to_lead_rate'] = (
            (data.get('total_leads_created', 0) * 100.0 / data.get('total_interactions', 1)) 
            if data.get('total_interactions', 0) > 0 else 0
        )
        
        data['lead_conversion_rate'] = (
            (data.get('converted_leads', 0) * 100.0 / data.get('total_leads_created', 1)) 
            if data.get('total_leads_created', 0) > 0 else 0
        )
        
        return data
        
    except Exception as e:
        logger.error(f"Error getting basic analytics: {e}")
        return {
            'total_interactions': 0,
            'total_leads_created': 0,
            'avg_lead_score': 50,
            'ai_recommendations': 0,
            'face_analyses': 0,
            'cost_calculations': 0,
            'appointment_bookings': 0,
            'interaction_to_lead_rate': 0,
            'lead_conversion_rate': 0
        }

def get_lead_source_breakdown(start_date, end_date):
    """Get breakdown of leads by source."""
    try:
        result = db.session.execute(text("""
            SELECT 
                COALESCE(source, 'Unknown') as interaction_type,
                COUNT(*) as total_count,
                COUNT(CASE WHEN status IN ('contacted', 'converted') THEN 1 END) as converted_count,
                ROUND(AVG(CASE WHEN status IN ('contacted', 'converted') THEN 100.0 ELSE 0.0 END), 2) as conversion_rate
            FROM leads
            WHERE created_at >= :start_date AND created_at <= :end_date
            GROUP BY source
            ORDER BY total_count DESC
        """), {'start_date': start_date, 'end_date': end_date}).fetchall()
        
        return [dict(row._mapping) for row in result]
        
    except Exception as e:
        logger.error(f"Error getting lead source breakdown: {e}")
        return []

def get_simple_funnel(start_date, end_date):
    """Get simple conversion funnel using available data."""
    try:
        # Get lead funnel data
        total_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE created_at >= :start_date AND created_at <= :end_date
        """), {'start_date': start_date, 'end_date': end_date}).scalar()
        
        contacted_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE created_at >= :start_date AND created_at <= :end_date
            AND status IN ('contacted', 'converted')
        """), {'start_date': start_date, 'end_date': end_date}).scalar()
        
        converted_leads = db.session.execute(text("""
            SELECT COUNT(*) FROM leads 
            WHERE created_at >= :start_date AND created_at <= :end_date
            AND status = 'converted'
        """), {'start_date': start_date, 'end_date': end_date}).scalar()
        
        # Get interaction data if available
        total_interactions = db.session.execute(text("""
            SELECT COUNT(*) FROM user_interactions 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
        """), {'start_date': start_date, 'end_date': end_date}).scalar()
        
        return {
            'total_sessions': total_interactions or total_leads,
            'interactive_sessions': total_leads or 0,
            'converted_sessions': contacted_leads or 0,
            'customer_conversions': converted_leads or 0,
            'interaction_rate': (total_leads * 100.0 / total_interactions) if total_interactions > 0 else 100,
            'lead_conversion_rate': (contacted_leads * 100.0 / total_leads) if total_leads > 0 else 0,
            'customer_conversion_rate': (converted_leads * 100.0 / contacted_leads) if contacted_leads > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting simple funnel: {e}")
        return {
            'total_sessions': 0,
            'interactive_sessions': 0,
            'converted_sessions': 0,
            'customer_conversions': 0,
            'interaction_rate': 0,
            'lead_conversion_rate': 0,
            'customer_conversion_rate': 0
        }

def get_recent_leads(limit=10):
    """Get recent leads."""
    try:
        result = db.session.execute(text("""
            SELECT patient_name, mobile_number, procedure_name, source as interaction_type, 
                   lead_score, created_at as interaction_date, status
            FROM leads
            WHERE lead_score >= 70 OR lead_score IS NULL
            ORDER BY created_at DESC
            LIMIT :limit
        """), {'limit': limit}).fetchall()
        
        return [dict(row._mapping) for row in result]
        
    except Exception as e:
        logger.error(f"Error getting recent leads: {e}")
        return []

def get_lead_sources(start_date, end_date):
    """Get performance by lead source."""
    try:
        result = db.session.execute(text("""
            SELECT 
                COALESCE(source, 'Direct') as source,
                COUNT(*) as total_interactions,
                COUNT(*) as leads_generated,
                ROUND(AVG(COALESCE(lead_score, 50)), 2) as avg_lead_score,
                COUNT(CASE WHEN status = 'converted' THEN 1 END) as conversions
            FROM leads
            WHERE created_at >= :start_date AND created_at <= :end_date
            GROUP BY source
            ORDER BY leads_generated DESC
        """), {'start_date': start_date, 'end_date': end_date}).fetchall()
        
        return [dict(row._mapping) for row in result]
        
    except Exception as e:
        logger.error(f"Error getting lead sources: {e}")
        return []