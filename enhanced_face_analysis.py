"""
Enhanced Face Analysis System with Lead Capture
Converts face analysis submissions into high-intent qualified leads
"""

from flask import Blueprint, request, session, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user
import json
import logging
from datetime import datetime
from interaction_tracker import track_user_interaction, should_show_contact_form, create_lead_from_form
from app import db
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_face_bp = Blueprint('enhanced_face', __name__, url_prefix='/enhanced-face')

@enhanced_face_bp.route('/analysis-form', methods=['GET'])
def show_analysis_form():
    """Display the enhanced face analysis form with lead capture."""
    return render_template('face_analysis/enhanced_analysis_form.html')

@enhanced_face_bp.route('/submit-analysis', methods=['POST'])
def submit_face_analysis():
    """Process face analysis with integrated lead capture."""
    try:
        # Extract form data
        uploaded_image = request.files.get('face_image')
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        skin_concerns = request.form.getlist('skin_concerns')
        treatment_history = request.form.get('treatment_history', '').strip()
        budget_range = request.form.get('budget_range', '').strip()
        
        # Contact information (progressive capture)
        contact_name = request.form.get('contact_name', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_city = request.form.get('contact_city', '').strip()
        
        # Validate required fields
        if not uploaded_image or not age or not gender:
            flash('Please upload your photo and provide basic information.', 'danger')
            return redirect(url_for('enhanced_face.show_analysis_form'))
        
        # Process face analysis (simplified for demo)
        analysis_results = process_face_analysis(uploaded_image, age, gender, skin_concerns, treatment_history)
        
        # Track interaction with high-intent scoring
        interaction_data = {
            'has_image': True,
            'age': age,
            'gender': gender,
            'skin_concerns': skin_concerns,
            'treatment_history': bool(treatment_history),
            'budget_range': budget_range,
            'recommendations_count': len(analysis_results.get('recommendations', [])),
            'top_recommendation': analysis_results.get('recommendations', [{}])[0].get('procedure', '') if analysis_results.get('recommendations') else '',
            'confidence_score': analysis_results.get('confidence', 75),
            'urgency_level': determine_urgency_from_concerns(skin_concerns)
        }
        
        # Track the face analysis interaction (high-intent by default)
        interaction_id = track_user_interaction(
            interaction_type='face_analysis',
            data=interaction_data,
            source_page=request.path
        )
        
        # Face analysis is always high-intent, so prompt for contact info
        session_id = session.get('session_id')
        
        # If contact info provided, create lead immediately
        if contact_name and contact_phone:
            lead_data = {
                'name': contact_name,
                'phone': contact_phone,
                'email': contact_email,
                'city': contact_city
            }
            
            lead_id = create_lead_from_form(interaction_id, lead_data)
            
            if lead_id:
                flash('Thank you! Your face analysis is complete and a specialist will contact you soon with detailed recommendations.', 'success')
                return render_template('face_analysis/analysis_results_with_contact.html',
                                     analysis_results=analysis_results,
                                     lead_created=True,
                                     contact_name=contact_name,
                                     lead_id=lead_id)
            else:
                flash('Analysis completed successfully. There was an issue saving your contact information.', 'warning')
        
        # Show analysis results with contact form (high-intent prompt)
        return render_template('face_analysis/analysis_results_with_form.html',
                             analysis_results=analysis_results,
                             interaction_id=interaction_id,
                             show_urgent_contact=True)
    
    except Exception as e:
        logger.error(f"Error processing face analysis: {e}")
        flash('An error occurred while processing your analysis. Please try again.', 'danger')
        return redirect(url_for('enhanced_face.show_analysis_form'))

@enhanced_face_bp.route('/capture-analysis-lead', methods=['POST'])
def capture_analysis_lead():
    """Capture lead information after face analysis viewing."""
    try:
        interaction_id = request.form.get('interaction_id')
        contact_name = request.form.get('contact_name', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_city = request.form.get('contact_city', '').strip()
        preferred_date = request.form.get('preferred_date', '').strip()
        
        # Validate required fields
        if not interaction_id or not contact_name or not contact_phone:
            flash('Please provide your name and phone number to receive your detailed analysis.', 'danger')
            return redirect(request.referrer or url_for('enhanced_face.show_analysis_form'))
        
        # Create lead from interaction
        lead_data = {
            'name': contact_name,
            'phone': contact_phone,
            'email': contact_email,
            'city': contact_city,
            'preferred_date': preferred_date
        }
        
        lead_id = create_lead_from_form(int(interaction_id), lead_data)
        
        if lead_id:
            flash('Excellent! Your face analysis lead has been captured. Our specialists will contact you within 4 hours with your personalized treatment plan.', 'success')
            return render_template('face_analysis/lead_capture_success.html',
                                 contact_name=contact_name,
                                 lead_id=lead_id,
                                 preferred_date=preferred_date)
        else:
            flash('There was an issue processing your request. Please try again.', 'danger')
            return redirect(request.referrer or url_for('enhanced_face.show_analysis_form'))
    
    except Exception as e:
        logger.error(f"Error capturing face analysis lead: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('enhanced_face.show_analysis_form'))

def process_face_analysis(image_file, age, gender, skin_concerns, treatment_history):
    """Process face analysis and generate recommendations (simplified implementation)."""
    try:
        # Simulate AI analysis with realistic results
        age_int = int(age) if age.isdigit() else 25
        
        # Generate recommendations based on age, gender, and concerns
        recommendations = []
        confidence = 85
        
        # Age-based recommendations
        if age_int < 25:
            recommendations.extend([
                {
                    'procedure': 'Preventive Skincare Treatment',
                    'confidence': 90,
                    'description': 'Early intervention skincare to maintain youthful appearance',
                    'estimated_cost': '₹15,000 - ₹30,000',
                    'priority': 'high'
                }
            ])
        elif age_int < 35:
            recommendations.extend([
                {
                    'procedure': 'Botox/Fillers',
                    'confidence': 88,
                    'description': 'Non-surgical treatments for early signs of aging',
                    'estimated_cost': '₹25,000 - ₹50,000',
                    'priority': 'high'
                }
            ])
        else:
            recommendations.extend([
                {
                    'procedure': 'Facelift/Facial Rejuvenation',
                    'confidence': 85,
                    'description': 'Comprehensive facial rejuvenation for mature skin',
                    'estimated_cost': '₹1,50,000 - ₹3,00,000',
                    'priority': 'high'
                }
            ])
        
        # Concern-based recommendations
        if 'acne' in skin_concerns:
            recommendations.append({
                'procedure': 'Acne Treatment',
                'confidence': 92,
                'description': 'Professional acne treatment and scar reduction',
                'estimated_cost': '₹20,000 - ₹40,000',
                'priority': 'medium'
            })
        
        if 'wrinkles' in skin_concerns:
            recommendations.append({
                'procedure': 'Anti-Aging Treatment',
                'confidence': 89,
                'description': 'Wrinkle reduction and skin tightening procedures',
                'estimated_cost': '₹30,000 - ₹75,000',
                'priority': 'high'
            })
        
        if 'pigmentation' in skin_concerns:
            recommendations.append({
                'procedure': 'Pigmentation Treatment',
                'confidence': 87,
                'description': 'Laser and chemical treatments for even skin tone',
                'estimated_cost': '₹25,000 - ₹60,000',
                'priority': 'medium'
            })
        
        # Ensure we have at least one recommendation
        if not recommendations:
            recommendations = [{
                'procedure': 'Comprehensive Consultation',
                'confidence': 80,
                'description': 'Detailed assessment to determine optimal treatment plan',
                'estimated_cost': '₹2,000 - ₹5,000',
                'priority': 'high'
            }]
        
        # Sort by confidence and limit to top 3
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        recommendations = recommendations[:3]
        
        # Calculate overall analysis
        analysis_summary = {
            'skin_age': estimate_skin_age(age_int, skin_concerns),
            'treatment_urgency': determine_treatment_urgency(skin_concerns, age_int),
            'estimated_timeline': '2-6 months for optimal results',
            'maintenance_required': 'Annual touch-ups recommended'
        }
        
        return {
            'recommendations': recommendations,
            'confidence': confidence,
            'analysis_summary': analysis_summary,
            'next_steps': [
                'Schedule consultation with certified specialist',
                'Discuss treatment timeline and budget',
                'Begin with highest priority recommendations',
                'Plan maintenance schedule'
            ]
        }
        
    except Exception as e:
        logger.error(f"Error processing face analysis: {e}")
        return {
            'recommendations': [{
                'procedure': 'Consultation Required',
                'confidence': 50,
                'description': 'Please schedule a consultation for personalized recommendations',
                'estimated_cost': 'Consultation fee applies',
                'priority': 'high'
            }],
            'confidence': 50,
            'analysis_summary': {
                'skin_age': 'Assessment needed',
                'treatment_urgency': 'To be determined',
                'estimated_timeline': 'Varies by treatment',
                'maintenance_required': 'To be discussed'
            },
            'next_steps': ['Schedule consultation with our specialists']
        }

def estimate_skin_age(actual_age, concerns):
    """Estimate skin age based on actual age and concerns."""
    skin_age = actual_age
    
    # Add years based on concerns
    if 'wrinkles' in concerns:
        skin_age += 3
    if 'sun_damage' in concerns:
        skin_age += 2
    if 'pigmentation' in concerns:
        skin_age += 1
    
    # Subtract for good habits
    if 'acne' in concerns and actual_age > 25:
        skin_age -= 1  # Often indicates active skin
    
    return f"{skin_age} years (actual: {actual_age})"

def determine_treatment_urgency(concerns, age):
    """Determine treatment urgency based on concerns and age."""
    if 'acne' in concerns or 'severe_wrinkles' in concerns:
        return 'High - Immediate treatment recommended'
    elif len(concerns) > 2 or age > 40:
        return 'Medium - Treatment within 3-6 months'
    else:
        return 'Low - Preventive care recommended'

def determine_urgency_from_concerns(concerns):
    """Determine urgency level from skin concerns."""
    if not concerns:
        return 'medium'
    
    high_urgency = ['acne', 'severe_wrinkles', 'sun_damage']
    if any(concern in high_urgency for concern in concerns):
        return 'high'
    elif len(concerns) > 2:
        return 'medium'
    else:
        return 'low'