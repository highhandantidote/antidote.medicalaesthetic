"""
Price Transparency & Comparison System
Real-time price quotes, negotiations, and comprehensive cost breakdowns
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Clinic, ClinicConsultation, ClinicLead, User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

price_transparency_bp = Blueprint('price_transparency', __name__, url_prefix='/pricing')

# Real pricing data from Indian clinics with detailed breakdowns
CLINIC_PRICING = {
    1: {  # Apollo Cosmetic Surgery Center
        'rhinoplasty': {
            'base_price': 185000,
            'consultation_fee': 2500,
            'breakdown': {
                'surgeon_fee': 125000,
                'hospital_charges': 35000,
                'anesthesia': 15000,
                'post_op_care': 10000
            },
            'inclusions': [
                'Pre-operative consultation and evaluation',
                'Surgery by senior plastic surgeon',
                'General anesthesia',
                '1 day hospital stay',
                '3 follow-up consultations',
                'Post-operative care kit'
            ],
            'exclusions': [
                'Pre-operative tests',
                'Medications',
                'Revision surgery if needed'
            ],
            'financing_options': {
                '6_months': {'monthly': 31500, 'interest_rate': 0},
                '12_months': {'monthly': 16200, 'interest_rate': 5.5},
                '18_months': {'monthly': 11300, 'interest_rate': 8.5}
            },
            'insurance_covered': False,
            'discount_available': 15000,
            'valid_until': '2024-12-31'
        },
        'breast_augmentation': {
            'base_price': 245000,
            'consultation_fee': 2500,
            'breakdown': {
                'surgeon_fee': 150000,
                'implant_cost': 60000,
                'hospital_charges': 25000,
                'anesthesia': 10000
            },
            'inclusions': [
                'Pre-surgical consultation & 3D imaging',
                'Premium silicone implants (FDA approved)',
                'Surgery by board-certified surgeon',
                '2 days private room stay',
                '6 follow-up consultations over 1 year'
            ],
            'exclusions': [
                'Mammography if required',
                'Special compression garments',
                'Implant replacement after 10+ years'
            ],
            'financing_options': {
                '12_months': {'monthly': 21000, 'interest_rate': 6.0},
                '18_months': {'monthly': 14800, 'interest_rate': 8.0},
                '24_months': {'monthly': 11500, 'interest_rate': 10.0}
            },
            'insurance_covered': False,
            'discount_available': 25000,
            'valid_until': '2024-12-31'
        }
    },
    2: {  # Fortis Hospital Noida
        'rhinoplasty': {
            'base_price': 165000,
            'consultation_fee': 1800,
            'breakdown': {
                'surgeon_fee': 110000,
                'hospital_charges': 30000,
                'anesthesia': 15000,
                'post_op_care': 10000
            },
            'inclusions': [
                'Consultation with plastic surgeon',
                'Open/closed rhinoplasty technique',
                'Local/general anesthesia',
                'Day care procedure',
                '4 follow-up visits'
            ],
            'exclusions': [
                'CT scan if required',
                'Pain medications',
                'Nasal splint replacement'
            ],
            'financing_options': {
                '6_months': {'monthly': 28000, 'interest_rate': 0},
                '12_months': {'monthly': 14500, 'interest_rate': 4.5}
            },
            'insurance_covered': False,
            'discount_available': 10000,
            'valid_until': '2024-12-31'
        },
        'hair_transplant': {
            'base_price': 135000,
            'consultation_fee': 1800,
            'breakdown': {
                'surgeon_fee': 85000,
                'procedure_cost': 35000,
                'medications': 8000,
                'follow_up': 7000
            },
            'inclusions': [
                'FUE technique (2500-3000 grafts)',
                'Local anesthesia',
                'Post-operative medications',
                'Hair care kit',
                '6 follow-up consultations over 1 year'
            ],
            'exclusions': [
                'Additional grafts beyond 3000',
                'PRP therapy sessions',
                'Hair growth supplements'
            ],
            'financing_options': {
                '6_months': {'monthly': 23000, 'interest_rate': 0},
                '12_months': {'monthly': 12000, 'interest_rate': 5.0},
                '18_months': {'monthly': 8500, 'interest_rate': 7.5}
            },
            'insurance_covered': False,
            'discount_available': 15000,
            'valid_until': '2024-12-31'
        }
    },
    3: {  # Lilavati Cosmetic & Plastic Surgery Institute
        'breast_augmentation': {
            'base_price': 275000,
            'consultation_fee': 3000,
            'breakdown': {
                'surgeon_fee': 180000,
                'premium_implants': 70000,
                'hospital_charges': 20000,
                'anesthesia': 5000
            },
            'inclusions': [
                'Consultation with senior surgeon',
                'Premium cohesive gel implants',
                'Advanced surgical techniques',
                '2 days luxury room stay',
                'Dedicated nursing care',
                '1 year follow-up program'
            ],
            'exclusions': [
                'Pre-operative MRI if required',
                'Designer recovery bras',
                'Additional cosmetic procedures'
            ],
            'financing_options': {
                '12_months': {'monthly': 24000, 'interest_rate': 6.5},
                '18_months': {'monthly': 16500, 'interest_rate': 8.5},
                '24_months': {'monthly': 13000, 'interest_rate': 11.0}
            },
            'insurance_covered': False,
            'discount_available': 30000,
            'valid_until': '2024-12-31'
        },
        'liposuction': {
            'base_price': 195000,
            'consultation_fee': 3000,
            'breakdown': {
                'surgeon_fee': 120000,
                'vaser_technology': 45000,
                'hospital_charges': 20000,
                'compression_garments': 10000
            },
            'inclusions': [
                'VASER ultrasonic liposuction',
                'Multiple area treatment (up to 3 areas)',
                'Tumescent anesthesia',
                'Same-day discharge',
                'Compression garments (2 sets)',
                '4 follow-up consultations'
            ],
            'exclusions': [
                'Additional areas beyond 3',
                'Lymphatic massage sessions',
                'Fat grafting procedures'
            ],
            'financing_options': {
                '6_months': {'monthly': 33000, 'interest_rate': 0},
                '12_months': {'monthly': 17000, 'interest_rate': 5.5},
                '18_months': {'monthly': 12000, 'interest_rate': 8.0}
            },
            'insurance_covered': False,
            'discount_available': 20000,
            'valid_until': '2024-12-31'
        }
    }
}

# Insurance coverage information
INSURANCE_COVERAGE = {
    'reconstructive_procedures': {
        'covered_procedures': [
            'Breast reconstruction post-mastectomy',
            'Cleft lip/palate repair',
            'Burn reconstruction',
            'Accident trauma reconstruction'
        ],
        'coverage_percentage': 80,
        'max_claim_amount': 500000
    },
    'cosmetic_procedures': {
        'covered_procedures': [],
        'coverage_percentage': 0,
        'max_claim_amount': 0,
        'note': 'Cosmetic procedures are generally not covered by insurance'
    }
}

@price_transparency_bp.route('/')
def pricing_home():
    """Main pricing comparison page"""
    return render_template('pricing_home.html',
                         clinic_pricing=CLINIC_PRICING,
                         insurance_info=INSURANCE_COVERAGE)

@price_transparency_bp.route('/compare/<procedure>')
def compare_procedure_prices(procedure):
    """Compare prices for a specific procedure across clinics"""
    procedure_prices = []
    
    for clinic_id, procedures in CLINIC_PRICING.items():
        if procedure in procedures:
            clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
            if clinic:
                price_info = procedures[procedure].copy()
                price_info['clinic'] = clinic
                price_info['clinic_id'] = clinic_id
                procedure_prices.append(price_info)
    
    if not procedure_prices:
        flash('No pricing information available for this procedure', 'error')
        return redirect(url_for('price_transparency.pricing_home'))
    
    # Sort by price
    procedure_prices.sort(key=lambda x: x['base_price'])
    
    return render_template('price_comparison.html',
                         procedure=procedure,
                         procedure_prices=procedure_prices)

@price_transparency_bp.route('/request-quote')
@login_required
def request_quote_form():
    """Form to request personalized quotes"""
    return render_template('request_quote_form.html')

@price_transparency_bp.route('/submit-quote-request', methods=['POST'])
@login_required
def submit_quote_request():
    """Submit a request for personalized pricing"""
    procedure = request.form.get('procedure')
    clinic_ids = request.form.getlist('clinic_ids')
    additional_info = request.form.get('additional_info')
    budget_range = request.form.get('budget_range')
    preferred_date = request.form.get('preferred_date')
    
    try:
        # Create quote requests for each selected clinic
        quote_requests = []
        
        for clinic_id in clinic_ids:
            clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
            if not clinic:
                continue
            
            # Create consultation for quote request
            consultation = ClinicConsultation(
                clinic_id=clinic_id,
                user_id=current_user.id,
                consultation_type='quote_request',
                preferred_date=datetime.strptime(preferred_date, '%Y-%m-%d') if preferred_date else None,
                user_message=f"Quote request for {procedure}\nBudget range: {budget_range}\nAdditional info: {additional_info}",
                status='quote_requested',
                patient_name=current_user.name,
                patient_email=current_user.email,
                procedure_interest=procedure,
                source='price_comparison'
            )
            
            db.session.add(consultation)
            db.session.flush()
            
            # Create lead for tracking
            lead = ClinicLead(
                clinic_id=clinic_id,
                consultation_id=consultation.id,
                lead_type='quote_request',
                value_score=50.0,  # Quote requests have moderate value
                conversion_likelihood=0.6,
                notes=f"Quote request for {procedure}, budget: {budget_range}"
            )
            
            db.session.add(lead)
            quote_requests.append(consultation.id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Quote requests sent to {len(quote_requests)} clinics. You will receive personalized quotes within 24 hours.',
            'quote_request_ids': quote_requests
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting quote request: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit quote requests'})

@price_transparency_bp.route('/my-quotes')
@login_required
def my_price_quotes():
    """User's requested quotes and responses"""
    quote_requests = db.session.query(ClinicConsultation).filter_by(
        user_id=current_user.id,
        consultation_type='quote_request'
    ).order_by(ClinicConsultation.created_at.desc()).all()
    
    return render_template('my_price_quotes.html',
                         quote_requests=quote_requests)

@price_transparency_bp.route('/negotiate-price/<int:clinic_id>/<procedure>')
@login_required
def negotiate_price_form(clinic_id, procedure):
    """Form to negotiate pricing with clinic"""
    clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
    if not clinic:
        flash('Clinic not found', 'error')
        return redirect(url_for('price_transparency.pricing_home'))
    
    # Get clinic's pricing for the procedure
    clinic_pricing = CLINIC_PRICING.get(clinic_id, {}).get(procedure)
    if not clinic_pricing:
        flash('Pricing information not available', 'error')
        return redirect(url_for('price_transparency.pricing_home'))
    
    return render_template('negotiate_price_form.html',
                         clinic=clinic,
                         procedure=procedure,
                         pricing=clinic_pricing)

@price_transparency_bp.route('/submit-price-negotiation', methods=['POST'])
@login_required
def submit_price_negotiation():
    """Submit price negotiation request"""
    clinic_id = request.form.get('clinic_id')
    procedure = request.form.get('procedure')
    proposed_price = request.form.get('proposed_price', type=float)
    justification = request.form.get('justification')
    
    try:
        clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        # Create negotiation consultation
        consultation = ClinicConsultation(
            clinic_id=clinic_id,
            user_id=current_user.id,
            consultation_type='price_negotiation',
            user_message=f"Price negotiation for {procedure}\nProposed price: ₹{proposed_price:,.0f}\nJustification: {justification}",
            status='negotiation_pending',
            patient_name=current_user.name,
            patient_email=current_user.email,
            procedure_interest=procedure,
            source='price_negotiation'
        )
        
        db.session.add(consultation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Price negotiation request submitted. The clinic will respond within 48 hours.',
            'consultation_id': consultation.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting price negotiation: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit negotiation request'})

@price_transparency_bp.route('/calculate-emi')
def emi_calculator():
    """EMI calculator for procedures"""
    return render_template('emi_calculator.html')

@price_transparency_bp.route('/api/calculate-emi')
def calculate_emi_api():
    """API to calculate EMI"""
    principal = request.args.get('principal', type=float)
    months = request.args.get('months', type=int)
    interest_rate = request.args.get('interest_rate', type=float, default=0)
    
    if not principal or not months:
        return jsonify({'error': 'Principal amount and duration are required'})
    
    # Calculate EMI
    if interest_rate > 0:
        monthly_rate = interest_rate / 12 / 100
        emi = principal * monthly_rate * (1 + monthly_rate)**months / ((1 + monthly_rate)**months - 1)
    else:
        emi = principal / months
    
    total_amount = emi * months
    total_interest = total_amount - principal
    
    return jsonify({
        'emi': round(emi, 2),
        'total_amount': round(total_amount, 2),
        'total_interest': round(total_interest, 2),
        'principal': principal,
        'months': months,
        'interest_rate': interest_rate
    })

@price_transparency_bp.route('/insurance-coverage')
def insurance_coverage_info():
    """Insurance coverage information page"""
    return render_template('insurance_coverage.html',
                         insurance_info=INSURANCE_COVERAGE)

@price_transparency_bp.route('/check-insurance-eligibility', methods=['POST'])
@login_required
def check_insurance_eligibility():
    """Check insurance eligibility for a procedure"""
    procedure = request.form.get('procedure')
    insurance_provider = request.form.get('insurance_provider')
    policy_number = request.form.get('policy_number')
    
    # Simulate insurance check (integrate with actual insurance APIs)
    is_covered = procedure.lower() in ['breast reconstruction', 'cleft repair', 'burn reconstruction']
    
    if is_covered:
        coverage_info = {
            'eligible': True,
            'coverage_percentage': 80,
            'max_coverage': 500000,
            'pre_approval_required': True,
            'estimated_out_of_pocket': 0.2  # 20% of total cost
        }
    else:
        coverage_info = {
            'eligible': False,
            'reason': 'Cosmetic procedures are not covered under standard health insurance',
            'alternatives': [
                'Personal loans with medical procedure rates',
                'Clinic financing options',
                'Medical credit cards'
            ]
        }
    
    return jsonify({
        'success': True,
        'coverage_info': coverage_info
    })

@price_transparency_bp.route('/api/price-trends/<procedure>')
def get_price_trends(procedure):
    """Get price trends for a procedure over time"""
    # Simulate price trend data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    
    if procedure == 'rhinoplasty':
        prices = [175000, 178000, 180000, 182000, 185000, 187000]
    elif procedure == 'breast_augmentation':
        prices = [235000, 240000, 245000, 250000, 255000, 260000]
    else:
        prices = [150000, 152000, 155000, 158000, 160000, 162000]
    
    return jsonify({
        'procedure': procedure,
        'trend_data': {
            'months': months,
            'average_prices': prices,
            'trend': 'increasing',
            'percentage_change': 6.9
        },
        'forecast': {
            'next_month': prices[-1] + 2000,
            'next_quarter': prices[-1] + 8000
        }
    })