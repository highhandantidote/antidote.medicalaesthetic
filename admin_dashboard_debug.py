"""
Admin dashboard debugging tool.

This script adds a route to diagnose admin dashboard rendering issues.
"""

from flask import Blueprint, render_template, jsonify
from app import db
from models import User, Doctor, Procedure, Lead, Review, Community, BodyPart, Category, Thread
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('admin_dashboard_debug')

# Create a blueprint for admin debugging routes
debug_blueprint = Blueprint('admin_debug', __name__, url_prefix='/admin-debug')

@debug_blueprint.route('/')
def debug_dashboard():
    """
    Debug route that returns JSON data with all the admin dashboard data.
    Use this to verify data is being retrieved correctly.
    """
    try:
        logger.info("=== STARTING ADMIN DASHBOARD DEBUG ===")
        
        # Get the data that should appear in the admin dashboard
        user_count = User.query.filter(User.role == 'user').count()
        doctor_count = Doctor.query.count()
        lead_count = Lead.query.count()
        community_count = Community.query.count()
        
        logger.info(f"User count: {user_count}")
        logger.info(f"Doctor count: {doctor_count}")
        logger.info(f"Lead count: {lead_count}")
        logger.info(f"Community count: {community_count}")
        
        # Get all users
        users = User.query.all()
        users_list = []
        for user in users:
            users_list.append({
                'id': user.id,
                'username': getattr(user, 'username', 'N/A'),
                'email': getattr(user, 'email', 'N/A'),
                'role': getattr(user, 'role', 'N/A')
            })
        
        # Get all doctors
        doctors = Doctor.query.all()
        doctors_list = []
        for doctor in doctors:
            doctors_list.append({
                'id': doctor.id,
                'name': getattr(doctor, 'name', 'N/A'),
                'specialty': getattr(doctor, 'specialty', 'N/A'),
                'is_verified': getattr(doctor, 'is_verified', False)
            })
        
        # Get all procedures
        procedures = Procedure.query.all()
        procedures_list = []
        for procedure in procedures:
            procedures_list.append({
                'id': procedure.id,
                'name': getattr(procedure, 'procedure_name', 'N/A')
            })
            
        # Get top 5 procedures by popularity score
        top_procedures = Procedure.query.order_by(Procedure.popularity_score.desc()).limit(5).all()
        top_procedures_list = []
        for procedure in top_procedures:
            # Try to get the category name
            category_name = "N/A"
            if hasattr(procedure, 'category') and procedure.category:
                category_name = procedure.category.name
                
            # Manually add required attributes
            top_procedures_list.append({
                'id': procedure.id,
                'name': getattr(procedure, 'procedure_name', 'N/A'),
                'category_name': category_name,
                'views': getattr(procedure, 'popularity_score', 0) * 10 if getattr(procedure, 'popularity_score', None) is not None else 0,
                'leads': Lead.query.filter_by(procedure_id=procedure.id).count()
            })
            
        return jsonify({
            'stats': {
                'user_count': user_count,
                'doctor_count': doctor_count,
                'lead_count': lead_count,
                'community_count': community_count
            },
            'users': users_list,
            'doctors': doctors_list,
            'procedures': procedures_list,
            'top_procedures': top_procedures_list
        })
    
    except Exception as e:
        logger.error(f"Error in debug_dashboard: {str(e)}")
        return jsonify({'error': str(e)})

# This blueprint will be registered in routes.py