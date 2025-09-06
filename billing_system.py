"""
Comprehensive billing system with Razorpay integration for clinic credit management.
"""
import os
import razorpay
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Clinic, Lead
from sqlalchemy import text
from sqlalchemy import desc
import logging

billing_bp = Blueprint('billing', __name__)
logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(
    os.environ.get('RAZORPAY_KEY_ID', ''),
    os.environ.get('RAZORPAY_KEY_SECRET', '')
))

# Credit packages available for purchase
CREDIT_PACKAGES = [
    {'credits': 1000, 'price': 5000, 'bonus': 0, 'popular': False},
    {'credits': 2500, 'price': 12000, 'bonus': 100, 'popular': True},
    {'credits': 5000, 'price': 22500, 'bonus': 500, 'popular': False},
    {'credits': 10000, 'price': 42000, 'bonus': 1500, 'popular': False},
]

# Lead pricing structure
LEAD_PRICING = {
    'chat': 300,  # Credits per chat lead
    'call': 500,  # Credits per call lead
    'consultation': 800,  # Credits per consultation booking
}

@billing_bp.route('/clinic/billing')
@login_required
def clinic_billing_dashboard():
    """Clinic billing dashboard showing credits, transactions, and top-up options."""
    # Get clinic for current user
    clinic = Clinic.query.filter_by(user_id=current_user.id).first()
    if not clinic:
        flash('Clinic profile not found', 'error')
        return redirect(url_for('routes.index'))
    
    # Get current credit balance
    current_credits = get_clinic_credits(clinic.id)
    
    # Get recent transactions
    recent_transactions = db.session.execute(text("""
        SELECT * FROM credit_transactions 
        WHERE clinic_id = :clinic_id 
        ORDER BY created_at DESC 
        LIMIT 10
    """), {"clinic_id": clinic.id}).fetchall()
    
    # Get this month's lead statistics
    current_month = datetime.now().replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    monthly_leads = db.session.execute(text("""
        SELECT COUNT(*) FROM leads 
        WHERE clinic_id = :clinic_id 
        AND created_at >= :start_date 
        AND created_at < :end_date
    """), {
        "clinic_id": clinic.id,
        "start_date": current_month,
        "end_date": next_month
    }).scalar() or 0
    
    monthly_spend = db.session.execute(text("""
        SELECT COALESCE(SUM(amount), 0) FROM credit_transactions 
        WHERE clinic_id = :clinic_id 
        AND transaction_type = 'deduction'
        AND created_at >= :start_date 
        AND created_at < :end_date
    """), {
        "clinic_id": clinic.id,
        "start_date": current_month,
        "end_date": next_month
    }).scalar() or 0
    
    return render_template('clinic/billing_dashboard.html',
                         clinic=clinic,
                         current_credits=current_credits,
                         recent_transactions=recent_transactions,
                         monthly_leads=monthly_leads,
                         monthly_spend=monthly_spend,
                         credit_packages=CREDIT_PACKAGES,
                         lead_pricing=LEAD_PRICING)

@billing_bp.route('/clinic/purchase-credits', methods=['POST'])
@login_required
def purchase_credits():
    """Create Razorpay order for credit purchase."""
    clinic = Clinic.query.filter_by(user_id=current_user.id).first()
    if not clinic:
        return jsonify({'error': 'Clinic not found'}), 404
    
    package_index = int(request.form.get('package'))
    if package_index < 0 or package_index >= len(CREDIT_PACKAGES):
        return jsonify({'error': 'Invalid package'}), 400
    
    package = CREDIT_PACKAGES[package_index]
    
    try:
        # Create Razorpay order
        order_data = {
            'amount': package['price'] * 100,  # Convert to paise
            'currency': 'INR',
            'receipt': f'credit_purchase_{clinic.id}_{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'notes': {
                'clinic_id': clinic.id,
                'credits': package['credits'],
                'bonus_credits': package['bonus']
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        return jsonify({
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key': os.environ.get('RAZORPAY_KEY_ID'),
            'clinic_name': clinic.name,
            'credits': package['credits'],
            'bonus': package['bonus']
        })
        
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {e}")
        return jsonify({'error': 'Payment order creation failed'}), 500

@billing_bp.route('/clinic/payment-success', methods=['POST'])
@login_required
def payment_success():
    """Handle successful payment and credit top-up."""
    try:
        # Verify payment signature
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Get order details
        order = razorpay_client.order.fetch(order_id)
        clinic_id = int(order['notes']['clinic_id'])
        credits = int(order['notes']['credits'])
        bonus_credits = int(order['notes']['bonus_credits'])
        
        # Add credits to clinic
        total_credits = credits + bonus_credits
        add_credits_to_clinic(clinic_id, total_credits, 'purchase', 
                            f'Credit purchase - Order {order_id}')
        
        # Record billing transaction
        billing_record = ClinicBilling(
            clinic_id=clinic_id,
            order_id=order_id,
            payment_id=payment_id,
            amount=order['amount'] / 100,  # Convert back to rupees
            credits_purchased=total_credits,
            status='completed',
            payment_method='razorpay'
        )
        db.session.add(billing_record)
        db.session.commit()
        
        flash(f'Successfully added {total_credits} credits to your account!', 'success')
        return redirect(url_for('billing.clinic_billing_dashboard'))
        
    except razorpay.errors.SignatureVerificationError:
        flash('Payment verification failed. Please contact support.', 'error')
        return redirect(url_for('billing.clinic_billing_dashboard'))
    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        flash('Payment processing failed. Please contact support.', 'error')
        return redirect(url_for('billing.clinic_billing_dashboard'))

@billing_bp.route('/clinic/payment-failed')
@login_required
def payment_failed():
    """Handle failed payment."""
    flash('Payment was unsuccessful. Please try again.', 'error')
    return redirect(url_for('billing.clinic_billing_dashboard'))

def get_clinic_credits(clinic_id):
    """Get current credit balance for a clinic."""
    # Get total credits purchased
    credits_purchased = db.session.execute(text("""
        SELECT COALESCE(SUM(amount), 0) as total 
        FROM credit_transactions 
        WHERE clinic_id = :clinic_id AND transaction_type = 'credit'
    """), {"clinic_id": clinic_id}).scalar() or 0
    
    # Get total credits used
    credits_used = db.session.execute(text("""
        SELECT COALESCE(SUM(amount), 0) as total 
        FROM credit_transactions 
        WHERE clinic_id = :clinic_id AND transaction_type = 'deduction'
    """), {"clinic_id": clinic_id}).scalar() or 0
    
    return max(0, credits_purchased - credits_used)

def add_credits_to_clinic(clinic_id, credits, transaction_type, description):
    """Add credits to clinic account."""
    db.session.execute(text("""
        INSERT INTO credit_transactions (clinic_id, amount, transaction_type, description, created_at)
        VALUES (:clinic_id, :amount, :transaction_type, :description, :created_at)
    """), {
        "clinic_id": clinic_id,
        "amount": credits,
        "transaction_type": transaction_type,
        "description": description,
        "created_at": datetime.utcnow()
    })
    db.session.commit()

def deduct_credits_for_lead(clinic_id, lead_type, description):
    """Deduct credits when a lead is generated."""
    credits_required = LEAD_PRICING.get(lead_type, 300)
    current_credits = get_clinic_credits(clinic_id)
    
    if current_credits >= credits_required:
        db.session.execute(text("""
            INSERT INTO credit_transactions (clinic_id, amount, transaction_type, description, created_at)
            VALUES (:clinic_id, :amount, :transaction_type, :description, :created_at)
        """), {
            "clinic_id": clinic_id,
            "amount": credits_required,
            "transaction_type": "deduction",
            "description": description,
            "created_at": datetime.utcnow()
        })
        db.session.commit()
        return True, credits_required
    else:
        return False, credits_required

@billing_bp.route('/admin/billing-overview')
@login_required
def admin_billing_overview():
    """Admin overview of all billing and revenue."""
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('routes.index'))
    
    # Revenue statistics
    total_revenue = db.session.query(db.func.sum(ClinicBilling.amount)).scalar() or 0
    
    # This month's revenue
    current_month = datetime.now().replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    monthly_revenue = db.session.query(db.func.sum(ClinicBilling.amount)).filter(
        ClinicBilling.created_at >= current_month,
        ClinicBilling.created_at < next_month
    ).scalar() or 0
    
    # Credit statistics
    total_credits_sold = db.session.query(db.func.sum(ClinicBilling.credits_purchased)).scalar() or 0
    total_credits_used = db.session.query(db.func.sum(CreditTransaction.credits_used)).filter(
        CreditTransaction.transaction_type == 'debit'
    ).scalar() or 0
    
    # Recent transactions
    recent_billings = ClinicBilling.query.order_by(
        desc(ClinicBilling.created_at)
    ).limit(20).all()
    
    return render_template('admin/billing_overview.html',
                         total_revenue=total_revenue,
                         monthly_revenue=monthly_revenue,
                         total_credits_sold=total_credits_sold,
                         total_credits_used=total_credits_used,
                         recent_billings=recent_billings)