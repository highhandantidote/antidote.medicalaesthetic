"""Smart recommendation system for cross-entity connections."""

from sqlalchemy import text
from app import db
import logging

logger = logging.getLogger(__name__)

class SmartRecommendationEngine:
    """Intelligent recommendation engine that connects all entities."""
    
    @staticmethod
    def get_related_packages(package_id, limit=6):
        """Get packages related to the given package."""
        try:
            query = text("""
                SELECT DISTINCT p.id, p.title, p.slug, p.price_discounted, p.price_actual,
                       p.description, c.name as clinic_name, er.relevance_score
                FROM packages p
                JOIN clinics c ON p.clinic_id = c.id
                JOIN entity_recommendations er ON p.id = er.target_entity_id
                WHERE er.source_entity_type = 'package' 
                  AND er.source_entity_id = :package_id
                  AND er.target_entity_type = 'package'
                  AND er.recommendation_type = 'related'
                  AND p.is_active = true
                ORDER BY er.relevance_score DESC, RANDOM()
                LIMIT :limit
            """)
            result = db.session.execute(query, {'package_id': package_id, 'limit': limit}).fetchall()
            return [dict(row._mapping) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting related packages for {package_id}: {e}")
            return []
    
    @staticmethod
    def get_available_packages(procedure_id, limit=8):
        """Get packages that offer the given procedure."""
        try:
            query = text("""
                SELECT DISTINCT p.id, p.title, p.slug, p.price_discounted, p.price_actual,
                       p.description, p.duration, p.downtime, c.name as clinic_name, 
                       c.city as clinic_city, er.relevance_score
                FROM packages p
                JOIN clinics c ON p.clinic_id = c.id
                JOIN entity_recommendations er ON p.id = er.target_entity_id
                WHERE er.source_entity_type = 'procedure' 
                  AND er.source_entity_id = :procedure_id
                  AND er.target_entity_type = 'package'
                  AND er.recommendation_type = 'available_at'
                  AND p.is_active = true
                ORDER BY er.relevance_score DESC, c.overall_rating DESC NULLS LAST
                LIMIT :limit
            """)
            result = db.session.execute(query, {'procedure_id': procedure_id, 'limit': limit}).fetchall()
            return [dict(row._mapping) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting available packages for procedure {procedure_id}: {e}")
            return []
    
    @staticmethod
    def get_complementary_procedures(procedure_id, limit=5):
        """Get procedures commonly done together with the given procedure."""
        try:
            query = text("""
                SELECT DISTINCT p.id, p.procedure_name, p.short_description, p.min_cost, p.max_cost,
                       c.name as category_name, er.relevance_score
                FROM procedures p
                JOIN categories c ON p.category_id = c.id
                JOIN entity_recommendations er ON p.id = er.target_entity_id
                WHERE er.source_entity_type = 'procedure' 
                  AND er.source_entity_id = :procedure_id
                  AND er.target_entity_type = 'procedure'
                  AND er.recommendation_type = 'complementary'
                ORDER BY er.relevance_score DESC
                LIMIT :limit
            """)
            result = db.session.execute(query, {'procedure_id': procedure_id, 'limit': limit}).fetchall()
            return [dict(row._mapping) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting complementary procedures for {procedure_id}: {e}")
            return []
    
    @staticmethod
    def get_clinic_specializations(clinic_id, limit=10):
        """Get procedures and specializations for a clinic."""
        try:
            query = text("""
                SELECT DISTINCT p.id, p.procedure_name, p.short_description, p.min_cost,
                       c.name as category_name, er.relevance_score
                FROM procedures p
                JOIN categories c ON p.category_id = c.id
                JOIN entity_recommendations er ON p.id = er.target_entity_id
                WHERE er.source_entity_type = 'clinic' 
                  AND er.source_entity_id = :clinic_id
                  AND er.target_entity_type = 'procedure'
                  AND er.recommendation_type = 'specializes_in'
                ORDER BY er.relevance_score DESC
                LIMIT :limit
            """)
            result = db.session.execute(query, {'clinic_id': clinic_id, 'limit': limit}).fetchall()
            return [dict(row._mapping) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting clinic specializations for {clinic_id}: {e}")
            return []
    
    @staticmethod
    def get_smart_homepage_recommendations(user_preferences=None, limit=6):
        """Get smart recommendations for homepage based on popularity and user preferences."""
        try:
            # Get most popular packages across different categories
            query = text("""
                SELECT DISTINCT p.id, p.title, p.slug, p.price_discounted, p.price_actual,
                       p.description, c.name as clinic_name, c.city as clinic_city,
                       ch.name as category_name, COUNT(er.target_entity_id) as recommendation_count
                FROM packages p
                JOIN clinics c ON p.clinic_id = c.id
                JOIN entity_categories ec ON p.id = ec.entity_id AND ec.entity_type = 'package'
                JOIN category_hierarchy ch ON ec.category_id = ch.id
                LEFT JOIN entity_recommendations er ON p.id = er.target_entity_id
                WHERE p.is_active = true AND ch.level <= 2
                GROUP BY p.id, p.title, p.slug, p.price_discounted, p.price_actual, 
                         p.description, c.name, c.city, ch.name
                ORDER BY recommendation_count DESC, RANDOM()
                LIMIT :limit
            """)
            result = db.session.execute(query, {'limit': limit}).fetchall()
            return [dict(row._mapping) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error getting smart homepage recommendations: {e}")
            return []