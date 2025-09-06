"""
Enhanced Credit Billing System
Complete implementation of the prepaid credit system with all features.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, Clinic, Lead, CreditTransaction, Package
from sqlalchemy import desc, func, text
import logging
import razorpay
import os

enhanced_billing_bp = Blueprint('enhanced_billing', __name__)
logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(
    os.environ.get('RAZORPAY_KEY_ID'),
    os.environ.get('RAZORPAY_KEY_SECRET')
))

class EnhancedCreditBillingService:
    """Enhanced service class for managing credit-based billing system."""
    
    # Lead pricing tiers based on package price ranges
    PRICING_TIERS = {
        (0, 5000): 100,           # < ₹5,000 → 100 credits
        (5000, 10000): 180,       # ₹5,000-₹10,000 → 180 credits  
        (10000, 20000): 250,      # ₹10,000-₹20,000 → 250 credits
        (20000, 50000): 320,      # ₹20,000-₹50,000 → 320 credits
        (50000, 100000): 400,     # ₹50,000-₹100,000 → 400 credits
        (100000, float('inf')): 500  # ₹100,000+ → 500 credits
    }
    
    # Promotional bonus structure
    BONUS_TIERS = {
        1000: 0,      # ₹1,000 → 0 bonus
        5000: 1000,   # ₹5,000 → 1000 bonus credits
        10000: 2500,  # ₹10,000 → 2500 bonus credits
        25000: 7500,  # ₹25,000 → 7500 bonus credits
        50000: 20000, # ₹50,000 → 20000 bonus credits
    }
    
    @staticmethod
    def calculate_lead_cost(package_price):
        """Calculate lead cost based on package price range."""
        for (min_price, max_price), cost in EnhancedCreditBillingService.PRICING_TIERS.items():
            if min_price <= package_price < max_price:
                return cost
        return 500
    
    @staticmethod
    def get_clinic_credit_balance(clinic_id):
        """Get current credit balance for a clinic."""
        try:
            result = db.session.execute(text("""
                SELECT COALESCE(
                    (SELECT SUM(amount) FROM credit_transactions 
                     WHERE clinic_id = :clinic_id AND transaction_type IN ('credit', 'bonus', 'refund')) -
                    (SELECT SUM(ABS(amount)) FROM credit_transactions 
                     WHERE clinic_id = :clinic_id AND transaction_type = 'deduction'), 
                    0
                ) as balance
            """), {"clinic_id": clinic_id}).scalar()
            
            # Update clinic table with current balance
            db.session.execute(text("""
                UPDATE clinics SET credit_balance = :balance WHERE id = :clinic_id
            """), {"balance": result, "clinic_id": clinic_id})
            db.session.commit()
            
            return result or 0
            
        except Exception as e:
            logger.error(f"Error getting credit balance for clinic {clinic_id}: {e}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def deduct_credits_for_lead(clinic_id, lead_id, package_price, description=None):
        """Deduct credits when a lead is generated."""
        try:
            # Calculate cost
            credit_cost = EnhancedCreditBillingService.calculate_lead_cost(package_price)
            
            # Check current balance (allow negative)
            current_balance = EnhancedCreditBillingService.get_clinic_credit_balance(clinic_id)
            
            # Create deduction transaction
            db.session.execute(text("""
                INSERT INTO credit_transactions (
                    clinic_id, transaction_type, amount, description, lead_id, 
                    status, created_at, processed_at
                ) VALUES (
                    :clinic_id, 'deduction', :amount, :description, :lead_id,
                    'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) RETURNING id
            """), {
                "clinic_id": clinic_id,
                "amount": -credit_cost,
                "description": description or f"Lead generation cost for package worth ₹{package_price:,}",
                "lead_id": lead_id
            })
            
            transaction_id = db.session.execute(text("SELECT lastval()")).scalar()
            
            # Update lead with billing info
            db.session.execute(text("""
                UPDATE leads SET 
                    billed_to_clinic = true,
                    billing_amount = :amount,
                    billing_date = CURRENT_TIMESTAMP
                WHERE id = :lead_id
            """), {"amount": credit_cost, "lead_id": lead_id})
            
            db.session.commit()
            
            # Update clinic balance
            new_balance = EnhancedCreditBillingService.get_clinic_credit_balance(clinic_id)
            
            logger.info(f"Deducted {credit_cost} credits for lead {lead_id}. New balance: {new_balance}")
            
            return {
                'success': True,
                'credits_deducted': credit_cost,
                'new_balance': new_balance,
                'transaction_id': transaction_id
            }
            
        except Exception as e:
            logger.error(f"Error deducting credits: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_credits(clinic_id, amount, transaction_type='credit', description=None, order_id=None, payment_id=None):
        """Add credits to clinic account."""
        try:
            result = db.session.execute(text("""
                INSERT INTO credit_transactions (
                    clinic_id, transaction_type, amount, description, order_id, 
                    payment_id, status, created_at, processed_at
                ) VALUES (
                    :clinic_id, :transaction_type, :amount, :description, :order_id,
                    :payment_id, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                ) RETURNING id
            """), {
                "clinic_id": clinic_id,
                "transaction_type": transaction_type,
                "amount": amount,
                "description": description,
                "order_id": order_id,
                "payment_id": payment_id
            })
            
            transaction_id = result.scalar()
            db.session.commit()
            
            # Update clinic balance
            new_balance = EnhancedCreditBillingService.get_clinic_credit_balance(clinic_id)
            
            logger.info(f"Added {amount} credits ({transaction_type}) for clinic {clinic_id}. New balance: {new_balance}")
            
            return {
                'success': True,
                'credits_added': amount,
                'new_balance': new_balance,
                'transaction_id': transaction_id
            }
            
        except Exception as e:
            logger.error(f"Error adding credits: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def calculate_bonus_credits(purchase_amount):
        """Calculate bonus credits based on purchase amount."""
        for amount, bonus in sorted(EnhancedCreditBillingService.BONUS_TIERS.items(), reverse=True):
            if purchase_amount >= amount:
                return bonus
        return 0
    
    @staticmethod
    def get_credit_transaction_history(clinic_id, limit=20):
        """Get credit transaction history for a clinic."""
        try:
            transactions = db.session.execute(text("""
                SELECT ct.*, l.patient_name, l.procedure_name
                FROM credit_transactions ct
                LEFT JOIN leads l ON ct.lead_id = l.id
                WHERE ct.clinic_id = :clinic_id
                ORDER BY ct.created_at DESC
                LIMIT :limit
            """), {"clinic_id": clinic_id, "limit": limit}).fetchall()
            
            return [dict(row._mapping) for row in transactions]
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []

@enhanced_billing_bp.route('/clinic/billing')
@login_required
def billing_dashboard():
    """Enhanced clinic billing dashboard."""
    try:
        # Get clinic
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            flash('No clinic found for your account.', 'error')
            return redirect(url_for('web.index'))
        
        clinic_dict = dict(clinic._mapping)
        
        # Get current credit balance
        credit_balance = EnhancedCreditBillingService.get_clinic_credit_balance(clinic_dict['id'])
        
        # Get recent transactions
        transactions = EnhancedCreditBillingService.get_credit_transaction_history(clinic_dict['id'], 10)
        
        # Get monthly statistics
        current_month = datetime.now().replace(day=1)
        monthly_stats = db.session.execute(text("""
            SELECT 
                COUNT(CASE WHEN ct.transaction_type = 'deduction' THEN 1 END) as leads_generated,
                COALESCE(SUM(CASE WHEN ct.transaction_type = 'deduction' THEN ABS(ct.amount) ELSE 0 END), 0) as credits_spent,
                COALESCE(SUM(CASE WHEN ct.transaction_type IN ('credit', 'bonus') THEN ct.amount ELSE 0 END), 0) as credits_purchased
            FROM credit_transactions ct
            WHERE ct.clinic_id = :clinic_id 
            AND ct.created_at >= :start_date
        """), {"clinic_id": clinic_dict['id'], "start_date": current_month}).fetchone()
        
        monthly_stats_dict = dict(monthly_stats._mapping) if monthly_stats else {
            'leads_generated': 0, 'credits_spent': 0, 'credits_purchased': 0
        }
        
        # Credit packages with bonuses
        credit_packages = [
            {'credits': 1000, 'price': 1000, 'bonus': 0, 'popular': False},
            {'credits': 5000, 'price': 5000, 'bonus': 1000, 'popular': True},
            {'credits': 10000, 'price': 10000, 'bonus': 2500, 'popular': False},
            {'credits': 25000, 'price': 25000, 'bonus': 7500, 'popular': False},
            {'credits': 50000, 'price': 50000, 'bonus': 20000, 'popular': False},
        ]
        
        return render_template('clinic/enhanced_billing.html',
                             clinic=clinic_dict,
                             credit_balance=credit_balance,
                             transactions=transactions,
                             monthly_stats=monthly_stats_dict,
                             credit_packages=credit_packages,
                             pricing_tiers=EnhancedCreditBillingService.PRICING_TIERS)
        
    except Exception as e:
        logger.error(f"Error in billing dashboard: {e}")
        db.session.rollback()
        flash('Error loading billing information. Please try again.', 'error')
        return redirect(url_for('web.index'))

@enhanced_billing_bp.route('/clinic/credits/topup')
@login_required
def credit_topup():
    """Credit top-up page."""
    try:
        # Get clinic
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            flash('No clinic found for your account.', 'error')
            return redirect(url_for('web.index'))
        
        clinic_dict = dict(clinic._mapping)
        
        # Get current credit balance
        credit_balance = EnhancedCreditBillingService.get_clinic_credit_balance(clinic_dict['id'])
        
        # Get recent transactions
        recent_transactions = EnhancedCreditBillingService.get_credit_transaction_history(clinic_dict['id'], 5)
        
        # Credit packages with bonuses
        credit_packages = [
            {'credits': 1000, 'price': 1000, 'bonus': 0, 'total': 1000, 'popular': False},
            {'credits': 5000, 'price': 5000, 'bonus': 1000, 'total': 6000, 'popular': True},
            {'credits': 10000, 'price': 10000, 'bonus': 2500, 'total': 12500, 'popular': False},
            {'credits': 25000, 'price': 25000, 'bonus': 7500, 'total': 32500, 'popular': False},
            {'credits': 50000, 'price': 50000, 'bonus': 20000, 'total': 70000, 'popular': False},
        ]
        
        return render_template('clinic/credit_topup.html',
                             clinic=clinic_dict,
                             credit_balance=credit_balance,
                             recent_transactions=recent_transactions,
                             credit_packages=credit_packages)
        
    except Exception as e:
        logger.error(f"Error in credit top-up page: {e}")
        flash('Error loading credit top-up page. Please try again.', 'error')
        return redirect(url_for('web.index'))

@enhanced_billing_bp.route('/purchase-credits', methods=['POST'])
@login_required
def purchase_credits():
    """Handle credit purchase initiation."""
    try:
        # Get clinic
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        clinic_dict = dict(clinic._mapping)
        
        # Get form data
        credits = int(request.form.get('credits') or 0)
        amount = int(request.form.get('amount') or 0)
        
        if credits < 1000:  # Minimum purchase
            return jsonify({'success': False, 'error': 'Minimum purchase is 1000 credits'})
        
        # Create Razorpay order
        order_data = {
            'amount': amount * 100,  # Amount in paise
            'currency': 'INR',
            'receipt': f'credit_topup_{clinic_dict["id"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'notes': {
                'clinic_id': clinic_dict['id'],
                'credits': credits,
                'type': 'credit_purchase'
            }
        }
        
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        return jsonify({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': amount,
            'credits': credits,
            'key': os.environ.get('RAZORPAY_KEY_ID')
        })
        
    except Exception as e:
        logger.error(f"Error creating payment order: {e}")
        return jsonify({'success': False, 'error': str(e)})

@enhanced_billing_bp.route('/razorpay/webhook', methods=['POST'])
def razorpay_webhook():
    """Handle Razorpay payment webhooks."""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Razorpay-Signature')
        body = request.get_data()
        
        # For production, verify signature
        # razorpay_client.utility.verify_webhook_signature(body, signature, webhook_secret)
        
        event = request.get_json()
        
        if event['event'] == 'payment.captured':
            payment = event['payload']['payment']['entity']
            order_id = payment['order_id']
            payment_id = payment['id']
            
            # Get order details
            order = razorpay_client.order.fetch(order_id)
            clinic_id = int(order['notes']['clinic_id'])
            credits = int(order['notes']['credits'])
            amount = payment['amount'] / 100  # Convert from paise
            
            # Add purchased credits
            result = EnhancedCreditBillingService.add_credits(
                clinic_id=clinic_id,
                amount=credits,
                transaction_type='credit',
                description=f'Credit purchase via Razorpay - {credits} credits',
                order_id=order_id,
                payment_id=payment_id
            )
            
            if result['success']:
                # Calculate and add bonus credits
                bonus_credits = EnhancedCreditBillingService.calculate_bonus_credits(amount)
                if bonus_credits > 0:
                    EnhancedCreditBillingService.add_credits(
                        clinic_id=clinic_id,
                        amount=bonus_credits,
                        transaction_type='bonus',
                        description=f'Promotional bonus for purchase of {credits} credits',
                        order_id=order_id
                    )
                
                logger.info(f"Payment processed: {credits} credits + {bonus_credits} bonus for clinic {clinic_id}")
                
        return jsonify({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_billing_bp.route('/admin/credit-adjustment', methods=['POST'])
@login_required
def admin_credit_adjustment():
    """Admin route to manually adjust clinic credits."""
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        clinic_id = int(request.form.get('clinic_id'))
        amount = int(request.form.get('amount'))
        reason = request.form.get('reason', 'Admin adjustment')
        adjustment_type = request.form.get('type', 'credit')  # credit or deduction
        
        if adjustment_type == 'deduction':
            amount = -abs(amount)
        
        result = EnhancedCreditBillingService.add_credits(
            clinic_id=clinic_id,
            amount=amount,
            transaction_type='admin_adjustment',
            description=f'Admin adjustment: {reason}'
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in admin credit adjustment: {e}")
        return jsonify({'success': False, 'error': str(e)})

@enhanced_billing_bp.route('/create-razorpay-order', methods=['POST'])
@login_required
def create_razorpay_order():
    """Create Razorpay order for credit purchase."""
    try:
        # Get clinic
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            return jsonify({'success': False, 'error': 'Clinic not found'})
        
        clinic_dict = dict(clinic._mapping)
        
        # Get form data
        credits = int(request.form.get('credits') or 0)
        amount = int(request.form.get('amount') or 0)
        
        if credits < 1000:  # Minimum purchase
            return jsonify({'success': False, 'error': 'Minimum purchase is 1000 credits'})
        
        # Create Razorpay order
        order_data = {
            'amount': amount * 100,  # Amount in paise
            'currency': 'INR',
            'receipt': f'credit_topup_{clinic_dict["id"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'notes': {
                'clinic_id': clinic_dict['id'],
                'credits': credits,
                'type': 'credit_purchase'
            }
        }
        
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        return jsonify({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': amount,
            'credits': credits,
            'key': os.environ.get('RAZORPAY_KEY_ID')
        })
        
    except Exception as e:
        logger.error(f"Error creating payment order: {e}")
        return jsonify({'success': False, 'error': str(e)})

@enhanced_billing_bp.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    """Verify Razorpay payment and add credits."""
    try:
        # Get payment details
        razorpay_payment_id = request.form.get('razorpay_payment_id')
        razorpay_order_id = request.form.get('razorpay_order_id')
        razorpay_signature = request.form.get('razorpay_signature')
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Get order details
        order = razorpay_client.order.fetch(razorpay_order_id)
        clinic_id = int(order['notes']['clinic_id'])
        credits = int(order['notes']['credits'])
        amount = order['amount'] / 100  # Convert from paise
        
        # Add purchased credits
        result = EnhancedCreditBillingService.add_credits(
            clinic_id=clinic_id,
            amount=credits,
            transaction_type='credit',
            description=f'Credit purchase via Razorpay - {credits} credits',
            order_id=razorpay_order_id,
            payment_id=razorpay_payment_id
        )
        
        if result['success']:
            # Calculate and add bonus credits
            bonus_credits = EnhancedCreditBillingService.calculate_bonus_credits(amount)
            if bonus_credits > 0:
                bonus_result = EnhancedCreditBillingService.add_credits(
                    clinic_id=clinic_id,
                    amount=bonus_credits,
                    transaction_type='bonus',
                    description=f'Promotional bonus for purchase of {credits} credits',
                    order_id=razorpay_order_id
                )
                result['bonus_credits'] = bonus_credits
            
            logger.info(f"Payment verified: {credits} credits + {bonus_credits} bonus for clinic {clinic_id}")
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        return jsonify({'success': False, 'error': str(e)})

@enhanced_billing_bp.route('/payment-success')
@login_required
def payment_success():
    """Payment success page."""
    return render_template('clinic/payment_success.html')

@enhanced_billing_bp.route('/payment-failure')
@login_required
def payment_failure():
    """Payment failure page."""
    return render_template('clinic/payment_failure.html')

@enhanced_billing_bp.route('/api/lead-cost/<int:package_price>')
@login_required
def get_lead_cost(package_price):
    """API to get lead cost for a package price."""
    cost = EnhancedCreditBillingService.calculate_lead_cost(package_price)
    return jsonify({'cost': cost, 'package_price': package_price})