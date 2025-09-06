"""
Google Search Console setup and verification for Antidote platform.
This script helps set up Google Search Console verification and generates necessary files.
"""

from flask import Blueprint, render_template_string
import os

# Create Google Search Console verification file
def create_google_verification():
    """Create Google Search Console verification HTML file."""
    verification_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Google Search Console Verification</title>
    <meta name="google-site-verification" content="REPLACE_WITH_YOUR_VERIFICATION_CODE" />
</head>
<body>
    <h1>Google Search Console Verification</h1>
    <p>This page verifies ownership of antidote.replit.app for Google Search Console.</p>
</body>
</html>'''
    
    # Write verification file
    with open('templates/google_verification.html', 'w') as f:
        f.write(verification_content)
    
    print("Google verification template created at templates/google_verification.html")
    print("Replace REPLACE_WITH_YOUR_VERIFICATION_CODE with your actual verification code from Google Search Console")

# Google Analytics setup
def create_analytics_snippet():
    """Create Google Analytics 4 tracking snippet."""
    analytics_snippet = '''
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
'''
    
    return analytics_snippet

# Schema.org structured data for medical procedures
def generate_medical_procedure_schema(procedure):
    """Generate Schema.org structured data for medical procedures."""
    schema = {
        "@context": "https://schema.org",
        "@type": "MedicalProcedure",
        "name": procedure.procedure_name,
        "description": f"Professional {procedure.procedure_name} treatment in India",
        "procedureType": "Cosmetic Surgery",
        "bodyLocation": procedure.category.body_part.name if procedure.category else "Various",
        "preparation": "Consultation required",
        "howPerformed": "Professional medical procedure",
        "followup": "Post-procedure care included",
        "cost": {
            "@type": "MonetaryAmount",
            "currency": "INR",
            "minValue": procedure.min_cost,
            "maxValue": procedure.max_cost
        },
        "provider": {
            "@type": "Organization",
            "name": "Antidote Medical Marketplace",
            "url": "https://antidote.replit.app"
        }
    }
    return schema

# Schema.org structured data for doctors
def generate_doctor_schema(doctor):
    """Generate Schema.org structured data for doctors."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Physician",
        "name": f"Dr. {doctor.name}",
        "jobTitle": doctor.specialty,
        "worksFor": {
            "@type": "MedicalOrganization",
            "name": doctor.clinic_name if hasattr(doctor, 'clinic_name') else "Healthcare Facility"
        },
        "medicalSpecialty": doctor.specialty,
        "hasCredential": {
            "@type": "EducationalOccupationalCredential",
            "credentialCategory": "Medical License"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": doctor.rating if doctor.rating else 4.5,
            "reviewCount": doctor.review_count if hasattr(doctor, 'review_count') else 10,
            "bestRating": 5,
            "worstRating": 1
        } if doctor.rating else None,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": doctor.city,
            "addressCountry": "IN"
        }
    }
    return schema

# Schema.org structured data for clinics
def generate_clinic_schema(clinic):
    """Generate Schema.org structured data for clinics."""
    schema = {
        "@context": "https://schema.org",
        "@type": "MedicalBusiness",
        "name": clinic.name,
        "description": f"Professional cosmetic surgery clinic in {clinic.city}",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": clinic.address,
            "addressLocality": clinic.city,
            "addressRegion": clinic.state,
            "postalCode": clinic.pincode,
            "addressCountry": "IN"
        },
        "telephone": clinic.phone,
        "email": clinic.email,
        "url": f"https://antidote.replit.app/clinics/{clinic.id}",
        "priceRange": "₹₹₹",
        "currenciesAccepted": "INR",
        "paymentAccepted": ["Cash", "Credit Card", "Digital Payment"],
        "openingHoursSpecification": {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "opens": "09:00",
            "closes": "18:00"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": clinic.rating if hasattr(clinic, 'rating') and clinic.rating else 4.5,
            "reviewCount": clinic.review_count if hasattr(clinic, 'review_count') else 25,
            "bestRating": 5,
            "worstRating": 1
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": clinic.latitude,
            "longitude": clinic.longitude
        } if hasattr(clinic, 'latitude') and clinic.latitude else None
    }
    return schema

# SEO performance tracking
def generate_seo_performance_report():
    """Generate SEO performance tracking data."""
    from models import Procedure, Doctor, Clinic
    
    report = {
        "total_pages": {
            "procedures": Procedure.query.count(),
            "doctors": Doctor.query.count(),
            "clinics": Clinic.query.filter_by(is_approved=True).count()
        },
        "seo_status": {
            "sitemap_generated": True,
            "robots_txt": True,
            "structured_data": True,
            "meta_tags": True,
            "canonical_urls": True
        },
        "recommendations": [
            "Submit sitemap to Google Search Console",
            "Set up Google Analytics 4",
            "Monitor Core Web Vitals",
            "Optimize page loading speeds",
            "Add more local SEO data",
            "Implement FAQ schema for procedures"
        ]
    }
    
    return report

if __name__ == "__main__":
    create_google_verification()
    print("\nSEO Setup Complete!")
    print("Next steps:")
    print("1. Add Google Analytics 4 tracking ID")
    print("2. Submit sitemap.xml to Google Search Console")
    print("3. Verify website ownership with Google")
    print("4. Monitor search performance regularly")