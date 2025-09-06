"""
Simple Billing System with Promo Code Support
Handles credit top-ups with amount input and promotional discounts.
"""

import os
import logging
import razorpay
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from flask_login import login_required, current_user
from models import db, Clinic, CreditTransaction, PromoCode, PromoUsage
from werkzeug.security import generate_password_hash
import hashlib
import hmac

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Razorpay client
try:
    razorpay_client = razorpay.Client(auth=(
        os.environ.get('RAZORPAY_KEY_ID'),
        os.environ.get('RAZORPAY_KEY_SECRET')
    ))
    logger.info("Razorpay client initialized successfully")
except Exception as e:
    logger.error(f"Razorpay initialization failed: {e}")
    razorpay_client = None

# Create blueprint
simple_billing = Blueprint('simple_billing', __name__)

@simple_billing.route('/credits/topup', methods=['GET', 'POST'])
@login_required
def simple_credit_topup():
    """Display the simple credit top-up page."""
    try:
        clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
        if not clinic:
            flash('Clinic profile not found', 'error')
            return redirect(url_for('web.index'))
        
        # Get active promo codes
        active_promos = PromoCode.query.filter(
            PromoCode.is_active == True,
            PromoCode.start_date <= datetime.utcnow(),
            PromoCode.end_date >= datetime.utcnow()
        ).all()
        
        return render_template('clinic/simple_credit_topup.html', 
                             clinic=clinic, 
                             active_promos=active_promos,
                             razorpay_key_id=os.environ.get('RAZORPAY_KEY_ID'))
    except Exception as e:
        logger.error(f"Error loading simple credit top-up page: {e}")
        flash('Error loading page', 'error')
        return redirect(url_for('web.index'))

@simple_billing.route('/simple-promotions', methods=['GET'])
@login_required
def get_simple_promotions():
    """Get all active promotional codes for display."""
    try:
        # Get active promo codes
        active_promos = PromoCode.query.filter(
            PromoCode.is_active == True,
            PromoCode.start_date <= datetime.utcnow(),
            PromoCode.end_date >= datetime.utcnow()
        ).all()
        
        promotions = []
        for promo in active_promos:
            promotions.append({
                'code': promo.code,
                'description': promo.description,
                'discount_type': promo.discount_type,
                'discount_value': float(promo.discount_value),
                'min_amount': float(promo.min_amount),
                'max_discount': float(promo.max_discount) if promo.max_discount else None,
                'bonus_credits': float(promo.bonus_credits) if promo.bonus_credits else 0
            })
        
        return jsonify({
            'success': True,
            'promotions': promotions
        })
        
    except Exception as e:
        logger.error(f"Error loading promotions: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load promotions'
        })

@simple_billing.route('/apply-promo', methods=['POST'])
@login_required
def apply_promo_code():
    """Apply a promotional code to calculate discounts."""
    try:
        promo_code = request.form.get('promo_code', '').strip().upper()
        amount = float(request.form.get('amount', 0))
        
        if not promo_code:
            return jsonify({'success': False, 'error': 'Promo code is required'})
        
        if amount < 100:
            return jsonify({'success': False, 'error': 'Minimum amount is ₹100'})
        
        # Find the promo code
        promo = PromoCode.query.filter(
            PromoCode.code == promo_code,
            PromoCode.is_active == True,
            PromoCode.start_date <= datetime.utcnow(),
            PromoCode.end_date >= datetime.utcnow()
        ).first()
        
        if not promo:
            return jsonify({'success': False, 'error': 'Invalid or expired promo code'})
        
        # Check minimum amount
        if amount < promo.min_amount:
            return jsonify({
                'success': False, 
                'error': f'Minimum amount for this promo is ₹{promo.min_amount:,.0f}'
            })
        
        # Check usage limits
        clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        # Check if user has already used this promo
        if promo.usage_limit_per_user:
            usage_count = PromoUsage.query.filter_by(
                clinic_id=clinic.id,
                promo_code_id=promo.id
            ).count()
            
            if usage_count >= promo.usage_limit_per_user:
                return jsonify({
                    'success': False, 
                    'error': 'You have already used this promo code'
                })
        
        # Check total usage limit
        if promo.total_usage_limit:
            total_usage = PromoUsage.query.filter_by(promo_code_id=promo.id).count()
            if total_usage >= promo.total_usage_limit:
                return jsonify({
                    'success': False, 
                    'error': 'This promo code has reached its usage limit'
                })
        
        # Calculate discount
        discount = 0
        bonus = 0
        
        if promo.discount_percent > 0:
            discount = amount * (promo.discount_percent / 100)
            if promo.max_discount and discount > promo.max_discount:
                discount = promo.max_discount
        
        if promo.bonus_percent > 0:
            bonus = amount * (promo.bonus_percent / 100)
        
        return jsonify({
            'success': True,
            'message': f'Promo code applied successfully!',
            'promo': {
                'code': promo.code,
                'description': promo.description,
                'discount_percent': promo.discount_percent,
                'bonus_percent': promo.bonus_percent or 0
            },
            'discount': discount,
            'bonus': bonus,
            'final_amount': amount - discount,
            'total_credits': amount + bonus
        })
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount'})
    except Exception as e:
        logger.error(f"Error applying promo code: {e}")
        return jsonify({'success': False, 'error': 'Error applying promo code'})

@simple_billing.route('/simple-purchase-credits', methods=['POST'])
@login_required
def simple_purchase_credits():
    """Create a Razorpay order for simple credit purchase."""
    try:
        if not razorpay_client:
            return jsonify({'success': False, 'error': 'Payment gateway not configured'})
        
        amount = float(request.form.get('amount', 0))
        promo_code = request.form.get('promo_code', '').strip().upper()
        
        if amount < 100:
            return jsonify({'success': False, 'error': 'Minimum amount is ₹100'})
        
        if amount > 100000:
            return jsonify({'success': False, 'error': 'Maximum amount is ₹1,00,000'})
        
        clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        # Apply promo code if provided
        discount = 0
        bonus = 0
        promo = None
        
        if promo_code:
            promo = PromoCode.query.filter(
                PromoCode.code == promo_code,
                PromoCode.is_active == True,
                PromoCode.start_date <= datetime.utcnow(),
                PromoCode.end_date >= datetime.utcnow()
            ).first()
            
            if promo and amount >= promo.min_amount:
                # Calculate discount
                if promo.discount_percent > 0:
                    discount = amount * (promo.discount_percent / 100)
                    if promo.max_discount and discount > promo.max_discount:
                        discount = promo.max_discount
                
                # Calculate bonus
                if promo.bonus_percent > 0:
                    bonus = amount * (promo.bonus_percent / 100)
        
        final_amount = amount - discount
        total_credits = amount + bonus
        
        # Create Razorpay order
        order_data = {
            'amount': int(final_amount * 100),  # Convert to paise
            'currency': 'INR',
            'receipt': f'credit_{clinic.id}_{int(datetime.utcnow().timestamp())}',
            'payment_capture': 1
        }
        
        order = razorpay_client.order.create(order_data)
        
        # Store order details in session for verification
        session['pending_order'] = {
            'order_id': order['id'],
            'amount': final_amount,
            'credits': total_credits,
            'clinic_id': clinic.id,
            'promo_code_id': promo.id if promo else None,
            'discount': discount,
            'bonus': bonus
        }
        
        logger.info(f"Created Razorpay order: {order['id']} for ₹{final_amount}")
        
        # Always use demo payment in Replit environment due to Razorpay restrictions
        return jsonify({
            'success': True,
            'redirect_url': url_for('simple_billing.demo_payment', order_id=order['id'])
        })
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid amount'})
    except Exception as e:
        logger.error(f"Error creating payment order: {e}")
        return jsonify({'success': False, 'error': 'Failed to create payment order'})

@simple_billing.route('/payment-checkout/<order_id>')
@login_required
def payment_checkout(order_id):
    """Display dedicated payment checkout page."""
    try:
        # Get pending order from session
        pending_order = session.get('pending_order')
        if not pending_order or pending_order['order_id'] != order_id:
            flash('Invalid or expired payment session', 'error')
            return redirect(url_for('simple_billing.simple_credit_topup'))
        
        clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
        if not clinic:
            flash('Clinic not found', 'error')
            return redirect(url_for('web.index'))
        
        return render_template('clinic/payment_checkout.html',
                             clinic=clinic,
                             order_id=order_id,
                             amount=pending_order['amount'],
                             credits=pending_order['credits'],
                             razorpay_amount=int(pending_order['amount'] * 100),
                             razorpay_key_id=os.environ.get('RAZORPAY_KEY_ID'))
        
    except Exception as e:
        logger.error(f"Error loading payment checkout: {e}")
        flash('Error loading payment page', 'error')
        return redirect(url_for('simple_billing.simple_credit_topup'))

@simple_billing.route('/demo-payment/<order_id>')
@login_required
def demo_payment(order_id):
    """Display demo payment page for testing."""
    try:
        # Get pending order from session
        pending_order = session.get('pending_order')
        if not pending_order or pending_order['order_id'] != order_id:
            flash('Invalid or expired payment session', 'error')
            return redirect(url_for('simple_billing.simple_credit_topup'))
        
        clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
        if not clinic:
            flash('Clinic not found', 'error')
            return redirect(url_for('web.index'))
        
        return render_template('clinic/demo_payment.html',
                             clinic=clinic,
                             order_id=order_id,
                             amount=pending_order['amount'],
                             credits=pending_order['credits'])
        
    except Exception as e:
        logger.error(f"Error loading demo payment: {e}")
        flash('Error loading payment page', 'error')
        return redirect(url_for('simple_billing.simple_credit_topup'))

@simple_billing.route('/demo-payment-complete', methods=['POST'])
@login_required
def demo_payment_complete():
    """Complete demo payment and add credits."""
    try:
        order_id = request.form.get('order_id')
        result = request.form.get('result')
        
        if result != 'success':
            return jsonify({'success': False, 'error': 'Payment simulation failed'})
        
        # Get pending order from session
        pending_order = session.get('pending_order')
        if not pending_order or pending_order['order_id'] != order_id:
            return jsonify({'success': False, 'error': 'Invalid order'})
        
        # Get clinic
        clinic = Clinic.query.filter_by(owner_user_id=current_user.id).first()
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        # Add credits to clinic
        credits_to_add = pending_order['credits']
        clinic.credit_balance += credits_to_add
        
        # Create transaction record
        from models import CreditTransaction
        transaction = CreditTransaction(
            clinic_id=clinic.id,
            transaction_type='purchase',
            amount=credits_to_add,
            order_id=order_id,
            payment_id=f'demo_{order_id}',
            monetary_value=pending_order['amount'],
            description=f"Demo credit top-up: ₹{pending_order['amount']:,.0f}",
            status='completed'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Clear pending order from session
        session.pop('pending_order', None)
        
        logger.info(f"Demo payment: Successfully added ₹{credits_to_add:,.0f} credits to clinic {clinic.id}")
        
        return jsonify({
            'success': True,
            'message': 'Demo payment successful',
            'credits_added': credits_to_add,
            'new_balance': clinic.credit_balance
        })
        
    except Exception as e:
        logger.error(f"Error completing demo payment: {e}")
        return jsonify({'success': False, 'error': 'Demo payment failed'})

@simple_billing.route('/verify-payment', methods=['POST', 'GET'])
@login_required
def verify_payment():
    """Verify Razorpay payment and add credits."""
    try:
        if not razorpay_client:
            flash('Payment gateway not configured', 'error')
            return redirect(url_for('simple_billing.simple_credit_topup'))
        
        # Handle both GET (hosted checkout callback) and POST (modal response)
        if request.method == 'GET':
            payment_id = request.args.get('razorpay_payment_id')
            order_id = request.args.get('razorpay_order_id')
            signature = request.args.get('razorpay_signature')
        else:
            payment_id = request.form.get('razorpay_payment_id')
            order_id = request.form.get('razorpay_order_id')
            signature = request.form.get('razorpay_signature')
        
        if not all([payment_id, order_id, signature]):
            flash('Missing payment details', 'error')
            return redirect(url_for('simple_billing.simple_credit_topup'))
        
        # Get pending order from session
        pending_order = session.get('pending_order')
        if not pending_order or pending_order['order_id'] != order_id:
            flash('Invalid order. Please try again.', 'error')
            return redirect(url_for('simple_billing.simple_credit_topup'))
        
        # Verify signature
        secret = os.environ.get('RAZORPAY_KEY_SECRET')
        body = order_id + "|" + payment_id
        generated_signature = hmac.new(
            secret.encode(), 
            body.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != signature:
            logger.error("Payment signature verification failed")
            flash('Payment verification failed', 'error')
            return redirect(url_for('simple_billing.simple_credit_topup'))
        
        # Get clinic
        clinic = Clinic.query.get(pending_order['clinic_id'])
        if not clinic:
            flash('Clinic not found', 'error')
            return redirect(url_for('simple_billing.simple_credit_topup'))
        
        # Add credits to clinic
        credits_to_add = pending_order['credits']
        clinic.credit_balance += credits_to_add
        
        # Create transaction record
        transaction = CreditTransaction(
            clinic_id=clinic.id,
            transaction_type='credit',
            amount=pending_order['amount'],
            credits=credits_to_add,
            razorpay_payment_id=payment_id,
            razorpay_order_id=order_id,
            description=f"Credit top-up: ₹{pending_order['amount']:,.0f}",
            status='completed'
        )
        
        # Record promo usage if applicable
        if pending_order['promo_code_id']:
            promo_usage = PromoUsage(
                clinic_id=clinic.id,
                promo_code_id=pending_order['promo_code_id'],
                transaction_id=None,  # Will be updated after transaction is saved
                discount_amount=pending_order['discount'],
                bonus_amount=pending_order['bonus']
            )
            db.session.add(promo_usage)
        
        db.session.add(transaction)
        db.session.commit()
        
        # Update promo usage transaction reference
        if pending_order['promo_code_id']:
            promo_usage.transaction_id = transaction.id
            db.session.commit()
        
        # Clear pending order from session
        session.pop('pending_order', None)
        
        logger.info(f"Successfully added ₹{credits_to_add:,.0f} credits to clinic {clinic.id}")
        
        # For AJAX requests, return JSON
        if request.is_xhr or request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': True,
                'message': 'Payment successful',
                'credits_added': credits_to_add,
                'new_balance': clinic.credit_balance
            })
        
        # For hosted checkout callback, redirect with success message
        flash(f'Payment successful! ₹{credits_to_add:,.0f} credits added to your account.', 'success')
        return redirect(url_for('simple_billing.simple_credit_topup'))
        
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        if request.is_xhr or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'error': 'Payment verification failed'})
        else:
            flash('Payment verification failed. Please contact support.', 'error')
            return redirect(url_for('simple_billing.simple_credit_topup'))

# Update the credit top-up route in routes.py to redirect to simple version
def update_credit_topup_route():
    """Function to update the main credit top-up route"""
    return redirect(url_for('simple_billing.simple_credit_topup'))