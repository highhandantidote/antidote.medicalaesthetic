#!/usr/bin/env python3
"""
Fix errors caused by empty database.

This script updates routes.py to add better error handling
for when the database is empty.
"""

import re
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_index_route():
    """Fix the index route to handle empty database properly."""
    try:
        # Backup the original file
        if os.path.exists('routes.py'):
            backup_name = f'routes.py.backup_{datetime.now().strftime("%Y%m%d%H%M%S")}'
            with open('routes.py', 'r') as f:
                with open(backup_name, 'w') as backup:
                    backup.write(f.read())
            logger.info(f"Created backup at {backup_name}")
        else:
            logger.error("Could not find routes.py")
            return False
            
        # Read the file
        with open('routes.py', 'r') as f:
            content = f.read()
        
        # Pattern 1: Fix the index route
        # Find: recent_threads = Thread.query.order_by(Thread.created_at.desc()).limit(3).all()
        # Replace with error handling to provide empty lists when no data
        pattern = r'popular_body_parts = BodyPart\.query\.limit\(4\)\.all\(\)'
        replacement = 'try:\n        popular_body_parts = BodyPart.query.limit(4).all()\n    except Exception as e:\n        logger.error(f"Error querying body parts: {str(e)}")\n        popular_body_parts = []'
        content = re.sub(pattern, replacement, content)
        
        pattern = r'popular_procedures = Procedure\.query\.order_by\(Procedure\.popularity_score\.desc\(\)\)\.limit\(6\)\.all\(\)'
        replacement = 'try:\n        popular_procedures = Procedure.query.order_by(Procedure.popularity_score.desc()).limit(6).all()\n    except Exception as e:\n        logger.error(f"Error querying procedures: {str(e)}")\n        popular_procedures = []'
        content = re.sub(pattern, replacement, content)
        
        pattern = r'procedure_categories = Category\.query\.limit\(6\)\.all\(\)'
        replacement = 'try:\n        procedure_categories = Category.query.limit(6).all()\n    except Exception as e:\n        logger.error(f"Error querying categories: {str(e)}")\n        procedure_categories = []'
        content = re.sub(pattern, replacement, content)
        
        pattern = r'recent_threads = Thread\.query\.order_by\(Thread\.created_at\.desc\(\)\)\.limit\(3\)\.all\(\)'
        replacement = 'try:\n        recent_threads = Thread.query.order_by(Thread.created_at.desc()).limit(3).all()\n    except Exception as e:\n        logger.error(f"Error querying threads: {str(e)}")\n        recent_threads = []'
        content = re.sub(pattern, replacement, content)
        
        pattern = r'top_doctors = Doctor\.query\.order_by\(Doctor\.id\)\.limit\(9\)\.all\(\)'
        replacement = 'try:\n        top_doctors = Doctor.query.order_by(Doctor.id).limit(9).all()\n    except Exception as e:\n        logger.error(f"Error querying doctors: {str(e)}")\n        top_doctors = []'
        content = re.sub(pattern, replacement, content)
        
        # Write the modified content back
        with open('routes.py', 'w') as f:
            f.write(content)
            
        logger.info("Successfully fixed index route to handle empty database")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing index route: {str(e)}")
        return False
        
def fix_doctor_detail_route():
    """Fix the doctor_detail route to handle empty database properly."""
    try:
        # Read the file (we already made a backup)
        with open('routes.py', 'r') as f:
            content = f.read()
        
        # Find the doctor_detail function definition with error handling
        # This is a more complete fix that adds proper empty default values
        pattern = r'def doctor_detail\(doctor_id\):.*?return render_template\(\s*\'doctor_detail.html\',\s*error=str\(e\),?'
        # Compile with DOTALL to match across newlines
        compiled_pattern = re.compile(pattern, re.DOTALL)
        
        # Look for a match
        match = compiled_pattern.search(content)
        if match:
            # Find the end of the except block
            end_index = content.find(')', content.find('error=str(e)', match.start()))
            if end_index != -1:
                # Insert default values for all expected variables
                improved_error_handling = 'error=str(e),\n            doctor=None,\n            doctor_procedures=[],\n            doctor_categories=[],\n            doctor_photos=[],\n            reviews=[],\n            rating_breakdown={}'
                content = content[:content.find('error=str(e)', match.start())] + improved_error_handling + content[end_index:]
                
                # Write the modified content back
                with open('routes.py', 'w') as f:
                    f.write(content)
                
                logger.info("Successfully fixed doctor_detail route to handle empty database")
                return True
            else:
                logger.error("Could not find end of except block in doctor_detail")
                return False
        else:
            logger.error("Could not find doctor_detail function in routes.py")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing doctor_detail route: {str(e)}")
        return False
    
if __name__ == "__main__":
    index_fixed = fix_index_route()
    doctor_fixed = fix_doctor_detail_route()
    
    if index_fixed and doctor_fixed:
        logger.info("Successfully fixed all routes to handle empty database")
    else:
        logger.warning("Fix was only partially successful")