"""
SEO Optimization Routes for Antidote Medical Marketplace
Handles sitemap generation, robots.txt serving, and SEO-specific routes
"""

from flask import Blueprint, Response, render_template, request, url_for
from datetime import datetime, timedelta
from models import db, Procedure, Doctor, Clinic, Category
import xml.etree.ElementTree as ET

seo_bp = Blueprint('seo_optimization', __name__)

@seo_bp.route('/robots.txt')
def robots_txt():
    """Serve robots.txt file"""
    try:
        with open('static/robots.txt', 'r') as f:
            content = f.read()
        return Response(content, mimetype='text/plain')
    except FileNotFoundError:
        # Fallback robots.txt
        content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/admin/
Sitemap: https://antidote.replit.app/sitemap.xml"""
        return Response(content, mimetype='text/plain')

@seo_bp.route('/sitemap.xml')
def sitemap_xml():
    """Generate dynamic XML sitemap"""
    try:
        # Create root element
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        urlset.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
        
        base_url = 'https://antidote.replit.app'
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Helper function to add URL
        def add_url(loc, lastmod=today, changefreq='weekly', priority='0.5', images=None):
            url = ET.SubElement(urlset, 'url')
            ET.SubElement(url, 'loc').text = f"{base_url}{loc}"
            ET.SubElement(url, 'lastmod').text = lastmod
            ET.SubElement(url, 'changefreq').text = changefreq
            ET.SubElement(url, 'priority').text = priority
            
            # Add image information if provided
            if images:
                for img_url, img_caption in images:
                    image = ET.SubElement(url, 'image:image')
                    ET.SubElement(image, 'image:loc').text = img_url
                    ET.SubElement(image, 'image:caption').text = img_caption
        
        # Homepage - highest priority
        add_url('/', today, 'daily', '1.0')
        
        # Main category pages - high priority
        add_url('/procedures', today, 'weekly', '0.9')
        add_url('/doctors', today, 'weekly', '0.9')
        add_url('/clinics', today, 'weekly', '0.9')
        add_url('/packages', today, 'weekly', '0.9')
        add_url('/community', today, 'daily', '0.8')
        
        # Special pages
        add_url('/ai-recommendation', today, 'monthly', '0.8')
        add_url('/face-analysis', today, 'monthly', '0.7')
        add_url('/search', today, 'monthly', '0.6')
        
        # Procedure pages
        try:
            procedures = Procedure.query.all()
            for procedure in procedures:
                images = []
                if procedure.image_url:
                    images.append((f"{base_url}{procedure.image_url}", f"{procedure.name} - Medical Procedure"))
                
                add_url(
                    f'/procedures/{procedure.id}',
                    today,
                    'monthly',
                    '0.8',
                    images
                )
        except Exception as e:
            print(f"Error adding procedures to sitemap: {e}")
        
        # Doctor pages
        try:
            doctors = Doctor.query.filter_by(is_verified=True).limit(100).all()
            for doctor in doctors:
                images = []
                if doctor.profile_image:
                    images.append((f"{base_url}{doctor.profile_image}", f"Dr. {doctor.name} - Medical Professional"))
                
                add_url(
                    f'/doctors/{doctor.id}',
                    today,
                    'monthly',
                    '0.7',
                    images
                )
        except Exception as e:
            print(f"Error adding doctors to sitemap: {e}")
        
        # Clinic pages
        try:
            clinics = Clinic.query.filter_by(is_verified=True).limit(100).all()
            for clinic in clinics:
                images = []
                if clinic.image_url:
                    images.append((f"{base_url}{clinic.image_url}", f"{clinic.name} - Medical Clinic"))
                
                add_url(
                    f'/clinic/{clinic.id}',
                    today,
                    'monthly',
                    '0.7',
                    images
                )
        except Exception as e:
            print(f"Error adding clinics to sitemap: {e}")
        
        # Treatment package pages
        try:
            packages = TreatmentPackage.query.filter_by(is_active=True).limit(100).all()
            for package in packages:
                images = []
                if package.image_url:
                    images.append((f"{base_url}{package.image_url}", f"{package.name} - Treatment Package"))
                
                add_url(
                    f'/packages/{package.id}',
                    today,
                    'monthly',
                    '0.6',
                    images
                )
        except Exception as e:
            print(f"Error adding packages to sitemap: {e}")
        
        # Community thread pages (recent only)
        try:
            recent_threads = CommunityThread.query.filter_by(is_active=True)\
                .order_by(CommunityThread.created_at.desc()).limit(50).all()
            for thread in recent_threads:
                thread_date = thread.created_at.strftime('%Y-%m-%d') if thread.created_at else today
                add_url(
                    f'/community/thread/{thread.id}',
                    thread_date,
                    'weekly',
                    '0.5'
                )
        except Exception as e:
            print(f"Error adding community threads to sitemap: {e}")
        
        # Category pages
        try:
            categories = Category.query.all()
            for category in categories:
                images = []
                if category.image_url:
                    images.append((f"{base_url}{category.image_url}", f"{category.name} - Medical Category"))
                
                add_url(
                    f'/categories/{category.id}',
                    today,
                    'monthly',
                    '0.6',
                    images
                )
        except Exception as e:
            print(f"Error adding categories to sitemap: {e}")
        
        # Generate XML string
        xml_str = ET.tostring(urlset, encoding='unicode', method='xml')
        xml_formatted = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
        
        return Response(xml_formatted, mimetype='application/xml')
        
    except Exception as e:
        print(f"Error generating sitemap: {e}")
        # Return minimal sitemap on error
        minimal_sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://antidote.replit.app/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://antidote.replit.app/procedures</loc>
        <lastmod>{today}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://antidote.replit.app/doctors</loc>
        <lastmod>{today}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
</urlset>'''
        return Response(minimal_sitemap, mimetype='application/xml')

@seo_bp.route('/google-site-verification')
def google_verification():
    """Google Search Console verification endpoint"""
    return Response("google-site-verification: antidote-medical-marketplace", mimetype='text/plain')

@seo_bp.route('/.well-known/assetlinks.json')
def asset_links():
    """Android App Links verification"""
    asset_links = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "web",
                "site": "https://antidote.replit.app"
            }
        }
    ]
    return Response(str(asset_links).replace("'", '"'), mimetype='application/json')

@seo_bp.route('/opensearch.xml')
def opensearch_xml():
    """OpenSearch description for search engines"""
    opensearch_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>Antidote Medical Search</ShortName>
    <Description>Search medical procedures, doctors, and clinics on Antidote</Description>
    <Tags>medical marketplace plastic surgery cosmetic procedures doctors India</Tags>
    <Contact>info@antidote.replit.app</Contact>
    <Url type="text/html" template="https://antidote.replit.app/search?q={{searchTerms}}"/>
    <Image height="16" width="16" type="image/png">https://antidote.replit.app/static/favicon-16x16.png</Image>
    <Image height="32" width="32" type="image/png">https://antidote.replit.app/static/favicon-32x32.png</Image>
    <Developer>Antidote Medical Marketplace</Developer>
    <Attribution>Antidote - Medical Aesthetic Marketplace</Attribution>
    <SyndicationRight>open</SyndicationRight>
    <AdultContent>false</AdultContent>
    <Language>en-IN</Language>
    <InputEncoding>UTF-8</InputEncoding>
    <OutputEncoding>UTF-8</OutputEncoding>
</OpenSearchDescription>'''
    return Response(opensearch_xml, mimetype='application/xml')

# Register the blueprint in your main app
def register_seo_routes(app):
    """Register SEO routes with the Flask app"""
    app.register_blueprint(seo_bp)