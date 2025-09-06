#!/usr/bin/env python3
"""
Add additional admin page routes for User Management, Community Moderation, and Analytics.
"""
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_admin_routes():
    """Add admin routes for new admin pages."""
    try:
        routes_file = 'routes.py'
        
        with open(routes_file, 'r') as f:
            routes_content = f.read()
        
        # Check if the admin page routes need to be added
        admin_pages_routes = '''
@web.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin user management page."""
    return render_template('admin/users.html')

@web.route('/admin/community-moderation')
@login_required
@admin_required
def admin_community_moderation():
    """Admin community moderation page."""
    return render_template('admin/community_moderation.html')

@web.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    """Admin analytics and reports page."""
    return render_template('admin/analytics.html')
'''
        
        # Find a good position to add the routes (just after the admin_dashboard route)
        admin_dashboard_pattern = '@web.route(\'/dashboard/admin\')'
        admin_dashboard_pos = routes_content.find(admin_dashboard_pattern)
        
        if admin_dashboard_pos != -1:
            # Find the end of the admin_dashboard function
            admin_dashboard_end = routes_content.find('\n\n', admin_dashboard_pos)
            if admin_dashboard_end == -1:
                admin_dashboard_end = len(routes_content)
                
            # Insert our new routes after the admin_dashboard function
            new_routes_content = routes_content[:admin_dashboard_end] + '\n' + admin_pages_routes + routes_content[admin_dashboard_end:]
            
            with open(routes_file, 'w') as f:
                f.write(new_routes_content)
                
            logger.info("Added admin page routes successfully")
            return True
        else:
            logger.error("Admin dashboard route not found - could not add admin page routes")
            return False
    
    except Exception as e:
        logger.error(f"Error adding admin page routes: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_admin_routes()
    if success:
        print("Admin page routes added successfully. Please restart the Flask application.")
    else:
        print("Failed to add admin page routes. See logs for details.")