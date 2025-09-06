"""
Dynamic Lead Pricing Service
Provides admin-configurable lead pricing based on package values.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf, CSRFError
from datetime import datetime
from sqlalchemy import text
from models import db
import logging
import json

pricing_bp = Blueprint('lead_pricing', __name__)
logger = logging.getLogger(__name__)

class DynamicPricingService:
    """Service for dynamic lead pricing calculations."""
    
    _pricing_cache = None
    _cache_timestamp = None
    _cache_duration = 300  # 5 minutes
    
    @classmethod
    def get_pricing_tiers(cls, force_refresh=False):
        """Get all active pricing tiers with caching."""
        current_time = datetime.now().timestamp()
        
        # Check if cache is valid
        if (not force_refresh and 
            cls._pricing_cache is not None and 
            cls._cache_timestamp is not None and 
            (current_time - cls._cache_timestamp) < cls._cache_duration):
            return cls._pricing_cache
        
        try:
            result = db.session.execute(text("""
                SELECT id, tier_name, min_package_value, max_package_value, 
                       credit_cost, is_active, created_at, updated_at
                FROM lead_pricing_tiers 
                WHERE is_active = TRUE 
                ORDER BY min_package_value ASC
            """))
            
            tiers = [dict(row._mapping) for row in result.fetchall()]
            
            # Update cache
            cls._pricing_cache = tiers
            cls._cache_timestamp = current_time
            
            return tiers
            
        except Exception as e:
            logger.error(f"Error fetching pricing tiers: {e}")
            return []
    
    @classmethod
    def calculate_lead_cost(cls, package_value):
        """Calculate credit cost based on package value using dynamic pricing."""
        try:
            # Convert to integer if string
            if isinstance(package_value, str):
                package_value = int(float(package_value.replace(',', '')))
            
            package_value = int(package_value) if package_value else 0
            
            # Get pricing tiers
            tiers = cls.get_pricing_tiers()
            
            if not tiers:
                # Fallback to hardcoded pricing if no tiers configured
                logger.warning("No pricing tiers found, using fallback pricing")
                return cls._fallback_pricing(package_value)
            
            # Find matching tier
            for tier in tiers:
                min_val = tier['min_package_value']
                max_val = tier['max_package_value']
                
                # Check if package value falls within this tier
                if min_val <= package_value:
                    if max_val is None or package_value <= max_val:
                        logger.info(f"Package value {package_value} matched tier '{tier['tier_name']}' - Cost: {tier['credit_cost']} credits")
                        return tier['credit_cost']
            
            # If no tier matches, use the highest tier
            if tiers:
                highest_tier = max(tiers, key=lambda x: x['min_package_value'])
                logger.info(f"Package value {package_value} exceeded all tiers, using highest tier: {highest_tier['credit_cost']} credits")
                return highest_tier['credit_cost']
            
            # Final fallback
            return cls._fallback_pricing(package_value)
            
        except Exception as e:
            logger.error(f"Error calculating lead cost for package value {package_value}: {e}")
            return cls._fallback_pricing(package_value)
    
    @classmethod
    def _fallback_pricing(cls, package_value):
        """Fallback pricing logic if dynamic tiers fail."""
        if package_value <= 5000:
            return 100
        elif package_value <= 10000:
            return 150
        elif package_value <= 20000:
            return 200
        elif package_value <= 50000:
            return 300
        else:
            return 400
    
    @staticmethod
    def validate_tier_data(tier_data):
        """Validate pricing tier data for overlaps and gaps."""
        errors = []
        
        # Basic validation
        if not tier_data.get('tier_name'):
            errors.append("Tier name is required")
        
        try:
            min_val = int(tier_data.get('min_package_value', 0))
            max_val = int(tier_data.get('max_package_value', 0)) if tier_data.get('max_package_value') else None
            credit_cost = int(tier_data.get('credit_cost', 0))
        except (ValueError, TypeError):
            errors.append("Invalid numeric values")
            return errors
        
        if min_val < 0:
            errors.append("Minimum package value cannot be negative")
        
        if max_val is not None and max_val <= min_val:
            errors.append("Maximum package value must be greater than minimum")
        
        if credit_cost <= 0:
            errors.append("Credit cost must be positive")
        
        # Check for overlaps with existing tiers
        existing_tiers = DynamicPricingService.get_pricing_tiers(force_refresh=True)
        tier_id = tier_data.get('id')
        
        for existing_tier in existing_tiers:
            # Skip self when editing
            if tier_id and existing_tier['id'] == int(tier_id):
                continue
            
            existing_min = existing_tier['min_package_value']
            existing_max = existing_tier['max_package_value']
            
            # Check for overlaps
            if existing_max is None:
                if min_val >= existing_min:
                    errors.append(f"Overlaps with tier '{existing_tier['tier_name']}' (${existing_min:,}+)")
            else:
                if not (max_val is not None and max_val < existing_min) and not (min_val > existing_max):
                    errors.append(f"Overlaps with tier '{existing_tier['tier_name']}' (${existing_min:,}-${existing_max:,})")
        
        return errors

    @staticmethod
    def create_pricing_tier(tier_data, admin_user_id):
        """Create a new pricing tier."""
        try:
            # Validate data
            errors = DynamicPricingService.validate_tier_data(tier_data)
            if errors:
                return False, errors
            
            # Insert new tier
            result = db.session.execute(text("""
                INSERT INTO lead_pricing_tiers 
                (tier_name, min_package_value, max_package_value, credit_cost, created_by)
                VALUES (:tier_name, :min_val, :max_val, :credit_cost, :admin_user_id)
                RETURNING id
            """), {
                "tier_name": tier_data['tier_name'],
                "min_val": int(tier_data['min_package_value']),
                "max_val": int(tier_data['max_package_value']) if tier_data.get('max_package_value') else None,
                "credit_cost": int(tier_data['credit_cost']),
                "admin_user_id": admin_user_id
            })
            
            tier_id = result.fetchone()[0]
            
            # Log audit trail
            db.session.execute(text("""
                INSERT INTO lead_pricing_audit (tier_id, action, new_values, changed_by)
                VALUES (:tier_id, 'CREATE', :new_values, :admin_user_id)
            """), {
                "tier_id": tier_id,
                "new_values": json.dumps(tier_data),
                "admin_user_id": admin_user_id
            })
            
            db.session.commit()
            
            # Clear cache
            DynamicPricingService._pricing_cache = None
            
            logger.info(f"Created pricing tier '{tier_data['tier_name']}' by user {admin_user_id}")
            return True, tier_id
            
        except Exception as e:
            logger.error(f"Error creating pricing tier: {e}")
            db.session.rollback()
            return False, [str(e)]

    @staticmethod
    def update_pricing_tier(tier_id, tier_data, admin_user_id):
        """Update an existing pricing tier."""
        try:
            # Get existing tier for audit
            existing_result = db.session.execute(text("""
                SELECT tier_name, min_package_value, max_package_value, credit_cost
                FROM lead_pricing_tiers WHERE id = :tier_id
            """), {"tier_id": tier_id})
            
            existing_tier = existing_result.fetchone()
            if not existing_tier:
                return False, ["Tier not found"]
            
            # Validate new data
            tier_data['id'] = tier_id
            errors = DynamicPricingService.validate_tier_data(tier_data)
            if errors:
                return False, errors
            
            # Update tier
            db.session.execute(text("""
                UPDATE lead_pricing_tiers 
                SET tier_name = :tier_name,
                    min_package_value = :min_val,
                    max_package_value = :max_val,
                    credit_cost = :credit_cost,
                    updated_at = NOW()
                WHERE id = :tier_id
            """), {
                "tier_id": tier_id,
                "tier_name": tier_data['tier_name'],
                "min_val": int(tier_data['min_package_value']),
                "max_val": int(tier_data['max_package_value']) if tier_data.get('max_package_value') else None,
                "credit_cost": int(tier_data['credit_cost'])
            })
            
            # Log audit trail
            old_values = dict(existing_tier._mapping)
            db.session.execute(text("""
                INSERT INTO lead_pricing_audit (tier_id, action, old_values, new_values, changed_by)
                VALUES (:tier_id, 'UPDATE', :old_values, :new_values, :admin_user_id)
            """), {
                "tier_id": tier_id,
                "old_values": json.dumps(old_values),
                "new_values": json.dumps(tier_data),
                "admin_user_id": admin_user_id
            })
            
            db.session.commit()
            
            # Clear cache
            DynamicPricingService._pricing_cache = None
            
            logger.info(f"Updated pricing tier {tier_id} by user {admin_user_id}")
            return True, tier_id
            
        except Exception as e:
            logger.error(f"Error updating pricing tier: {e}")
            db.session.rollback()
            return False, [str(e)]

    @staticmethod
    def delete_pricing_tier(tier_id, admin_user_id):
        """Delete a pricing tier and its related audit records."""
        try:
            # Get existing tier for logging
            existing_result = db.session.execute(text("""
                SELECT tier_name, min_package_value, max_package_value, credit_cost
                FROM lead_pricing_tiers WHERE id = :tier_id
            """), {"tier_id": tier_id})
            
            existing_tier = existing_result.fetchone()
            if not existing_tier:
                return False, "Tier not found"
            
            # First, delete all audit records for this tier
            db.session.execute(text("""
                DELETE FROM lead_pricing_audit WHERE tier_id = :tier_id
            """), {"tier_id": tier_id})
            
            # Then delete the tier itself
            db.session.execute(text("""
                DELETE FROM lead_pricing_tiers WHERE id = :tier_id
            """), {"tier_id": tier_id})
            
            db.session.commit()
            
            # Clear cache
            DynamicPricingService._pricing_cache = None
            
            logger.info(f"Deleted pricing tier '{existing_tier.tier_name}' (ID: {tier_id}) by user {admin_user_id}")
            return True, "Tier deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting pricing tier: {e}")
            db.session.rollback()
            return False, str(e)

# API Routes for pricing calculations
@pricing_bp.route('/api/pricing/calculate', methods=['POST'])
def calculate_pricing():
    """API endpoint to calculate lead cost based on package value."""
    try:
        data = request.get_json()
        package_value = data.get('package_value', 0)
        
        credit_cost = DynamicPricingService.calculate_lead_cost(package_value)
        
        return jsonify({
            'success': True,
            'package_value': package_value,
            'credit_cost': credit_cost
        })
        
    except Exception as e:
        logger.error(f"Error in pricing calculation API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pricing_bp.route('/api/pricing/preview', methods=['POST'])
def preview_pricing_impact():
    """Preview how pricing changes affect existing packages."""
    try:
        data = request.get_json()
        new_tiers = data.get('tiers', [])
        
        # Get sample packages to test against
        packages_result = db.session.execute(text("""
            SELECT id, name, price_actual 
            FROM packages 
            WHERE price_actual IS NOT NULL 
            ORDER BY price_actual ASC 
            LIMIT 20
        """))
        
        packages = [dict(row._mapping) for row in packages_result.fetchall()]
        
        # Calculate current vs new costs
        preview_data = []
        for package in packages:
            current_cost = DynamicPricingService.calculate_lead_cost(package['price_actual'])
            
            # Calculate new cost using provided tiers
            new_cost = current_cost  # Default to current if no matching tier
            for tier in new_tiers:
                min_val = int(tier.get('min_package_value', 0))
                max_val = int(tier.get('max_package_value', 0)) if tier.get('max_package_value') else None
                
                if min_val <= package['price_actual']:
                    if max_val is None or package['price_actual'] <= max_val:
                        new_cost = int(tier.get('credit_cost', current_cost))
                        break
            
            preview_data.append({
                'package_name': package['name'],
                'package_price': package['price_actual'],
                'current_cost': current_cost,
                'new_cost': new_cost,
                'difference': new_cost - current_cost
            })
        
        return jsonify({
            'success': True,
            'preview_data': preview_data
        })
        
    except Exception as e:
        logger.error(f"Error in pricing preview: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Admin routes
def admin_required(f):
    """Decorator to require admin access."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('web.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@pricing_bp.route('/admin/lead-pricing')
@login_required
@admin_required
def pricing_management():
    """Admin page for managing lead pricing tiers."""
    try:
        # Get all pricing tiers
        pricing_tiers = DynamicPricingService.get_pricing_tiers(force_refresh=True)
        
        # Calculate pricing statistics
        pricing_stats = {
            'total_tiers': len(pricing_tiers),
            'avg_cost': int(sum(t['credit_cost'] for t in pricing_tiers) / len(pricing_tiers)) if pricing_tiers else 0,
            'min_cost': min(t['credit_cost'] for t in pricing_tiers) if pricing_tiers else 0,
            'max_cost': max(t['credit_cost'] for t in pricing_tiers) if pricing_tiers else 0
        }
        
        return render_template('admin/lead_pricing.html', 
                             pricing_tiers=pricing_tiers,
                             pricing_stats=pricing_stats)
        
    except Exception as e:
        logger.error(f"Error loading pricing management page: {e}")
        flash('Error loading pricing data', 'danger')
        return redirect(url_for('admin_credit.credit_dashboard'))

@pricing_bp.route('/admin/pricing/create', methods=['POST'])
@login_required
@admin_required
def create_pricing_tier():
    """Create a new pricing tier."""
    try:
        data = request.get_json()
        
        # Skip CSRF validation for authenticated admin users making API calls
        pass
        
        success, result = DynamicPricingService.create_pricing_tier(data, current_user.id)
        
        if success:
            return jsonify({'success': True, 'tier_id': result})
        else:
            return jsonify({'success': False, 'errors': result})
            
    except Exception as e:
        logger.error(f"Error creating pricing tier: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@pricing_bp.route('/admin/pricing/update', methods=['POST'])
@login_required
@admin_required
def update_pricing_tier():
    """Update an existing pricing tier."""
    try:
        data = request.get_json()
        tier_id = data.get('tier_id')
        
        if not tier_id:
            return jsonify({'success': False, 'message': 'Tier ID is required'}), 400
        
        # Skip CSRF validation for authenticated admin users making API calls
        pass
        
        success, result = DynamicPricingService.update_pricing_tier(tier_id, data, current_user.id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'errors': result})
            
    except Exception as e:
        logger.error(f"Error updating pricing tier: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@pricing_bp.route('/admin/pricing/delete', methods=['POST'])
@login_required
@admin_required
def delete_pricing_tier():
    """Delete a pricing tier."""
    try:
        data = request.get_json()
        tier_id = data.get('tier_id')
        
        if not tier_id:
            return jsonify({'success': False, 'message': 'Tier ID is required'}), 400
        
        # Skip CSRF validation for authenticated admin users making API calls
        pass
        
        success, message = DynamicPricingService.delete_pricing_tier(tier_id, current_user.id)
        
        return jsonify({'success': success, 'message': message})
            
    except Exception as e:
        logger.error(f"Error deleting pricing tier: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

