"""
Enhanced Cost Calculator System with Lead Capture
Converts cost calculation requests into qualified leads
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
enhanced_cost_bp = Blueprint('enhanced_cost', __name__, url_prefix='/enhanced-cost')

@enhanced_cost_bp.route('/calculator', methods=['GET'])
def show_cost_calculator():
    """Display the enhanced cost calculator with lead capture."""
    # Get procedures for dropdown
    procedures = get_available_procedures()
    return render_template('cost_calculator/enhanced_calculator.html', procedures=procedures)

@enhanced_cost_bp.route('/calculate-cost', methods=['POST'])
def calculate_treatment_cost():
    """Process cost calculation with integrated lead capture."""
    try:
        # Extract form data
        selected_procedure = request.form.get('selected_procedure', '').strip()
        city = request.form.get('city', '').strip()
        budget_range = request.form.get('budget_range', '').strip()
        urgency = request.form.get('urgency', '').strip()
        additional_procedures = request.form.getlist('additional_procedures')
        
        # Contact information (progressive capture)
        contact_name = request.form.get('contact_name', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        get_detailed_quote = request.form.get('get_detailed_quote') == 'true'
        
        # Validate required fields
        if not selected_procedure or not city:
            flash('Please select a procedure and your city to continue.', 'danger')
            return redirect(url_for('enhanced_cost.show_cost_calculator'))
        
        # Calculate costs based on inputs
        cost_results = calculate_procedure_costs(selected_procedure, city, budget_range, additional_procedures)
        
        # Track interaction with cost intent scoring
        interaction_data = {
            'selected_procedure': selected_procedure,
            'city': city,
            'budget_range': budget_range,
            'urgency': urgency,
            'additional_procedures': additional_procedures,
            'total_procedures': len(additional_procedures) + 1,
            'estimated_cost': cost_results.get('estimated_cost', 0),
            'cost_range': cost_results.get('cost_range', ''),
            'wants_detailed_quote': get_detailed_quote,
            'price_intent_score': calculate_price_intent_score(budget_range, urgency, get_detailed_quote)
        }
        
        # Track the cost calculator interaction
        interaction_id = track_user_interaction(
            interaction_type='cost_calculator',
            data=interaction_data,
            source_page=request.path
        )
        
        # Check if we should prompt for contact information
        session_id = session.get('session_id')
        should_capture_lead = should_show_contact_form(session_id, 'cost_calculator', interaction_data)
        
        # If detailed quote requested or contact info provided, create lead
        if get_detailed_quote or (contact_name and contact_phone):
            if contact_name and contact_phone:
                lead_data = {
                    'name': contact_name,
                    'phone': contact_phone,
                    'email': contact_email,
                    'city': city
                }
                
                lead_id = create_lead_from_form(interaction_id, lead_data)
                
                if lead_id:
                    flash('Thank you! Your detailed cost estimate will be prepared and sent to you within 2 hours.', 'success')
                    return render_template('cost_calculator/results_with_quote.html',
                                         cost_results=cost_results,
                                         lead_created=True,
                                         contact_name=contact_name,
                                         selected_procedure=selected_procedure)
                else:
                    flash('Cost estimate generated. There was an issue saving your quote request.', 'warning')
            else:
                # Show detailed quote form
                return render_template('cost_calculator/results_with_form.html',
                                     cost_results=cost_results,
                                     interaction_id=interaction_id,
                                     selected_procedure=selected_procedure,
                                     show_quote_form=True)
        
        # Show basic cost results
        return render_template('cost_calculator/basic_results.html',
                             cost_results=cost_results,
                             interaction_id=interaction_id,
                             selected_procedure=selected_procedure)
    
    except Exception as e:
        logger.error(f"Error calculating treatment cost: {e}")
        flash('An error occurred while calculating costs. Please try again.', 'danger')
        return redirect(url_for('enhanced_cost.show_cost_calculator'))

@enhanced_cost_bp.route('/request-detailed-quote', methods=['POST'])
def request_detailed_quote():
    """Capture lead for detailed cost quote."""
    try:
        interaction_id = request.form.get('interaction_id')
        contact_name = request.form.get('contact_name', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        preferred_date = request.form.get('preferred_date', '').strip()
        budget_preference = request.form.get('budget_preference', '').strip()
        
        # Validate required fields
        if not interaction_id or not contact_name or not contact_phone:
            flash('Please provide your name and phone number to receive a detailed quote.', 'danger')
            return redirect(request.referrer or url_for('enhanced_cost.show_cost_calculator'))
        
        # Create lead from interaction
        lead_data = {
            'name': contact_name,
            'phone': contact_phone,
            'email': contact_email,
            'city': request.form.get('city', ''),
            'preferred_date': preferred_date,
            'budget_preference': budget_preference
        }
        
        lead_id = create_lead_from_form(int(interaction_id), lead_data)
        
        if lead_id:
            flash('Perfect! Your detailed quote request has been submitted. Our pricing specialists will contact you within 2 hours with a comprehensive cost breakdown.', 'success')
            return render_template('cost_calculator/quote_request_success.html',
                                 contact_name=contact_name,
                                 lead_id=lead_id,
                                 preferred_date=preferred_date)
        else:
            flash('There was an issue processing your quote request. Please try again.', 'danger')
            return redirect(request.referrer or url_for('enhanced_cost.show_cost_calculator'))
    
    except Exception as e:
        logger.error(f"Error requesting detailed quote: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('enhanced_cost.show_cost_calculator'))

def get_available_procedures():
    """Get list of available procedures for the calculator."""
    try:
        result = db.session.execute(text("""
            SELECT DISTINCT procedure_name, COUNT(*) as availability
            FROM procedures 
            WHERE procedure_name IS NOT NULL AND procedure_name != ''
            GROUP BY procedure_name
            ORDER BY availability DESC, procedure_name
            LIMIT 50
        """)).fetchall()
        
        procedures = [{'name': row[0], 'availability': row[1]} for row in result]
        
        # Add some default procedures if none found
        if not procedures:
            procedures = [
                {'name': 'Rhinoplasty', 'availability': 1},
                {'name': 'Breast Augmentation', 'availability': 1},
                {'name': 'Liposuction', 'availability': 1},
                {'name': 'Facelift', 'availability': 1},
                {'name': 'Tummy Tuck', 'availability': 1}
            ]
        
        return procedures
        
    except Exception as e:
        logger.error(f"Error getting procedures: {e}")
        return [
            {'name': 'Rhinoplasty', 'availability': 1},
            {'name': 'Breast Augmentation', 'availability': 1},
            {'name': 'Liposuction', 'availability': 1}
        ]

def calculate_procedure_costs(procedure, city, budget_range, additional_procedures):
    """Calculate estimated costs for procedures."""
    try:
        # Base cost estimation (simplified)
        base_costs = {
            'Rhinoplasty': {'min': 80000, 'max': 150000},
            'Breast Augmentation': {'min': 120000, 'max': 250000},
            'Liposuction': {'min': 60000, 'max': 120000},
            'Facelift': {'min': 150000, 'max': 300000},
            'Tummy Tuck': {'min': 100000, 'max': 200000},
            'Botox': {'min': 15000, 'max': 30000},
            'Fillers': {'min': 25000, 'max': 50000}
        }
        
        # City multipliers
        city_multipliers = {
            'Mumbai': 1.3,
            'Delhi': 1.25,
            'Bangalore': 1.2,
            'Chennai': 1.1,
            'Hyderabad': 1.1,
            'Pune': 1.15,
            'Kolkata': 1.0
        }
        
        # Get base cost
        base_cost = base_costs.get(procedure, {'min': 50000, 'max': 100000})
        city_multiplier = city_multipliers.get(city, 1.0)
        
        # Calculate adjusted costs
        min_cost = int(base_cost['min'] * city_multiplier)
        max_cost = int(base_cost['max'] * city_multiplier)
        estimated_cost = int((min_cost + max_cost) / 2)
        
        # Add additional procedures
        additional_cost = 0
        additional_details = []
        
        for add_proc in additional_procedures:
            if add_proc in base_costs:
                add_cost = base_costs[add_proc]
                add_min = int(add_cost['min'] * city_multiplier * 0.8)  # Discount for multiple
                add_max = int(add_cost['max'] * city_multiplier * 0.8)
                additional_cost += (add_min + add_max) / 2
                additional_details.append({
                    'procedure': add_proc,
                    'cost_range': f"₹{add_min:,} - ₹{add_max:,}",
                    'estimated': int((add_min + add_max) / 2)
                })
        
        total_estimated = estimated_cost + additional_cost
        
        # Generate cost breakdown
        cost_breakdown = {
            'consultation': 2000,
            'procedure': estimated_cost,
            'anesthesia': int(estimated_cost * 0.1),
            'facility': int(estimated_cost * 0.15),
            'follow_up': 5000
        }
        
        # Budget analysis
        budget_analysis = analyze_budget_fit(budget_range, total_estimated)
        
        return {
            'procedure': procedure,
            'city': city,
            'min_cost': min_cost,
            'max_cost': max_cost,
            'estimated_cost': estimated_cost,
            'total_estimated': int(total_estimated),
            'cost_range': f"₹{min_cost:,} - ₹{max_cost:,}",
            'total_range': f"₹{int(min_cost + additional_cost * 0.8):,} - ₹{int(max_cost + additional_cost * 1.2):,}",
            'additional_procedures': additional_details,
            'cost_breakdown': cost_breakdown,
            'budget_analysis': budget_analysis,
            'financing_options': get_financing_options(total_estimated),
            'savings_tips': get_savings_tips(),
            'next_steps': [
                'Schedule consultation to confirm pricing',
                'Discuss payment plans and financing',
                'Compare multiple surgeon quotes',
                'Plan treatment timeline'
            ]
        }
        
    except Exception as e:
        logger.error(f"Error calculating costs: {e}")
        return {
            'procedure': procedure,
            'city': city,
            'estimated_cost': 75000,
            'cost_range': '₹50,000 - ₹1,00,000',
            'total_estimated': 75000,
            'budget_analysis': 'Please consult for accurate pricing',
            'next_steps': ['Schedule consultation for detailed quote']
        }

def calculate_price_intent_score(budget_range, urgency, wants_quote):
    """Calculate lead score based on price-related factors."""
    score = 70  # Base score for cost calculator usage
    
    # Budget range scoring
    if budget_range:
        if 'high' in budget_range.lower() or '200000' in budget_range:
            score += 20
        elif 'medium' in budget_range.lower() or '100000' in budget_range:
            score += 10
    
    # Urgency scoring
    if urgency == 'immediate':
        score += 25
    elif urgency == 'within_month':
        score += 15
    elif urgency == 'within_3months':
        score += 10
    
    # Quote request is high intent
    if wants_quote:
        score += 15
    
    return min(score, 100)

def analyze_budget_fit(budget_range, estimated_cost):
    """Analyze how well the procedure fits the budget."""
    if not budget_range:
        return "Budget assessment needed during consultation"
    
    budget_ranges = {
        'under_50000': 50000,
        '50000_100000': 100000,
        '100000_200000': 200000,
        '200000_plus': 300000
    }
    
    max_budget = budget_ranges.get(budget_range, 100000)
    
    if estimated_cost <= max_budget * 0.8:
        return "Excellent fit within your budget with room for upgrades"
    elif estimated_cost <= max_budget:
        return "Good fit within your stated budget range"
    elif estimated_cost <= max_budget * 1.2:
        return "Slightly above budget - financing options available"
    else:
        return "Above current budget - consider alternative procedures or financing"

def get_financing_options(cost):
    """Get financing options based on cost."""
    options = []
    
    if cost > 50000:
        monthly_12 = int(cost / 12)
        monthly_24 = int(cost / 24)
        
        options = [
            f"12-month plan: ₹{monthly_12:,}/month",
            f"24-month plan: ₹{monthly_24:,}/month",
            "Medical loan partnerships available",
            "Credit card EMI options",
            "Insurance coverage evaluation"
        ]
    
    return options

def get_savings_tips():
    """Get cost-saving tips."""
    return [
        "Book multiple procedures together for package discounts",
        "Consider off-peak season timing",
        "Look for promotional offers",
        "Compare multiple surgeon quotes",
        "Check insurance coverage options"
    ]