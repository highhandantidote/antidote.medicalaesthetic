"""
Intelligent Treatment Classification and Procedure Breakdown Generator
Automatically generates realistic, treatment-specific procedure breakdowns based on medical knowledge.
"""
import re
import json
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class TreatmentClassifier:
    """Classifies treatments based on title and category keywords."""
    
    def __init__(self):
        self.classification_rules = {
            # Hair Treatments
            'FUE_HAIR_TRANSPLANT': {
                'keywords': ['hair transplant', 'fue', 'hair implant', 'per graft'],
                'categories': ['hair restoration', 'aesthetic medicine'],
                'exclude': ['prp', 'gfc', 'regrowth', 'nutrition']
            },
            'PRP_HAIR_THERAPY': {
                'keywords': ['prp hair', 'hair prp', 'prp therapy'],
                'categories': ['hair restoration', 'aesthetic medicine'],
                'exclude': ['transplant', 'fue']
            },
            'GFC_HAIR_THERAPY': {
                'keywords': ['gfc hair', 'hair gfc', 'growth factor', 'advanced hair'],
                'categories': ['hair restoration', 'aesthetic medicine'],
                'exclude': ['transplant', 'fue']
            },
            'HAIR_NUTRITION_THERAPY': {
                'keywords': ['hair nutrition', 'hair regain', 'hair fall', 'hair loss'],
                'categories': ['hair restoration', 'aesthetic medicine'],
                'exclude': ['transplant', 'fue', 'prp', 'gfc']
            },
            
            # Facial Injectables
            'TEAR_TROUGH_FILLER': {
                'keywords': ['under eye', 'under-eye', 'tear trough', 'eye bag'],
                'categories': ['injectable', 'aesthetic medicine', 'eye enhancement'],
                'exclude': ['botox', 'thread']
            },
            'LIP_ENHANCEMENT_FILLER': {
                'keywords': ['lip filler', 'lip enhancement', 'lip augmentation'],
                'categories': ['injectable', 'aesthetic medicine', 'lip enhancement'],
                'exclude': ['botox', 'thread']
            },
            'CHEEK_CONTOURING_FILLER': {
                'keywords': ['cheek filler', 'cheek contour', 'cheek enhancement'],
                'categories': ['injectable', 'aesthetic medicine', 'facial contouring'],
                'exclude': ['botox', 'thread']
            },
            'BOTOX_INJECTION': {
                'keywords': ['botox', 'anti-aging', 'wrinkle', 'anti wrinkle'],
                'categories': ['injectable', 'anti-aging', 'aesthetic medicine'],
                'exclude': ['filler', 'thread']
            },
            
            # Thread Treatments
            'THREAD_LIFT_FACE': {
                'keywords': ['thread lift', 'instant lift', 'pdo thread', 'face lift'],
                'categories': ['thread lifting', 'aesthetic medicine'],
                'exclude': ['body', 'neck']
            },
            
            # Facial Treatments
            'HYDRAFACIAL': {
                'keywords': ['hydrafacial', 'hydra facial', 'aqua', 'glow facial'],
                'categories': ['facial', 'aesthetic medicine'],
                'exclude': ['laser', 'chemical']
            },
            'CHEMICAL_PEEL': {
                'keywords': ['peel', 'crystal peel', 'skin peel'],
                'categories': ['facial', 'aesthetic medicine', 'chemical peels'],
                'exclude': ['laser', 'hydra']
            },
            'LASER_FACIAL': {
                'keywords': ['laser', 'laser glow', 'laser treatment'],
                'categories': ['laser', 'aesthetic medicine'],
                'exclude': ['hair removal', 'body']
            },
            
            # Body Treatments
            'LIPOSUCTION': {
                'keywords': ['liposuction', 'lipo', 'fat removal'],
                'categories': ['body contouring', 'body surgery'],
                'exclude': ['non-surgical']
            },
            'COOLSCULPTING': {
                'keywords': ['coolsculpting', 'cryolipolysis', 'fat freezing'],
                'categories': ['body contouring', 'non-surgical'],
                'exclude': ['surgical']
            },
            
            # Laser Hair Removal
            'LASER_HAIR_REMOVAL': {
                'keywords': ['hair removal', 'hair free', 'laser hair'],
                'categories': ['laser', 'aesthetic medicine'],
                'exclude': ['growth', 'transplant']
            },
            
            # Scar Treatments
            'SCAR_TREATMENT': {
                'keywords': ['scar', 'acne scar', 'stretch mark'],
                'categories': ['scar treatment', 'aesthetic medicine'],
                'exclude': []
            },
            
            # Pigmentation Treatments
            'BROW_SHAPING': {
                'keywords': ['brow', 'eyebrow', 'microblading', 'ombre', '3d brow'],
                'categories': ['pigmentation', 'aesthetic medicine'],
                'exclude': []
            },
            'LIP_BLUSH': {
                'keywords': ['lip blush', 'lip pigment', 'lip tint'],
                'categories': ['pigmentation', 'aesthetic medicine'],
                'exclude': ['filler']
            },
            'SCALP_PIGMENTATION': {
                'keywords': ['scalp pigmentation', 'smp', 'scalp tattoo'],
                'categories': ['pigmentation', 'hair restoration'],
                'exclude': []
            },
            
            # Advanced Facial Treatments
            'MICRONEEDLING': {
                'keywords': ['microneedling', 'micro needling', 'derma roller'],
                'categories': ['facial', 'aesthetic medicine'],
                'exclude': []
            },
            'MESOTHERAPY': {
                'keywords': ['mesotherapy', 'meso', 'skin nutrition'],
                'categories': ['aesthetic medicine', 'facial'],
                'exclude': []
            }
        }

    def classify_treatment(self, title: str, category: str, actual_treatment_name: str = "") -> str:
        """Classify treatment based on title, category, and actual treatment name."""
        text_to_analyze = f"{title} {category} {actual_treatment_name}".lower()
        
        for treatment_type, rules in self.classification_rules.items():
            # Check if any keywords match
            keyword_match = any(keyword in text_to_analyze for keyword in rules['keywords'])
            
            # Check if category matches
            category_match = any(cat in category.lower() for cat in rules['categories'])
            
            # Check if any exclude words are present
            exclude_match = any(exclude in text_to_analyze for exclude in rules['exclude'])
            
            if keyword_match and category_match and not exclude_match:
                return treatment_type
        
        return 'GENERAL_AESTHETIC'

class MedicalKnowledgeDatabase:
    """Contains medical knowledge for different treatment types."""
    
    def __init__(self):
        self.treatment_data = {
            'FUE_HAIR_TRANSPLANT': {
                'components': [
                    {
                        'name': 'FUE Hair Extraction & Implantation',
                        'description': 'Follicular Unit Extraction using advanced micro punches',
                        'pricing_formula': 'graft_based',  # Special formula for graft-based pricing
                        'base_price_per_graft': 80,
                        'typical_graft_range': (1000, 3000),
                        'details': 'Advanced FUE technique with minimal scarring'
                    },
                    {
                        'name': 'Local Anesthesia & Sedation',
                        'description': 'Complete pain management during procedure',
                        'price_actual': 15000,
                        'price_discounted': 12000,
                        'discount_percentage': 20,
                        'details': 'Professional anesthesia monitoring throughout procedure'
                    },
                    {
                        'name': 'Post-Surgical Care Package',
                        'description': 'Specialized aftercare kit and follow-up consultations',
                        'price_actual': 8000,
                        'price_discounted': 6000,
                        'discount_percentage': 25,
                        'details': 'Antibiotic shampoo, growth serum, and 3 follow-up visits'
                    }
                ]
            },
            
            'PRP_HAIR_THERAPY': {
                'components': [
                    {
                        'name': 'PRP Hair Restoration Session',
                        'description': 'Platelet-Rich Plasma injection for hair regrowth',
                        'price_actual': 12000,
                        'price_discounted': 10200,
                        'discount_percentage': 15,
                        'details': 'Advanced centrifugation and micro-injection technique'
                    },
                    {
                        'name': 'Scalp Analysis & Consultation',
                        'description': 'Comprehensive hair and scalp assessment',
                        'price_actual': 2000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Digital hair analysis and personalized treatment plan'
                    },
                    {
                        'name': 'Growth Factor Serum',
                        'description': 'Post-treatment growth enhancement serum',
                        'price_actual': 3500,
                        'price_discounted': 2800,
                        'discount_percentage': 20,
                        'details': 'Specialized peptide complex for enhanced results'
                    }
                ]
            },
            
            'GFC_HAIR_THERAPY': {
                'components': [
                    {
                        'name': 'Growth Factor Concentrate Treatment',
                        'description': 'Advanced growth factor therapy for hair regrowth',
                        'price_actual': 18000,
                        'price_discounted': 14400,
                        'discount_percentage': 20,
                        'details': 'Concentrated growth factors from patient\'s own blood'
                    },
                    {
                        'name': 'Micro-needling Hair Stimulation',
                        'description': 'Scalp micro-needling to enhance absorption',
                        'price_actual': 4000,
                        'price_discounted': 3200,
                        'discount_percentage': 20,
                        'details': 'Professional micro-needling for better penetration'
                    },
                    {
                        'name': 'Hair Growth Assessment',
                        'description': 'Pre and post-treatment hair density analysis',
                        'price_actual': 2500,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Digital tracking of hair growth progress'
                    }
                ]
            },
            
            'HAIR_NUTRITION_THERAPY': {
                'components': [
                    {
                        'name': 'Hair Nutrition Infusion',
                        'description': 'Vitamin and mineral cocktail for hair health',
                        'price_actual': 8000,
                        'price_discounted': 6400,
                        'discount_percentage': 20,
                        'details': 'Biotin, vitamins, and essential minerals for hair growth'
                    },
                    {
                        'name': 'Scalp Detox Treatment',
                        'description': 'Deep cleansing and follicle preparation',
                        'price_actual': 3000,
                        'price_discounted': 2400,
                        'discount_percentage': 20,
                        'details': 'Removes DHT buildup and improves circulation'
                    },
                    {
                        'name': 'Home Care Kit',
                        'description': 'Specialized shampoo and nutrition supplements',
                        'price_actual': 4000,
                        'price_discounted': 3200,
                        'discount_percentage': 20,
                        'details': 'Month supply of hair nutrition supplements'
                    }
                ]
            },
            
            'TEAR_TROUGH_FILLER': {
                'components': [
                    {
                        'name': 'Juvederm Volbella XC - 1ml',
                        'description': 'Premium hyaluronic acid filler for delicate under-eye area',
                        'price_actual': 30000,
                        'price_discounted': 25500,
                        'discount_percentage': 15,
                        'details': 'FDA-approved filler with Vycross technology'
                    },
                    {
                        'name': 'Micro-cannula Injection Technique',
                        'description': 'Advanced injection method to minimize bruising',
                        'price_actual': 12000,
                        'price_discounted': 9600,
                        'discount_percentage': 20,
                        'details': 'Precise placement with reduced trauma'
                    },
                    {
                        'name': 'Post-Treatment Care Package',
                        'description': 'Healing cream and follow-up consultation',
                        'price_actual': 3000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Arnica cream and 2-week follow-up appointment'
                    }
                ]
            },
            
            'LIP_ENHANCEMENT_FILLER': {
                'components': [
                    {
                        'name': 'Restylane Kysse - 1ml',
                        'description': 'Specialized lip filler for natural movement and feel',
                        'price_actual': 28000,
                        'price_discounted': 23800,
                        'discount_percentage': 15,
                        'details': 'Maintains natural lip texture and flexibility'
                    },
                    {
                        'name': 'Dental Block Anesthesia',
                        'description': 'Professional numbing for comfortable procedure',
                        'price_actual': 8000,
                        'price_discounted': 6000,
                        'discount_percentage': 25,
                        'details': 'Complete pain management during injection'
                    },
                    {
                        'name': 'Lip Care Kit',
                        'description': 'Healing balm and post-care instructions',
                        'price_actual': 2500,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Specialized lip care products for optimal healing'
                    }
                ]
            },
            
            'CHEEK_CONTOURING_FILLER': {
                'components': [
                    {
                        'name': 'Juvederm Voluma XC - 2ml',
                        'description': 'Premium volumizing filler for cheek enhancement',
                        'price_actual': 45000,
                        'price_discounted': 38250,
                        'discount_percentage': 15,
                        'details': 'Long-lasting results up to 2 years'
                    },
                    {
                        'name': 'Facial Mapping & Design',
                        'description': 'Professional facial analysis and contouring plan',
                        'price_actual': 5000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Golden ratio analysis for optimal cheek projection'
                    },
                    {
                        'name': 'Post-Treatment Support',
                        'description': 'Follow-up care and touch-up if needed',
                        'price_actual': 8000,
                        'price_discounted': 4000,
                        'discount_percentage': 50,
                        'details': 'Includes massage techniques and follow-up evaluation'
                    }
                ]
            },
            
            'BOTOX_INJECTION': {
                'components': [
                    {
                        'name': 'Botox Injection - 50 Units',
                        'description': 'Premium botulinum toxin for wrinkle reduction',
                        'price_actual': 25000,
                        'price_discounted': 21250,
                        'discount_percentage': 15,
                        'details': 'Allergan Botox with proven safety record'
                    },
                    {
                        'name': 'Facial Muscle Analysis',
                        'description': 'Professional assessment of facial dynamics',
                        'price_actual': 3000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Customized injection pattern for natural results'
                    },
                    {
                        'name': 'Post-Injection Care',
                        'description': 'Instructions and follow-up consultation',
                        'price_actual': 2000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Detailed aftercare and 2-week progress check'
                    }
                ]
            },
            
            'THREAD_LIFT_FACE': {
                'components': [
                    {
                        'name': 'PDO Thread Lift - 8 Threads',
                        'description': 'Premium PDO threads for facial lifting',
                        'price_actual': 32000,
                        'price_discounted': 25600,
                        'discount_percentage': 20,
                        'details': 'Korean PDO threads with barbs for lifting'
                    },
                    {
                        'name': 'Local Anesthetic',
                        'description': 'Nerve block for comfortable procedure',
                        'price_actual': 5000,
                        'price_discounted': 4000,
                        'discount_percentage': 20,
                        'details': 'Professional anesthesia for pain-free treatment'
                    },
                    {
                        'name': 'Recovery Care Package',
                        'description': 'Post-procedure care and instructions',
                        'price_actual': 3000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Anti-inflammatory medication and care guidelines'
                    }
                ]
            },
            
            'HYDRAFACIAL': {
                'components': [
                    {
                        'name': 'HydraFacial MD Treatment',
                        'description': 'Multi-step facial resurfacing treatment',
                        'price_actual': 8000,
                        'price_discounted': 6800,
                        'discount_percentage': 15,
                        'details': 'Cleanse, extract, and hydrate in single session'
                    },
                    {
                        'name': 'Customized Booster Serum',
                        'description': 'Targeted serum for specific skin concerns',
                        'price_actual': 3000,
                        'price_discounted': 2400,
                        'discount_percentage': 20,
                        'details': 'Vitamin C, growth factors, or brightening peptides'
                    },
                    {
                        'name': 'LED Light Therapy',
                        'description': 'Red light therapy for collagen stimulation',
                        'price_actual': 2000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Additional collagen boost and healing enhancement'
                    }
                ]
            },
            
            'CHEMICAL_PEEL': {
                'components': [
                    {
                        'name': 'Professional Chemical Peel',
                        'description': 'Medium-depth peel for skin renewal',
                        'price_actual': 6000,
                        'price_discounted': 4800,
                        'discount_percentage': 20,
                        'details': 'TCA or glycolic acid peel for texture improvement'
                    },
                    {
                        'name': 'Pre-Peel Preparation',
                        'description': 'Skin conditioning and sensitivity test',
                        'price_actual': 2000,
                        'price_discounted': 1500,
                        'discount_percentage': 25,
                        'details': 'Prepares skin for optimal peel results'
                    },
                    {
                        'name': 'Post-Peel Recovery Kit',
                        'description': 'Healing cream and sun protection',
                        'price_actual': 3500,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Specialized healing cream and SPF 50 sunscreen'
                    }
                ]
            },
            
            'LASER_FACIAL': {
                'components': [
                    {
                        'name': 'Fractional Laser Treatment',
                        'description': 'Advanced laser resurfacing for skin renewal',
                        'price_actual': 15000,
                        'price_discounted': 12000,
                        'discount_percentage': 20,
                        'details': 'CO2 fractional laser for texture improvement'
                    },
                    {
                        'name': 'Cooling and Comfort System',
                        'description': 'Advanced cooling for comfortable treatment',
                        'price_actual': 3000,
                        'price_discounted': 2400,
                        'discount_percentage': 20,
                        'details': 'Continuous cooling reduces discomfort'
                    },
                    {
                        'name': 'Post-Laser Care Package',
                        'description': 'Healing gel and recovery instructions',
                        'price_actual': 4000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Aloe vera gel and detailed recovery guidelines'
                    }
                ]
            },
            
            'LASER_HAIR_REMOVAL': {
                'components': [
                    {
                        'name': 'Diode Laser Hair Removal',
                        'description': 'Professional laser hair removal session',
                        'price_actual': 5000,
                        'price_discounted': 4000,
                        'discount_percentage': 20,
                        'details': 'Advanced diode laser for permanent hair reduction'
                    },
                    {
                        'name': 'Skin Cooling System',
                        'description': 'Integrated cooling for comfort',
                        'price_actual': 1500,
                        'price_discounted': 1200,
                        'discount_percentage': 20,
                        'details': 'Continuous cooling during laser treatment'
                    },
                    {
                        'name': 'Post-Treatment Soothing',
                        'description': 'Aloe gel and aftercare instructions',
                        'price_actual': 1000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Soothing gel and sun protection guidelines'
                    }
                ]
            },
            
            'SCAR_TREATMENT': {
                'components': [
                    {
                        'name': 'Microneedling with RF',
                        'description': 'Radiofrequency microneedling for scar reduction',
                        'price_actual': 12000,
                        'price_discounted': 9600,
                        'discount_percentage': 20,
                        'details': 'Combines microneedling with radiofrequency energy'
                    },
                    {
                        'name': 'Collagen Induction Serum',
                        'description': 'Specialized serum for scar healing',
                        'price_actual': 4000,
                        'price_discounted': 3200,
                        'discount_percentage': 20,
                        'details': 'Growth factors and peptides for tissue repair'
                    },
                    {
                        'name': 'Home Care Protocol',
                        'description': 'Prescribed creams and healing instructions',
                        'price_actual': 3000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Silicone gel and vitamin E cream for healing'
                    }
                ]
            },
            
            'BROW_SHAPING': {
                'components': [
                    {
                        'name': 'Eyebrow Design & Mapping',
                        'description': 'Professional brow architecture and golden ratio mapping',
                        'price_actual': 8000,
                        'price_discounted': 6400,
                        'discount_percentage': 20,
                        'details': 'Customized brow shape design based on facial structure'
                    },
                    {
                        'name': 'Microblading/Ombre Technique',
                        'description': 'Advanced pigmentation technique for natural-looking brows',
                        'price_actual': 25000,
                        'price_discounted': 20000,
                        'discount_percentage': 20,
                        'details': 'Hair-stroke technique or powder ombre shading'
                    },
                    {
                        'name': 'Touch-up Session & Aftercare',
                        'description': 'Complimentary touch-up and healing ointment',
                        'price_actual': 8000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': '4-6 week touch-up session and specialized healing balm'
                    }
                ]
            },
            
            'LIP_BLUSH': {
                'components': [
                    {
                        'name': 'Lip Color Consultation',
                        'description': 'Custom color matching and lip design',
                        'price_actual': 5000,
                        'price_discounted': 4000,
                        'discount_percentage': 20,
                        'details': 'Personalized color selection based on skin tone'
                    },
                    {
                        'name': 'Lip Blush Pigmentation',
                        'description': 'Semi-permanent lip tinting for natural enhancement',
                        'price_actual': 28000,
                        'price_discounted': 22400,
                        'discount_percentage': 20,
                        'details': 'Natural-looking lip color enhancement with fade-resistant pigments'
                    },
                    {
                        'name': 'Healing Care Package',
                        'description': 'Specialized lip healing balm and instructions',
                        'price_actual': 3000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Medical-grade healing balm and detailed aftercare guide'
                    }
                ]
            },
            
            'SCALP_PIGMENTATION': {
                'components': [
                    {
                        'name': 'Scalp Analysis & Hairline Design',
                        'description': 'Detailed scalp assessment and natural hairline mapping',
                        'price_actual': 6000,
                        'price_discounted': 4800,
                        'discount_percentage': 20,
                        'details': 'Professional assessment of balding pattern and hairline design'
                    },
                    {
                        'name': 'Scalp Micro Pigmentation Treatment',
                        'description': 'Advanced SMP technique for hair follicle simulation',
                        'price_actual': 35000,
                        'price_discounted': 28000,
                        'discount_percentage': 20,
                        'details': 'Multiple sessions to create realistic hair follicle appearance'
                    },
                    {
                        'name': 'Touch-up & Maintenance Plan',
                        'description': 'Follow-up sessions and long-term maintenance',
                        'price_actual': 8000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Annual touch-up sessions and scalp care guidance'
                    }
                ]
            },
            
            'MICRONEEDLING': {
                'components': [
                    {
                        'name': 'Skin Analysis & Preparation',
                        'description': 'Comprehensive skin assessment and pre-treatment prep',
                        'price_actual': 3000,
                        'price_discounted': 2400,
                        'discount_percentage': 20,
                        'details': 'Digital skin analysis and customized treatment planning'
                    },
                    {
                        'name': 'Professional Microneedling Session',
                        'description': 'Medical-grade microneedling with depth customization',
                        'price_actual': 15000,
                        'price_discounted': 12000,
                        'discount_percentage': 20,
                        'details': 'Controlled micro-injuries to stimulate collagen production'
                    },
                    {
                        'name': 'Post-Treatment Serum & Care',
                        'description': 'Growth factor serum and recovery protocol',
                        'price_actual': 5000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Specialized healing serum and detailed aftercare instructions'
                    }
                ]
            },
            
            'MESOTHERAPY': {
                'components': [
                    {
                        'name': 'Skin Assessment & Formula Selection',
                        'description': 'Personalized vitamin cocktail selection for skin needs',
                        'price_actual': 4000,
                        'price_discounted': 3200,
                        'discount_percentage': 20,
                        'details': 'Custom blend of vitamins, antioxidants, and hyaluronic acid'
                    },
                    {
                        'name': 'Mesotherapy Injection Treatment',
                        'description': 'Micro-injection of nutrients directly into skin layers',
                        'price_actual': 18000,
                        'price_discounted': 14400,
                        'discount_percentage': 20,
                        'details': 'Precise micro-injections for optimal nutrient delivery'
                    },
                    {
                        'name': 'Recovery & Hydration Support',
                        'description': 'Post-treatment care and hydration therapy',
                        'price_actual': 3000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Soothing gel mask and hydration maintenance plan'
                    }
                ]
            },
            
            'GENERAL_AESTHETIC': {
                'components': [
                    {
                        'name': 'Advanced Treatment Session',
                        'description': 'Specialized aesthetic procedure with expert techniques',
                        'price_actual': 15000,
                        'price_discounted': 12000,
                        'discount_percentage': 20,
                        'details': 'State-of-the-art treatment using advanced medical technology'
                    },
                    {
                        'name': 'Professional Consultation & Planning',
                        'description': 'Comprehensive assessment and personalized treatment strategy',
                        'price_actual': 3000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Detailed consultation with treatment customization'
                    },
                    {
                        'name': 'Premium Aftercare Package',
                        'description': 'Complete post-treatment support and follow-up care',
                        'price_actual': 4000,
                        'price_discounted': 0,
                        'discount_percentage': 100,
                        'details': 'Professional-grade aftercare products and guidance'
                    }
                ]
            }
        }

    def get_treatment_components(self, treatment_type: str, package_price: float = None, title: str = "") -> List[Dict]:
        """Get procedure components for a specific treatment type."""
        if treatment_type not in self.treatment_data:
            # Generate intelligent fallback based on treatment name/title
            return self._generate_smart_fallback_components(title, package_price)
        
        components = self.treatment_data[treatment_type]['components'].copy()
        
        # Handle special cases like graft-based pricing for hair transplants
        if treatment_type == 'FUE_HAIR_TRANSPLANT' and package_price:
            components = self._adjust_hair_transplant_pricing(components, package_price, title)
        
        return components
    
    def _generate_smart_fallback_components(self, title: str, package_price: float = None) -> List[Dict]:
        """Generate intelligent treatment-specific components for unknown treatments."""
        title_lower = title.lower()
        base_price = package_price or 20000
        
        # Main treatment component - make it specific to the treatment
        main_component = {
            'name': f'{title} - Premium Treatment',
            'description': f'Advanced {title.lower()} procedure using state-of-the-art techniques',
            'price_actual': int(base_price * 0.7),
            'price_discounted': int(base_price * 0.56),  # 20% discount
            'discount_percentage': 20,
            'details': f'Professional {title.lower()} treatment with expert precision and care'
        }
        
        # Add treatment-specific secondary components based on keywords
        secondary_components = []
        
        if any(word in title_lower for word in ['laser', 'light', 'ipl']):
            secondary_components.append({
                'name': 'Advanced Laser Technology',
                'description': 'Cutting-edge laser system for optimal results',
                'price_actual': int(base_price * 0.15),
                'price_discounted': int(base_price * 0.12),
                'discount_percentage': 20,
                'details': 'FDA-approved laser technology with safety protocols'
            })
        
        if any(word in title_lower for word in ['skin', 'facial', 'glow', 'rejuven']):
            secondary_components.append({
                'name': 'Premium Skin Analysis',
                'description': 'Comprehensive skin assessment and customization',
                'price_actual': int(base_price * 0.1),
                'price_discounted': 0,
                'discount_percentage': 100,
                'details': 'Digital skin analysis for personalized treatment approach'
            })
        
        if any(word in title_lower for word in ['injection', 'filler', 'botox', 'injectable']):
            secondary_components.append({
                'name': 'Premium Injectable Products',
                'description': 'High-quality medical-grade injectables',
                'price_actual': int(base_price * 0.2),
                'price_discounted': int(base_price * 0.16),
                'discount_percentage': 20,
                'details': 'FDA-approved products from leading manufacturers'
            })
        
        # Always include aftercare as the final component
        aftercare_component = {
            'name': 'Comprehensive Aftercare Package',
            'description': f'Post-{title.lower()} care and recovery support',
            'price_actual': int(base_price * 0.1),
            'price_discounted': 0,
            'discount_percentage': 100,
            'details': 'Professional aftercare products and detailed recovery guidance'
        }
        
        # Combine all components
        all_components = [main_component] + secondary_components + [aftercare_component]
        
        # Adjust pricing to match package total if needed
        total_discounted = sum(comp['price_discounted'] for comp in all_components)
        if package_price and abs(total_discounted - package_price) > package_price * 0.1:
            # Adjust main component if total is significantly off
            adjustment = package_price - total_discounted
            main_component['price_discounted'] += int(adjustment)
            main_component['price_actual'] = int(main_component['price_discounted'] / 0.8)  # Assuming 20% discount
        
        return all_components
    
    def _adjust_hair_transplant_pricing(self, components: List[Dict], package_price: float, title: str) -> List[Dict]:
        """Adjust hair transplant pricing based on graft count."""
        # Try to extract graft count from title
        graft_match = re.search(r'(\d+)\s*graft', title.lower())
        if graft_match:
            graft_count = int(graft_match.group(1))
        else:
            # Estimate graft count based on price
            estimated_price_per_graft = 80
            graft_count = max(1000, min(3000, int(package_price / estimated_price_per_graft)))
        
        # Update the main procedure component
        for component in components:
            if 'pricing_formula' in component and component['pricing_formula'] == 'graft_based':
                component['name'] = f"FUE Hair Extraction & Implantation - {graft_count} Grafts"
                component['description'] = f"Follicular Unit Extraction of {graft_count} grafts using advanced micro punches"
                component['price_actual'] = graft_count * component['base_price_per_graft']
                component['price_discounted'] = int(component['price_actual'] * 0.85)  # 15% discount
                component['discount_percentage'] = 15
                component['details'] = f"Advanced FUE technique for {graft_count} grafts with minimal scarring"
                # Remove the pricing formula fields
                del component['pricing_formula']
                del component['base_price_per_graft']
                del component['typical_graft_range']
        
        return components

class IntelligentProcedureGenerator:
    """Main class that combines classification and knowledge to generate procedure breakdowns."""
    
    def __init__(self):
        self.classifier = TreatmentClassifier()
        self.knowledge_db = MedicalKnowledgeDatabase()
    
    def generate_procedure_breakdown(self, title: str, category: str, actual_treatment_name: str = "", 
                                   package_price: float = None) -> List[Dict]:
        """Generate a realistic procedure breakdown for a treatment."""
        try:
            # Classify the treatment
            treatment_type = self.classifier.classify_treatment(title, category, actual_treatment_name)
            
            # Get components from knowledge database
            components = self.knowledge_db.get_treatment_components(treatment_type, package_price, title)
            
            logger.info(f"Generated procedure breakdown for '{title}' - classified as {treatment_type}")
            return components
            
        except Exception as e:
            logger.error(f"Error generating procedure breakdown for '{title}': {e}")
            # Return enhanced fallback breakdown
            return self.knowledge_db._generate_smart_fallback_components(title, package_price)

# Global instance for easy import
procedure_generator = IntelligentProcedureGenerator()