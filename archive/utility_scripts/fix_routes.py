#!/usr/bin/env python3
"""
Fix routes.py file with correct indentation.

This script fixes the indentation issues in the index function to prevent syntax errors.
"""

import re
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_routes():
    """Fix the index route indentation issues."""
    try:
        # Backup the original file
        backup_name = f'routes.py.backup_{datetime.now().strftime("%Y%m%d%H%M%S")}'
        with open('routes.py', 'r') as f:
            content = f.read()
            
        with open(backup_name, 'w') as backup:
            backup.write(content)
        logger.info(f"Created backup at {backup_name}")
        
        # Define the problematic function with proper indentation
        old_index_function = re.search(r'@web\.route\(\'/\'\)\ndef index\(\):(.*?)def modern_index', content, re.DOTALL)
        
        if not old_index_function:
            logger.error("Could not find index function in routes.py")
            return False
            
        old_function = old_index_function.group(0)
        
        # Create a properly indented version
        new_function = """@web.route('/')
def index():
    \"\"\"Render the home page.\"\"\""""
    try:
        try:
            popular_body_parts = BodyPart.query.limit(4).all()
        except Exception as e:
            logger.error(f"Error querying body parts: {str(e)}")
            popular_body_parts = []
        
        try:
            popular_procedures = Procedure.query.order_by(Procedure.popularity_score.desc()).limit(6).all()
        except Exception as e:
            logger.error(f"Error querying procedures: {str(e)}")
            popular_procedures = []
        
        # Get procedure categories
        try:
            procedure_categories = Category.query.limit(6).all()
        except Exception as e:
            logger.error(f"Error querying categories: {str(e)}")
            procedure_categories = []
        
        # Get recent community threads
        try:
            recent_threads = Thread.query.order_by(Thread.created_at.desc()).limit(3).all()
        except Exception as e:
            logger.error(f"Error querying threads: {str(e)}")
            recent_threads = []
        
        # Filter out doctors with None ratings to avoid __round__ error
        try:
            top_doctors = Doctor.query.order_by(Doctor.id).limit(9).all()
        except Exception as e:
            logger.error(f"Error querying doctors: {str(e)}")
            top_doctors = []
            
        # Process doctor data
        if all([d.rating is not None for d in top_doctors]):
            # Regular sorting if all doctors have ratings
            top_doctors.sort(key=lambda x: x.rating, reverse=True)
        else:
            # If some doctors have None ratings, only sort those with ratings
            rated_doctors = [d for d in top_doctors if d.rating is not None]
            unrated_doctors = [d for d in top_doctors if d.rating is None]
            rated_doctors.sort(key=lambda x: x.rating, reverse=True)
            top_doctors = rated_doctors + unrated_doctors
        
        # Check if modern index is enabled via query param
        if request.args.get('modern'):
            return modern_index()
            
        return render_template('index.html',
            top_doctors=top_doctors, 
            popular_procedures=popular_procedures,
            recent_threads=recent_threads,
            popular_body_parts=popular_body_parts,
            procedure_categories=procedure_categories
        )
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html',
            top_doctors=[], 
            popular_procedures=[],
            recent_threads=[],
            popular_body_parts=[],
            procedure_categories=[]
        )

@web.route('/modern')
def modern_index()"""
        
        # Replace the old function with the new one
        new_content = content.replace(old_function, new_function)
        
        # Write the fixed content back to the file
        with open('routes.py', 'w') as f:
            f.write(new_content)
            
        logger.info("Successfully fixed routes.py")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing routes.py: {str(e)}")
        return False

if __name__ == "__main__":
    fix_routes()