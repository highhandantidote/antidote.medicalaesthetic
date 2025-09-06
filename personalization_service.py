"""
Personalization service for anonymous user tracking and content recommendations.
This service handles user behavior tracking without requiring login.
"""

from flask import Blueprint, request, jsonify, session
from sqlalchemy import text, func
from app import db
from models import Category, Procedure, Doctor, UserInteraction, UserCategoryAffinity, CategoryRelationship
import json
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

personalization_bp = Blueprint('personalization', __name__, url_prefix='/api/personalization')

class PersonalizationService:
    
    @staticmethod
    def create_browser_fingerprint(user_agent, ip_address, accept_language=""):
        """Create a unique browser fingerprint for anonymous user tracking."""
        fingerprint_data = f"{user_agent}|{ip_address}|{accept_language}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    @staticmethod
    def get_or_create_anonymous_user(fingerprint):
        """Get or create an anonymous user record with consistent integer ID."""
        try:
            # Convert fingerprint to consistent integer ID
            user_id = PersonalizationService.fingerprint_to_user_id(fingerprint)
            
            # Check if user exists by ID (not fingerprint since we're not using anonymous_users table)
            # Since we're using user_interactions table directly, we just need to ensure the user_id is valid
            # For simplicity, we'll create a minimal user record if needed
            
            return {"id": user_id, "fingerprint": fingerprint}
            
        except Exception as e:
            logger.error(f"Error in get_or_create_anonymous_user: {e}")
            return None
    
    @staticmethod
    def fingerprint_to_user_id(fingerprint):
        """Convert fingerprint string to consistent integer ID."""
        # Create a hash and convert to positive integer
        hash_obj = hashlib.sha256(fingerprint.encode())
        return abs(int(hash_obj.hexdigest()[:8], 16)) % (2**31 - 1)
    
    @staticmethod
    def track_interaction(user_id, session_id, interaction_type, target_type=None, target_id=None, metadata=None):
        """Track a user interaction for personalization."""
        try:
            interaction = UserInteraction(
                user_id=user_id,
                session_id=session_id,
                interaction_type=interaction_type,
                target_type=target_type,
                target_id=target_id,
                extra_data=json.dumps(metadata) if metadata else None
            )
            db.session.add(interaction)
            db.session.commit()
            
            # Update category affinity if applicable
            if target_type == 'category' and target_id:
                PersonalizationService.update_category_affinity(user_id, target_id, interaction_type)
            elif target_type == 'procedure' and target_id:
                # Get procedure's category and update affinity
                procedure = Procedure.query.get(target_id)
                if procedure and procedure.category_id:
                    PersonalizationService.update_category_affinity(user_id, procedure.category_id, interaction_type)
                    
            return True
        except Exception as e:
            logger.error(f"Error tracking interaction: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def update_category_affinity(user_id, category_id, interaction_type):
        """Update user's affinity score for a category."""
        try:
            # Define score increments based on interaction type
            score_increments = {
                'view': 0.1,
                'click': 0.2,
                'search': 0.15,
                'form_submit': 0.3,
                'bookmark': 0.25
            }
            
            increment = score_increments.get(interaction_type, 0.1)
            
            # Get or create affinity record
            affinity = UserCategoryAffinity.query.filter_by(
                user_id=user_id, 
                category_id=category_id
            ).first()
            
            if affinity:
                # Update existing affinity (with decay factor)
                affinity.affinity_score = min(1.0, affinity.affinity_score * 0.95 + increment)
                affinity.last_updated = datetime.utcnow()
            else:
                # Create new affinity
                affinity = UserCategoryAffinity(
                    user_id=user_id,
                    category_id=category_id,
                    affinity_score=increment
                )
                db.session.add(affinity)
            
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating category affinity: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_personalized_categories(user_id, limit=20):
        """Get personalized categories based on user's interests."""
        try:
            # Get user's top categories by affinity
            user_categories = db.session.query(
                UserCategoryAffinity.category_id,
                UserCategoryAffinity.affinity_score
            ).filter_by(user_id=user_id)\
             .order_by(UserCategoryAffinity.affinity_score.desc())\
             .limit(limit//2).all()
            
            category_ids = [cat.category_id for cat in user_categories]
            
            # Get related categories
            if category_ids:
                related_categories = db.session.query(
                    CategoryRelationship.related_category_id
                ).filter(
                    CategoryRelationship.primary_category_id.in_(category_ids),
                    CategoryRelationship.strength > 0.5
                ).distinct().limit(limit//2).all()
                
                category_ids.extend([rel.related_category_id for rel in related_categories])
            
            # Get categories with procedures and images
            if category_ids:
                categories = Category.query.filter(
                    Category.id.in_(category_ids),
                    Category.image_url.isnot(None),
                    Category.image_url != '/static/images/categories/default-procedure.jpg'
                ).all()
            else:
                # Fallback to popular categories
                categories = Category.query.filter(
                    Category.image_url.isnot(None),
                    Category.image_url != '/static/images/categories/default-procedure.jpg'
                ).limit(limit).all()
            
            return categories
        except Exception as e:
            logger.error(f"Error getting personalized categories: {e}")
            return []
    
    @staticmethod
    def get_personalized_procedures(user_id, limit=10):
        """Get personalized procedures based on user's interests."""
        try:
            # Get user's top categories
            user_categories = db.session.query(
                UserCategoryAffinity.category_id
            ).filter_by(user_id=user_id)\
             .order_by(UserCategoryAffinity.affinity_score.desc())\
             .limit(5).all()
            
            category_ids = [cat.category_id for cat in user_categories]
            
            if category_ids:
                # Get procedures from user's preferred categories
                procedures = Procedure.query.filter(
                    Procedure.category_id.in_(category_ids)
                ).order_by(func.random()).limit(limit).all()
            else:
                # Fallback to popular procedures
                procedures = Procedure.query.order_by(func.random()).limit(limit).all()
            
            return procedures
        except Exception as e:
            logger.error(f"Error getting personalized procedures: {e}")
            return []

# API Routes
@personalization_bp.route('/track', methods=['POST'])
def track_interaction():
    """API endpoint to track user interactions."""
    try:
        data = request.get_json()
        
        # Get user fingerprint from headers or data
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        fingerprint = PersonalizationService.create_browser_fingerprint(user_agent, ip_address)
        user_id = PersonalizationService.fingerprint_to_user_id(fingerprint)
        
        # Track the interaction
        success = PersonalizationService.track_interaction(
            user_id=str(user_id),
            session_id=data.get('sessionId', ''),
            interaction_type=data.get('type', 'view'),
            target_type=data.get('targetType'),
            target_id=data.get('targetId'),
            metadata=data.get('metadata')
        )
        
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error in track_interaction endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@personalization_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """API endpoint to get personalized recommendations."""
    try:
        # Get user fingerprint
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        fingerprint = PersonalizationService.create_browser_fingerprint(user_agent, ip_address)
        user_id = PersonalizationService.fingerprint_to_user_id(fingerprint)
        
        # Get personalized content
        categories = PersonalizationService.get_personalized_categories(str(user_id))
        procedures = PersonalizationService.get_personalized_procedures(str(user_id))
        
        return jsonify({
            'success': True,
            'categories': [{'id': c.id, 'name': c.name, 'image_url': c.image_url} for c in categories],
            'procedures': [{'id': p.id, 'name': p.procedure_name, 'category_id': p.category_id} for p in procedures]
        })
    except Exception as e:
        logger.error(f"Error in get_recommendations endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    @staticmethod
    def track_interaction(fingerprint, interaction_type, content_type, content_id, 
                         content_name="", page_url="", session_id=""):
        """Track user interaction for personalization."""
        try:
            # First ensure the anonymous user exists
            PersonalizationService.get_or_create_anonymous_user(fingerprint)
            
            # Convert fingerprint to consistent user ID
            user_id = PersonalizationService.fingerprint_to_user_id(fingerprint)
            
            # Insert interaction with the user ID
            db.session.execute(
                text("""INSERT INTO user_interactions 
                       (anonymous_user_id, interaction_type, content_type, content_id, 
                        content_name, page_url, session_id, created_at)
                       VALUES (:user_id, :type, :ctype, :cid, :cname, :page, :session, :now)"""),
                {
                    "user_id": user_id,
                    "type": interaction_type,
                    "ctype": content_type,
                    "cid": content_id,
                    "cname": content_name,
                    "page": page_url,
                    "session": session_id,
                    "now": datetime.utcnow()
                }
            )
            
            # Update user preferences based on interaction
            if content_type == "category" or content_type == "procedure":
                PersonalizationService.update_user_interests(fingerprint, content_type, content_id, content_name)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error tracking interaction: {e}")
            db.session.rollback()
    
    @staticmethod
    def update_user_interests(fingerprint, content_type, content_id, content_name):
        """Update user interest scores based on interactions."""
        try:
            # Get current user data
            result = db.session.execute(
                text("SELECT preferred_categories, interest_keywords FROM anonymous_users WHERE browser_fingerprint = :fp"),
                {"fp": fingerprint}
            ).fetchone()
            
            if result:
                categories = json.loads(result.preferred_categories or '{}')
                keywords = json.loads(result.interest_keywords or '{}')
                
                # Update category interest
                if content_type == "category":
                    category_id = str(content_id)
                    categories[category_id] = min(10.0, categories.get(category_id, 0) + 1.0)
                
                # Update keyword interests
                if content_name:
                    words = content_name.lower().split()
                    for word in words:
                        if len(word) > 3:
                            keywords[word] = min(10.0, keywords.get(word, 0) + 0.5)
                
                # If it's a procedure, also update its category
                if content_type == "procedure":
                    proc_result = db.session.execute(
                        text("SELECT category_id FROM procedures WHERE id = :pid"),
                        {"pid": content_id}
                    ).fetchone()
                    
                    if proc_result:
                        category_id = str(proc_result.category_id)
                        categories[category_id] = min(10.0, categories.get(category_id, 0) + 0.8)
                
                # Update database
                db.session.execute(
                    text("""UPDATE anonymous_users 
                           SET preferred_categories = :cats, interest_keywords = :keywords, updated_at = :now
                           WHERE browser_fingerprint = :fp"""),
                    {
                        "fp": fingerprint,
                        "cats": json.dumps(categories),
                        "keywords": json.dumps(keywords),
                        "now": datetime.utcnow()
                    }
                )
                
        except Exception as e:
            logger.error(f"Error updating user interests: {e}")
    
    @staticmethod
    def get_personalized_content(fingerprint, content_type="procedure", limit=10):
        """Get personalized content recommendations for user."""
        try:
            # Get user preferences
            result = db.session.execute(
                text("SELECT preferred_categories, interest_keywords, visit_count FROM anonymous_users WHERE browser_fingerprint = :fp"),
                {"fp": fingerprint}
            ).fetchone()
            
            if not result:
                return PersonalizationService.get_default_content(content_type, limit)
            
            categories = json.loads(result.preferred_categories or '{}')
            keywords = json.loads(result.interest_keywords or '{}')
            visit_count = result.visit_count
            
            if content_type == "procedure":
                return PersonalizationService.get_personalized_procedures(categories, keywords, visit_count, limit)
            elif content_type == "category":
                return PersonalizationService.get_personalized_categories(categories, limit)
            elif content_type == "doctor":
                return PersonalizationService.get_personalized_doctors(categories, keywords, limit)
            
            return PersonalizationService.get_default_content(content_type, limit)
            
        except Exception as e:
            logger.error(f"Error getting personalized content: {e}")
            return PersonalizationService.get_default_content(content_type, limit)
    
    @staticmethod
    def get_personalized_procedures(categories, keywords, visit_count, limit):
        """Get personalized procedure recommendations."""
        try:
            if not categories and not keywords:
                return PersonalizationService.get_default_content("procedure", limit)
            
            # Build category filter
            category_ids = list(categories.keys()) if categories else []
            
            if category_ids:
                # Get procedures from interested categories
                category_filter = ','.join(category_ids)
                procedures = db.session.execute(
                    text(f"""SELECT p.*, c.name as category_name 
                           FROM procedures p 
                           JOIN categories c ON p.category_id = c.id 
                           WHERE p.category_id IN ({category_filter})
                           ORDER BY p.popularity_score DESC 
                           LIMIT :limit"""),
                    {"limit": limit}
                ).fetchall()
            else:
                # Fallback to keyword-based search
                keyword_list = list(keywords.keys())[:5]  # Top 5 keywords
                if keyword_list:
                    keyword_pattern = '|'.join(keyword_list)
                    procedures = db.session.execute(
                        text("""SELECT p.*, c.name as category_name 
                               FROM procedures p 
                               JOIN categories c ON p.category_id = c.id 
                               WHERE p.procedure_name ~* :pattern
                               ORDER BY p.popularity_score DESC 
                               LIMIT :limit"""),
                        {"pattern": keyword_pattern, "limit": limit}
                    ).fetchall()
                else:
                    return PersonalizationService.get_default_content("procedure", limit)
            
            return [dict(proc._mapping) for proc in procedures]
            
        except Exception as e:
            logger.error(f"Error getting personalized procedures: {e}")
            return PersonalizationService.get_default_content("procedure", limit)
    
    @staticmethod
    def get_personalized_categories(categories, limit):
        """Get personalized category recommendations."""
        try:
            if not categories:
                return PersonalizationService.get_default_content("category", limit)
            
            # Sort categories by user interest
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            top_category_ids = [cat_id for cat_id, score in sorted_categories[:limit]]
            
            if top_category_ids:
                category_filter = ','.join(top_category_ids)
                result = db.session.execute(
                    text(f"""SELECT c.*, bp.name as body_part_name 
                           FROM categories c 
                           JOIN body_parts bp ON c.body_part_id = bp.id 
                           WHERE c.id IN ({category_filter})
                           ORDER BY CASE c.id {' '.join([f'WHEN {cat_id} THEN {i}' for i, cat_id in enumerate(top_category_ids)])} END""")
                ).fetchall()
                
                return [dict(cat._mapping) for cat in result]
            
            return PersonalizationService.get_default_content("category", limit)
            
        except Exception as e:
            logger.error(f"Error getting personalized categories: {e}")
            return PersonalizationService.get_default_content("category", limit)
    
    @staticmethod
    def get_personalized_doctors(categories, keywords, limit):
        """Get personalized doctor recommendations."""
        try:
            if not categories:
                return PersonalizationService.get_default_content("doctor", limit)
            
            category_ids = list(categories.keys())[:5]  # Top 5 categories
            if category_ids:
                category_filter = ','.join(category_ids)
                doctors = db.session.execute(
                    text(f"""SELECT DISTINCT d.*, COUNT(dc.category_id) as relevance_score 
                           FROM doctors d 
                           JOIN doctor_categories dc ON d.id = dc.doctor_id 
                           WHERE dc.category_id IN ({category_filter})
                           GROUP BY d.id 
                           ORDER BY relevance_score DESC, d.rating DESC 
                           LIMIT :limit"""),
                    {"limit": limit}
                ).fetchall()
                
                return [dict(doc._mapping) for doc in doctors]
            
            return PersonalizationService.get_default_content("doctor", limit)
            
        except Exception as e:
            logger.error(f"Error getting personalized doctors: {e}")
            return PersonalizationService.get_default_content("doctor", limit)
    
    @staticmethod
    def get_default_content(content_type, limit):
        """Get default content when no personalization data is available."""
        try:
            if content_type == "procedure":
                procedures = Procedure.query.order_by(Procedure.popularity_score.desc()).limit(limit).all()
                return [{"id": p.id, "procedure_name": p.procedure_name, "category_id": p.category_id} for p in procedures]
            
            elif content_type == "category":
                categories = Category.query.order_by(Category.popularity_score.desc()).limit(limit).all()
                return [{"id": c.id, "name": c.name, "body_part_id": c.body_part_id} for c in categories]
            
            elif content_type == "doctor":
                doctors = Doctor.query.order_by(Doctor.rating.desc()).limit(limit).all()
                return [{"id": d.id, "name": d.name, "specialty": d.specialty} for d in doctors]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting default content: {e}")
            return []

# API Routes
@personalization_bp.route('/api/track-interactions', methods=['POST'])
def track_interactions():
    """API endpoint to receive user interaction data."""
    try:
        data = request.get_json()
        fingerprint = data.get('fingerprint')
        interactions = data.get('interactions', [])
        
        if not fingerprint:
            return jsonify({"error": "Fingerprint required"}), 400
        
        # Ensure anonymous user exists
        user = PersonalizationService.get_or_create_anonymous_user(fingerprint)
        if not user:
            return jsonify({"error": "Failed to create user"}), 500
        
        # Process each interaction
        for interaction in interactions:
            PersonalizationService.track_interaction(
                fingerprint=fingerprint,
                interaction_type=interaction.get('type', 'unknown'),
                content_type=interaction.get('content_type', 'unknown'),
                content_id=interaction.get('data', {}).get('procedure_id') or 
                          interaction.get('data', {}).get('category_id') or 
                          interaction.get('data', {}).get('doctor_id', 0),
                content_name=interaction.get('data', {}).get('procedure_name', '') or
                           interaction.get('data', {}).get('category_name', '') or
                           interaction.get('data', {}).get('doctor_name', ''),
                page_url=interaction.get('page_url', ''),
                session_id=data.get('session_id', '')
            )
        
        return jsonify({"status": "success", "processed": len(interactions)})
        
    except Exception as e:
        logger.error(f"Error in track_interactions: {e}")
        return jsonify({"error": "Internal server error"}), 500

@personalization_bp.route('/api/personalized-content/<content_type>')
def get_personalized_content_api(content_type):
    """API endpoint to get personalized content recommendations."""
    try:
        fingerprint = request.args.get('fingerprint')
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 items
        
        if fingerprint:
            content = PersonalizationService.get_personalized_content(fingerprint, content_type, limit)
        else:
            content = PersonalizationService.get_default_content(content_type, limit)
        
        return jsonify({
            "status": "success",
            "content": content,
            "personalized": bool(fingerprint)
        })
        
    except Exception as e:
        logger.error(f"Error in get_personalized_content_api: {e}")
        return jsonify({"error": "Internal server error"}), 500