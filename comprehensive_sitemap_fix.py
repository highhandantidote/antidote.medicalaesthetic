"""
Comprehensive Sitemap Generation Fix for Antidote Medical Marketplace
Generates proper XML sitemap with all 3,100+ pages for maximum SEO impact
"""

from flask import Blueprint, render_template_string
from datetime import datetime
import logging

# Create blueprint
sitemap_bp = Blueprint('comprehensive_sitemap', __name__)

logger = logging.getLogger(__name__)

def get_all_sitemap_urls():
    """Generate complete sitemap URLs for all content types."""
    urls = []
    
    # Static high-priority pages
    static_pages = [
        {'loc': 'https://antidote.fit/', 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': 'https://antidote.fit/clinics', 'changefreq': 'daily', 'priority': '0.9'},
        {'loc': 'https://antidote.fit/doctors', 'changefreq': 'daily', 'priority': '0.9'},
        {'loc': 'https://antidote.fit/procedures', 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': 'https://antidote.fit/packages', 'changefreq': 'daily', 'priority': '0.8'},
        {'loc': 'https://antidote.fit/categories', 'changefreq': 'weekly', 'priority': '0.7'},
        {'loc': 'https://antidote.fit/community', 'changefreq': 'daily', 'priority': '0.7'},
        {'loc': 'https://antidote.fit/face-analysis', 'changefreq': 'weekly', 'priority': '0.6'},
        {'loc': 'https://antidote.fit/cost-calculator', 'changefreq': 'weekly', 'priority': '0.6'},
        {'loc': 'https://antidote.fit/ai-recommendation', 'changefreq': 'weekly', 'priority': '0.6'},
        {'loc': 'https://antidote.fit/learn', 'changefreq': 'weekly', 'priority': '0.5'},
    ]
    
    urls.extend(static_pages)
    
    # Add all procedures (521 pages)
    try:
        from models import Procedure
        procedures = Procedure.query.all()
        logger.info(f"Adding {len(procedures)} procedures to sitemap")
        
        for procedure in procedures:
            lastmod = datetime.now().isoformat()
            if hasattr(procedure, 'updated_at') and procedure.updated_at:
                lastmod = procedure.updated_at.isoformat()
            elif hasattr(procedure, 'created_at') and procedure.created_at:
                lastmod = procedure.created_at.isoformat()
                
            urls.append({
                'loc': f"https://antidote.fit/procedures/{procedure.id}",
                'lastmod': lastmod,
                'changefreq': 'weekly',
                'priority': '0.8'
            })
    except Exception as e:
        logger.error(f"Error adding procedures to sitemap: {e}")
    
    # Add all approved clinics (2,399 pages)
    try:
        from models import Clinic
        clinics = Clinic.query.filter_by(is_approved=True).all()
        logger.info(f"Adding {len(clinics)} approved clinics to sitemap")
        
        for clinic in clinics:
            lastmod = datetime.now().isoformat()
            if hasattr(clinic, 'updated_at') and clinic.updated_at:
                lastmod = clinic.updated_at.isoformat()
            elif hasattr(clinic, 'created_at') and clinic.created_at:
                lastmod = clinic.created_at.isoformat()
                
            urls.append({
                'loc': f"https://antidote.fit/clinics/{clinic.id}",
                'lastmod': lastmod,
                'changefreq': 'weekly',
                'priority': '0.9'
            })
    except Exception as e:
        logger.error(f"Error adding clinics to sitemap: {e}")
    
    # Add all verified doctors (106 pages)
    try:
        from models import Doctor
        doctors = Doctor.query.filter_by(verification_status='approved').all()
        logger.info(f"Adding {len(doctors)} verified doctors to sitemap")
        
        for doctor in doctors:
            lastmod = datetime.now().isoformat()
            if hasattr(doctor, 'verification_date') and doctor.verification_date:
                lastmod = doctor.verification_date.isoformat()
            elif hasattr(doctor, 'created_at') and doctor.created_at:
                lastmod = doctor.created_at.isoformat()
                
            urls.append({
                'loc': f"https://antidote.fit/doctors/{doctor.id}",
                'lastmod': lastmod,
                'changefreq': 'monthly',
                'priority': '0.7'
            })
    except Exception as e:
        logger.error(f"Error adding doctors to sitemap: {e}")
    
    # Add all active packages (36 pages)
    try:
        from models import Package
        packages = Package.query.filter_by(is_active=True).all()
        logger.info(f"Adding {len(packages)} active packages to sitemap")
        
        for package in packages:
            lastmod = datetime.now().isoformat()
            if hasattr(package, 'updated_at') and package.updated_at:
                lastmod = package.updated_at.isoformat()
            elif hasattr(package, 'created_at') and package.created_at:
                lastmod = package.created_at.isoformat()
                
            urls.append({
                'loc': f"https://antidote.fit/packages/{package.id}",
                'lastmod': lastmod,
                'changefreq': 'weekly',
                'priority': '0.8'
            })
    except Exception as e:
        logger.error(f"Error adding packages to sitemap: {e}")
    
    # Add all categories (43 pages)
    try:
        from models import Category
        categories = Category.query.all()
        logger.info(f"Adding {len(categories)} categories to sitemap")
        
        for category in categories:
            lastmod = datetime.now().isoformat()
            if hasattr(category, 'updated_at') and category.updated_at:
                lastmod = category.updated_at.isoformat()
            elif hasattr(category, 'created_at') and category.created_at:
                lastmod = category.created_at.isoformat()
                
            urls.append({
                'loc': f"https://antidote.fit/categories/{category.id}",
                'lastmod': lastmod,
                'changefreq': 'monthly',
                'priority': '0.6'
            })
    except Exception as e:
        logger.error(f"Error adding categories to sitemap: {e}")
    
    logger.info(f"Total sitemap URLs generated: {len(urls)}")
    return urls

@sitemap_bp.route('/sitemap.xml')
def comprehensive_sitemap():
    """Generate comprehensive XML sitemap with all 3,100+ pages."""
    urls = get_all_sitemap_urls()
    
    # Enhanced XML template with proper mobile optimization
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
    
    return render_template_string(xml_template, urls=urls), 200, {
        'Content-Type': 'application/xml; charset=utf-8',
        'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
        'X-Robots-Tag': 'index, follow, all'  # Override noindex headers for sitemap
    }

def register_comprehensive_sitemap(app):
    """Comprehensive sitemap disabled - using optimized sitemap index in routes.py instead."""
    # This prevents timeout issues and improves GSC compatibility
    logger.info("⚠️ Comprehensive sitemap disabled - using optimized sitemap index instead")