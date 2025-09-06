#!/usr/bin/env python3
"""
Enhanced Medical Package Import with Detailed Treatment Information
Creates comprehensive, medically accurate package pages
"""

import os
import sys
import csv
from datetime import datetime
from sqlalchemy import create_engine, text
from medical_content_database import get_treatment_content

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")

def create_slug(title, clinic_id=196):
    """Create a unique URL-friendly slug from title"""
    base_slug = title.lower().replace(' ', '-').replace('&', 'and')
    base_slug = ''.join(c for c in base_slug if c.isalnum() or c == '-')
    # Add clinic identifier to make it unique
    slug = f"zoh-{base_slug}"
    return slug

def categorize_treatment(treatment_name):
    """Intelligently categorize treatment based on medical knowledge"""
    treatment_lower = treatment_name.lower()
    
    # Detailed categorization based on medical knowledge
    if any(word in treatment_lower for word in ['prp', 'gfc', 'hair transplant', 'hair fall', 'hair loss', 'hair regrowth', 'hair nutrition', 'mesotherapy', 'dandruff', 'baldness', 'scalp']):
        return 'Hair Restoration'
    elif any(word in treatment_lower for word in ['botox', 'filler', 'dermal', 'lip enhancement', 'nose job', 'chin augmentation', 'thread lift']):
        return 'Injectable Treatments'
    elif any(word in treatment_lower for word in ['laser hair', 'laser skin', 'laser tattoo', 'laser scar', 'laser stretch', 'ipl']):
        return 'Laser Treatments'
    elif any(word in treatment_lower for word in ['hydrafacial', 'oxygen facial', 'carbon facial', 'vampire facial', 'chemical peel', 'microneedling', 'skin rejuvenation']):
        return 'Advanced Facial Treatments'
    elif any(word in treatment_lower for word in ['microblading', 'ombrebrows', 'combination brow', 'scalp micro', 'lip blush']):
        return 'Cosmetic Tattooing'
    elif any(word in treatment_lower for word in ['acne', 'pigmentation', 'melasma', 'age spots', 'dark circles', 'moles', 'skin tags', 'warts']):
        return 'Medical Dermatology'
    elif any(word in treatment_lower for word in ['skin tightening', 'lifting', 'anti-aging', 'wrinkle']):
        return 'Anti-Aging Treatments'
    else:
        return 'Aesthetic Medicine'

def create_enhanced_package_content(package_name, treatment_name, price, discount_pct):
    """Create comprehensive medical content for package"""
    
    # Get detailed medical information
    content = get_treatment_content(treatment_name)
    
    # Calculate pricing
    discounted_price = price * (1 - discount_pct / 100) if discount_pct > 0 else None
    
    # Create comprehensive description
    description = f"Professional {treatment_name} at ZOH Aesthetic Clinic, Nallagandla - Hyderabad's premier destination for advanced aesthetic treatments. "
    if discount_pct > 0:
        description += f"Limited time offer: {discount_pct}% discount on this treatment! "
    description += "Experience world-class medical aesthetics with personalized care and proven results."
    
    # Enhanced about procedure content
    about_procedure = f"""
    {content['about']}
    
    <h4>Why Choose ZOH Aesthetic Clinic for {treatment_name}?</h4>
    <ul>
    <li><strong>Expert Medical Team:</strong> Highly trained aesthetic physicians and dermatologists</li>
    <li><strong>Advanced Technology:</strong> Latest FDA-approved equipment and techniques</li>
    <li><strong>Personalized Approach:</strong> Customized treatment plans for each patient</li>
    <li><strong>Safety First:</strong> Strict hygiene protocols and safety standards</li>
    <li><strong>Proven Results:</strong> 4.9/5 rating with 169+ satisfied patients</li>
    <li><strong>Convenient Location:</strong> Modern facility in heart of Nallagandla</li>
    </ul>
    
    <h4>What to Expect During Your Visit:</h4>
    <ol>
    <li><strong>Consultation:</strong> Detailed assessment and treatment planning</li>
    <li><strong>Preparation:</strong> Skin preparation and comfort measures</li>
    <li><strong>Treatment:</strong> {content['duration']} of professional care</li>
    <li><strong>Recovery Guidance:</strong> Comprehensive aftercare instructions</li>
    <li><strong>Follow-up:</strong> Ongoing support and monitoring</li>
    </ol>
    """
    
    return {
        'description': description,
        'about_procedure': about_procedure,
        'category': categorize_treatment(treatment_name),
        'recommended_for': content['ideal_candidates'],
        'duration': content['duration'],
        'downtime': content['recovery_details'],
        'precautions': ' | '.join(content['precautions']) if isinstance(content['precautions'], list) else str(content['precautions']),
        'sessions_info': content.get('sessions', 'Customized based on individual needs'),
        'contraindications': content.get('contraindications', 'Consultation required to determine suitability')
    }

def update_existing_packages_with_medical_content():
    """Update existing ZOH packages with enhanced medical content"""
    
    engine = create_engine(DATABASE_URL)
    
    print("🔄 Updating existing ZOH packages with enhanced medical content...")
    print("=" * 60)
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Get all existing ZOH packages
            packages_result = conn.execute(text("""
                SELECT id, title, price_actual, discount_percentage 
                FROM packages 
                WHERE clinic_id = 196
                ORDER BY id
            """))
            
            packages = packages_result.fetchall()
            
            for package in packages:
                package_id, title, price, discount_pct = package
                
                print(f"📝 Updating: {title} (ID: {package_id})")
                
                # Try to extract treatment name from title
                # Remove "ZOH" prefix and common suffixes to get clean treatment name
                treatment_name = title.replace('ZOH ', '').strip()
                
                # Map display names back to medical names where possible
                treatment_mapping = {
                    'Aqua Glow Facial': 'Hydrafacial',
                    'Perfect Brow Design': 'Microblading',
                    'Anti-Wrinkle Botox': 'Botox (Facial)',
                    'Face Contour Fillers': 'Dermal Fillers',
                    'PRP Hair Regrowth': 'PRP for Hair Regrowth',
                    'Advanced GFC Hair Regrowth': 'GFC for Hair Regrowth',
                    'Hair Transplant (per graft)': 'Hair Transplantation',
                    'Permanent Hair-Free Laser': 'Laser Hair Reduction',
                    'Spot Clear Therapy': 'Acne'
                }
                
                medical_name = treatment_mapping.get(title, treatment_name)
                
                # Generate enhanced content
                enhanced_content = create_enhanced_package_content(
                    title, medical_name, float(price), int(discount_pct or 0)
                )
                
                # Update the package with enhanced content
                update_sql = """
                    UPDATE packages SET
                        description = :description,
                        about_procedure = :about_procedure,
                        category = :category,
                        recommended_for = :recommended_for,
                        duration = :duration,
                        downtime_description = :downtime,
                        precautions = :precautions,
                        updated_at = :updated_at
                    WHERE id = :package_id
                """
                
                conn.execute(text(update_sql), {
                    'description': enhanced_content['description'],
                    'about_procedure': enhanced_content['about_procedure'],
                    'category': enhanced_content['category'],
                    'recommended_for': enhanced_content['recommended_for'],
                    'duration': enhanced_content['duration'],
                    'downtime': enhanced_content['downtime'],
                    'precautions': enhanced_content['precautions'],
                    'updated_at': datetime.utcnow(),
                    'package_id': package_id
                })
            
            trans.commit()
            print(f"\n🎉 Successfully updated {len(packages)} packages with enhanced medical content!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error updating packages: {e}")
            raise

if __name__ == "__main__":
    print("ZOH Aesthetic Clinic - Enhanced Medical Content Update")
    print("=" * 60)
    print("This will update all existing packages with detailed medical information")
    print("including comprehensive treatment descriptions, benefits, and precautions.")
    print()
    
    update_existing_packages_with_medical_content()