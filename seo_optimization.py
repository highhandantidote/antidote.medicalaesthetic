"""
SEO optimization system for clinic, package, and doctor pages with structured data.
"""
from flask import Blueprint, request, render_template_string
from models import db, Clinic, Doctor, Package, Procedure, Category
from sqlalchemy import text
import json

seo_bp = Blueprint('seo', __name__)

def generate_clinic_schema(clinic):
    """Generate structured data schema for clinic pages."""
    schema = {
        "@context": "https://schema.org",
        "@type": "MedicalOrganization",
        "name": clinic.name,
        "description": clinic.description or f"Professional cosmetic surgery clinic in {clinic.city}",
        "url": f"https://antidote.com/clinics/{clinic.id}",
        "telephone": clinic.contact_number,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": clinic.address,
            "addressLocality": clinic.city,
            "addressCountry": "IN"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": str(clinic.rating or 4.5),
            "reviewCount": str(clinic.review_count or 0),
            "bestRating": "5",
            "worstRating": "1"
        },
        "medicalSpecialty": clinic.specialties or ["Cosmetic Surgery", "Aesthetic Medicine"],
        "priceRange": "₹₹₹",
        "availableService": []
    }
    
    # Add services based on packages
    packages = Package.query.filter_by(clinic_id=clinic.id, is_active=True).all()
    for package in packages:
        service = {
            "@type": "MedicalProcedure",
            "name": package.title,
            "description": package.procedure_info[:200] if package.procedure_info else "",
            "offers": {
                "@type": "Offer",
                "price": str(package.price_discounted or package.price_actual),
                "priceCurrency": "INR"
            }
        }
        schema["availableService"].append(service)
    
    return schema

def generate_doctor_schema(doctor):
    """Generate structured data schema for doctor pages."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Physician",
        "name": doctor.name,
        "description": doctor.bio or f"Experienced {doctor.specialty} specialist",
        "url": f"https://antidote.com/doctors/{doctor.id}",
        "medicalSpecialty": doctor.specialty,
        "yearsOfExperience": doctor.experience,
        "worksFor": {
            "@type": "MedicalOrganization",
            "name": doctor.clinic.name if doctor.clinic else doctor.hospital
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": str(doctor.rating or 4.5),
            "reviewCount": str(doctor.review_count or 0)
        },
        "offers": {
            "@type": "Offer",
            "name": "Medical Consultation",
            "price": str(doctor.consultation_fee or 1000),
            "priceCurrency": "INR"
        }
    }
    
    if doctor.qualification:
        schema["hasCredential"] = {
            "@type": "EducationalOccupationalCredential",
            "credentialCategory": "degree",
            "educationalLevel": doctor.qualification
        }
    
    return schema

def generate_package_schema(package):
    """Generate structured data schema for package pages."""
    schema = {
        "@context": "https://schema.org",
        "@type": "MedicalProcedure",
        "name": package.title,
        "description": package.procedure_info[:300] if package.procedure_info else "",
        "url": f"https://antidote.com/packages/{package.id}",
        "provider": {
            "@type": "MedicalOrganization",
            "name": package.clinic.name,
            "address": package.clinic.address
        },
        "offers": {
            "@type": "Offer",
            "price": str(package.price_discounted or package.price_actual),
            "priceCurrency": "INR",
            "availability": "https://schema.org/InStock"
        }
    }
    
    if package.duration:
        schema["duration"] = package.duration
    
    if package.downtime:
        schema["followup"] = {
            "@type": "MedicalProcedure",
            "name": "Recovery Period",
            "description": f"Expected downtime: {package.downtime}"
        }
    
    return schema

def generate_procedure_schema(procedure):
    """Generate structured data schema for procedure pages."""
    schema = {
        "@context": "https://schema.org",
        "@type": "MedicalProcedure",
        "name": procedure.procedure_name,
        "description": procedure.short_description,
        "url": f"https://antidote.com/procedures/{procedure.id}",
        "procedureType": procedure.procedure_types,
        "bodyLocation": procedure.body_part,
        "preparation": procedure.ideal_candidates,
        "followup": procedure.recovery_process,
        "howPerformed": procedure.procedure_details,
        "expectedPrognosis": procedure.benefits,
        "riskFactor": procedure.risks,
        "typicalAgeRange": "18-65",
        "offers": {
            "@type": "AggregateOffer",
            "lowPrice": str(procedure.min_cost),
            "highPrice": str(procedure.max_cost),
            "priceCurrency": "INR"
        }
    }
    
    if procedure.procedure_duration:
        schema["duration"] = procedure.procedure_duration
    
    return schema

def generate_meta_tags(page_type, entity):
    """Generate meta tags for different page types."""
    meta_tags = {}
    
    if page_type == 'clinic':
        meta_tags = {
            'title': f"{entity.name} - Best Cosmetic Surgery Clinic in {entity.city} | Antidote",
            'description': f"Book consultation at {entity.name} in {entity.city}. {len(entity.specialties or [])} specialties available. Rated {entity.rating or 4.5}/5 by {entity.review_count or 0} patients.",
            'keywords': f"cosmetic surgery {entity.city}, plastic surgeon {entity.city}, {entity.name}, aesthetic clinic",
            'og:title': f"{entity.name} - Premium Cosmetic Surgery in {entity.city}",
            'og:description': f"Professional cosmetic surgery services at {entity.name}. Expert doctors, modern facilities, proven results.",
            'og:type': 'business.business',
            'og:url': f"https://antidote.com/clinics/{entity.id}",
            'twitter:card': 'summary_large_image'
        }
    
    elif page_type == 'doctor':
        meta_tags = {
            'title': f"Dr. {entity.name} - {entity.specialty} Specialist in {entity.city} | Antidote",
            'description': f"Consult Dr. {entity.name}, {entity.specialty} specialist with {entity.experience} years experience. Book consultation for ₹{entity.consultation_fee or 1000}.",
            'keywords': f"{entity.specialty} doctor {entity.city}, Dr. {entity.name}, cosmetic surgeon {entity.city}",
            'og:title': f"Dr. {entity.name} - Expert {entity.specialty} Specialist",
            'og:description': f"Professional {entity.specialty} treatments by Dr. {entity.name}. {entity.experience} years experience.",
            'og:type': 'profile',
            'og:url': f"https://antidote.com/doctors/{entity.id}",
            'twitter:card': 'summary'
        }
    
    elif page_type == 'package':
        meta_tags = {
            'title': f"{entity.title} at {entity.clinic.name} - ₹{entity.price_discounted or entity.price_actual} | Antidote",
            'description': f"Book {entity.title} package at {entity.clinic.name}. Professional treatment with {entity.duration or 'quick'} duration. Starting from ₹{entity.price_discounted or entity.price_actual}.",
            'keywords': f"{entity.category} package, {entity.title}, cosmetic surgery package {entity.clinic.city}",
            'og:title': f"{entity.title} - Professional Treatment Package",
            'og:description': f"Complete {entity.title} package with expert care and proven results.",
            'og:type': 'product',
            'og:url': f"https://antidote.com/packages/{entity.id}",
            'twitter:card': 'summary_large_image'
        }
    
    elif page_type == 'procedure':
        meta_tags = {
            'title': f"{entity.procedure_name} Cost, Benefits & Best Doctors in India | Antidote",
            'description': f"Complete guide to {entity.procedure_name}. Cost range: ₹{entity.min_cost:,}-₹{entity.max_cost:,}. Benefits, risks, recovery time and best doctors in India.",
            'keywords': f"{entity.procedure_name} cost India, {entity.procedure_name} doctors, {entity.body_part} surgery",
            'og:title': f"{entity.procedure_name} - Complete Treatment Guide",
            'og:description': f"Everything about {entity.procedure_name}: costs, benefits, recovery and expert doctors.",
            'og:type': 'article',
            'og:url': f"https://antidote.com/procedures/{entity.id}",
            'twitter:card': 'summary_large_image'
        }
    
    return meta_tags

def generate_breadcrumb_schema(breadcrumbs):
    """Generate breadcrumb structured data."""
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }
    
    for index, (name, url) in enumerate(breadcrumbs, 1):
        item = {
            "@type": "ListItem",
            "position": index,
            "name": name,
            "item": f"https://antidote.com{url}"
        }
        schema["itemListElement"].append(item)
    
    return schema

def generate_faq_schema(faqs):
    """Generate FAQ structured data."""
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }
    
    for question, answer in faqs:
        faq_item = {
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": answer
            }
        }
        schema["mainEntity"].append(faq_item)
    
    return schema

def get_related_procedures(procedure_id, limit=5):
    """Get related procedures for internal linking."""
    procedure = Procedure.query.get(procedure_id)
    if not procedure:
        return []
    
    # Find procedures in same category or body part
    related = Procedure.query.filter(
        Procedure.id != procedure_id,
        (Procedure.category_id == procedure.category_id) | 
        (Procedure.body_part == procedure.body_part)
    ).limit(limit).all()
    
    return related

def get_procedure_sitemap_urls():
    """Generate sitemap URLs for all procedures."""
    try:
        from models import Procedure
        procedures = Procedure.query.all()
        urls = []
        
        for procedure in procedures:
            # Handle missing timestamps safely
            lastmod = None
            if hasattr(procedure, 'updated_at') and procedure.updated_at:
                lastmod = procedure.updated_at.isoformat()
            elif hasattr(procedure, 'created_at') and procedure.created_at:
                lastmod = procedure.created_at.isoformat()
            else:
                from datetime import datetime
                lastmod = datetime.now().isoformat()
                
            urls.append({
                'loc': f"https://antidote.replit.app/procedures/{procedure.id}",
                'lastmod': lastmod,
                'changefreq': 'weekly',
                'priority': '0.8'
            })
        
        return urls
    except Exception as e:
        print(f"Error generating procedure sitemap URLs: {e}")
        return []

def get_clinic_sitemap_urls():
    """Generate sitemap URLs for all approved clinics."""
    try:
        from models import Clinic
        clinics = Clinic.query.filter_by(is_approved=True).all()
        urls = []
        
        for clinic in clinics:
            # Handle missing timestamps safely
            lastmod = None
            if hasattr(clinic, 'updated_at') and clinic.updated_at:
                lastmod = clinic.updated_at.isoformat()
            elif hasattr(clinic, 'created_at') and clinic.created_at:
                lastmod = clinic.created_at.isoformat()
            else:
                from datetime import datetime
                lastmod = datetime.now().isoformat()
                
            urls.append({
                'loc': f"https://antidote.replit.app/clinics/{clinic.id}",
                'lastmod': lastmod,
                'changefreq': 'weekly',
                'priority': '0.9'
            })
        
        return urls
    except Exception as e:
        return []

def get_doctor_sitemap_urls():
    """Generate sitemap URLs for all verified doctors."""
    try:
        from models import Doctor
        doctors = Doctor.query.filter_by(verification_status='approved').all()
        urls = []
        
        for doctor in doctors:
            urls.append({
                'loc': f"https://antidote.replit.app/doctors/{doctor.id}",
                'lastmod': doctor.verification_date.isoformat() if doctor.verification_date else doctor.created_at.isoformat(),
                'changefreq': 'monthly',
                'priority': '0.7'
            })
        
        return urls
    except Exception as e:
        return []

def get_package_sitemap_urls():
    """Generate sitemap URLs for all active packages."""
    try:
        from models import Package
        packages = Package.query.filter_by(is_active=True).all()
        urls = []
        
        for package in packages:
            urls.append({
                'loc': f"https://antidote.replit.app/packages/{package.id}",
                'lastmod': package.updated_at.isoformat() if package.updated_at else package.created_at.isoformat(),
                'changefreq': 'weekly',
                'priority': '0.8'
            })
        
        return urls
    except Exception as e:
        return []

def get_category_sitemap_urls():
    """Generate sitemap URLs for all categories."""
    try:
        categories = Category.query.all()
        urls = []
        
        for category in categories:
            urls.append({
                'loc': f"https://antidote.replit.app/categories/{category.id}",
                'lastmod': category.updated_at.isoformat() if category.updated_at else category.created_at.isoformat(),
                'changefreq': 'monthly',
                'priority': '0.6'
            })
        
        return urls
    except Exception as e:
        return []

@seo_bp.route('/sitemap.xml')
def sitemap():
    """Generate comprehensive XML sitemap for all content."""
    urls = []
    
    # Static pages with enhanced priorities
    static_pages = [
        {'loc': 'https://antidote.replit.app/', 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': 'https://antidote.replit.app/clinics', 'changefreq': 'daily', 'priority': '0.9'},
        {'loc': 'https://antidote.replit.app/doctors', 'changefreq': 'daily', 'priority': '0.9'},
        {'loc': 'https://antidote.replit.app/procedures', 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': 'https://antidote.replit.app/packages', 'changefreq': 'daily', 'priority': '0.8'},
        {'loc': 'https://antidote.replit.app/community', 'changefreq': 'daily', 'priority': '0.7'},
        {'loc': 'https://antidote.replit.app/face-analysis', 'changefreq': 'weekly', 'priority': '0.6'},
        {'loc': 'https://antidote.replit.app/cost-calculator', 'changefreq': 'weekly', 'priority': '0.6'},
        {'loc': 'https://antidote.replit.app/learn', 'changefreq': 'weekly', 'priority': '0.5'},
    ]
    
    urls.extend(static_pages)
    urls.extend(get_procedure_sitemap_urls())
    urls.extend(get_clinic_sitemap_urls())
    urls.extend(get_doctor_sitemap_urls())
    urls.extend(get_package_sitemap_urls())
    urls.extend(get_category_sitemap_urls())
    
    # Generate XML with proper encoding
    xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:mobile="http://www.google.com/schemas/sitemap-mobile/1.0"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
{% for url in urls %}
    <url>
        <loc>{{ url.loc }}</loc>
        {% if url.lastmod %}<lastmod>{{ url.lastmod }}</lastmod>{% endif %}
        <changefreq>{{ url.changefreq }}</changefreq>
        <priority>{{ url.priority }}</priority>
        <mobile:mobile/>
    </url>
{% endfor %}
</urlset>'''
    
    return render_template_string(xml_template, urls=urls), 200, {'Content-Type': 'application/xml; charset=utf-8'}

@seo_bp.route('/robots.txt')
def robots():
    """Generate robots.txt file."""
    robot_txt = '''User-agent: *
Allow: /
Disallow: /admin/
Disallow: /clinic/dashboard/
Disallow: /api/
Sitemap: https://antidote.com/sitemap.xml
'''
    return robot_txt, 200, {'Content-Type': 'text/plain'}

def generate_canonical_url(page_type, entity_id):
    """Generate canonical URL for pages."""
    base_urls = {
        'clinic': f"https://antidote.com/clinics/{entity_id}",
        'doctor': f"https://antidote.com/doctors/{entity_id}",
        'procedure': f"https://antidote.com/procedures/{entity_id}",
        'package': f"https://antidote.com/packages/{entity_id}"
    }
    return base_urls.get(page_type, "https://antidote.com/")

def get_location_based_content(city, procedure_type=None):
    """Get location-based content for local SEO."""
    if procedure_type:
        title = f"Best {procedure_type} Doctors in {city} - Top Clinics & Costs"
        description = f"Find top-rated {procedure_type} doctors and clinics in {city}. Compare costs, read reviews, book consultations. Expert care with proven results."
    else:
        title = f"Best Cosmetic Surgery Clinics in {city} - Expert Doctors & Treatments"
        description = f"Discover top cosmetic surgery clinics in {city}. Expert doctors, modern facilities, comprehensive treatments. Book consultation today."
    
    return {
        'title': title,
        'description': description,
        'local_keywords': f"cosmetic surgery {city}, plastic surgeon {city}, aesthetic clinic {city}"
    }