"""
Credit Billing System for Antidote Platform
Handles dynamic lead pricing, credit deductions, and payment processing
"""

from datetime import datetime
from sqlalchemy import text
from app import db
import logging

logger = logging.getLogger(__name__)

class CreditBillingService:
    """Service class for managing credit-based billing system."""
    
    # Lead pricing tiers based on package price ranges
    PRICING_TIERS = {
        (0, 5000): 100,           # < ₹5,000 → 100 credits
        (5000, 10000): 180,       # ₹5,000-₹10,000 → 180 credits  
        (10000, 20000): 250,      # ₹10,000-₹20,000 → 250 credits
        (20000, 50000): 320,      # ₹20,000-₹50,000 → 320 credits
        (50000, 100000): 400,     # ₹50,000-₹100,000 → 400 credits
        (100000, float('inf')): 500  # ₹100,000+ → 500 credits
    }
    
    @staticmethod
    def calculate_lead_cost(package_price):
        """
        Calculate lead cost based on package price using dynamic pricing.
        
        Args:
            package_price (int): Package price in INR
            
        Returns:
            int: Credit cost for the lead
        """
        from dynamic_lead_pricing import DynamicPricingService
        return DynamicPricingService.calculate_lead_cost(package_price)
    
    @staticmethod
    def get_clinic_credit_balance(clinic_id):
        """
        Get current credit balance for a clinic.
        
        Args:
            clinic_id (int): Clinic ID
            
        Returns:
            int: Current credit balance
        """
        try:
            result = db.session.execute(
                text("SELECT credit_balance FROM clinics WHERE id = :clinic_id"),
                {'clinic_id': clinic_id}
            ).fetchone()
            
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting credit balance for clinic {clinic_id}: {e}")
            return 0
    
    @staticmethod
    def deduct_credits_for_lead(clinic_id, lead_id, package_id, action_type):
        """
        Deduct credits for a new lead based on package price and action type.
        
        Args:
            clinic_id (int): Clinic ID
            lead_id (int): Lead ID
            package_id (int): Package ID
            action_type (str): 'chat' or 'call'
            
        Returns:
            dict: Result with success status and details
        """
        try:
            # Get package price
            package_result = db.session.execute(
                text("SELECT price_actual FROM packages WHERE id = :package_id"),
                {'package_id': package_id}
            ).fetchone()
            
            if not package_result:
                return {'success': False, 'message': 'Package not found'}
            
            package_price = package_result[0]
            
            # Calculate lead cost based on package price
            base_cost = CreditBillingService.calculate_lead_cost(package_price)
            
            # Apply action type multiplier (if needed in future)
            credit_cost = base_cost
            
            # Get current balance
            current_balance = CreditBillingService.get_clinic_credit_balance(clinic_id)
            
            # Allow negative balance with alert (as per requirements)
            new_balance = current_balance - credit_cost
            
            # Update clinic balance and stats
            db.session.execute(text("""
                UPDATE clinics 
                SET credit_balance = :new_balance,
                    total_credits_used = COALESCE(total_credits_used, 0) + :cost,
                    lead_count = COALESCE(lead_count, 0) + 1
                WHERE id = :clinic_id
            """), {
                'new_balance': new_balance,
                'cost': credit_cost,
                'clinic_id': clinic_id
            })
            
            # Create credit transaction record
            db.session.execute(text("""
                INSERT INTO credit_transactions (
                    clinic_id, amount, transaction_type, description, 
                    lead_id, created_at, status
                ) VALUES (
                    :clinic_id, :amount, 'deduction', :description,
                    :lead_id, :created_at, 'completed'
                )
            """), {
                'clinic_id': clinic_id,
                'amount': -credit_cost,  # Negative for deduction
                'description': f'Lead generation cost for {action_type} action (Package ₹{package_price:,})',
                'lead_id': lead_id,
                'created_at': datetime.utcnow()
            })
            
            # Create lead quality tracking record
            CreditBillingService.create_lead_quality_tracking(lead_id)
            
            # Check if balance is negative and flag for alert
            low_balance_alert = new_balance < 0
            
            db.session.commit()
            
            return {
                'success': True,
                'credit_cost': credit_cost,
                'previous_balance': current_balance,
                'new_balance': new_balance,
                'low_balance_alert': low_balance_alert,
                'message': f'₹{credit_cost} credits deducted for {action_type} lead'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deducting credits for lead {lead_id}: {e}")
            return {'success': False, 'message': 'Error processing credit deduction'}
    
    @staticmethod
    def create_lead_quality_tracking(lead_id, ip_address=None, user_agent=None, referrer_url=None):
        """
        Create lead quality tracking record for spam detection.
        
        Args:
            lead_id (int): Lead ID
            ip_address (str): Client IP address
            user_agent (str): Browser user agent
            referrer_url (str): Referrer URL
        """
        try:
            # Get lead contact info for duplicate detection
            lead_result = db.session.execute(
                text("SELECT contact_info FROM leads WHERE id = :lead_id"),
                {'lead_id': lead_id}
            ).fetchone()
            
            if not lead_result:
                return
            
            contact_info = lead_result[0] or ''
            
            # Extract phone number for frequency check
            phone_frequency = 1
            if contact_info:
                # Count how many times this contact info appeared
                frequency_result = db.session.execute(
                    text("SELECT COUNT(*) FROM leads WHERE contact_info ILIKE :pattern"),
                    {'pattern': f'%{contact_info.split(",")[1].strip() if "," in contact_info else contact_info}%'}
                ).fetchone()
                phone_frequency = frequency_result[0] if frequency_result else 1
            
            # Calculate spam risk score based on frequency
            spam_risk_score = min(0.9, (phone_frequency - 1) * 0.2)
            
            # Determine quality flags
            quality_flags = []
            if phone_frequency > 3:
                quality_flags.append('duplicate_phone')
            if phone_frequency > 5:
                quality_flags.append('high_frequency')
            
            # Insert quality tracking record
            db.session.execute(text("""
                INSERT INTO lead_quality_tracking (
                    lead_id, phone_number_frequency, spam_risk_score,
                    quality_flags, ip_address, user_agent, referrer_url,
                    is_flagged, created_at
                ) VALUES (
                    :lead_id, :phone_frequency, :spam_risk_score,
                    :quality_flags, :ip_address, :user_agent, :referrer_url,
                    :is_flagged, :created_at
                )
            """), {
                'lead_id': lead_id,
                'phone_frequency': phone_frequency,
                'spam_risk_score': spam_risk_score,
                'quality_flags': quality_flags,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'referrer_url': referrer_url,
                'is_flagged': spam_risk_score > 0.5,
                'created_at': datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error creating lead quality tracking for lead {lead_id}: {e}")
    
    @staticmethod
    def process_credit_topup(clinic_id, amount, payment_id=None, order_id=None, promo_code=None):
        """
        Process credit top-up for a clinic.
        
        Args:
            clinic_id (int): Clinic ID
            amount (int): Top-up amount in credits
            payment_id (str): Payment gateway payment ID
            order_id (str): Payment gateway order ID
            promo_code (str): Promotional code if used
            
        Returns:
            dict: Result with success status and details
        """
        try:
            # Validate minimum top-up amount (₹1000 = 1000 credits)
            if amount < 1000:
                return {'success': False, 'message': 'Minimum top-up amount is ₹1,000'}
            
            # Check for promotional bonuses
            bonus_credits = 0
            if promo_code:
                bonus_credits = CreditBillingService.calculate_promo_bonus(amount, promo_code)
            
            total_credits = amount + bonus_credits
            
            # Get current balance
            current_balance = CreditBillingService.get_clinic_credit_balance(clinic_id)
            new_balance = current_balance + total_credits
            
            # Update clinic balance and stats
            db.session.execute(text("""
                UPDATE clinics 
                SET credit_balance = :new_balance,
                    total_credits_purchased = COALESCE(total_credits_purchased, 0) + :total_credits
                WHERE id = :clinic_id
            """), {
                'new_balance': new_balance,
                'total_credits': total_credits,
                'clinic_id': clinic_id
            })
            
            # Create credit transaction record
            db.session.execute(text("""
                INSERT INTO credit_transactions (
                    clinic_id, amount, transaction_type, description,
                    order_id, payment_id, monetary_value, status, created_at, processed_at
                ) VALUES (
                    :clinic_id, :amount, 'purchase', :description,
                    :order_id, :payment_id, :monetary_value, 'completed', :created_at, :processed_at
                )
            """), {
                'clinic_id': clinic_id,
                'amount': total_credits,
                'description': f'Credit top-up ₹{amount:,}' + (f' + ₹{bonus_credits} bonus' if bonus_credits else ''),
                'order_id': order_id,
                'payment_id': payment_id,
                'monetary_value': amount,  # INR value
                'created_at': datetime.utcnow(),
                'processed_at': datetime.utcnow()
            })
            
            # Update promo code usage if applicable
            if promo_code and bonus_credits > 0:
                CreditBillingService.update_promo_usage(promo_code)
            
            db.session.commit()
            
            return {
                'success': True,
                'credits_added': amount,
                'bonus_credits': bonus_credits,
                'total_credits': total_credits,
                'previous_balance': current_balance,
                'new_balance': new_balance,
                'message': f'₹{amount:,} credits added successfully' + (f' (₹{bonus_credits} bonus)' if bonus_credits else '')
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error processing credit top-up for clinic {clinic_id}: {e}")
            return {'success': False, 'message': 'Error processing credit top-up'}
    
    @staticmethod
    def calculate_promo_bonus(topup_amount, promo_code):
        """
        Calculate bonus credits for promotional codes.
        
        Args:
            topup_amount (int): Top-up amount
            promo_code (str): Promotional code
            
        Returns:
            int: Bonus credits to add
        """
        try:
            # Get active promotion
            promo_result = db.session.execute(text("""
                SELECT bonus_type, bonus_value, max_bonus, min_topup_amount
                FROM credit_promotions 
                WHERE promo_code = :promo_code 
                AND is_active = TRUE 
                AND start_date <= CURRENT_TIMESTAMP 
                AND end_date >= CURRENT_TIMESTAMP
                AND (usage_limit IS NULL OR usage_count < usage_limit)
            """), {'promo_code': promo_code}).fetchone()
            
            if not promo_result:
                return 0
            
            bonus_type, bonus_value, max_bonus, min_topup = promo_result
            
            # Check minimum top-up requirement
            if topup_amount < min_topup:
                return 0
            
            # Calculate bonus
            if bonus_type == 'percentage':
                bonus = int(topup_amount * bonus_value / 100)
            else:  # fixed_amount
                bonus = bonus_value
            
            # Apply maximum bonus limit
            if max_bonus and bonus > max_bonus:
                bonus = max_bonus
            
            return bonus
            
        except Exception as e:
            logger.error(f"Error calculating promo bonus for code {promo_code}: {e}")
            return 0
    
    @staticmethod
    def update_promo_usage(promo_code):
        """Update promotional code usage count."""
        try:
            db.session.execute(text("""
                UPDATE credit_promotions 
                SET usage_count = usage_count + 1 
                WHERE promo_code = :promo_code
            """), {'promo_code': promo_code})
        except Exception as e:
            logger.error(f"Error updating promo usage for code {promo_code}: {e}")
    
    @staticmethod
    def create_lead_dispute(lead_id, clinic_id, reason, description, evidence_urls=None):
        """
        Create a lead dispute for refund request.
        
        Args:
            lead_id (int): Lead ID
            clinic_id (int): Clinic ID
            reason (str): Dispute reason
            description (str): Dispute description
            evidence_urls (list): List of evidence URLs
            
        Returns:
            dict: Result with success status and dispute ID
        """
        try:
            dispute_result = db.session.execute(text("""
                INSERT INTO lead_disputes (
                    lead_id, clinic_id, reason, description, evidence_urls, created_at
                ) VALUES (
                    :lead_id, :clinic_id, :reason, :description, :evidence_urls, :created_at
                ) RETURNING id
            """), {
                'lead_id': lead_id,
                'clinic_id': clinic_id,
                'reason': reason,
                'description': description,
                'evidence_urls': evidence_urls or [],
                'created_at': datetime.utcnow()
            }).fetchone()
            
            dispute_id = dispute_result[0] if dispute_result else None
            
            db.session.commit()
            
            return {
                'success': True,
                'dispute_id': dispute_id,
                'message': 'Dispute submitted successfully. Our team will review it within 24 hours.'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating lead dispute: {e}")
            return {'success': False, 'message': 'Error submitting dispute'}
    
    @staticmethod
    def get_credit_transaction_history(clinic_id, limit=50, offset=0):
        """
        Get credit transaction history for a clinic.
        
        Args:
            clinic_id (int): Clinic ID
            limit (int): Number of records to fetch
            offset (int): Offset for pagination
            
        Returns:
            list: List of transaction records
        """
        try:
            transactions = db.session.execute(text("""
                SELECT id, transaction_type, amount, description, status,
                       monetary_value, created_at, processed_at
                FROM credit_transactions 
                WHERE clinic_id = :clinic_id 
                ORDER BY created_at DESC 
                LIMIT :limit OFFSET :offset
            """), {
                'clinic_id': clinic_id,
                'limit': limit,
                'offset': offset
            }).fetchall()
            
            return [dict(row._mapping) for row in transactions]
            
        except Exception as e:
            logger.error(f"Error getting transaction history for clinic {clinic_id}: {e}")
            return []