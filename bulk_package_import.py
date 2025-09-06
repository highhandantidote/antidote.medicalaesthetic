#!/usr/bin/env python3
"""
Bulk Package Import System with AI Generation
Processes CSV files with 4 basic fields and generates all other package details using AI.
"""
import csv
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import db
from models import Package, Clinic
from sqlalchemy import text
from intelligent_procedure_generator import procedure_generator
from ai_utils import genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIPackageGenerator:
    """Generates complete package data using AI from minimal input."""
    
    def __init__(self):
        self.medical_categories = {
            'facial': ['facial', 'glow', 'hydra', 'oxygen', 'carbon', 'radiance', 'peel', 'detox'],
            'hair_restoration': ['hair', 'scalp', 'prp', 'gfc', 'transplant', 'regrow', 'follicle'],
            'injectable': ['botox', 'filler', 'dermal', 'thread', 'micro botox', 'meso botox'],
            'laser': ['laser', 'smooth', 'bright', 'lift', 'erase', 'reduction'],
            'pigmentation': ['brow', 'ombre', 'microblading', 'lip blush', 'pigmentation'],
            'skin_treatment': ['acne', 'scar', 'spot', 'dark circles', 'hydration', 'rejuvenation'],
            'body_contouring': ['chin', 'double chin', 'contour', 'v-line']
        }
    
    def classify_treatment_category(self, package_name: str, actual_treatment: str) -> str:
        """Classify treatment into appropriate category."""
        text = f"{package_name} {actual_treatment}".lower()
        
        for category, keywords in self.medical_categories.items():
            if any(keyword in text for keyword in keywords):
                return category.replace('_', ' ').title()
        
        return 'Aesthetic Medicine'
    
    def generate_description(self, package_name: str, actual_treatment: str, category: str) -> str:
        """Generate AI-powered package description."""
        try:
            if not genai:
                return self._generate_template_description(package_name, actual_treatment, category)
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            Generate a professional, medical-grade description for this aesthetic treatment package:
            
            Package Name: {package_name}
            Actual Treatment: {actual_treatment}
            Category: {category}
            
            Requirements:
            - 2-3 sentences maximum
            - Focus on benefits and results
            - Use medical terminology appropriately
            - Mention the specific treatment technique
            - Sound professional and trustworthy
            - Avoid generic phrases
            
            Return only the description text, no quotes or formatting.
            """
            
            response = model.generate_content(prompt)
            description = response.text.strip()
            
            # Clean up the response
            description = description.replace('"', '').replace("'", "")
            if description.startswith('Description:'):
                description = description.replace('Description:', '').strip()
            
            return description[:500]  # Limit length
            
        except Exception as e:
            logger.warning(f"AI description generation failed for {package_name}: {e}")
            return self._generate_template_description(package_name, actual_treatment, category)
    
    def _generate_template_description(self, package_name: str, actual_treatment: str, category: str) -> str:
        """Fallback template-based description generation."""
        templates = {
            'facial': f"Advanced {actual_treatment.lower()} treatment designed to rejuvenate and enhance your skin's natural radiance. Professional-grade procedure delivering visible results with minimal downtime.",
            'hair_restoration': f"Specialized {actual_treatment.lower()} therapy using proven techniques to address hair concerns and promote healthy growth. Expert treatment with personalized care.",
            'injectable': f"Premium {actual_treatment.lower()} treatment for natural enhancement and rejuvenation. Professional injection technique ensuring optimal results and patient comfort.",
            'laser': f"State-of-the-art {actual_treatment.lower()} using advanced laser technology for precise and effective results. Safe, professional treatment with proven outcomes.",
            'pigmentation': f"Expert {actual_treatment.lower()} procedure for long-lasting, natural-looking results. Professional technique with attention to detail and artistic precision.",
            'skin_treatment': f"Targeted {actual_treatment.lower()} therapy addressing specific skin concerns with proven medical-grade techniques. Professional care for optimal healing and results."
        }
        
        category_key = category.lower().replace(' ', '_')
        return templates.get(category_key, f"Professional {actual_treatment.lower()} treatment with expert care and proven results. Advanced technique ensuring patient satisfaction and optimal outcomes.")
    
    def generate_duration(self, actual_treatment: str, category: str) -> str:
        """Generate realistic treatment duration."""
        duration_map = {
            'botox': '30-45 minutes',
            'filler': '45-60 minutes',
            'facial': '60-90 minutes',
            'laser': '30-60 minutes',
            'microblading': '2-3 hours',
            'thread': '60-90 minutes',
            'prp': '45-60 minutes',
            'transplant': '4-8 hours',
            'peel': '30-45 minutes',
            'microneedling': '45-60 minutes'
        }
        
        treatment_lower = actual_treatment.lower()
        for key, duration in duration_map.items():
            if key in treatment_lower:
                return duration
        
        return '45-60 minutes'
    
    def generate_downtime(self, actual_treatment: str, category: str) -> str:
        """Generate realistic downtime information."""
        downtime_map = {
            'botox': 'Minimal (24-48 hours)',
            'filler': '2-3 days mild swelling',
            'laser': '3-7 days',
            'microblading': '7-10 days',
            'facial': 'None to minimal',
            'peel': '3-7 days peeling',
            'thread': '3-5 days',
            'transplant': '7-14 days',
            'prp': '1-2 days',
            'surgery': '1-2 weeks'
        }
        
        treatment_lower = actual_treatment.lower()
        for key, downtime in downtime_map.items():
            if key in treatment_lower:
                return downtime
        
        return 'Minimal (24-48 hours)'
    
    def generate_anesthetic_type(self, actual_treatment: str, category: str) -> str:
        """Generate appropriate anesthetic type."""
        treatment_lower = actual_treatment.lower()
        
        if any(word in treatment_lower for word in ['transplant', 'surgery', 'thread']):
            return 'Local anesthesia'
        elif any(word in treatment_lower for word in ['microblading', 'tattoo', 'laser']):
            return 'Topical numbing cream'
        elif any(word in treatment_lower for word in ['botox', 'filler', 'injection']):
            return 'Topical anesthetic'
        else:
            return 'Not required'
    
    def generate_aftercare_kit(self, actual_treatment: str, category: str) -> str:
        """Generate appropriate aftercare kit."""
        treatment_lower = actual_treatment.lower()
        
        if 'microblading' in treatment_lower or 'brow' in treatment_lower:
            return 'Healing balm and aftercare instructions'
        elif any(word in treatment_lower for word in ['laser', 'peel']):
            return 'Soothing gel and SPF cream'
        elif any(word in treatment_lower for word in ['facial', 'glow']):
            return 'Moisturizing serum'
        elif any(word in treatment_lower for word in ['hair', 'scalp']):
            return 'Growth serum and special shampoo'
        else:
            return 'Post-treatment care kit'

def parse_price(price_str: str) -> float:
    """Parse price from string format."""
    if 'per' in price_str.lower():
        # Handle "per unit" or "per graft" pricing
        numbers = re.findall(r'\d+', price_str.replace(',', ''))
        return float(numbers[0]) if numbers else 0.0
    else:
        # Handle regular pricing with commas
        clean_price = price_str.replace(',', '').replace('₹', '').strip()
        try:
            return float(clean_price)
        except ValueError:
            return 0.0

def process_csv_file(csv_file_path: str, clinic_id: int = 1) -> Dict:
    """Process CSV file and create packages with AI-generated content."""
    generator = AIPackageGenerator()
    results = {
        'success': [],
        'errors': [],
        'total_processed': 0
    }
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    # Extract basic data
                    package_name = row['package_name'].strip()
                    actual_treatment = row['actual_treatment_name'].strip()
                    price = parse_price(row['price'])
                    discount_percentage = int(row['discount_percentage'])
                    
                    # Calculate discounted price
                    price_discounted = price * (100 - discount_percentage) / 100
                    
                    # Generate AI content
                    category = generator.classify_treatment_category(package_name, actual_treatment)
                    description = generator.generate_description(package_name, actual_treatment, category)
                    duration = generator.generate_duration(actual_treatment, category)
                    downtime = generator.generate_downtime(actual_treatment, category)
                    anesthetic_type = generator.generate_anesthetic_type(actual_treatment, category)
                    aftercare_kit = generator.generate_aftercare_kit(actual_treatment, category)
                    
                    # Generate procedure breakdown using existing AI system
                    procedure_breakdown = procedure_generator.generate_procedure_breakdown(
                        title=package_name,
                        category=category,
                        actual_treatment_name=actual_treatment,
                        package_price=price
                    )
                    
                    # Create slug
                    slug = re.sub(r'[^a-zA-Z0-9\s]', '', package_name.lower())
                    slug = re.sub(r'\s+', '-', slug.strip())
                    
                    # Prepare package data
                    package_data = {
                        'clinic_id': clinic_id,
                        'title': package_name,
                        'slug': slug,
                        'description': description,
                        'actual_treatment_name': actual_treatment,
                        'price_actual': price,
                        'price_discounted': price_discounted,
                        'discount_percentage': discount_percentage,
                        'category': category,
                        'duration': duration,
                        'downtime': downtime,
                        'anesthetic_type': anesthetic_type,
                        'aftercare_kit': aftercare_kit,
                        'procedure_breakdown': json.dumps(procedure_breakdown),
                        'is_active': True,
                        'created_at': datetime.now()
                    }
                    
                    # Insert package with transaction handling
                    try:
                        package_sql = """
                            INSERT INTO packages (
                                clinic_id, title, slug, description, actual_treatment_name, 
                                price_actual, price_discounted, discount_percentage, category,
                                duration, downtime, anesthetic_type, aftercare_kit,
                                procedure_breakdown, is_active, created_at
                            ) VALUES (
                                :clinic_id, :title, :slug, :description, :actual_treatment_name,
                                :price_actual, :price_discounted, :discount_percentage, :category,
                                :duration, :downtime, :anesthetic_type, :aftercare_kit,
                                :procedure_breakdown, :is_active, :created_at
                            )
                        """
                        
                        db.session.execute(text(package_sql), package_data)
                        db.session.commit()
                    except Exception as db_error:
                        db.session.rollback()
                        raise db_error
                    
                    results['success'].append({
                        'row': row_num,
                        'package_name': package_name,
                        'price': price,
                        'category': category
                    })
                    
                    logger.info(f"✅ Created package: {package_name} (Row {row_num})")
                    
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(f"❌ Error processing row {row_num}: {e}")
                
                results['total_processed'] += 1
    
    except Exception as e:
        logger.error(f"Failed to process CSV file: {e}")
        results['errors'].append(f"File processing error: {str(e)}")
    
    return results

def main():
    """Main function to process the uploaded CSV file."""
    from app import create_app
    
    csv_file = 'attached_assets/Neoskin - Sheet1 (1)_1756413049898.csv'
    
    print("🚀 Starting bulk package import with AI generation...")
    print(f"📁 Processing file: {csv_file}")
    
    app = create_app()
    with app.app_context():
        results = process_csv_file(csv_file)
        
        print(f"\n📊 Import Results:")
        print(f"✅ Successfully created: {len(results['success'])} packages")
        print(f"❌ Errors: {len(results['errors'])}")
        print(f"📈 Total processed: {results['total_processed']}")
        
        if results['errors']:
            print(f"\n❌ Error Details:")
            for error in results['errors']:
                print(f"   - {error}")
        
        if results['success']:
            print(f"\n✅ Successfully Created Packages:")
            for package in results['success'][:10]:  # Show first 10
                print(f"   - {package['package_name']} (₹{package['price']:,.0f}) - {package['category']}")
            if len(results['success']) > 10:
                print(f"   ... and {len(results['success']) - 10} more packages")

if __name__ == '__main__':
    main()