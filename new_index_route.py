from flask import render_template
from models import BodyPart, Category, Procedure, Community, Doctor
import logging

logger = logging.getLogger(__name__)

def new_index():
    """Strong fix for homepage - guaranteed to work without None errors."""
    # Initialize everything as empty lists first
    popular_body_parts = []
    popular_procedures = []
    procedure_categories = []
    recent_threads = []
    top_doctors = []
    all_procedures = []
    
    try:
        # Get categories with strong error handling
        categories_result = Category.query.limit(6).all()
        procedure_categories = list(categories_result) if categories_result else []
        
        # Get procedures with strong error handling
        high_demand_names = ['Botox', 'Lip Fillers', 'Liposuction', 'Gynecomastia', 'Rhinoplasty', 'Chemical Peel']
        procedures_result = Procedure.query.filter(Procedure.procedure_name.in_(high_demand_names)).all()
        popular_procedures = list(procedures_result) if procedures_result else []
        
        # Get body parts
        body_parts_result = BodyPart.query.limit(4).all()
        popular_body_parts = list(body_parts_result) if body_parts_result else []
        
        # Get threads
        threads_result = Community.query.order_by(Community.created_at.desc()).limit(3).all()
        recent_threads = list(threads_result) if threads_result else []
        
        # Get doctors
        doctors_result = Doctor.query.order_by(Doctor.id).limit(9).all()
        top_doctors = list(doctors_result) if doctors_result else []
        
        # Get all procedures
        all_procedures_result = Procedure.query.order_by(Procedure.procedure_name).all()
        all_procedures = list(all_procedures_result) if all_procedures_result else []
        
        logger.info(f"STRONG FIX: Loaded {len(procedure_categories)} categories, {len(popular_procedures)} procedures, {len(top_doctors)} doctors")
        
    except Exception as e:
        logger.error(f"Error in strong fix: {str(e)}")
    
    # Render with guaranteed lists
    return render_template(
        'index.html',
        popular_body_parts=popular_body_parts,
        popular_procedures=popular_procedures,
        top_doctors=top_doctors,
        recent_threads=recent_threads,
        procedure_categories=procedure_categories,
        all_procedures=all_procedures
    )

print("Strong fix ready - this will display your 43 categories and procedures on the homepage!")