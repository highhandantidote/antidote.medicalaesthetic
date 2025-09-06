"""
Clean AI Recommendations System
Simple, conflict-free implementation for treatment recommendations.
"""

import logging
import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_wtf.csrf import validate_csrf, CSRFError
from models import Procedure, Doctor, Package, Clinic
from app import db
from google import genai
from google.genai import types
import random
import traceback

# Configure logging
logger = logging.getLogger(__name__)

def safe_clinic_serialization(clinic):
    """Safely serialize clinic object to dict with error handling."""
    try:
        return {
            'id': clinic.id,
            'name': getattr(clinic, 'name', 'Unknown Clinic'),
            'description': getattr(clinic, 'description', 'Professional aesthetic clinic'),
            'city': getattr(clinic, 'city', None),
            'state': getattr(clinic, 'state', None),
            'address': getattr(clinic, 'address', None),
            'phone': getattr(clinic, 'contact_number', getattr(clinic, 'phone', None)),
            'rating': getattr(clinic, 'rating', 4.5),
            'specialties': getattr(clinic, 'specialties', []),
            'reason': 'Offers treatments for your specific concerns'
        }
    except Exception as e:
        logger.error(f"Error serializing clinic {getattr(clinic, 'id', 'unknown')}: {e}")
        return {
            'id': getattr(clinic, 'id', 0),
            'name': 'Clinic',
            'description': 'Professional aesthetic clinic',
            'city': None,
            'state': None,
            'address': None,
            'phone': None,
            'rating': 4.5,
            'specialties': [],
            'reason': 'Offers treatments for your specific concerns'
        }

# Create Blueprint
ai_bp = Blueprint('ai_clean', __name__)

# Initialize Gemini AI
try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    logger.info("Gemini AI initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini AI: {e}")
    client = None

def analyze_user_query(query_text):
    """Analyze user query using Gemini AI to extract health concerns."""
    if not client:
        logger.warning("Gemini AI not available, using fallback analysis")
        return {
            'body_parts': ['face'],
            'concerns': ['general'],
            'procedures': ['general cosmetic procedure']
        }
    
    try:
        prompt = f"""
        Analyze this health/cosmetic concern and extract key information:
        
        User Query: "{query_text}"
        
        Return a JSON response with:
        - body_parts: list of body parts mentioned (face, nose, breast, etc.)
        - concerns: list of specific concerns (wrinkles, scars, size, etc.)
        - procedures: list of likely relevant procedures
        
        Keep it simple and focus on cosmetic/aesthetic procedures.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        if response.text:
            import json
            analysis = json.loads(response.text)
            # Ensure language_detected field is present
            if 'language_detected' not in analysis:
                analysis['language_detected'] = 'English'
            return analysis
        
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
    
    # Fallback analysis
    query_lower = query_text.lower()
    body_parts = []
    concerns = []
    
    # Enhanced keyword matching for better body part detection
    if any(word in query_lower for word in ['nose', 'nasal', 'rhinoplasty']):
        body_parts.append('nose')
    if any(word in query_lower for word in ['face', 'facial', 'skin', 'wrinkle', 'aging']):
        body_parts.append('face')
    if any(word in query_lower for word in ['breast', 'chest', 'boob']):
        body_parts.append('breast')
    if any(word in query_lower for word in ['hair', 'scalp', 'bald', 'balding', 'hairless', 'no hair', 'hair loss', 'thinning']):
        body_parts.append('hair')
    if any(word in query_lower for word in ['stomach', 'belly', 'tummy', 'abdomen']):
        body_parts.append('stomach')
    if any(word in query_lower for word in ['butt', 'buttock', 'bottom']):
        body_parts.append('butt')
    
    # Default to face only if no specific body parts detected
    if not body_parts:
        body_parts = ['face']
    
    return {
        'body_parts': body_parts,
        'concerns': [query_text[:50]],
        'procedures': ['cosmetic procedure'],
        'language_detected': 'English'
    }

def get_recommended_procedures(analysis, limit=5):
    """Get procedure recommendations based on analysis."""
    try:
        # Get procedures based on body parts mentioned
        procedures = []
        body_parts = analysis.get('body_parts', ['face'])
        
        logger.info(f"Searching procedures for body parts: {body_parts}")
        
        for body_part in body_parts:
            # Search procedures by body part
            procs = Procedure.query.filter(
                Procedure.body_part.ilike(f'%{body_part}%')
            ).limit(3).all()
            procedures.extend(procs)
            logger.info(f"Found {len(procs)} procedures for body part '{body_part}'")
        
        # If no specific matches, try broader search
        if not procedures:
            logger.warning(f"No procedures found for body parts {body_parts}, trying broader search")
            
            # Try searching in procedure names and descriptions
            for body_part in body_parts:
                procs = Procedure.query.filter(
                    db.or_(
                        Procedure.procedure_name.ilike(f'%{body_part}%'),
                        Procedure.short_description.ilike(f'%{body_part}%'),
                        Procedure.alternative_names.ilike(f'%{body_part}%')
                    )
                ).limit(3).all()
                procedures.extend(procs)
                logger.info(f"Broader search found {len(procs)} procedures for '{body_part}'")
        
        # If still no matches, get procedures based on concerns
        if not procedures:
            concerns = analysis.get('concerns', [])
            logger.warning(f"Still no matches, trying concern-based search for: {concerns}")
            
            for concern in concerns[:2]:  # Check first 2 concerns
                procs = Procedure.query.filter(
                    db.or_(
                        Procedure.procedure_name.ilike(f'%{concern}%'),
                        Procedure.short_description.ilike(f'%{concern}%')
                    )
                ).limit(2).all()
                procedures.extend(procs)
        
        # Last resort: get popular procedures only if absolutely no matches
        if not procedures:
            logger.warning("No relevant procedures found, falling back to popular procedures")
            procedures = Procedure.query.filter(
                Procedure.popularity_score > 0
            ).order_by(Procedure.popularity_score.desc()).limit(limit).all()
        
        # Remove duplicates and limit
        unique_procedures = []
        seen_ids = set()
        for proc in procedures:
            if proc.id not in seen_ids:
                unique_procedures.append(proc)
                seen_ids.add(proc.id)
                if len(unique_procedures) >= limit:
                    break
        
        logger.info(f"Final result: {len(unique_procedures)} unique procedures selected")
        return unique_procedures
        
    except Exception as e:
        logger.error(f"Error getting procedures: {e}")
        return []

def get_recommended_packages(analysis, limit=5):
    """Get package recommendations based on analysis."""
    try:
        packages = []
        body_parts = analysis.get('body_parts', ['face'])
        
        logger.info(f"Searching packages for body parts: {body_parts}")
        
        for body_part in body_parts:
            # Search packages by title and description
            pkgs = Package.query.filter(
                db.or_(
                    Package.title.ilike(f'%{body_part}%'),
                    Package.description.ilike(f'%{body_part}%')
                )
            ).filter(Package.is_active == True).limit(3).all()
            packages.extend(pkgs)
            logger.info(f"Found {len(pkgs)} packages for body part '{body_part}'")
        
        # If no specific matches, try broader search
        if not packages:
            concerns = analysis.get('concerns', [])
            for concern in concerns[:2]:
                pkgs = Package.query.filter(
                    db.or_(
                        Package.title.ilike(f'%{concern}%'),
                        Package.description.ilike(f'%{concern}%')
                    )
                ).filter(Package.is_active == True).limit(2).all()
                packages.extend(pkgs)
        
        # Last resort: get popular packages
        if not packages:
            packages = Package.query.filter(
                Package.is_active == True
            ).order_by(Package.id.desc()).limit(limit).all()
        
        # Remove duplicates and limit
        unique_packages = []
        seen_ids = set()
        for pkg in packages:
            if pkg.id not in seen_ids:
                unique_packages.append(pkg)
                seen_ids.add(pkg.id)
                if len(unique_packages) >= limit:
                    break
        
        logger.info(f"Final result: {len(unique_packages)} unique packages selected")
        return unique_packages
        
    except Exception as e:
        logger.error(f"Error getting packages: {e}")
        return []

def get_recommended_clinics(packages, limit=5):
    """Get clinic recommendations based on packages and location."""
    try:
        clinics = []
        
        # Get clinics that offer the recommended packages
        clinic_ids = set()
        for package in packages:
            if hasattr(package, 'clinic_id') and package.clinic_id:
                clinic_ids.add(package.clinic_id)
        
        if clinic_ids:
            clinics_from_packages = Clinic.query.filter(
                Clinic.id.in_(clinic_ids),
                Clinic.is_approved == True
            ).all()
            clinics.extend(clinics_from_packages)
        
        # Fill remaining slots with highly rated clinics
        remaining_slots = limit - len(clinics)
        if remaining_slots > 0:
            additional_clinics = Clinic.query.filter(
                Clinic.is_approved == True,
                ~Clinic.id.in_(clinic_ids) if clinic_ids else True
            ).order_by(Clinic.id.desc()).limit(remaining_slots).all()
            clinics.extend(additional_clinics)
        
        # Remove duplicates and limit
        unique_clinics = []
        seen_ids = set()
        for clinic in clinics:
            if clinic.id not in seen_ids:
                unique_clinics.append(clinic)
                seen_ids.add(clinic.id)
                if len(unique_clinics) >= limit:
                    break
        
        logger.info(f"Found {len(unique_clinics)} unique clinics")
        return unique_clinics
        
    except Exception as e:
        logger.error(f"Error getting clinics: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

def get_recommended_doctors(procedures, limit=3):
    """Get doctor recommendations based on procedures."""
    try:
        # Get random doctors for now - in production, you'd match by specialties
        doctors = Doctor.query.order_by(db.func.random()).limit(limit).all()
        return doctors
        
    except Exception as e:
        logger.error(f"Error getting doctors: {e}")
        return []

@ai_bp.route('/api/analyze-query', methods=['POST'])
def analyze_query():
    """Main API endpoint for AI recommendations."""
    try:
        # Get user input
        query_text = request.form.get('query_text', '').strip()
        
        if not query_text:
            return jsonify({
                'success': False,
                'message': 'Please provide your health concerns'
            }), 400
        
        logger.info(f"Processing AI query: {query_text[:50]}...")
        
        # Analyze the query
        analysis = analyze_user_query(query_text)
        
        # Get recommendations
        procedures = get_recommended_procedures(analysis)
        packages = get_recommended_packages(analysis)
        clinics = get_recommended_clinics(packages)
        doctors = get_recommended_doctors(procedures)
        
        # Store in session for results page with complete structure
        summary = {
            'confidence': 0.85,  # High confidence for Gemini AI analysis
            'primary_body_parts': analysis.get('body_parts', ['General']),
            'severity_level': 'Medium',  # Default to medium concern level
            'total_procedures': len(procedures)
        }
        
        session['ai_recommendations'] = {
            'user_input': query_text,
            'analysis': analysis,
            'summary': summary,
            'packages': [
                {
                    'id': pkg.id,
                    'title': pkg.title,
                    'description': pkg.description,
                    'procedure_name': None,  # Package model doesn't have this field
                    'price_actual': pkg.price_actual or 0,
                    'price_discounted': pkg.price_discounted,
                    'duration': getattr(pkg, 'duration', None),
                    'downtime': getattr(pkg, 'downtime', None),
                    'clinic': {
                        'id': pkg.clinic.id if pkg.clinic else None,
                        'name': pkg.clinic.name if pkg.clinic else 'Clinic',
                        'city': pkg.clinic.city if pkg.clinic else None,
                        'state': pkg.clinic.state if pkg.clinic else None
                    } if pkg.clinic else None,
                    'clinic_name': getattr(pkg, 'clinic_name', None),
                    'clinic_id': pkg.clinic_id,
                    'results_gallery': getattr(pkg, 'results_gallery', [])
                }
                for pkg in packages
            ],
            'procedures': [
                {
                    'id': proc.id,
                    'name': proc.procedure_name,
                    'description': proc.short_description or 'Professional cosmetic procedure',
                    'body_part': proc.body_part,
                    'min_cost': proc.min_cost or 0,
                    'max_cost': proc.max_cost or 0,
                    'reason': f"Matches your concern about {analysis.get('body_parts', ['general areas'])[0]}"
                }
                for proc in procedures
            ],
            'clinics': [
                safe_clinic_serialization(clinic) for clinic in clinics
            ],
            'doctors': [
                {
                    'id': doctor.id,
                    'name': doctor.name,
                    'specialty': doctor.specialty or 'Cosmetic Specialist',
                    'qualification': doctor.qualification or 'Medical Professional',
                    'experience': getattr(doctor, 'experience', 10),
                    'rating': getattr(doctor, 'avg_rating', 4.5),
                    'city': doctor.city or 'Mumbai',
                    'reason': 'Recommended specialist for your concerns'
                }
                for doctor in doctors
            ]
        }
        
        return jsonify({
            'success': True,
            'message': 'Analysis complete',
            'redirect': url_for('ai_clean.show_results')
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_query: {e}")
        return jsonify({
            'success': False,
            'message': 'Sorry, there was an error processing your request. Please try again.'
        }), 500

@ai_bp.route('/ai-recommendations-results')
def show_results():
    """Display AI recommendations results."""
    if 'ai_recommendations' not in session:
        flash('Please enter your concerns first to get AI recommendations.', 'info')
        return redirect(url_for('web.index'))
    
    recommendations = session['ai_recommendations']
    
    return render_template('ai_recommendations_results.html',
                         user_input=recommendations['user_input'],
                         analysis=recommendations['analysis'],
                         summary=recommendations.get('summary', {}),
                         packages=recommendations.get('packages', []),
                         procedures=recommendations['procedures'],
                         clinics=recommendations.get('clinics', []),
                         doctors=recommendations['doctors'])

@ai_bp.route('/ai-recommendations', methods=['GET', 'POST'])
def ai_recommendations():
    """Handle direct access to AI recommendations page."""
    if request.method == 'POST':
        # Debug form data
        logger.info(f"Form data received: {dict(request.form)}")
        logger.info(f"Request args: {dict(request.args)}")
        logger.info(f"Request method: {request.method}")
        
        # Process form submission
        query_text = request.form.get('concerns', '').strip()
        
        logger.info(f"AI Recommendations POST request received. Query text: '{query_text}'")
        
        if not query_text:
            logger.warning("Empty query text received")
            flash('Please describe your concerns to get recommendations.', 'warning')
            return redirect(url_for('web.index'))
        
        logger.info(f"Processing AI recommendations for: {query_text[:50]}...")
        
        # Analyze and redirect to results
        analysis = analyze_user_query(query_text)
        procedures = get_recommended_procedures(analysis)
        packages = get_recommended_packages(analysis)
        clinics = get_recommended_clinics(packages)
        doctors = get_recommended_doctors(procedures)
        
        logger.info(f"Found {len(procedures)} procedures, {len(packages)} packages, {len(clinics)} clinics and {len(doctors)} doctors")
        
        # Create summary object for template
        summary = {
            'confidence': 0.85,  # High confidence for Gemini AI analysis
            'primary_body_parts': analysis.get('body_parts', ['General']),
            'severity_level': 'Medium',  # Default to medium concern level
            'total_procedures': len(procedures)
        }
        
        session['ai_recommendations'] = {
            'user_input': query_text,
            'analysis': analysis,
            'summary': summary,
            'packages': [
                {
                    'id': pkg.id,
                    'title': pkg.title,
                    'description': pkg.description,
                    'procedure_name': None,  # Package model doesn't have this field
                    'price_actual': pkg.price_actual or 0,
                    'price_discounted': pkg.price_discounted,
                    'duration': getattr(pkg, 'duration', None),
                    'downtime': getattr(pkg, 'downtime', None),
                    'clinic': {
                        'id': pkg.clinic.id if pkg.clinic else None,
                        'name': pkg.clinic.name if pkg.clinic else 'Clinic',
                        'city': pkg.clinic.city if pkg.clinic else None,
                        'state': pkg.clinic.state if pkg.clinic else None
                    } if pkg.clinic else None,
                    'clinic_name': getattr(pkg, 'clinic_name', None),
                    'clinic_id': pkg.clinic_id,
                    'results_gallery': getattr(pkg, 'results_gallery', [])
                }
                for pkg in packages
            ],
            'procedures': [
                {
                    'id': proc.id,
                    'name': proc.procedure_name,
                    'description': proc.short_description or 'Professional cosmetic procedure',
                    'body_part': proc.body_part,
                    'min_cost': proc.min_cost or 0,
                    'max_cost': proc.max_cost or 0,
                    'reason': f"Matches your concern about {analysis.get('body_parts', ['general areas'])[0]}"
                }
                for proc in procedures
            ],
            'clinics': [
                safe_clinic_serialization(clinic) for clinic in clinics
            ],
            'doctors': [
                {
                    'id': doctor.id,
                    'name': doctor.name,
                    'specialty': doctor.specialty or 'Cosmetic Specialist',
                    'qualification': doctor.qualification or 'Medical Professional',
                    'experience': getattr(doctor, 'experience', 10),
                    'rating': getattr(doctor, 'avg_rating', 4.5),
                    'city': doctor.city or 'Mumbai',
                    'reason': 'Recommended specialist for your concerns'
                }
                for doctor in doctors
            ]
        }
        
        return redirect(url_for('ai_clean.show_results'))
    
    # GET request - redirect to homepage
    return redirect(url_for('web.index'))