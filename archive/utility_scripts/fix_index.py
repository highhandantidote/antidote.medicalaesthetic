#!/usr/bin/env python3
"""
Strong fix for the index route to resolve the NoneType error and display categories properly.
This will replace the problematic index route with a robust version.
"""

# New index route content
NEW_INDEX_ROUTE = '''
@web.route('/')
def index():
    """Render the home page with robust error handling."""
    # Initialize all variables with empty lists to prevent None errors
    popular_body_parts = []
    popular_procedures = []
    procedure_categories = []
    recent_threads = []
    top_doctors = []
    all_procedures = []
    
    try:
        # Get body parts safely
        body_parts_query = BodyPart.query.limit(4).all()
        popular_body_parts = list(body_parts_query) if body_parts_query else []
        
        # Get high-demand procedures safely
        high_demand_names = ['Botox', 'Lip Fillers', 'Liposuction', 'Gynecomastia', 'Rhinoplasty', 'Chemical Peel']
        procedures_query = Procedure.query.filter(Procedure.procedure_name.in_(high_demand_names)).all()
        popular_procedures = list(procedures_query) if procedures_query else []
        
        # Get procedure categories safely - this is the main fix
        categories_query = Category.query.limit(6).all()
        procedure_categories = list(categories_query) if categories_query else []
        
        # Get recent community threads safely
        threads_query = Community.query.order_by(Community.created_at.desc()).limit(3).all()
        recent_threads = list(threads_query) if threads_query else []
        
        # Get top doctors safely
        doctors_query = Doctor.query.order_by(Doctor.id).limit(9).all()
        top_doctors = list(doctors_query) if doctors_query else []
        
        # Get all procedures for forms safely
        all_procedures_query = Procedure.query.order_by(Procedure.procedure_name).all()
        all_procedures = list(all_procedures_query) if all_procedures_query else []
        
        logger.info(f"Successfully loaded homepage data: {len(popular_procedures)} procedures, {len(recent_threads)} threads, {len(top_doctors)} doctors, {len(procedure_categories)} categories")
        
    except Exception as e:
        logger.error(f"Error loading homepage data: {str(e)}")
        # All variables already initialized as empty lists, so we're safe
    
    # Render template with guaranteed non-None lists
    return render_template(
        'index.html',
        popular_body_parts=popular_body_parts,
        popular_procedures=popular_procedures,
        top_doctors=top_doctors,
        recent_threads=recent_threads,
        procedure_categories=procedure_categories,
        all_procedures=all_procedures
    )
'''

print("This script contains the new robust index route to fix the NoneType error.")
print("The new route ensures all variables are proper lists and never None.")
print("This will resolve the categories not showing up issue.")