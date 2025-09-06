#!/usr/bin/env python3
"""
Fix the admin routes to ensure they properly direct to the correct admin pages.
"""
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_admin_route():
    """Fix the admin_dashboard route in routes.py"""
    try:
        routes_file = 'routes.py'
        
        with open(routes_file, 'r') as f:
            routes_content = f.read()
        
        # Check if the admin_dashboard route needs to be modified
        admin_dashboard_route = '''
@web.route('/dashboard/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard route."""
    return render_template('admin/dashboard.html')
'''
        
        # Find the current admin_dashboard function
        import re
        admin_dashboard_pattern = r'@web.route\([\'"]\/dashboard\/admin[\'"]\)[^}]*?def admin_dashboard\(\):.*?return.*?$'
        match = re.search(admin_dashboard_pattern, routes_content, re.DOTALL | re.MULTILINE)
        
        if match:
            # Replace the existing function with our new implementation
            new_routes_content = routes_content.replace(match.group(0), admin_dashboard_route.strip())
            
            with open(routes_file, 'w') as f:
                f.write(new_routes_content)
                
            logger.info("Updated admin_dashboard route to render the admin/dashboard.html template")
            return True
        else:
            # If not found, add it near the end of the file
            add_position = routes_content.rfind('if __name__ ==')
            if add_position == -1:
                add_position = len(routes_content)
                
            new_routes_content = routes_content[:add_position] + "\n" + admin_dashboard_route + "\n" + routes_content[add_position:]
            
            with open(routes_file, 'w') as f:
                f.write(new_routes_content)
                
            logger.info("Added admin_dashboard route to render the admin/dashboard.html template")
            return True
    
    except Exception as e:
        logger.error(f"Error fixing admin route: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_admin_route()
    if success:
        print("Admin routes updated successfully. Please restart the Flask application.")
    else:
        print("Failed to update admin routes. Check the logs for details.")