"""
Integrated Billing System - Complete Implementation
Combines all billing features into existing infrastructure.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import text
from models import db
import logging
import os

integrated_billing_bp = Blueprint('integrated_billing', __name__)
logger = logging.getLogger(__name__)

class BillingService:
    """Complete billing service for credit management."""
    
    # Lead pricing tiers based on package price ranges
    PRICING_TIERS = {
        (0, 5000): 100,           # < ₹5,000 → 100 credits
        (5000, 10000): 180,       # ₹5,000-₹10,000 → 180 credits  
        (10000, 20000): 250,      # ₹10,000-₹20,000 → 250 credits
        (20000, 50000): 320,      # ₹20,000-₹50,000 → 320 credits
        (50000, 100000): 400,     # ₹50,000-₹100,000 → 400 credits
        (100000, float('inf')): 500  # ₹100,000+ → 500 credits
    }
    
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
        try:
            package_price = float(package_price)
            for (min_price, max_price), cost in BillingService.PRICING_TIERS.items():
                if min_price <= package_price < max_price:
                    return cost
            return 500
        except (ValueError, TypeError):
            return 100  # Default minimum cost
    
    @staticmethod
    def get_clinic_credit_balance(clinic_id):
        """Get current credit balance for a clinic."""
        try:
            result = db.session.execute(text("""
                SELECT COALESCE(
                    (SELECT SUM(amount) FROM credit_transactions 
                     WHERE clinic_id = :clinic_id AND transaction_type IN ('credit', 'bonus', 'refund', 'admin_adjustment')) -
                    (SELECT SUM(ABS(amount)) FROM credit_transactions 
                     WHERE clinic_id = :clinic_id AND transaction_type = 'deduction'), 
                    0
                ) as balance
            """), {"clinic_id": clinic_id}).scalar()
            
            balance = result or 0
            
            # Update clinic table with current balance
            db.session.execute(text("""
                UPDATE clinics SET credit_balance = :balance WHERE id = :clinic_id
            """), {"balance": balance, "clinic_id": clinic_id})
            db.session.commit()
            
            return balance
            
        except Exception as e:
            logger.error(f"Error getting credit balance for clinic {clinic_id}: {e}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def deduct_credits_for_lead(clinic_id, lead_id, package_price, description=None):
        """Deduct credits when a lead is generated."""
        try:
            # Calculate cost
            credit_cost = BillingService.calculate_lead_cost(package_price)
            
            # Check current balance (allow negative as per requirements)
            current_balance = BillingService.get_clinic_credit_balance(clinic_id)
            
            # Create deduction transaction
            db.session.execute(text("""
                INSERT INTO credit_transactions (
                    clinic_id, transaction_type, amount, description, lead_id, 
                    status, created_at, processed_at
                ) VALUES (
                    :clinic_id, 'deduction', :amount, :description, :lead_id,
                    'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """), {
                "clinic_id": clinic_id,
                "amount": -credit_cost,
                "description": description or f"Lead generation cost for package worth ₹{package_price:,}",
                "lead_id": lead_id
            })
            
            # Update lead with billing info
            db.session.execute(text("""
                UPDATE leads SET 
                    billed_to_clinic = true,
                    billing_amount = :amount,
                    billing_date = CURRENT_TIMESTAMP
                WHERE id = :lead_id
            """), {"amount": credit_cost, "lead_id": lead_id})
            
            db.session.commit()
            
            # Get new balance
            new_balance = BillingService.get_clinic_credit_balance(clinic_id)
            
            logger.info(f"Deducted {credit_cost} credits for lead {lead_id}. New balance: {new_balance}")
            
            return {
                'success': True,
                'credits_deducted': credit_cost,
                'new_balance': new_balance,
                'is_negative': new_balance < 0
            }
            
        except Exception as e:
            logger.error(f"Error deducting credits: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_credits(clinic_id, amount, transaction_type='credit', description=None, order_id=None):
        """Add credits to clinic account."""
        try:
            db.session.execute(text("""
                INSERT INTO credit_transactions (
                    clinic_id, transaction_type, amount, description, order_id,
                    status, created_at, processed_at
                ) VALUES (
                    :clinic_id, :transaction_type, :amount, :description, :order_id,
                    'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """), {
                "clinic_id": clinic_id,
                "transaction_type": transaction_type,
                "amount": amount,
                "description": description,
                "order_id": order_id
            })
            
            db.session.commit()
            
            # Update clinic balance
            new_balance = BillingService.get_clinic_credit_balance(clinic_id)
            
            logger.info(f"Added {amount} credits ({transaction_type}) for clinic {clinic_id}. New balance: {new_balance}")
            
            return {
                'success': True,
                'credits_added': amount,
                'new_balance': new_balance
            }
            
        except Exception as e:
            logger.error(f"Error adding credits: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_transaction_history(clinic_id, limit=20):
        """Get credit transaction history for a clinic."""
        try:
            transactions = db.session.execute(text("""
                SELECT 
                    ct.*,
                    l.patient_name,
                    l.procedure_name,
                    l.mobile_number
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

# Integrate with existing lead generation
def integrate_billing_with_lead_generation():
    """Function to modify existing lead generation routes."""
    
    def enhanced_lead_submission(original_function):
        """Decorator to add billing to lead submission."""
        def wrapper(*args, **kwargs):
            try:
                # Call original function
                result = original_function(*args, **kwargs)
                
                # Extract lead and package info from result/request
                if request.method == 'POST' and 'package_id' in request.form:
                    package_id = request.form.get('package_id')
                    
                    # Get package price
                    package = db.session.execute(text("""
                        SELECT price FROM packages WHERE id = :package_id
                    """), {"package_id": package_id}).fetchone()
                    
                    if package:
                        package_price = package[0]
                        
                        # Get clinic ID from package
                        clinic = db.session.execute(text("""
                            SELECT clinic_id FROM packages WHERE id = :package_id
                        """), {"package_id": package_id}).fetchone()
                        
                        if clinic:
                            clinic_id = clinic[0]
                            
                            # Get the latest lead for this clinic
                            lead = db.session.execute(text("""
                                SELECT id FROM leads 
                                WHERE clinic_id = :clinic_id 
                                ORDER BY created_at DESC 
                                LIMIT 1
                            """), {"clinic_id": clinic_id}).fetchone()
                            
                            if lead:
                                lead_id = lead[0]
                                
                                # Deduct credits
                                billing_result = BillingService.deduct_credits_for_lead(
                                    clinic_id, lead_id, package_price
                                )
                                
                                if billing_result['success']:
                                    logger.info(f"Credits deducted successfully for lead {lead_id}")
                                    
                                    # Add alert if balance is negative
                                    if billing_result['is_negative']:
                                        flash(f'Lead submitted! Clinic balance is now negative (₹{abs(billing_result["new_balance"])}). Please top up credits.', 'warning')
                                else:
                                    logger.error(f"Failed to deduct credits: {billing_result.get('error')}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error in enhanced lead submission: {e}")
                return original_function(*args, **kwargs)
        
        return wrapper
    
    return enhanced_lead_submission

@integrated_billing_bp.route('/clinic/billing-dashboard')
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
        credit_balance = BillingService.get_clinic_credit_balance(clinic_dict['id'])
        
        # Get recent transactions
        transactions = BillingService.get_transaction_history(clinic_dict['id'], 10)
        
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
            {'credits': 1000, 'price': 1000, 'bonus': 0, 'popular': False, 'total': 1000},
            {'credits': 5000, 'price': 5000, 'bonus': 1000, 'popular': True, 'total': 6000},
            {'credits': 10000, 'price': 10000, 'bonus': 2500, 'popular': False, 'total': 12500},
            {'credits': 25000, 'price': 25000, 'bonus': 7500, 'popular': False, 'total': 32500},
            {'credits': 50000, 'price': 50000, 'bonus': 20000, 'popular': False, 'total': 70000},
        ]
        
        return render_template('clinic/billing_dashboard.html',
                             clinic=clinic_dict,
                             credit_balance=credit_balance,
                             transactions=transactions,
                             monthly_stats=monthly_stats_dict,
                             credit_packages=credit_packages,
                             pricing_tiers=BillingService.PRICING_TIERS)
        
    except Exception as e:
        logger.error(f"Error in billing dashboard: {e}")
        db.session.rollback()
        flash('Error loading billing information. Please try again.', 'error')
        return redirect(url_for('web.index'))

@integrated_billing_bp.route('/credits/topup', methods=['GET', 'POST'])
@login_required
def credit_topup():
    """Credit top-up page with package selection and payment options."""
    try:
        # Get clinic for current user
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic profile found. Please create your clinic profile first.', 'info')
            return redirect(url_for('clinic.create_clinic'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get current credit balance
        credit_balance = BillingService.get_clinic_credit_balance(clinic['id'])
        
        # Get recent transactions
        recent_transactions = BillingService.get_transaction_history(clinic['id'], 5)
        
        # Credit packages with bonuses
        credit_packages = [
            {'credits': 1000, 'price': 1000, 'bonus': 0, 'popular': False, 'total': 1000},
            {'credits': 5000, 'price': 5000, 'bonus': 500, 'popular': True, 'total': 5500},
            {'credits': 10000, 'price': 10000, 'bonus': 1500, 'popular': False, 'total': 11500},
            {'credits': 25000, 'price': 25000, 'bonus': 5000, 'popular': False, 'total': 30000},
            {'credits': 50000, 'price': 50000, 'bonus': 12500, 'popular': False, 'total': 62500},
        ]
        
        return render_template('clinic/credit_topup.html',
                             clinic=clinic,
                             credit_balance=credit_balance,
                             recent_transactions=recent_transactions,
                             credit_packages=credit_packages,
                             razorpay_key_id=os.environ.get('RAZORPAY_KEY_ID'))
        
    except Exception as e:
        logger.error(f"Error in credit top-up page: {e}")
        flash('Error loading top-up page. Please try again.', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

@integrated_billing_bp.route('/credits/history')
@login_required
def credit_history():
    """Credit transaction history page."""
    try:
        # Get clinic for current user
        clinic_result = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic_result:
            flash('No clinic profile found.', 'error')
            return redirect(url_for('clinic.clinic_dashboard'))
        
        clinic = dict(clinic_result._mapping)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Get total count
        total_count = db.session.execute(text("""
            SELECT COUNT(*) FROM credit_transactions WHERE clinic_id = :clinic_id
        """), {"clinic_id": clinic['id']}).scalar() or 0
        
        # Get transactions for current page
        offset = (page - 1) * per_page
        transactions = db.session.execute(text("""
            SELECT 
                ct.*,
                l.patient_name,
                l.procedure_name,
                l.mobile_number
            FROM credit_transactions ct
            LEFT JOIN leads l ON ct.lead_id = l.id
            WHERE ct.clinic_id = :clinic_id
            ORDER BY ct.created_at DESC
            LIMIT :limit OFFSET :offset
        """), {"clinic_id": clinic['id'], "limit": per_page, "offset": offset}).fetchall()
        
        transactions_list = [dict(row._mapping) for row in transactions]
        
        # Get current balance
        credit_balance = BillingService.get_clinic_credit_balance(clinic['id'])
        
        return render_template('clinic/credit_history.html',
                             clinic=clinic,
                             transactions=transactions_list,
                             credit_balance=credit_balance,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=(total_count + per_page - 1) // per_page)
        
    except Exception as e:
        logger.error(f"Error in credit history: {e}")
        flash('Error loading transaction history.', 'error')
        return redirect(url_for('clinic.clinic_dashboard'))

@integrated_billing_bp.route('/admin/credit-management')
@login_required
def admin_credit_management():
    """Admin interface for credit management."""
    if not current_user.role == 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('web.index'))
    
    try:
        # Get all clinics with credit balances
        clinics = db.session.execute(text("""
            SELECT 
                c.id,
                c.name,
                c.city,
                c.credit_balance,
                COUNT(ct.id) as total_transactions,
                COALESCE(SUM(CASE WHEN ct.transaction_type = 'deduction' THEN ABS(ct.amount) ELSE 0 END), 0) as total_spent,
                COALESCE(SUM(CASE WHEN ct.transaction_type IN ('credit', 'bonus') THEN ct.amount ELSE 0 END), 0) as total_purchased
            FROM clinics c
            LEFT JOIN credit_transactions ct ON c.id = ct.clinic_id
            WHERE c.is_active = true
            GROUP BY c.id, c.name, c.city, c.credit_balance
            ORDER BY c.credit_balance ASC
        """)).fetchall()
        
        clinics_data = [dict(row._mapping) for row in clinics]
        
        # Get overall statistics
        overall_stats = db.session.execute(text("""
            SELECT 
                COUNT(DISTINCT clinic_id) as active_clinics,
                COALESCE(SUM(CASE WHEN transaction_type = 'deduction' THEN ABS(amount) ELSE 0 END), 0) as total_revenue,
                COALESCE(SUM(CASE WHEN transaction_type IN ('credit', 'bonus') THEN amount ELSE 0 END), 0) as total_credits_issued,
                COUNT(CASE WHEN transaction_type = 'deduction' THEN 1 END) as total_leads_billed
            FROM credit_transactions
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """)).fetchone()
        
        overall_stats_dict = dict(overall_stats._mapping) if overall_stats else {
            'active_clinics': 0, 'total_revenue': 0, 'total_credits_issued': 0, 'total_leads_billed': 0
        }
        
        return render_template('admin/credit_management.html',
                             clinics=clinics_data,
                             overall_stats=overall_stats_dict)
        
    except Exception as e:
        logger.error(f"Error in admin credit management: {e}")
        flash('Error loading credit management. Please try again.', 'error')
        return redirect(url_for('web.admin_dashboard'))

@integrated_billing_bp.route('/admin/adjust-credits', methods=['POST'])
@login_required
def adjust_credits():
    """Admin route to manually adjust clinic credits."""
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        clinic_id = int(request.form.get('clinic_id') or 0)
        amount = int(request.form.get('amount') or 0)
        reason = request.form.get('reason', 'Admin adjustment')
        adjustment_type = request.form.get('type', 'credit')  # credit or deduction
        
        if adjustment_type == 'deduction':
            amount = -abs(amount)
        
        result = BillingService.add_credits(
            clinic_id=clinic_id,
            amount=amount,
            transaction_type='admin_adjustment',
            description=f'Admin adjustment by {current_user.name}: {reason}'
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in admin credit adjustment: {e}")
        return jsonify({'success': False, 'error': str(e)})

@integrated_billing_bp.route('/api/lead-cost/<int:package_price>')
def get_lead_cost_api(package_price):
    """API to get lead cost for a package price."""
    cost = BillingService.calculate_lead_cost(package_price)
    return jsonify({
        'cost': cost, 
        'package_price': package_price,
        'tier_info': f'₹{package_price:,} package → {cost} credits'
    })

@integrated_billing_bp.route('/clinic/low-balance-alert')
@login_required
def low_balance_alert():
    """Check if clinic has low balance and show alert."""
    try:
        clinic = db.session.execute(text("""
            SELECT * FROM clinics WHERE owner_user_id = :user_id
        """), {"user_id": current_user.id}).fetchone()
        
        if not clinic:
            return jsonify({'has_alert': False})
        
        clinic_dict = dict(clinic._mapping)
        balance = BillingService.get_clinic_credit_balance(clinic_dict['id'])
        
        # Show alert if balance is less than 500 credits
        has_alert = balance < 500
        
        return jsonify({
            'has_alert': has_alert,
            'balance': balance,
            'is_negative': balance < 0,
            'alert_message': f'Low credit balance: {balance} credits remaining' if has_alert and balance >= 0 else f'Negative balance: {abs(balance)} credits overdrawn' if balance < 0 else None
        })
        
    except Exception as e:
        logger.error(f"Error checking balance alert: {e}")
        return jsonify({'has_alert': False})

# Initialize billing system
def init_billing_system(app):
    """Initialize the billing system with the Flask app."""
    app.register_blueprint(integrated_billing_bp)
    logger.info("Integrated billing system initialized successfully")