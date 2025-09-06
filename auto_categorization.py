"""
Auto-categorization system for new packages
This module provides intelligent categorization for new packages based on title and description.
Maps packages to Level 1 categories in the hierarchical category system.
"""

import re
from typing import Dict, List, Tuple

class PackageCategorizer:
    """Intelligent package categorization system for Level 1 categories"""
    
    def __init__(self):
        # Updated to map to Level 1 categories (ID: name mapping)
        self.level1_category_keywords = {
            1: {  # Face & Head
                'name': 'Face & Head',
                'keywords': [
                    'face', 'facial', 'facelift', 'rhinoplasty', 'nose job', 'botox', 'filler',
                    'dermal', 'cheek', 'lip', 'forehead', 'chin', 'jaw', 'anti-aging',
                    'wrinkle', 'hydrafacial', 'peel', 'glow', 'skin treatment', 'microneedling',
                    'thread lift', 'vampire facial', 'rejuvenation', 'brightening', 'cleansing'
                ]
            },
            38: {  # Eyes & Vision
                'name': 'Eyes & Vision',
                'keywords': [
                    'eye', 'eyelid', 'blepharoplasty', 'dark circles', 'eye bags', 'under eye',
                    'eyebrow', 'lash', 'vision', 'tear trough', 'crow feet', 'ptosis'
                ]
            },
            39: {  # Neck & Jawline
                'name': 'Neck & Jawline',
                'keywords': [
                    'neck', 'jawline', 'double chin', 'neck lift', 'jaw', 'jowl',
                    'neck tightening', 'platysmal', 'submental', 'jaw enhancement'
                ]
            },
            2: {  # Breast & Chest
                'name': 'Breast & Chest',
                'keywords': [
                    'breast', 'chest', 'augmentation', 'implant', 'reduction', 'lift',
                    'mastopexy', 'gynecomastia', 'nipple', 'areola', 'mammary'
                ]
            },
            3: {  # Body & Abdomen
                'name': 'Body & Abdomen',
                'keywords': [
                    'abdomen', 'tummy', 'belly', 'abdominoplasty', 'liposuction', 'coolsculpting',
                    'body contouring', 'waist', 'love handles', 'flanks', 'muffin top', 'back fat',
                    'mommy makeover', 'post pregnancy', 'diastasis', 'tummy tuck'
                ]
            },
            4: {  # Arms & Legs
                'name': 'Arms & Legs',
                'keywords': [
                    'arm', 'leg', 'thigh', 'calf', 'hand', 'finger', 'arm lift', 'thigh lift',
                    'hand rejuvenation', 'varicose', 'spider veins', 'leg contouring',
                    'brachioplasty', 'arm tuck', 'hand treatment'
                ]
            },
            5: {  # Hair & Scalp
                'name': 'Hair & Scalp',
                'keywords': [
                    'hair', 'scalp', 'follicle', 'transplant', 'regrowth', 'hair loss',
                    'baldness', 'fue', 'fut', 'hair implant', 'prp hair', 'mesotherapy hair',
                    'hair stimulation', 'alopecia', 'hairline'
                ]
            },
            40: {  # Reconstructive & Medical
                'name': 'Reconstructive & Medical',
                'keywords': [
                    'reconstructive', 'medical', 'scar', 'keloid', 'reconstruction', 'repair',
                    'medical treatment', 'therapeutic', 'corrective', 'revision', 'medical peel',
                    'skin correction', 'trauma', 'birth defect', 'congenital'
                ]
            },
            41: {  # Weight & Metabolism
                'name': 'Weight & Metabolism',
                'keywords': [
                    'weight', 'metabolism', 'fat', 'obesity', 'bariatric', 'gastric',
                    'weight loss', 'slimming', 'metabolic', 'body sculpting', 'fat reduction',
                    'inch loss', 'cellulite'
                ]
            },
            6: {  # Intimate & Private Areas
                'name': 'Intimate & Private Areas',
                'keywords': [
                    'intimate', 'private', 'vagina', 'genital', 'brazilian', 'butt lift',
                    'bbl', 'buttock', 'labial', 'vaginal', 'intimate rejuvenation',
                    'intimate enhancement', 'sexual wellness', 'intimate surgery'
                ]
            },
            31: {  # Dental & Oral Health
                'name': 'Dental & Oral Health',
                'keywords': [
                    'dental', 'tooth', 'teeth', 'oral', 'smile', 'dentistry', 'orthodontic',
                    'implant dental', 'crown', 'veneer', 'whitening', 'gum', 'periodontal',
                    'oral surgery', 'maxillofacial'
                ]
            }
        }
    
    def categorize_package(self, title: str, description: str = "") -> Tuple[int, str]:
        """
        Automatically categorize a package based on title and description
        
        Args:
            title: Package title
            description: Package description (optional)
            
        Returns:
            Tuple of (category_id, category_name)
        """
        # Combine title and description for analysis
        text = f"{title} {description}".lower()
        
        # Score each Level 1 category based on keyword matches
        category_scores = {}
        
        for category_id, category_data in self.level1_category_keywords.items():
            score = 0
            keywords = category_data['keywords']
            
            for keyword in keywords:
                # Count occurrences of each keyword
                matches = len(re.findall(rf'\b{re.escape(keyword)}\b', text))
                score += matches
                # Give extra weight to exact matches in title
                if keyword in title.lower():
                    score += 3
                # Extra weight for multiple word matches
                if len(keyword.split()) > 1 and keyword in text:
                    score += 2
            
            if score > 0:
                category_scores[category_id] = score
        
        # Return category with highest score
        if category_scores:
            best_category_id = max(category_scores.items(), key=lambda x: x[1])[0]
            best_category_name = self.level1_category_keywords[best_category_id]['name']
            return (best_category_id, best_category_name)
        
        # Default fallback logic based on common patterns
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['eye', 'eyelid', 'dark circle']):
            return (38, 'Eyes & Vision')
        elif any(word in title_lower for word in ['neck', 'jaw', 'double chin']):
            return (39, 'Neck & Jawline')
        elif any(word in title_lower for word in ['breast', 'chest']):
            return (2, 'Breast & Chest')
        elif any(word in title_lower for word in ['body', 'abdomen', 'tummy', 'lipo']):
            return (3, 'Body & Abdomen')
        elif any(word in title_lower for word in ['arm', 'leg', 'hand', 'thigh']):
            return (4, 'Arms & Legs')
        elif any(word in title_lower for word in ['hair', 'scalp']):
            return (5, 'Hair & Scalp')
        elif any(word in title_lower for word in ['scar', 'medical', 'reconstruct']):
            return (40, 'Reconstructive & Medical')
        elif any(word in title_lower for word in ['weight', 'fat', 'slim']):
            return (41, 'Weight & Metabolism')
        elif any(word in title_lower for word in ['intimate', 'brazilian', 'butt']):
            return (6, 'Intimate & Private Areas')
        elif any(word in title_lower for word in ['dental', 'tooth', 'smile']):
            return (31, 'Dental & Oral Health')
        else:
            return (1, 'Face & Head')  # Default fallback
    
    def get_category_suggestions(self, title: str, description: str = "") -> List[Tuple[str, float]]:
        """
        Get suggested Level 1 categories with confidence scores
        
        Args:
            title: Package title
            description: Package description (optional)
            
        Returns:
            List of (category_name, confidence_score) tuples
        """
        text = f"{title} {description}".lower()
        category_scores = {}
        
        for category_id, category_data in self.level1_category_keywords.items():
            category_name = category_data['name']
            keywords = category_data['keywords']
            score = 0
            matches = 0
            
            for keyword in keywords:
                keyword_matches = len(re.findall(rf'\b{re.escape(keyword)}\b', text))
                if keyword_matches > 0:
                    matches += 1
                    score += keyword_matches
                    # Bonus for title matches
                    if keyword in title.lower():
                        score += 3
            
            # Calculate confidence based on matches and score
            if matches > 0:
                confidence = min(score * 0.15, 1.0)  # Cap at 1.0
                category_scores[category_name] = confidence
        
        # Sort by confidence score
        return sorted(category_scores.items(), key=lambda x: x[1], reverse=True)

# Global instance for use in package creation
package_categorizer = PackageCategorizer()

def auto_categorize_package(title: str, description: str = "") -> Tuple[int, str]:
    """
    Convenience function to auto-categorize a package
    
    Args:
        title: Package title
        description: Package description (optional)
        
    Returns:
        Tuple of (category_id, category_name)
    """
    return package_categorizer.categorize_package(title, description)

def auto_categorize_and_assign_package(package_id: int, title: str, description: str = "") -> bool:
    """
    Auto-categorize a package and assign it to the appropriate Level 1 category
    
    Args:
        package_id: The package ID to categorize
        title: Package title
        description: Package description (optional)
        
    Returns:
        True if categorization was successful, False otherwise
    """
    try:
        from app import db
        from sqlalchemy import text
        
        # Get the best category
        category_id, category_name = auto_categorize_package(title, description)
        
        # Find the appropriate Level 2 category under this Level 1 category
        level2_query = text("""
            SELECT id FROM category_hierarchy 
            WHERE parent_id = :parent_id AND level = 2 
            ORDER BY sort_order LIMIT 1
        """)
        
        result = db.session.execute(level2_query, {'parent_id': category_id}).fetchone()
        
        if result:
            level2_category_id = result[0]
            
            # Insert into entity_categories table
            insert_query = text("""
                INSERT INTO entity_categories (entity_type, entity_id, category_id, relevance_score)
                VALUES ('package', :package_id, :category_id, 90)
                ON CONFLICT (entity_type, entity_id, category_id) DO NOTHING
            """)
            
            db.session.execute(insert_query, {
                'package_id': package_id,
                'category_id': level2_category_id
            })
            
            # Also add to Level 1 category for broader categorization
            db.session.execute(insert_query, {
                'package_id': package_id,
                'category_id': category_id
            })
            
            db.session.commit()
            return True
        else:
            # Fallback: Just assign to Level 1 category
            insert_query = text("""
                INSERT INTO entity_categories (entity_type, entity_id, category_id, relevance_score)
                VALUES ('package', :package_id, :category_id, 85)
                ON CONFLICT (entity_type, entity_id, category_id) DO NOTHING
            """)
            
            db.session.execute(insert_query, {
                'package_id': package_id,
                'category_id': category_id
            })
            
            db.session.commit()
            return True
            
    except Exception as e:
        print(f"Error auto-categorizing package {package_id}: {str(e)}")
        db.session.rollback()
        return False