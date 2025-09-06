"""
Medical Content Optimizer for Antidote SEO Strategy
Phase 2: Content & Authority Building
Implements E-E-A-T compliance, medical schema markup, and content optimization
"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
import re

class MedicalContentOptimizer:
    """Optimize medical content for E-E-A-T compliance and SEO"""
    
    def __init__(self):
        self.medical_keywords = {
            'plastic_surgery': [
                'plastic surgery', 'cosmetic surgery', 'aesthetic surgery', 'facial surgery',
                'breast augmentation', 'rhinoplasty', 'liposuction', 'tummy tuck',
                'facelift', 'brow lift', 'eyelid surgery', 'nose job'
            ],
            'procedures': [
                'surgical procedure', 'non-surgical treatment', 'minimally invasive',
                'consultation', 'recovery time', 'results', 'before and after'
            ],
            'medical_authority': [
                'board certified', 'medical license', 'qualified surgeon', 'experienced doctor',
                'medical training', 'fellowship', 'residency', 'specialization'
            ],
            'location_keywords': [
                'India', 'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad',
                'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur'
            ]
        }
    
    def optimize_procedure_content(self, procedure_data):
        """Optimize procedure content for medical SEO"""
        optimized_content = {
            'title': self._create_seo_title(procedure_data),
            'meta_description': self._create_meta_description(procedure_data),
            'structured_content': self._structure_medical_content(procedure_data),
            'schema_markup': self._generate_procedure_schema(procedure_data),
            'content_score': 0
        }
        
        # Calculate content quality score
        optimized_content['content_score'] = self._calculate_content_score(optimized_content)
        
        return optimized_content
    
    def _create_seo_title(self, procedure_data):
        """Create SEO-optimized title for medical procedures"""
        procedure_name = procedure_data.get('name', '')
        location = procedure_data.get('location', 'India')
        
        # Create compelling, keyword-rich title
        title_templates = [
            f"{procedure_name} in {location} - Expert Surgeons | Antidote",
            f"Best {procedure_name} Surgery in {location} - Book Consultation",
            f"{procedure_name} Cost & Procedure in {location} - Qualified Doctors",
            f"Expert {procedure_name} Surgery in {location} - Compare Clinics"
        ]
        
        # Choose based on procedure type
        if 'consultation' in procedure_name.lower():
            return title_templates[1]
        elif 'cost' in procedure_data.get('description', '').lower():
            return title_templates[2]
        else:
            return title_templates[0]
    
    def _create_meta_description(self, procedure_data):
        """Create compelling meta description with medical authority"""
        procedure_name = procedure_data.get('name', '')
        description = procedure_data.get('description', '')
        location = procedure_data.get('location', 'India')
        
        # Extract key benefits or details
        word_count = len(description.split()) if description else 0
        
        if word_count > 20:
            # Use existing description but optimize it
            optimized = description[:120] + "..."
        else:
            # Create new description
            optimized = f"Expert {procedure_name} surgery in {location}. Board-certified surgeons, modern facilities, competitive pricing. Book consultation with qualified specialists. Compare costs and reviews."
        
        # Ensure it's within Google's preferred length
        return optimized[:155] + "..." if len(optimized) > 155 else optimized
    
    def _structure_medical_content(self, procedure_data):
        """Structure content for medical E-E-A-T compliance"""
        procedure_name = procedure_data.get('name', '')
        description = procedure_data.get('description', '')
        
        # Create comprehensive medical content structure
        structured_content = {
            'introduction': f"Learn about {procedure_name}, a medical procedure performed by qualified plastic surgeons and aesthetic specialists.",
            
            'what_is_section': {
                'title': f"What is {procedure_name}?",
                'content': f"{procedure_name} is a medical procedure that requires proper evaluation by board-certified surgeons. {description}"
            },
            
            'procedure_details': {
                'title': "Procedure Overview",
                'content': f"The {procedure_name} procedure involves several steps and requires medical expertise. Qualified surgeons assess each patient individually to determine the best approach."
            },
            
            'qualifications_section': {
                'title': "Qualified Surgeons",
                'content': "All procedures should only be performed by board-certified plastic surgeons with proper medical training and licensing."
            },
            
            'consultation_section': {
                'title': "Medical Consultation",
                'content': "A thorough consultation with a qualified medical professional is essential before any surgical procedure. This includes medical history review and physical examination."
            },
            
            'safety_section': {
                'title': "Safety & Considerations",
                'content': "Patient safety is paramount. All procedures carry risks that must be discussed with qualified medical professionals. Proper medical facilities and aftercare are essential."
            },
            
            'cost_section': {
                'title': "Cost Considerations",
                'content': f"The cost of {procedure_name} varies based on individual needs, surgeon expertise, and facility quality. Consultation with multiple qualified providers is recommended."
            },
            
            'recovery_section': {
                'title': "Recovery Process",
                'content': "Recovery varies by individual and procedure complexity. Following post-operative instructions from qualified medical professionals is crucial for optimal results."
            }
        }
        
        return structured_content
    
    def _generate_procedure_schema(self, procedure_data):
        """Generate medical procedure Schema.org markup"""
        procedure_name = procedure_data.get('name', '')
        description = procedure_data.get('description', '')
        category = procedure_data.get('category', 'Cosmetic Surgery')
        
        schema = {
            "@context": "https://schema.org",
            "@type": "MedicalProcedure",
            "name": procedure_name,
            "description": description,
            "procedureType": {
                "@type": "MedicalProcedureType",
                "name": category
            },
            "howPerformed": "Performed by board-certified medical professionals in accredited facilities",
            "preparation": "Medical consultation, health assessment, and pre-operative instructions",
            "followup": "Post-operative care and follow-up appointments with qualified medical staff",
            "typicalAgeRange": "18-65",
            "bodyLocation": {
                "@type": "AnatomicalStructure",
                "name": procedure_data.get('body_part', 'Various')
            },
            "seriousAdverseOutcome": {
                "@type": "MedicalEntity",
                "name": "Risks minimized when performed by qualified professionals in proper medical facilities"
            }
        }
        
        return schema
    
    def _calculate_content_score(self, content_data):
        """Calculate content quality score for SEO"""
        score = 0
        
        # Check title optimization
        title = content_data.get('title', '')
        if len(title) >= 50 and len(title) <= 60:
            score += 15
        elif len(title) >= 40:
            score += 10
        
        # Check meta description
        meta_desc = content_data.get('meta_description', '')
        if len(meta_desc) >= 140 and len(meta_desc) <= 155:
            score += 15
        elif len(meta_desc) >= 120:
            score += 10
        
        # Check structured content depth
        structured = content_data.get('structured_content', {})
        section_count = len(structured)
        if section_count >= 8:
            score += 25
        elif section_count >= 6:
            score += 20
        elif section_count >= 4:
            score += 15
        
        # Check for medical authority keywords
        all_text = f"{title} {meta_desc} {str(structured)}"
        authority_keywords = self.medical_keywords['medical_authority']
        authority_count = sum(1 for keyword in authority_keywords if keyword.lower() in all_text.lower())
        
        if authority_count >= 5:
            score += 20
        elif authority_count >= 3:
            score += 15
        elif authority_count >= 1:
            score += 10
        
        # Check for location keywords
        location_keywords = self.medical_keywords['location_keywords']
        location_count = sum(1 for keyword in location_keywords if keyword.lower() in all_text.lower())
        
        if location_count >= 2:
            score += 15
        elif location_count >= 1:
            score += 10
        
        # Check schema markup presence
        if content_data.get('schema_markup'):
            score += 10
        
        return min(score, 100)  # Cap at 100

class DoctorProfileOptimizer:
    """Optimize doctor profiles for medical authority and trust"""
    
    def optimize_doctor_profile(self, doctor_data):
        """Optimize doctor profile for E-E-A-T compliance"""
        optimized_profile = {
            'seo_title': self._create_doctor_seo_title(doctor_data),
            'meta_description': self._create_doctor_meta_description(doctor_data),
            'structured_profile': self._structure_doctor_content(doctor_data),
            'credentials_section': self._enhance_credentials(doctor_data),
            'schema_markup': self._generate_doctor_schema(doctor_data)
        }
        
        return optimized_profile
    
    def _create_doctor_seo_title(self, doctor_data):
        """Create SEO title emphasizing medical credentials"""
        name = doctor_data.get('name', '')
        specialization = doctor_data.get('specialization', '')
        location = doctor_data.get('location', 'India')
        
        return f"Dr. {name} - {specialization} Specialist in {location} | Antidote"
    
    def _create_doctor_meta_description(self, doctor_data):
        """Create meta description highlighting qualifications"""
        name = doctor_data.get('name', '')
        specialization = doctor_data.get('specialization', '')
        experience = doctor_data.get('experience', '')
        location = doctor_data.get('location', 'India')
        
        description = f"Dr. {name}, qualified {specialization} in {location}. "
        if experience:
            description += f"{experience} years experience. "
        description += "Board-certified surgeon. Book consultation for expert medical care."
        
        return description[:155]
    
    def _structure_doctor_content(self, doctor_data):
        """Structure doctor profile content for authority"""
        name = doctor_data.get('name', '')
        specialization = doctor_data.get('specialization', '')
        
        return {
            'introduction': f"Dr. {name} is a qualified {specialization} with expertise in medical aesthetic procedures.",
            'qualifications': "Board-certified with proper medical licensing and training.",
            'approach': "Committed to patient safety and achieving optimal medical outcomes through evidence-based practices.",
            'consultation': "Provides thorough medical consultations and personalized treatment plans."
        }
    
    def _enhance_credentials(self, doctor_data):
        """Enhance credentials section for trust signals"""
        return {
            'medical_license': "Valid medical license and board certification",
            'training': "Completed specialized training in aesthetic and plastic surgery",
            'experience': f"Years of experience: {doctor_data.get('experience', 'Multiple years')}",
            'specialization': f"Specialized in: {doctor_data.get('specialization', 'Medical Aesthetics')}",
            'affiliations': "Member of recognized medical associations"
        }
    
    def _generate_doctor_schema(self, doctor_data):
        """Generate doctor Schema.org markup"""
        name = doctor_data.get('name', '')
        specialization = doctor_data.get('specialization', '')
        
        return {
            "@context": "https://schema.org",
            "@type": "Physician",
            "name": f"Dr. {name}",
            "jobTitle": specialization,
            "medicalSpecialty": specialization,
            "hasCredential": [
                {
                    "@type": "EducationalOccupationalCredential",
                    "credentialCategory": "Medical License"
                },
                {
                    "@type": "EducationalOccupationalCredential", 
                    "credentialCategory": "Board Certification"
                }
            ]
        }

# Create blueprint for medical content optimization
medical_content_bp = Blueprint('medical_content', __name__)

@medical_content_bp.route('/api/medical-content/optimize-procedure/<int:procedure_id>')
def optimize_procedure_api(procedure_id):
    """API endpoint to get optimized content for a procedure"""
    try:
        # Mock procedure data - in real implementation, fetch from database
        procedure_data = {
            'id': procedure_id,
            'name': 'Rhinoplasty',
            'description': 'Nose reshaping surgery to improve appearance and function',
            'category': 'Facial Surgery',
            'body_part': 'Nose',
            'location': 'Mumbai'
        }
        
        optimizer = MedicalContentOptimizer()
        optimized_content = optimizer.optimize_procedure_content(procedure_data)
        
        return jsonify(optimized_content)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@medical_content_bp.route('/api/medical-content/optimize-doctor/<int:doctor_id>')
def optimize_doctor_api(doctor_id):
    """API endpoint to get optimized content for a doctor profile"""
    try:
        # Mock doctor data - in real implementation, fetch from database
        doctor_data = {
            'id': doctor_id,
            'name': 'Sharma',
            'specialization': 'Plastic Surgery',
            'experience': '15',
            'location': 'Mumbai'
        }
        
        optimizer = DoctorProfileOptimizer()
        optimized_profile = optimizer.optimize_doctor_profile(doctor_data)
        
        return jsonify(optimized_profile)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500