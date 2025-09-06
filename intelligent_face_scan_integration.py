"""Intelligent face scan integration with unified category system."""

from sqlalchemy import text
from app import db
import logging

logger = logging.getLogger(__name__)

class IntelligentFaceScanEngine:
    """Connect face scan results to procedures and packages through unified hierarchy."""
    
    @staticmethod
    def get_recommendations_from_scan(scan_results, limit_per_category=3):
        """
        Convert face scan analysis results into procedure and package recommendations.
        
        Args:
            scan_results (dict): Face scan analysis results with keys like 'wrinkles', 'asymmetry', etc.
            limit_per_category (int): Max recommendations per category
            
        Returns:
            dict: Organized recommendations by category
        """
        try:
            recommendations = {
                'procedures': [],
                'packages': [],
                'categories': [],
                'scan_insights': []
            }
            
            for scan_key, confidence in scan_results.items():
                if confidence < 0.3:  # Skip low-confidence detections
                    continue
                    
                # Get mapping for this scan result
                mapping_query = text("""
                    SELECT fsr.*, ch.name as category_name, ch.level
                    FROM face_scan_recommendations fsr
                    JOIN category_hierarchy ch ON fsr.category_id = ch.id
                    WHERE fsr.scan_analysis_key = :scan_key
                    ORDER BY fsr.recommendation_priority DESC
                """)
                
                mappings = db.session.execute(mapping_query, {'scan_key': scan_key}).fetchall()
                
                for mapping in mappings:
                    # Find relevant procedures
                    procedure_query = text("""
                        SELECT DISTINCT p.*, c.name as category_name
                        FROM procedures p
                        JOIN entity_categories ec ON p.id = ec.entity_id AND ec.entity_type = 'procedure'
                        JOIN categories c ON p.category_id = c.id
                        WHERE ec.category_id = :category_id
                          AND (
                            p.procedure_name ILIKE ANY(:keywords) OR
                            p.short_description ILIKE ANY(:keywords) OR
                            p.overview ILIKE ANY(:keywords)
                          )
                        ORDER BY p.popularity_score DESC NULLS LAST
                        LIMIT :limit
                    """)
                    
                    # Convert keywords to SQL pattern
                    keywords = [f'%{kw}%' for kw in mapping.procedure_keywords]
                    
                    procedures = db.session.execute(procedure_query, {
                        'category_id': mapping.category_id,
                        'keywords': keywords,
                        'limit': limit_per_category
                    }).fetchall()
                    
                    # Find relevant packages
                    package_query = text("""
                        SELECT DISTINCT p.*, c.name as clinic_name, c.city as clinic_city
                        FROM packages p
                        JOIN clinics c ON p.clinic_id = c.id
                        JOIN entity_categories ec ON p.id = ec.entity_id AND ec.entity_type = 'package'
                        WHERE ec.category_id = :category_id
                          AND (
                            p.title ILIKE ANY(:keywords) OR
                            p.description ILIKE ANY(:keywords) OR
                            p.actual_treatment_name ILIKE ANY(:keywords)
                          )
                          AND p.is_active = true
                        ORDER BY c.overall_rating DESC NULLS LAST, p.view_count DESC NULLS LAST
                        LIMIT :limit
                    """)
                    
                    packages = db.session.execute(package_query, {
                        'category_id': mapping.category_id,
                        'keywords': keywords,
                        'limit': limit_per_category
                    }).fetchall()
                    
                    # Add to recommendations
                    for proc in procedures:
                        rec = dict(proc._mapping)
                        rec['scan_confidence'] = confidence
                        rec['scan_reason'] = scan_key
                        recommendations['procedures'].append(rec)
                    
                    for pkg in packages:
                        rec = dict(pkg._mapping)
                        rec['scan_confidence'] = confidence
                        rec['scan_reason'] = scan_key
                        recommendations['packages'].append(rec)
                    
                    # Add category info
                    recommendations['categories'].append({
                        'name': mapping.category_name,
                        'scan_key': scan_key,
                        'confidence': confidence,
                        'priority': mapping.recommendation_priority
                    })
                    
                    # Add scan insight
                    recommendations['scan_insights'].append({
                        'detected': scan_key,
                        'confidence': confidence,
                        'suggested_category': mapping.category_name,
                        'treatment_keywords': mapping.procedure_keywords
                    })
            
            # Remove duplicates and sort by confidence
            recommendations['procedures'] = list({p['id']: p for p in recommendations['procedures']}.values())
            recommendations['packages'] = list({p['id']: p for p in recommendations['packages']}.values())
            
            # Sort by scan confidence
            recommendations['procedures'].sort(key=lambda x: x.get('scan_confidence', 0), reverse=True)
            recommendations['packages'].sort(key=lambda x: x.get('scan_confidence', 0), reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating face scan recommendations: {e}")
            return {'procedures': [], 'packages': [], 'categories': [], 'scan_insights': []}
    
    @staticmethod
    def create_personalized_journey(scan_recommendations, user_budget=None, user_location=None):
        """Create a personalized treatment journey based on scan results and user preferences."""
        try:
            journey = {
                'immediate': [],  # Quick fixes (injectables, facials)
                'medium_term': [], # Laser treatments, advanced procedures
                'long_term': [],   # Surgical procedures
                'budget_friendly': [],
                'premium': []
            }
            
            for package in scan_recommendations.get('packages', []):
                price = package.get('price_discounted') or package.get('price_actual') or 0
                
                # Categorize by treatment type and timeline
                if any(kw in package.get('title', '').lower() for kw in ['botox', 'filler', 'facial']):
                    journey['immediate'].append(package)
                elif any(kw in package.get('title', '').lower() for kw in ['laser', 'peel', 'microneedling']):
                    journey['medium_term'].append(package)
                elif any(kw in package.get('title', '').lower() for kw in ['surgery', 'lift', 'rhinoplasty']):
                    journey['long_term'].append(package)
                
                # Categorize by budget
                if price < 50000:
                    journey['budget_friendly'].append(package)
                else:
                    journey['premium'].append(package)
            
            return journey
            
        except Exception as e:
            logger.error(f"Error creating personalized journey: {e}")
            return {}
    
    @staticmethod
    def get_face_scan_analytics(scan_results):
        """Provide analytics and insights based on face scan results."""
        try:
            analytics = {
                'top_concerns': [],
                'treatment_areas': set(),
                'recommended_approach': '',
                'confidence_score': 0
            }
            
            # Analyze top concerns
            sorted_results = sorted(scan_results.items(), key=lambda x: x[1], reverse=True)
            analytics['top_concerns'] = sorted_results[:3]
            
            # Calculate overall confidence
            if sorted_results:
                analytics['confidence_score'] = sum(conf for _, conf in sorted_results) / len(sorted_results)
            
            # Determine treatment areas
            for scan_key, confidence in sorted_results:
                if 'nose' in scan_key:
                    analytics['treatment_areas'].add('Nose & Profile')
                elif any(kw in scan_key for kw in ['wrinkles', 'lines', 'sagging']):
                    analytics['treatment_areas'].add('Anti-Aging')
                elif any(kw in scan_key for kw in ['spots', 'scars', 'texture']):
                    analytics['treatment_areas'].add('Skin Quality')
                elif 'asymmetry' in scan_key:
                    analytics['treatment_areas'].add('Facial Balance')
            
            analytics['treatment_areas'] = list(analytics['treatment_areas'])
            
            # Recommend approach
            if analytics['confidence_score'] > 0.8:
                analytics['recommended_approach'] = 'comprehensive_treatment'
            elif analytics['confidence_score'] > 0.5:
                analytics['recommended_approach'] = 'targeted_treatment'  
            else:
                analytics['recommended_approach'] = 'consultation_recommended'
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating face scan analytics: {e}")
            return {}