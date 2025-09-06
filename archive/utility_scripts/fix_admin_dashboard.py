#!/usr/bin/env python3
"""
Fix the admin dashboard to properly link to the banner management page.
"""
import os
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_banner_link():
    """Add an admin banner link to the base template."""
    
    try:
        # Create a templates/admin directory if it doesn't exist
        os.makedirs('templates/admin', exist_ok=True)
        
        # Create an admin dashboard template that redirects to the banner management page
        admin_dashboard_template = '''{% extends 'base.html' %}

{% block title %}Admin Dashboard | Antidote{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row">
        <div class="col-12">
            <h1 class="mb-4">Admin Dashboard</h1>
            
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">Banner Management</h5>
                            <p class="card-text">Create, edit, and manage banner displays for the homepage.</p>
                            <a href="{{ url_for('banners.admin_banners') }}" class="btn btn-primary">Manage Banners</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">Doctor Verification</h5>
                            <p class="card-text">Review and verify doctor accounts and credentials.</p>
                            <a href="#" class="btn btn-primary">Manage Doctors</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">User Management</h5>
                            <p class="card-text">Manage user accounts, roles, and permissions.</p>
                            <a href="#" class="btn btn-primary">Manage Users</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">Content Management</h5>
                            <p class="card-text">Manage procedures, categories, and educational content.</p>
                            <a href="#" class="btn btn-primary">Manage Content</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">Community Moderation</h5>
                            <p class="card-text">Moderate community posts, threads, and replies.</p>
                            <a href="#" class="btn btn-primary">Moderate Community</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title">Analytics & Reports</h5>
                            <p class="card-text">View platform analytics, reports, and statistics.</p>
                            <a href="#" class="btn btn-primary">View Analytics</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
        
        # Write the template to file
        with open('templates/admin/dashboard.html', 'w') as f:
            f.write(admin_dashboard_template)
        
        logger.info("Created admin dashboard template with banner management link")
        
        # Create a direct access link in the navigation
        add_admin_menu_link()
        
        return True
    except Exception as e:
        logger.error(f"Error creating admin dashboard template: {str(e)}")
        return False

def add_admin_menu_link():
    """Add a direct link to the admin banners page in the dropdown menu for admins."""
    try:
        # Modify the base.html template to add a direct link
        base_html_path = 'templates/base.html'
        
        with open(base_html_path, 'r') as f:
            base_html = f.read()
        
        # Check if we need to add a direct link to banners
        admin_banner_link = '''                                    <li><a class="dropdown-item" href="{{ url_for('banners.admin_banners') }}">
                                        <i class="fas fa-images me-2"></i> Banner Management
                                    </a></li>'''
        
        # Find the admin section in the dropdown
        admin_section = '''{% if current_user.role == 'admin' %}
                                    <li><hr class="dropdown-divider"></li>
                                    <li><a class="dropdown-item" href="{{ url_for('web.admin_dashboard') }}">
                                        <i class="fas fa-shield-alt me-2"></i> Admin Dashboard
                                    </a></li>'''
        
        # If the banner link doesn't exist, add it after the admin dashboard link
        if admin_banner_link not in base_html and admin_section in base_html:
            modified_section = admin_section + '\n' + admin_banner_link
            new_base_html = base_html.replace(admin_section, modified_section)
            
            with open(base_html_path, 'w') as f:
                f.write(new_base_html)
                
            logger.info("Added direct banner management link to admin dropdown menu")
            return True
        else:
            logger.info("Admin banner link already exists or admin section not found")
            return False
            
    except Exception as e:
        logger.error(f"Error adding admin menu link: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_admin_banner_link()
    if success:
        logger.info("Successfully added admin banner management links")
        print("Admin dashboard updated with banner management links. Please restart the Flask application.")
    else:
        logger.error("Failed to update admin dashboard")
        print("Error updating admin dashboard. See logs for details.")