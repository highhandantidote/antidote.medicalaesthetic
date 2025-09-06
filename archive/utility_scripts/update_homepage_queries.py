#!/usr/bin/env python3
"""
Update the homepage queries to show all doctors and fix any display issues.
This script checks the current database content and ensures the homepage 
shows the correct number of doctors, procedures, and categories.
"""
import os
import sys
import logging
import json
import psycopg2

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def check_database_counts():
    """Check the counts of key tables in the database."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return
    
    try:
        with conn.cursor() as cursor:
            # Check doctors count
            cursor.execute("SELECT COUNT(*) FROM doctors")
            doctor_count = cursor.fetchone()[0]
            logger.info(f"Total doctors in database: {doctor_count}")
            
            # Check procedures count
            cursor.execute("SELECT COUNT(*) FROM procedures")
            procedure_count = cursor.fetchone()[0]
            logger.info(f"Total procedures in database: {procedure_count}")
            
            # Check categories count
            cursor.execute("SELECT COUNT(*) FROM categories")
            category_count = cursor.fetchone()[0]
            logger.info(f"Total categories in database: {category_count}")
            
            # Check body parts count
            cursor.execute("SELECT COUNT(*) FROM body_parts")
            body_part_count = cursor.fetchone()[0]
            logger.info(f"Total body parts in database: {body_part_count}")
            
            # Check doctor-procedure links
            cursor.execute("SELECT COUNT(*) FROM doctor_procedures")
            dp_count = cursor.fetchone()[0]
            logger.info(f"Total doctor-procedure links: {dp_count}")
            
            # Check doctor-category links
            cursor.execute("SELECT COUNT(*) FROM doctor_categories")
            dc_count = cursor.fetchone()[0]
            logger.info(f"Total doctor-category links: {dc_count}")
            
            # Get doctor distribution by city
            cursor.execute("""
                SELECT city, COUNT(*) as doc_count 
                FROM doctors 
                GROUP BY city 
                ORDER BY doc_count DESC
            """)
            city_distribution = cursor.fetchall()
            logger.info("Doctor distribution by city:")
            for city, count in city_distribution:
                logger.info(f"  - {city}: {count} doctors")
    except Exception as e:
        logger.error(f"Error checking database counts: {e}")
    finally:
        conn.close()

def find_routes_file():
    """Find the main routes file path."""
    possible_paths = [
        "./routes.py",
        "./routes/__init__.py",
        "./routes/web.py",
        "./web/routes.py"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found routes file at: {path}")
            return path
    
    # Search for routes files
    logger.info("Searching for routes file...")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py') and 'route' in file.lower():
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                    if '@app.route(\'/\')' in content or 'def index()' in content:
                        logger.info(f"Found index route in: {path}")
                        return path
    
    logger.error("Could not find routes file")
    return None

def check_index_route_content(file_path):
    """Check the content of the index route."""
    if not file_path or not os.path.exists(file_path):
        logger.error("Invalid routes file path")
        return
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        if '@app.route(\'/\')' in content or 'def index()' in content:
            logger.info("Found index route definition")
            
            # Check for doctor limit in query
            if 'doctors = Doctor.query.limit(' in content:
                logger.info("Found doctor limit in index route")
            elif 'doctors = db.session.query(Doctor).limit(' in content:
                logger.info("Found doctor session query limit in index route")
            
            # Check if we're using SQLAlchemy
            using_sqlalchemy = 'from sqlalchemy' in content or 'import sqlalchemy' in content
            logger.info(f"Using SQLAlchemy: {using_sqlalchemy}")
            
            return content
    except Exception as e:
        logger.error(f"Error checking index route content: {e}")
    
    return None

def update_index_route(file_path, content):
    """Update the index route to show all doctors."""
    if not file_path or not content:
        logger.error("Invalid file path or content")
        return False
    
    try:
        # Backup the original file
        backup_path = file_path + '.bak'
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Created backup of routes file at: {backup_path}")
        
        # Look for patterns to update
        new_content = content
        
        # Update doctor limit
        if 'doctors = Doctor.query.limit(' in new_content:
            new_content = new_content.replace('doctors = Doctor.query.limit(', 'doctors = Doctor.query.limit(18 #')
        elif 'doctors = db.session.query(Doctor).limit(' in new_content:
            new_content = new_content.replace('doctors = db.session.query(Doctor).limit(', 'doctors = db.session.query(Doctor).limit(18 #')
        
        # Only write if changes were made
        if new_content != content:
            with open(file_path, 'w') as f:
                f.write(new_content)
            logger.info(f"Updated routes file at: {file_path}")
            return True
        else:
            logger.info("No changes needed to routes file")
            return False
    except Exception as e:
        logger.error(f"Error updating index route: {e}")
        return False

def main():
    """Run the homepage query update process."""
    logger.info("Starting homepage query update process...")
    
    # Check current database counts
    check_database_counts()
    
    # Find and update the routes file
    routes_file = find_routes_file()
    if routes_file:
        content = check_index_route_content(routes_file)
        if content:
            updated = update_index_route(routes_file, content)
            if updated:
                logger.info("Successfully updated homepage queries")
            else:
                logger.info("No updates were needed for homepage queries")
    
    logger.info("Homepage query update process completed.")

if __name__ == "__main__":
    main()