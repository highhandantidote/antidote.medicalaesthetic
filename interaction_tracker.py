"""
Universal Interaction Tracker
Core system for tracking all user interactions and converting to leads
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from flask import session, request, g
from sqlalchemy import text
from app import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InteractionTracker:
    """Core class for tracking user interactions across the platform."""
    
    @staticmethod
    def get_or_create_session_id():
        """Get existing session ID or create new one."""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        return session['session_id']
    
    @staticmethod
    def track_interaction(interaction_type, data=None, source_page=None):
        """
        Track any user interaction in the system.
        
        Args:
            interaction_type: Type of interaction (ai_recommendation, face_analysis, etc.)
            data: Dictionary of interaction data
            source_page: Source page URL
        
        Returns:
            interaction_id: ID of created interaction record
        """
        try:
            session_id = InteractionTracker.get_or_create_session_id()
            user_id = getattr(g, 'current_user', {}).get('id') if hasattr(g, 'current_user') else None
            
            # Prepare interaction data
            interaction_data = {
                'session_id': session_id,
                'user_id': user_id,
                'interaction_type': interaction_type,
                'source_page': source_page or request.path if request else None,
                'data': json.dumps(data) if data else None,
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.headers.get('User-Agent') if request else None,
                'referrer_url': request.referrer if request else None
            }
            
            # Insert interaction record
            result = db.session.execute(text("""
                INSERT INTO user_interactions 
                (session_id, user_id, interaction_type, source_page, data, ip_address, user_agent, referrer_url)
                VALUES (:session_id, :user_id, :interaction_type, :source_page, :data, :ip_address, :user_agent, :referrer_url)
                RETURNING id
            """), interaction_data)
            
            interaction_id = result.fetchone()[0]
            db.session.commit()
            
            # Update session tracking
            InteractionTracker.update_session_tracking(session_id, source_page)
            
            logger.info(f"Tracked interaction: {interaction_type} for session {session_id[:8]}...")
            return interaction_id
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error tracking interaction: {e}")
            return None
    
    @staticmethod
    def update_session_tracking(session_id, current_page=None):
        """Update session tracking with page visit."""
        try:
            # Get or create session record
            session_result = db.session.execute(text("""
                SELECT id, page_count, first_page, created_at 
                FROM user_sessions 
                WHERE session_id = :session_id
            """), {'session_id': session_id}).fetchone()
            
            if session_result:
                # Update existing session
                session_data = dict(session_result._mapping)
                time_diff = datetime.now() - session_data['created_at']
                total_seconds = int(time_diff.total_seconds())
                
                db.session.execute(text("""
                    UPDATE user_sessions 
                    SET page_count = page_count + 1,
                        last_page = :current_page,
                        total_time_seconds = :total_seconds,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = :session_id
                """), {
                    'session_id': session_id,
                    'current_page': current_page,
                    'total_seconds': total_seconds
                })
            else:
                # Create new session
                user_id = getattr(g, 'current_user', {}).get('id') if hasattr(g, 'current_user') else None
                
                db.session.execute(text("""
                    INSERT INTO user_sessions 
                    (session_id, user_id, ip_address, user_agent, referrer_url, first_page, last_page)
                    VALUES (:session_id, :user_id, :ip_address, :user_agent, :referrer_url, :first_page, :last_page)
                """), {
                    'session_id': session_id,
                    'user_id': user_id,
                    'ip_address': request.remote_addr if request else None,
                    'user_agent': request.headers.get('User-Agent') if request else None,
                    'referrer_url': request.referrer if request else None,
                    'first_page': current_page,
                    'last_page': current_page
                })
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating session tracking: {e}")

class LeadScorer:
    """Lead scoring system based on interactions and behavior."""
    
    @staticmethod
    def calculate_interaction_score(interaction_type, interaction_data=None):
        """Calculate base score for an interaction type."""
        try:
            # Get scoring rules from database
            rules_result = db.session.execute(text("""
                SELECT points, condition_field, condition_operator, condition_value
                FROM lead_scoring_rules 
                WHERE interaction_type = :interaction_type AND is_active = true
            """), {'interaction_type': interaction_type}).fetchall()
            
            total_score = 0
            
            for rule in rules_result:
                rule_data = dict(rule._mapping)
                base_points = rule_data['points']
                
                # Apply conditional scoring if data provided
                if interaction_data and rule_data['condition_field'] != 'base':
                    condition_met = LeadScorer.evaluate_condition(
                        interaction_data,
                        rule_data['condition_field'],
                        rule_data['condition_operator'],
                        rule_data['condition_value']
                    )
                    if condition_met:
                        total_score += base_points
                else:
                    # Base score for interaction type
                    if rule_data['condition_field'] == 'base':
                        total_score += base_points
            
            return min(total_score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating interaction score: {e}")
            return 50  # Default score
    
    @staticmethod
    def evaluate_condition(data, field, operator, value):
        """Evaluate scoring condition against interaction data."""
        try:
            field_value = data.get(field)
            
            if operator == 'equals':
                return str(field_value) == str(value)
            elif operator == 'greater_than':
                return float(field_value or 0) > float(value)
            elif operator == 'less_than':
                return float(field_value or 0) < float(value)
            elif operator == 'contains':
                return value.lower() in str(field_value).lower()
            elif operator == 'within_days':
                if field_value:
                    target_date = datetime.strptime(field_value, '%Y-%m-%d')
                    days_diff = (target_date - datetime.now()).days
                    return days_diff <= int(value)
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    @staticmethod
    def calculate_lead_score(session_id, additional_data=None):
        """Calculate comprehensive lead score for a session."""
        try:
            # Get all interactions for session
            interactions_result = db.session.execute(text("""
                SELECT interaction_type, data, created_at
                FROM user_interactions 
                WHERE session_id = :session_id
                ORDER BY created_at
            """), {'session_id': session_id}).fetchall()
            
            total_score = 0
            interaction_bonus = 0
            
            for interaction in interactions_result:
                interaction_data = dict(interaction._mapping)
                data = json.loads(interaction_data['data']) if interaction_data['data'] else {}
                
                # Add additional data if provided
                if additional_data:
                    data.update(additional_data)
                
                # Calculate score for this interaction
                interaction_score = LeadScorer.calculate_interaction_score(
                    interaction_data['interaction_type'], 
                    data
                )
                total_score += interaction_score
                
                # Bonus for multiple interactions
                interaction_bonus += 5
            
            # Get session engagement data
            session_result = db.session.execute(text("""
                SELECT page_count, total_time_seconds
                FROM user_sessions 
                WHERE session_id = :session_id
            """), {'session_id': session_id}).fetchone()
            
            if session_result:
                session_data = dict(session_result._mapping)
                
                # Engagement bonuses
                if session_data['page_count'] > 3:
                    total_score += 10  # Multiple page visits
                if session_data['total_time_seconds'] > 300:  # 5+ minutes
                    total_score += 15  # High time on site
            
            # Add interaction bonus (capped)
            total_score += min(interaction_bonus, 25)
            
            return min(total_score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating lead score: {e}")
            return 50  # Default score

class LeadConverter:
    """Convert high-value interactions to leads."""
    
    @staticmethod
    def should_convert_to_lead(session_id, interaction_type, interaction_data=None):
        """Determine if interaction should trigger lead conversion prompt."""
        try:
            # High-intent interaction types that should always prompt
            high_intent_types = ['ai_recommendation', 'face_analysis', 'appointment_booking', 'cost_calculator']
            
            if interaction_type in high_intent_types:
                return True
            
            # Check overall session score
            session_score = LeadScorer.calculate_lead_score(session_id, interaction_data)
            
            # Convert if score is high enough
            if session_score >= 70:
                return True
            
            # Check for multiple interactions
            interaction_count = db.session.execute(text("""
                SELECT COUNT(*) FROM user_interactions WHERE session_id = :session_id
            """), {'session_id': session_id}).scalar()
            
            if interaction_count >= 3:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking lead conversion criteria: {e}")
            return False
    
    @staticmethod
    def create_lead_from_interaction(interaction_id, contact_data):
        """Create a lead record from an interaction."""
        try:
            # Get interaction details
            interaction_result = db.session.execute(text("""
                SELECT ui.*, us.utm_source, us.utm_medium, us.utm_campaign
                FROM user_interactions ui
                LEFT JOIN user_sessions us ON ui.session_id = us.session_id
                WHERE ui.id = :interaction_id
            """), {'interaction_id': interaction_id}).fetchone()
            
            if not interaction_result:
                return None
            
            interaction = dict(interaction_result._mapping)
            interaction_data = json.loads(interaction['data']) if interaction['data'] else {}
            
            # Calculate lead score
            lead_score = LeadScorer.calculate_lead_score(interaction['session_id'], contact_data)
            
            # Determine engagement level
            engagement_level = 'high' if lead_score >= 80 else 'medium' if lead_score >= 60 else 'low'
            
            # Extract procedure name from interaction data
            procedure_name = LeadConverter.extract_procedure_name(interaction['interaction_type'], interaction_data)
            
            # Create lead record
            lead_result = db.session.execute(text("""
                INSERT INTO leads 
                (patient_name, mobile_number, email, city, procedure_name, source, 
                 interaction_id, lead_score, engagement_level, source_campaign,
                 utm_source, utm_medium, utm_campaign, status, created_at)
                VALUES 
                (:patient_name, :mobile_number, :email, :city, :procedure_name, :source,
                 :interaction_id, :lead_score, :engagement_level, :source_campaign,
                 :utm_source, :utm_medium, :utm_campaign, 'new', CURRENT_TIMESTAMP)
                RETURNING id
            """), {
                'patient_name': contact_data.get('name'),
                'mobile_number': contact_data.get('phone'),
                'email': contact_data.get('email'),
                'city': contact_data.get('city'),
                'procedure_name': procedure_name,
                'source': f"{interaction['interaction_type']}_form",
                'interaction_id': interaction_id,
                'lead_score': lead_score,
                'engagement_level': engagement_level,
                'source_campaign': interaction['source_page'],
                'utm_source': interaction.get('utm_source'),
                'utm_medium': interaction.get('utm_medium'),
                'utm_campaign': interaction.get('utm_campaign')
            })
            
            lead_id = lead_result.fetchone()[0]
            
            # Update interaction and session as converted
            db.session.execute(text("""
                UPDATE user_interactions 
                SET converted_to_lead = true, lead_id = :lead_id, updated_at = CURRENT_TIMESTAMP
                WHERE id = :interaction_id
            """), {'interaction_id': interaction_id, 'lead_id': lead_id})
            
            db.session.execute(text("""
                UPDATE user_sessions 
                SET converted_to_lead = true, lead_id = :lead_id, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = :session_id
            """), {'session_id': interaction['session_id'], 'lead_id': lead_id})
            
            db.session.commit()
            
            logger.info(f"Created lead {lead_id} from interaction {interaction_id}")
            return lead_id
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating lead from interaction: {e}")
            return None
    
    @staticmethod
    def extract_procedure_name(interaction_type, interaction_data):
        """Extract procedure name from interaction data."""
        try:
            if interaction_type == 'ai_recommendation':
                return interaction_data.get('primary_procedure', 'AI Recommended Treatment')
            elif interaction_type == 'face_analysis':
                return interaction_data.get('top_recommendation', 'Face Analysis Recommendation')
            elif interaction_type == 'cost_calculator':
                return interaction_data.get('selected_procedure', 'Cost Calculator Inquiry')
            elif interaction_type == 'appointment_booking':
                return interaction_data.get('procedure_name', 'Consultation Booking')
            elif interaction_type == 'package_inquiry':
                return interaction_data.get('package_name', 'Package Inquiry')
            else:
                return f"{interaction_type.replace('_', ' ').title()} Inquiry"
                
        except Exception:
            return "General Inquiry"

# Utility functions for easy integration
def track_user_interaction(interaction_type, data=None, source_page=None):
    """Convenient function to track interactions from anywhere in the app."""
    return InteractionTracker.track_interaction(interaction_type, data, source_page)

def should_show_contact_form(session_id, interaction_type, interaction_data=None):
    """Check if we should show contact form to user."""
    return LeadConverter.should_convert_to_lead(session_id, interaction_type, interaction_data)

def create_lead_from_form(interaction_id, form_data):
    """Create lead from form submission."""
    return LeadConverter.create_lead_from_interaction(interaction_id, form_data)