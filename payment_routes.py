"""
Payment Routes for Credit Top-up System
Handles Razorpay integration for clinic credit purchases
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
import razorpay
import os
import logging
from datetime import datetime
from credit_billing_system import CreditBillingService
from models import db, Clinic
from sqlalchemy import text

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')
logger = logging.getLogger(__name__)

# Initialize Razorpay client
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    logger.info("Razorpay client initialized successfully")
else:
    razorpay_client = None
    logger.warning("Razorpay credentials not found in environment variables")

@payment_bp.route('/topup', methods=['GET', 'POST'])
@login_required
def credit_topup():
    """Credit top-up page with package selection and payment initiation."""
    try:
        # Get clinic for current user
        clinic = db.session.execute(
            text("SELECT * FROM clinics WHERE owner_user_id = :user_id"),
            {'user_id': current_user.id}
        ).fetchone()
        
        if not clinic:
            flash('Clinic profile not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic_dict = dict(clinic._mapping)
        
        if request.method == 'POST':
            return handle_payment_initiation(clinic_dict)
        
        # GET request - show top-up options
        credit_packages = [
            {'credits': 1000, 'price': 1000, 'bonus': 0, 'popular': False},
            {'credits': 5000, 'price': 5000, 'bonus': 1000, 'popular': True},
            {'credits': 10000, 'price': 10000, 'bonus': 2500, 'popular': False},
            {'credits': 25000, 'price': 25000, 'bonus': 7500, 'popular': False},
            {'credits': 50000, 'price': 50000, 'bonus': 20000, 'popular': False},
        ]
        
        # Get current balance
        current_balance = CreditBillingService.get_clinic_credit_balance(clinic_dict['id'])
        
        # Get recent transactions
        recent_transactions = CreditBillingService.get_credit_transaction_history(
            clinic_dict['id'], limit=5
        )
        
        return render_template('payment/credit_topup.html',
                             clinic=clinic_dict,
                             credit_packages=credit_packages,
                             current_balance=current_balance,
                             recent_transactions=recent_transactions,
                             razorpay_key_id=RAZORPAY_KEY_ID)
        
    except Exception as e:
        logger.error(f"Error in credit top-up page: {e}")
        flash('Error loading top-up page. Please try again.', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

def handle_payment_initiation(clinic):
    """Handle payment initiation for credit top-up."""
    try:
        if not razorpay_client:
            return jsonify({
                'success': False, 
                'message': 'Payment system temporarily unavailable. Please contact support.'
            })
        
        amount = int(request.form.get('amount', 0))
        promo_code = request.form.get('promo_code', '').strip()
        
        # Validate minimum amount
        if amount < 1000:
            return jsonify({
                'success': False,
                'message': 'Minimum top-up amount is ₹1,000'
            })
        
        # Calculate bonus credits if promo code provided
        bonus_credits = 0
        if promo_code:
            bonus_credits = CreditBillingService.calculate_promo_bonus(amount, promo_code)
        
        # Create Razorpay order
        order_data = {
            'amount': amount * 100,  # Amount in paise
            'currency': 'INR',
            'receipt': f'credit_topup_{clinic["id"]}_{int(datetime.now().timestamp())}',
            'notes': {
                'clinic_id': clinic['id'],
                'clinic_name': clinic['name'],
                'promo_code': promo_code,
                'bonus_credits': bonus_credits
            }
        }
        
        razorpay_order = razorpay_client.order.create(order_data)
        
        return jsonify({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': amount,
            'bonus_credits': bonus_credits,
            'total_credits': amount + bonus_credits,
            'razorpay_key': RAZORPAY_KEY_ID,
            'clinic_name': clinic['name'],
            'clinic_email': clinic.get('email', ''),
            'clinic_phone': clinic.get('contact_number', '')
        })
        
    except Exception as e:
        logger.error(f"Error initiating payment: {e}")
        return jsonify({
            'success': False,
            'message': 'Error initiating payment. Please try again.'
        })

@payment_bp.route('/verify', methods=['POST'])
@login_required
def verify_payment():
    """Verify Razorpay payment and process credit top-up."""
    try:
        if not razorpay_client:
            return jsonify({
                'success': False,
                'message': 'Payment verification temporarily unavailable'
            })
        
        # Get payment details from request
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')
        
        if not all([payment_id, order_id, signature]):
            return jsonify({
                'success': False,
                'message': 'Missing payment verification details'
            })
        
        # Verify payment signature
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })
        except razorpay.errors.SignatureVerificationError:
            logger.error("Payment signature verification failed")
            return jsonify({
                'success': False,
                'message': 'Payment verification failed'
            })
        
        # Get order details
        order = razorpay_client.order.fetch(order_id)
        payment = razorpay_client.payment.fetch(payment_id)
        
        # Verify payment status
        if payment['status'] != 'captured':
            return jsonify({
                'success': False,
                'message': 'Payment not completed'
            })
        
        # Get clinic
        clinic = db.session.execute(
            text("SELECT * FROM clinics WHERE owner_user_id = :user_id"),
            {'user_id': current_user.id}
        ).fetchone()
        
        if not clinic:
            return jsonify({
                'success': False,
                'message': 'Clinic not found'
            })
        
        clinic_dict = dict(clinic._mapping)
        
        # Extract details from order
        amount = order['amount'] // 100  # Convert from paise to rupees
        promo_code = order['notes'].get('promo_code', '')
        
        # Process credit top-up
        result = CreditBillingService.process_credit_topup(
            clinic_id=clinic_dict['id'],
            amount=amount,
            payment_id=payment_id,
            order_id=order_id,
            promo_code=promo_code if promo_code else None
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'credits_added': result['credits_added'],
                'bonus_credits': result['bonus_credits'],
                'new_balance': result['new_balance']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            })
        
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        return jsonify({
            'success': False,
            'message': 'Error processing payment verification'
        })

@payment_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """Handle Razorpay webhooks for payment status updates."""
    try:
        # Verify webhook signature
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        webhook_secret = os.environ.get('RAZORPAY_WEBHOOK_SECRET')
        
        if webhook_secret:
            try:
                razorpay_client.utility.verify_webhook_signature(
                    request.get_data().decode(),
                    webhook_signature,
                    webhook_secret
                )
            except razorpay.errors.SignatureVerificationError:
                logger.error("Webhook signature verification failed")
                return jsonify({'status': 'error'}), 400
        
        webhook_data = request.get_json()
        event = webhook_data.get('event')
        
        if event == 'payment.captured':
            # Handle successful payment
            payment_entity = webhook_data['payload']['payment']['entity']
            order_id = payment_entity['order_id']
            payment_id = payment_entity['id']
            
            logger.info(f"Payment captured: {payment_id} for order: {order_id}")
            
        elif event == 'payment.failed':
            # Handle failed payment
            payment_entity = webhook_data['payload']['payment']['entity']
            order_id = payment_entity['order_id']
            payment_id = payment_entity['id']
            
            logger.warning(f"Payment failed: {payment_id} for order: {order_id}")
            
            # Update transaction status to failed
            db.session.execute(text("""
                UPDATE credit_transactions 
                SET status = 'failed' 
                WHERE order_id = :order_id
            """), {'order_id': order_id})
            
            db.session.commit()
        
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'status': 'error'}), 500

@payment_bp.route('/history')
@login_required
def transaction_history():
    """Display complete transaction history for clinic."""
    try:
        # Get clinic
        clinic = db.session.execute(
            text("SELECT * FROM clinics WHERE owner_user_id = :user_id"),
            {'user_id': current_user.id}
        ).fetchone()
        
        if not clinic:
            flash('Clinic profile not found', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic_dict = dict(clinic._mapping)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # Get transactions
        transactions = CreditBillingService.get_credit_transaction_history(
            clinic_dict['id'], limit=per_page, offset=offset
        )
        
        # Get total count for pagination
        total_count = db.session.execute(text("""
            SELECT COUNT(*) FROM credit_transactions WHERE clinic_id = :clinic_id
        """), {'clinic_id': clinic_dict['id']}).scalar()
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('payment/transaction_history.html',
                             clinic=clinic_dict,
                             transactions=transactions,
                             page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             total_count=total_count)
        
    except Exception as e:
        logger.error(f"Error loading transaction history: {e}")
        flash('Error loading transaction history', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))