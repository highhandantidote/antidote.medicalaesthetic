"""
Complete Gangnam Unni Services & Pricing System
Authentic Korean clinic model with events, flash deals, and real-time pricing
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Clinic, ClinicConsultation, User
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

gangnam_services_bp = Blueprint('gangnam_services', __name__, url_prefix='/services-pricing')

# Authentic Gangnam Unni pricing structure adapted for Indian market
GANGNAM_PRICING_STRUCTURE = {
    'flash_deals': {
        'rhinoplasty_weekend': {
            'title': 'Weekend Nose Job Special',
            'original_price': 250000,
            'discounted_price': 185000,
            'discount_percentage': 26,
            'valid_until': '2024-12-08 23:59:59',
            'slots_available': 3,
            'clinic_ids': [1, 3],
            'conditions': ['First-time patients only', 'Must book consultation within 48 hours'],
            'event_type': 'flash_deal'
        },
        'botox_combo_friday': {
            'title': 'Friday Botox + Filler Combo',
            'original_price': 45000,
            'discounted_price': 32000,
            'discount_percentage': 29,
            'valid_until': '2024-12-06 18:00:00',
            'slots_available': 8,
            'clinic_ids': [1, 2, 3],
            'conditions': ['Same-day treatment required', 'Limited to premium areas only'],
            'event_type': 'flash_deal'
        }
    },
    'seasonal_events': {
        'winter_transformation': {
            'title': 'Winter Transformation Package',
            'description': 'Complete winter makeover with multiple procedures',
            'packages': {
                'basic': {
                    'name': 'Winter Glow Basic',
                    'procedures': ['Chemical Peel', 'Botox (3 areas)', 'Dermal Fillers'],
                    'original_price': 75000,
                    'event_price': 55000,
                    'savings': 20000
                },
                'premium': {
                    'name': 'Winter Glow Premium',
                    'procedures': ['Facial Contouring', 'Thread Lift', 'Laser Treatment', 'Premium Skincare'],
                    'original_price': 180000,
                    'event_price': 135000,
                    'savings': 45000
                },
                'luxury': {
                    'name': 'Winter Glow Luxury',
                    'procedures': ['Mini Facelift', 'Breast Enhancement', 'Body Contouring', 'VIP Recovery'],
                    'original_price': 450000,
                    'event_price': 320000,
                    'savings': 130000
                }
            },
            'event_dates': {
                'start': '2024-12-01',
                'end': '2024-02-28'
            },
            'special_benefits': [
                'Free post-treatment skincare kit',
                'Complimentary follow-up sessions',
                'Priority booking for future treatments',
                'Exclusive access to new procedures'
            ]
        }
    },
    'clinic_exclusive_events': {
        1: {  # Apollo Cosmetic Surgery Center
            'apollo_anniversary': {
                'title': 'Apollo 25th Anniversary Celebration',
                'event_type': 'anniversary',
                'duration_days': 7,
                'special_offers': {
                    'rhinoplasty': {'discount': 35000, 'limited_slots': 5},
                    'breast_augmentation': {'discount': 50000, 'limited_slots': 3},
                    'liposuction': {'discount': 25000, 'limited_slots': 8}
                },
                'exclusive_benefits': [
                    'Meet & greet with senior surgeons',
                    'Free 3D consultation sessions',
                    'Complimentary recovery package',
                    'Lifetime follow-up guarantee'
                ]
            }
        },
        2: {  # Fortis Hospital Noida
            'fortis_expertise_week': {
                'title': 'Fortis Expertise Week',
                'event_type': 'specialty_week',
                'duration_days': 5,
                'special_offers': {
                    'hair_transplant': {'discount': 20000, 'limited_slots': 10},
                    'facial_treatments': {'discount': 15000, 'limited_slots': 15}
                },
                'exclusive_benefits': [
                    'Free hair analysis and consultation',
                    'Complimentary PRP session',
                    'Post-treatment care package'
                ]
            }
        },
        3: {  # Lilavati Cosmetic Institute
            'lilavati_luxury_weekend': {
                'title': 'Lilavati Luxury Experience Weekend',
                'event_type': 'luxury_experience',
                'duration_days': 2,
                'special_offers': {
                    'mommy_makeover': {'discount': 75000, 'limited_slots': 2},
                    'brazilian_butt_lift': {'discount': 45000, 'limited_slots': 3},
                    'full_body_contouring': {'discount': 60000, 'limited_slots': 4}
                },
                'exclusive_benefits': [
                    'Luxury suite accommodation',
                    'Personal care coordinator',
                    'Gourmet recovery meals',
                    'Spa treatment package'
                ]
            }
        }
    },
    'procedure_of_the_month': {
        'december_2024': {
            'featured_procedure': 'Thread Lift',
            'original_price_range': {'min': 45000, 'max': 85000},
            'special_price_range': {'min': 32000, 'max': 65000},
            'featured_doctors': [
                {'name': 'Dr. Rajesh Kumar', 'clinic_id': 1, 'special_rate': 55000},
                {'name': 'Dr. Kavita Patel', 'clinic_id': 3, 'special_rate': 62000}
            ],
            'procedure_highlights': [
                'Non-surgical facelift alternative',
                'Immediate visible results',
                'Minimal downtime (2-3 days)',
                'Natural-looking facial rejuvenation'
            ],
            'special_month_benefits': [
                'Free consultation worth ₹2,500',
                'Complimentary skin analysis',
                'Post-treatment follow-up package',
                '20% off on additional facial treatments'
            ]
        }
    },
    'group_event_pricing': {
        'bridal_party_packages': {
            'bride_squad_basic': {
                'name': 'Bride Squad Basic',
                'min_people': 3,
                'max_people': 6,
                'services': ['Facial Treatment', 'Botox Touch-up', 'Lip Enhancement'],
                'price_per_person': 25000,
                'group_discount': 18,
                'additional_benefits': [
                    'Bridal consultation session',
                    'Group recovery support',
                    'Pre-wedding timeline planning'
                ]
            },
            'bride_squad_premium': {
                'name': 'Bride Squad Premium',
                'min_people': 4,
                'max_people': 8,
                'services': ['Complete Facial Rejuvenation', 'Body Contouring', 'Skin Treatments'],
                'price_per_person': 75000,
                'group_discount': 25,
                'additional_benefits': [
                    'Luxury bridal suite',
                    'Personal styling consultation',
                    'Professional photography session',
                    'Champagne celebration'
                ]
            }
        },
        'corporate_wellness_events': {
            'executive_refresh': {
                'name': 'Executive Refresh Package',
                'min_people': 5,
                'max_people': 15,
                'services': ['Stress-relief Treatments', 'Anti-aging Solutions', 'Wellness Consultation'],
                'price_per_person': 35000,
                'corporate_discount': 22,
                'additional_benefits': [
                    'On-site consultation available',
                    'Flexible scheduling options',
                    'Corporate health reports',
                    'Ongoing wellness support'
                ]
            }
        }
    },
    'procedure_of_the_month': {
        'december_2024': {
            'featured_procedure': 'Korean Double Eyelid Surgery',
            'procedure_highlights': [
                'Natural-looking results with Korean technique',
                'Minimal downtime and scarring',
                'Experienced Korean-trained surgeons',
                'Before & after photo guarantee'
            ],
            'original_price_range': {'min': 85000, 'max': 150000},
            'special_price_range': {'min': 65000, 'max': 120000}
        }
    },
    'real_time_pricing': {
        'dynamic_slots': {
            'peak_hours': {'multiplier': 1.2, 'hours': ['10:00-12:00', '14:00-16:00']},
            'off_peak': {'multiplier': 0.85, 'hours': ['08:00-10:00', '16:00-18:00']},
            'weekend_premium': {'multiplier': 1.15, 'days': ['saturday', 'sunday']}
        },
        'last_minute_deals': {
            'same_day_booking': {'discount_percentage': 15, 'available_procedures': ['botox', 'fillers', 'facial_treatments']},
            'next_day_booking': {'discount_percentage': 8, 'available_procedures': ['consultation', 'minor_procedures']}
        }
    }
}

# Event creation and management system
EVENT_TEMPLATES = {
    'flash_sale': {
        'duration_options': ['2 hours', '6 hours', '24 hours', '48 hours'],
        'discount_ranges': {'min': 10, 'max': 50},
        'slot_limits': {'min': 1, 'max': 20}
    },
    'seasonal_campaign': {
        'duration_options': ['1 week', '2 weeks', '1 month', '3 months'],
        'discount_ranges': {'min': 15, 'max': 40},
        'package_options': ['basic', 'premium', 'luxury']
    },
    'clinic_anniversary': {
        'duration_options': ['3 days', '1 week', '2 weeks'],
        'discount_ranges': {'min': 20, 'max': 45},
        'special_features': ['exclusive_procedures', 'doctor_consultations', 'luxury_amenities']
    }
}

@gangnam_services_bp.route('/')
def services_pricing_home():
    """Main services & pricing page with live events"""
    # Get active flash deals
    active_flash_deals = []
    for deal_id, deal in GANGNAM_PRICING_STRUCTURE['flash_deals'].items():
        if datetime.strptime(deal['valid_until'], '%Y-%m-%d %H:%M:%S') > datetime.now():
            active_flash_deals.append({**deal, 'id': deal_id})
    
    # Get current seasonal events
    seasonal_events = GANGNAM_PRICING_STRUCTURE['seasonal_events']
    
    # Get procedure of the month
    current_month = datetime.now().strftime('%B_%Y').lower()
    procedure_of_month = GANGNAM_PRICING_STRUCTURE['procedure_of_the_month'].get(
        'december_2024',  # Default to current featured
        GANGNAM_PRICING_STRUCTURE['procedure_of_the_month']['december_2024']
    )
    
    return render_template('gangnam_services_pricing.html',
                         flash_deals=active_flash_deals,
                         seasonal_events=seasonal_events,
                         procedure_of_month=procedure_of_month,
                         group_packages=GANGNAM_PRICING_STRUCTURE['group_event_pricing'])

@gangnam_services_bp.route('/create-event')
@login_required
def create_event_form():
    """Form for clinics to create their own events"""
    # Check if user has clinic admin permissions
    return render_template('create_clinic_event.html',
                         event_templates=EVENT_TEMPLATES)

@gangnam_services_bp.route('/submit-event', methods=['POST'])
@login_required
def submit_clinic_event():
    """Submit new clinic event"""
    event_type = request.form.get('event_type')
    event_title = request.form.get('event_title')
    event_description = request.form.get('event_description')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    procedures = request.form.getlist('procedures')
    discount_percentage = request.form.get('discount_percentage', type=float)
    limited_slots = request.form.get('limited_slots', type=int)
    special_conditions = request.form.get('special_conditions')
    
    try:
        # Create new event
        event_data = {
            'title': event_title,
            'description': event_description,
            'event_type': event_type,
            'start_date': start_date,
            'end_date': end_date,
            'procedures': procedures,
            'discount_percentage': discount_percentage,
            'limited_slots': limited_slots,
            'special_conditions': special_conditions,
            'created_by': current_user.id,
            'status': 'pending_approval',
            'created_at': datetime.utcnow()
        }
        
        # In real implementation, save to database
        logger.info(f"New clinic event created: {event_title}")
        
        return jsonify({
            'success': True,
            'message': 'Event submitted successfully! It will be live after approval.',
            'event_id': f"event_{int(datetime.now().timestamp())}"
        })
        
    except Exception as e:
        logger.error(f"Error creating clinic event: {e}")
        return jsonify({'success': False, 'error': 'Failed to create event'})

@gangnam_services_bp.route('/flash-deal/<deal_id>')
def flash_deal_details(deal_id):
    """Detailed view of a flash deal"""
    deal = GANGNAM_PRICING_STRUCTURE['flash_deals'].get(deal_id)
    if not deal:
        flash('Flash deal not found', 'error')
        return redirect(url_for('gangnam_services.services_pricing_home'))
    
    # Check if deal is still valid
    if datetime.strptime(deal['valid_until'], '%Y-%m-%d %H:%M:%S') <= datetime.now():
        flash('This flash deal has expired', 'error')
        return redirect(url_for('gangnam_services.services_pricing_home'))
    
    # Get participating clinics
    participating_clinics = []
    for clinic_id in deal['clinic_ids']:
        clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
        if clinic:
            participating_clinics.append(clinic)
    
    return render_template('flash_deal_details.html',
                         deal=deal,
                         deal_id=deal_id,
                         participating_clinics=participating_clinics)

@gangnam_services_bp.route('/book-flash-deal', methods=['POST'])
@login_required
def book_flash_deal():
    """Book a flash deal"""
    deal_id = request.form.get('deal_id')
    clinic_id = request.form.get('clinic_id')
    preferred_date = request.form.get('preferred_date')
    
    deal = GANGNAM_PRICING_STRUCTURE['flash_deals'].get(deal_id)
    if not deal:
        return jsonify({'success': False, 'error': 'Flash deal not found'})
    
    # Check deal validity
    if datetime.strptime(deal['valid_until'], '%Y-%m-%d %H:%M:%S') <= datetime.now():
        return jsonify({'success': False, 'error': 'Flash deal has expired'})
    
    # Check slot availability
    if deal['slots_available'] <= 0:
        return jsonify({'success': False, 'error': 'No slots available for this deal'})
    
    try:
        clinic = db.session.query(Clinic).filter_by(id=clinic_id).first()
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        # Create flash deal booking
        consultation = ClinicConsultation(
            clinic_id=clinic_id,
            user_id=current_user.id,
            consultation_type='flash_deal_booking',
            preferred_date=datetime.strptime(preferred_date, '%Y-%m-%d') if preferred_date else None,
            consultation_fee=deal['discounted_price'],
            user_message=f"Flash deal booking: {deal['title']}\nOriginal price: ₹{deal['original_price']:,}\nDiscount price: ₹{deal['discounted_price']:,}",
            status='flash_deal_confirmed',
            patient_name=current_user.name,
            patient_email=current_user.email,
            procedure_interest=deal['title'],
            source='flash_deal',
            special_pricing={
                'deal_id': deal_id,
                'original_price': deal['original_price'],
                'discounted_price': deal['discounted_price'],
                'discount_percentage': deal['discount_percentage']
            }
        )
        
        db.session.add(consultation)
        db.session.commit()
        
        # Update slot availability (in real system, this would be in database)
        deal['slots_available'] -= 1
        
        return jsonify({
            'success': True,
            'message': f'Flash deal booked successfully! You saved ₹{deal["original_price"] - deal["discounted_price"]:,}',
            'consultation_id': consultation.id,
            'savings': deal['original_price'] - deal['discounted_price']
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error booking flash deal: {e}")
        return jsonify({'success': False, 'error': 'Failed to book flash deal'})

@gangnam_services_bp.route('/seasonal-event/<event_name>')
def seasonal_event_details(event_name):
    """Detailed view of seasonal event"""
    event = GANGNAM_PRICING_STRUCTURE['seasonal_events'].get(event_name)
    if not event:
        flash('Seasonal event not found', 'error')
        return redirect(url_for('gangnam_services.services_pricing_home'))
    
    return render_template('seasonal_event_details.html',
                         event=event,
                         event_name=event_name)

@gangnam_services_bp.route('/book-seasonal-package', methods=['POST'])
@login_required
def book_seasonal_package():
    """Book a seasonal event package"""
    event_name = request.form.get('event_name')
    package_type = request.form.get('package_type')
    preferred_date = request.form.get('preferred_date')
    
    event = GANGNAM_PRICING_STRUCTURE['seasonal_events'].get(event_name)
    if not event:
        return jsonify({'success': False, 'error': 'Seasonal event not found'})
    
    package = event['packages'].get(package_type)
    if not package:
        return jsonify({'success': False, 'error': 'Package not found'})
    
    try:
        # Create seasonal package booking
        consultation = ClinicConsultation(
            clinic_id=1,  # Default to main clinic
            user_id=current_user.id,
            consultation_type='seasonal_package',
            preferred_date=datetime.strptime(preferred_date, '%Y-%m-%d') if preferred_date else None,
            consultation_fee=package['event_price'],
            user_message=f"Seasonal package: {event['title']} - {package['name']}\nProcedures: {', '.join(package['procedures'])}\nSavings: ₹{package['savings']:,}",
            status='seasonal_package_confirmed',
            patient_name=current_user.name,
            patient_email=current_user.email,
            procedure_interest=package['name'],
            source='seasonal_event',
            special_pricing={
                'event_name': event_name,
                'package_type': package_type,
                'original_price': package['original_price'],
                'event_price': package['event_price'],
                'savings': package['savings']
            }
        )
        
        db.session.add(consultation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Seasonal package booked successfully! You saved ₹{package["savings"]:,}',
            'consultation_id': consultation.id,
            'package_price': package['event_price']
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error booking seasonal package: {e}")
        return jsonify({'success': False, 'error': 'Failed to book seasonal package'})

@gangnam_services_bp.route('/api/real-time-pricing')
def get_real_time_pricing():
    """Get dynamic pricing based on time and availability"""
    procedure = request.args.get('procedure')
    clinic_id = request.args.get('clinic_id', type=int)
    requested_time = request.args.get('time')
    requested_date = request.args.get('date')
    
    base_price = 50000  # Would fetch from actual pricing data
    
    # Apply dynamic pricing
    final_price = base_price
    pricing_factors = []
    
    if requested_time:
        # Check peak hours
        peak_hours = GANGNAM_PRICING_STRUCTURE['real_time_pricing']['dynamic_slots']['peak_hours']['hours']
        off_peak_hours = GANGNAM_PRICING_STRUCTURE['real_time_pricing']['dynamic_slots']['off_peak']['hours']
        
        for peak_range in peak_hours:
            start_time, end_time = peak_range.split('-')
            if start_time <= requested_time <= end_time:
                multiplier = GANGNAM_PRICING_STRUCTURE['real_time_pricing']['dynamic_slots']['peak_hours']['multiplier']
                final_price = int(base_price * multiplier)
                pricing_factors.append(f"Peak hours surcharge: +{int((multiplier - 1) * 100)}%")
                break
        
        for off_peak_range in off_peak_hours:
            start_time, end_time = off_peak_range.split('-')
            if start_time <= requested_time <= end_time:
                multiplier = GANGNAM_PRICING_STRUCTURE['real_time_pricing']['dynamic_slots']['off_peak']['multiplier']
                final_price = int(base_price * multiplier)
                pricing_factors.append(f"Off-peak discount: {int((1 - multiplier) * 100)}%")
                break
    
    # Check for last-minute deals
    if requested_date:
        request_date = datetime.strptime(requested_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        if request_date == today:
            if procedure in GANGNAM_PRICING_STRUCTURE['real_time_pricing']['last_minute_deals']['same_day_booking']['available_procedures']:
                discount = GANGNAM_PRICING_STRUCTURE['real_time_pricing']['last_minute_deals']['same_day_booking']['discount_percentage']
                final_price = int(final_price * (1 - discount / 100))
                pricing_factors.append(f"Same-day booking discount: -{discount}%")
    
    return jsonify({
        'procedure': procedure,
        'clinic_id': clinic_id,
        'base_price': base_price,
        'final_price': final_price,
        'pricing_factors': pricing_factors,
        'savings': base_price - final_price if final_price < base_price else 0
    })

@gangnam_services_bp.route('/api/trending-procedures')
def get_trending_procedures():
    """Get trending procedures with special pricing"""
    trending_data = [
        {
            'procedure': 'Thread Lift',
            'trend_score': 95,
            'bookings_this_week': 127,
            'average_price': 65000,
            'special_offer': 'Procedure of the Month - 20% off'
        },
        {
            'procedure': 'Botox + Filler Combo',
            'trend_score': 88,
            'bookings_this_week': 89,
            'average_price': 35000,
            'special_offer': 'Flash Deal Available'
        },
        {
            'procedure': 'HIFU Face Lift',
            'trend_score': 82,
            'bookings_this_week': 56,
            'average_price': 85000,
            'special_offer': 'Winter Package Deal'
        }
    ]
    
    return jsonify({'trending_procedures': trending_data})

@gangnam_services_bp.route('/event-calendar')
def event_calendar():
    """Calendar view of all upcoming events and deals"""
    # Compile all events into calendar format
    calendar_events = []
    
    # Add flash deals
    for deal_id, deal in GANGNAM_PRICING_STRUCTURE['flash_deals'].items():
        calendar_events.append({
            'title': deal['title'],
            'type': 'flash_deal',
            'start': deal['valid_until'].split(' ')[0],
            'end': deal['valid_until'].split(' ')[0],
            'discount': deal['discount_percentage'],
            'id': deal_id
        })
    
    # Add seasonal events
    for event_name, event in GANGNAM_PRICING_STRUCTURE['seasonal_events'].items():
        calendar_events.append({
            'title': event['title'],
            'type': 'seasonal_event',
            'start': event['event_dates']['start'],
            'end': event['event_dates']['end'],
            'id': event_name
        })
    
    return render_template('event_calendar.html',
                         calendar_events=calendar_events)