"""
Content Landing Pages for SEO Optimization
Creates keyword-targeted landing pages for improved search ranking
"""

from flask import Blueprint, render_template, request, jsonify
from models import db, Procedure, Doctor, Clinic, Category

content_bp = Blueprint('content_landing', __name__, url_prefix='/content')

@content_bp.route('/antidote-medical-marketplace')
def antidote_medical_marketplace():
    """Landing page optimized for 'Antidote medical marketplace' searches"""
    # Get featured content
    featured_procedures = Procedure.query.limit(6).all()
    top_doctors = Doctor.query.limit(6).all()
    verified_clinics = Clinic.query.limit(6).all()
    
    seo_data = {
        'title': 'Antidote Medical Marketplace - India\'s Premier Platform for Aesthetic Medicine',
        'description': 'Antidote Medical Marketplace connects patients with verified plastic surgeons and cosmetic specialists across India. Compare procedures, read reviews, book consultations.',
        'keywords': 'antidote medical marketplace, plastic surgery India, cosmetic procedures, aesthetic medicine, verified doctors, medical tourism India',
        'canonical': '/content/antidote-medical-marketplace'
    }
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>{seo_data['title']}</title>
        <meta name="description" content="{seo_data['description']}">
        <meta name="keywords" content="{seo_data['keywords']}">
        <link rel="canonical" href="https://antidote.replit.app{seo_data['canonical']}">
        <meta property="og:title" content="{seo_data['title']}">
        <meta property="og:description" content="{seo_data['description']}">
        <meta property="og:url" content="https://antidote.replit.app{seo_data['canonical']}">
    </head>
    <body>
        <h1>Antidote Medical Marketplace</h1>
        <p>India's premier platform for aesthetic medicine procedures and treatments.</p>
        <p>We have {len(featured_procedures)} featured procedures, {len(top_doctors)} top doctors, and {len(verified_clinics)} verified clinics.</p>
        <a href="/">Visit Main Site</a>
    </body>
    </html>
    """

@content_bp.route('/antidote-plastic-surgery-india')
def antidote_plastic_surgery():
    """Landing page for plastic surgery searches"""
    # Get plastic surgery procedures
    plastic_procedures = db.session.query(Procedure).filter(
        Procedure.procedure_name.contains('surgery') | 
        Procedure.procedure_name.contains('plastic') |
        Procedure.procedure_name.contains('Surgery') |
        Procedure.procedure_name.contains('Plastic')
    ).limit(10).all()
    
    specialist_doctors = db.session.query(Doctor).limit(8).all()
    
    seo_data = {
        'title': 'Antidote Plastic Surgery - Find Top Plastic Surgeons in India',
        'description': 'Discover qualified plastic surgeons on Antidote. Compare procedures, view credentials, read patient reviews. Your trusted marketplace for plastic surgery in India.',
        'keywords': 'antidote plastic surgery, plastic surgeons India, cosmetic surgery, aesthetic procedures, board certified surgeons',
        'canonical': '/content/antidote-plastic-surgery-india'
    }
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>{seo_data['title']}</title>
        <meta name="description" content="{seo_data['description']}">
        <meta name="keywords" content="{seo_data['keywords']}">
        <link rel="canonical" href="https://antidote.replit.app{seo_data['canonical']}">
        <meta property="og:title" content="{seo_data['title']}">
        <meta property="og:description" content="{seo_data['description']}">
        <meta property="og:url" content="https://antidote.replit.app{seo_data['canonical']}">
    </head>
    <body>
        <h1>Antidote Plastic Surgery</h1>
        <p>Find top plastic surgeons in India. Compare procedures, view credentials, read patient reviews.</p>
        <p>We have {len(plastic_procedures)} plastic surgery procedures and {len(specialist_doctors)} specialist doctors.</p>
        <a href="/">Visit Main Site</a>
    </body>
    </html>
    """

@content_bp.route('/antidote-cosmetic-treatments')
def antidote_cosmetic_treatments():
    """Landing page for cosmetic treatment searches"""
    cosmetic_procedures = Procedure.query.filter(
        Procedure.name.contains('cosmetic') |
        Procedure.name.contains('aesthetic') |
        Procedure.name.contains('treatment')
    ).filter_by(is_active=True).limit(12).all()
    
    treatment_packages = TreatmentPackage.query.filter_by(is_active=True).limit(8).all()
    
    seo_data = {
        'title': 'Antidote Cosmetic Treatments - Advanced Aesthetic Procedures',
        'description': 'Explore comprehensive cosmetic treatments on Antidote. Non-surgical and surgical options from verified specialists. Book consultations today.',
        'keywords': 'antidote cosmetic treatments, aesthetic procedures, non-surgical treatments, cosmetic specialists, beauty treatments India',
        'canonical': '/content/antidote-cosmetic-treatments'
    }
    
    return render_template('content/cosmetic_treatments.html',
                         procedures=cosmetic_procedures,
                         packages=treatment_packages,
                         seo_data=seo_data)

@content_bp.route('/antidote-medical-tourism-india')
def medical_tourism():
    """Landing page for medical tourism searches"""
    top_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune']
    city_clinics = {}
    
    for city in top_cities:
        clinics = Clinic.query.filter(
            Clinic.location.contains(city)
        ).filter_by(is_verified=True).limit(3).all()
        if clinics:
            city_clinics[city] = clinics
    
    international_packages = TreatmentPackage.query.filter(
        TreatmentPackage.description.contains('international') |
        TreatmentPackage.name.contains('package')
    ).filter_by(is_active=True).limit(6).all()
    
    seo_data = {
        'title': 'Antidote Medical Tourism - World-Class Healthcare in India',
        'description': 'Experience premium medical tourism with Antidote. Connect with top hospitals and specialists across India. Comprehensive care packages for international patients.',
        'keywords': 'antidote medical tourism, healthcare India, medical travel, international patients, plastic surgery tourism, cosmetic surgery abroad',
        'canonical': '/content/antidote-medical-tourism-india'
    }
    
    return render_template('content/medical_tourism.html',
                         city_clinics=city_clinics,
                         packages=international_packages,
                         seo_data=seo_data)

@content_bp.route('/antidote-ai-recommendations')
def ai_recommendations_landing():
    """Landing page for AI recommendation searches"""
    # Get popular procedures for AI recommendations
    popular_procedures = Procedure.query.filter_by(is_active=True).limit(8).all()
    
    seo_data = {
        'title': 'Antidote AI Recommendations - Personalized Treatment Guidance',
        'description': 'Get AI-powered treatment recommendations on Antidote. Discover procedures suited to your needs with advanced facial analysis and expert guidance.',
        'keywords': 'antidote AI recommendations, AI treatment guidance, facial analysis, personalized procedures, smart healthcare, AI cosmetic surgery',
        'canonical': '/content/antidote-ai-recommendations'
    }
    
    return render_template('content/ai_recommendations.html',
                         procedures=popular_procedures,
                         seo_data=seo_data)

# City-specific landing pages for local SEO
@content_bp.route('/antidote-mumbai')
def antidote_mumbai():
    """Mumbai-specific landing page"""
    mumbai_clinics = Clinic.query.filter(
        Clinic.location.contains('Mumbai')
    ).filter_by(is_verified=True).limit(10).all()
    
    mumbai_doctors = Doctor.query.filter(
        Doctor.location.contains('Mumbai')
    ).filter_by(is_verified=True).limit(8).all()
    
    seo_data = {
        'title': 'Antidote Mumbai - Top Plastic Surgeons & Cosmetic Clinics',
        'description': 'Find the best plastic surgeons and cosmetic clinics in Mumbai through Antidote. Verified specialists, transparent pricing, easy booking.',
        'keywords': 'antidote mumbai, plastic surgery mumbai, cosmetic clinics mumbai, aesthetic treatments mumbai, doctors mumbai',
        'canonical': '/content/antidote-mumbai'
    }
    
    return render_template('content/city_page.html',
                         city='Mumbai',
                         clinics=mumbai_clinics,
                         doctors=mumbai_doctors,
                         seo_data=seo_data)

@content_bp.route('/antidote-delhi')
def antidote_delhi():
    """Delhi-specific landing page"""
    delhi_clinics = Clinic.query.filter(
        Clinic.location.contains('Delhi') | Clinic.location.contains('NCR')
    ).filter_by(is_verified=True).limit(10).all()
    
    delhi_doctors = Doctor.query.filter(
        Doctor.location.contains('Delhi') | Doctor.location.contains('NCR')
    ).filter_by(is_verified=True).limit(8).all()
    
    seo_data = {
        'title': 'Antidote Delhi - Premier Cosmetic Surgery & Aesthetic Centers',
        'description': 'Discover top-rated plastic surgeons and aesthetic centers in Delhi NCR. Book consultations with verified specialists on Antidote.',
        'keywords': 'antidote delhi, plastic surgery delhi ncr, cosmetic clinics delhi, aesthetic treatments delhi, doctors delhi',
        'canonical': '/content/antidote-delhi'
    }
    
    return render_template('content/city_page.html',
                         city='Delhi',
                         clinics=delhi_clinics,
                         doctors=delhi_doctors,
                         seo_data=seo_data)

@content_bp.route('/antidote-bangalore')
def antidote_bangalore():
    """Bangalore-specific landing page"""
    bangalore_clinics = Clinic.query.filter(
        Clinic.location.contains('Bangalore') | Clinic.location.contains('Bengaluru')
    ).filter_by(is_verified=True).limit(10).all()
    
    bangalore_doctors = Doctor.query.filter(
        Doctor.location.contains('Bangalore') | Doctor.location.contains('Bengaluru')
    ).filter_by(is_verified=True).limit(8).all()
    
    seo_data = {
        'title': 'Antidote Bangalore - Advanced Cosmetic Surgery & Treatments',
        'description': 'Connect with leading cosmetic surgeons and aesthetic clinics in Bangalore. Experience world-class treatments with Antidote.',
        'keywords': 'antidote bangalore, plastic surgery bangalore, cosmetic clinics bengaluru, aesthetic treatments bangalore, doctors bangalore',
        'canonical': '/content/antidote-bangalore'
    }
    
    return render_template('content/city_page.html',
                         city='Bangalore',
                         clinics=bangalore_clinics,
                         doctors=bangalore_doctors,
                         seo_data=seo_data)

# Register the blueprint
def register_content_routes(app):
    """Register content landing page routes with the Flask app"""
    app.register_blueprint(content_bp)