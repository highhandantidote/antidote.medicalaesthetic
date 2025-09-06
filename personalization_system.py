"""
Complete Personalization System Implementation
Integrates anonymous user tracking with homepage content personalization.
"""

import hashlib
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from app import db
from models import UserInteraction, UserCategoryAffinity, Procedure, Category, Doctor, Community

class PersonalizationEngine:
    """
    Core personalization engine that tracks anonymous users and personalizes content.
    Uses browser fingerprinting for anonymous tracking without requiring login.
    """
    
    @staticmethod
    def create_browser_fingerprint(user_agent, ip_address, accept_language):
        """Create a unique browser fingerprint for anonymous user tracking."""
        fingerprint_data = f"{user_agent}:{ip_address}:{accept_language}"
        return hashlib.md5(fingerprint_data.encode()).hexdigest()
    
    @staticmethod
    def track_user_interaction(fingerprint, interaction_type, target_type=None, target_id=None, metadata=None):
        """Track user interactions for personalization."""
        try:
            # Create interaction record
            interaction = UserInteraction()
            interaction.user_id = fingerprint
            interaction.session_id = metadata.get('session_id', '') if metadata else ''
            interaction.interaction_type = interaction_type
            interaction.target_type = target_type
            interaction.target_id = target_id
            interaction.extra_data = json.dumps(metadata) if metadata else None
            interaction.timestamp = datetime.utcnow()
            
            db.session.add(interaction)
            db.session.commit()
            
            # Update category affinity if viewing procedure or category
            if target_type == 'category' and target_id:
                PersonalizationEngine.update_category_affinity(fingerprint, target_id, interaction_type)
            elif target_type == 'procedure' and target_id:
                # Get procedure's category and update affinity
                procedure = Procedure.query.get(target_id)
                if procedure and procedure.category_id:
                    PersonalizationEngine.update_category_affinity(fingerprint, procedure.category_id, interaction_type)
                    
        except Exception as e:
            print(f"Error tracking interaction: {e}")
            db.session.rollback()
    
    @staticmethod
    def update_category_affinity(fingerprint, category_id, interaction_type):
        """Update user's affinity score for a category based on interaction."""
        try:
            # Get or create affinity record
            affinity = UserCategoryAffinity.query.filter_by(
                user_id=fingerprint,
                category_id=category_id
            ).first()
            
            if not affinity:
                affinity = UserCategoryAffinity()
                affinity.user_id = fingerprint
                affinity.category_id = category_id
                affinity.affinity_score = 0.0
                affinity.last_updated = datetime.utcnow()
                db.session.add(affinity)
            
            # Update affinity score based on interaction type
            score_increment = {
                'view': 0.1,
                'click': 0.2,
                'search': 0.15,
                'form_submit': 0.3,
                'save': 0.25
            }.get(interaction_type, 0.1)
            
            affinity.affinity_score = min(1.0, affinity.affinity_score + score_increment)
            affinity.last_updated = datetime.utcnow()
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error updating category affinity: {e}")
            db.session.rollback()
    
    @staticmethod
    def get_personalized_categories(fingerprint, limit=6):
        """Get personalized categories based on user's interaction history."""
        try:
            # Get top categories by affinity score
            top_affinities = db.session.query(UserCategoryAffinity)\
                .filter_by(user_id=fingerprint)\
                .order_by(UserCategoryAffinity.affinity_score.desc())\
                .limit(limit).all()
            
            if top_affinities:
                category_ids = [a.category_id for a in top_affinities]
                categories = Category.query.filter(Category.id.in_(category_ids)).all()
                # Sort by affinity score order
                category_dict = {c.id: c for c in categories}
                return [category_dict[cid] for cid in category_ids if cid in category_dict]
            
            # Fallback to popular categories
            return PersonalizationEngine.get_popular_categories(limit)
            
        except Exception as e:
            print(f"Error getting personalized categories: {e}")
            return PersonalizationEngine.get_popular_categories(limit)
    
    @staticmethod
    def get_personalized_procedures(fingerprint, limit=6):
        """Get personalized procedures based on user's category preferences."""
        try:
            # Get user's top category affinities
            top_affinities = db.session.query(UserCategoryAffinity)\
                .filter_by(user_id=fingerprint)\
                .order_by(UserCategoryAffinity.affinity_score.desc())\
                .limit(3).all()
            
            if top_affinities:
                category_ids = [a.category_id for a in top_affinities]
                procedures = Procedure.query.filter(Procedure.category_id.in_(category_ids))\
                    .order_by(Procedure.id.desc())\
                    .limit(limit).all()
                
                if procedures:
                    return procedures
            
            # Fallback to popular procedures
            return PersonalizationEngine.get_popular_procedures(limit)
            
        except Exception as e:
            print(f"Error getting personalized procedures: {e}")
            return PersonalizationEngine.get_popular_procedures(limit)
    
    @staticmethod
    def get_personalized_doctors(fingerprint, limit=9):
        """Get personalized doctors based on user's procedure interests."""
        try:
            # Get procedures from user's preferred categories
            top_affinities = db.session.query(UserCategoryAffinity)\
                .filter_by(user_id=fingerprint)\
                .order_by(UserCategoryAffinity.affinity_score.desc())\
                .limit(3).all()
            
            if top_affinities:
                category_ids = [a.category_id for a in top_affinities]
                procedures = Procedure.query.filter(Procedure.category_id.in_(category_ids)).all()
                procedure_ids = [p.id for p in procedures]
                
                if procedure_ids:
                    # Get doctors who perform these procedures
                    doctors = db.session.execute(text("""
                        SELECT DISTINCT d.* FROM doctors d
                        JOIN doctor_procedures dp ON d.id = dp.doctor_id
                        WHERE dp.procedure_id IN :procedure_ids
                        AND d.is_verified = true
                        ORDER BY d.rating DESC
                        LIMIT :limit
                    """), {'procedure_ids': tuple(procedure_ids), 'limit': limit}).fetchall()
                    
                    if doctors:
                        # Convert to Doctor objects
                        doctor_ids = [d[0] for d in doctors]  # d[0] is the id column
                        return Doctor.query.filter(Doctor.id.in_(doctor_ids)).all()
            
            # Fallback to top-rated doctors
            return PersonalizationEngine.get_popular_doctors(limit)
            
        except Exception as e:
            print(f"Error getting personalized doctors: {e}")
            return PersonalizationEngine.get_popular_doctors(limit)
    
    @staticmethod
    def get_popular_categories(limit=6):
        """Get popular categories as fallback - use procedure count and randomization."""
        try:
            # Get categories with the most procedures (more popular)
            # and randomize the order to avoid static results
            result = db.session.execute(text("""
                SELECT c.* FROM categories c
                JOIN (
                    SELECT category_id, COUNT(*) as proc_count
                    FROM procedures 
                    WHERE category_id IS NOT NULL
                    GROUP BY category_id
                ) as pc ON c.id = pc.category_id
                ORDER BY pc.proc_count DESC, RANDOM()
                LIMIT :limit
            """), {'limit': limit}).fetchall()
            
            # Convert to Category objects
            categories = []
            for row in result:
                category = Category.query.get(row.id)
                if category:
                    categories.append(category)
            
            return categories
        except Exception as e:
            print(f"Error getting popular categories: {e}")
            # Emergency fallback - still randomize
            try:
                return Category.query.order_by(text('RANDOM()')).limit(limit).all()
            except:
                return []
    
    @staticmethod
    def get_popular_procedures(limit=6):
        """Get popular procedures as fallback."""
        try:
            return Procedure.query.order_by(Procedure.id.desc()).limit(limit).all()
        except:
            return []
    
    @staticmethod
    def get_popular_doctors(limit=9):
        """Get popular doctors as fallback."""
        try:
            return Doctor.query.filter_by(is_verified=True)\
                .order_by(Doctor.rating.desc().nullslast())\
                .limit(limit).all()
        except:
            return []
    
    @staticmethod
    def get_user_interaction_summary(fingerprint):
        """Get summary of user's interaction patterns."""
        try:
            # Get recent interactions
            recent_interactions = UserInteraction.query.filter_by(user_id=fingerprint)\
                .filter(UserInteraction.timestamp >= datetime.utcnow() - timedelta(days=30))\
                .all()
            
            # Count by type
            interaction_counts = {}
            target_types = {}
            
            for interaction in recent_interactions:
                interaction_counts[interaction.interaction_type] = interaction_counts.get(interaction.interaction_type, 0) + 1
                if interaction.target_type:
                    target_types[interaction.target_type] = target_types.get(interaction.target_type, 0) + 1
            
            return {
                'total_interactions': len(recent_interactions),
                'interaction_types': interaction_counts,
                'target_types': target_types,
                'first_seen': recent_interactions[-1].timestamp if recent_interactions else None,
                'last_seen': recent_interactions[0].timestamp if recent_interactions else None
            }
            
        except Exception as e:
            print(f"Error getting user interaction summary: {e}")
            return {
                'total_interactions': 0,
                'interaction_types': {},
                'target_types': {},
                'first_seen': None,
                'last_seen': None
            }