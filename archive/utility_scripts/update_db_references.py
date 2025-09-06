"""
Update database connection references in application files.

This script scans for files that might contain database connection references
and updates them to use the new Supabase database URL.
"""
import os
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Patterns that might need to be updated
PATTERNS = [
    # Pattern for direct connection string creation
    (
        r"conn\s*=\s*psycopg2\.connect\(\s*os\.environ\.get\(['\"]SOURCE_DATABASE_URL['\"]",
        r"conn = psycopg2.connect(os.environ.get('DATABASE_URL'"
    ),
    # Pattern for database URL in dotenv files
    (
        r"^SOURCE_DATABASE_URL=.*$",
        "# Previous database URL has been migrated to Supabase"
    ),
]

# List of files or directories to exclude
EXCLUDE = [
    'migrate_to_supabase.py',
    'venv',
    'node_modules',
    '.git',
]

def should_process_file(path):
    """Check if the file should be processed."""
    # Skip excluded paths
    for excluded in EXCLUDE:
        if excluded in str(path):
            return False
    
    # Only process certain file types
    valid_extensions = ['.py', '.env', '.env.example', '.json', '.yaml', '.yml', '.toml']
    return path.suffix in valid_extensions or str(path).endswith('.env')

def update_file_content(content, filename):
    """Update database connection references in the file content."""
    original = content
    
    for pattern, replacement in PATTERNS:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content, content != original

def process_file(file_path):
    """Process a single file to update database references."""
    try:
        if not file_path.is_file():
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated_content, changed = update_file_content(content, file_path.name)
        
        if changed:
            logger.info(f"Updating database references in {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return False

def update_config(file_path='config.py'):
    """Update the config.py file specifically to use Supabase database."""
    try:
        if not Path(file_path).exists():
            logger.warning(f"Config file {file_path} not found")
            return False
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if we need to update
        if "# Database URL is set directly from DATABASE_URL environment variable" in content:
            logger.info(f"Config file {file_path} already updated")
            return False
            
        # Define patterns to look for and replace
        patterns = [
            # Replace PostgreSQL setup with direct DATABASE_URL usage
            (
                r"    # PostgreSQL database configuration\s+POSTGRES_HOST = os\.environ\.get\('PGHOST', 'localhost'\)\s+POSTGRES_PORT = os\.environ\.get\('PGPORT', '5432'\)\s+POSTGRES_USER = os\.environ\.get\('PGUSER', 'postgres'\)\s+POSTGRES_PASSWORD = os\.environ\.get\('PGPASSWORD', 'postgres'\)\s+POSTGRES_DB = os\.environ\.get\('PGDATABASE', 'antidote'\)",
                "    # Database URL is set directly from DATABASE_URL environment variable"
            ),
            # Update the SQLALCHEMY_DATABASE_URI line
            (
                r"    SQLALCHEMY_DATABASE_URI = os\.environ\.get\('DATABASE_URL', f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'\)",
                "    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')"
            ),
        ]
        
        # Apply the replacements
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
        # Write the updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Updated config file {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error updating config file {file_path}: {str(e)}")
        return False

def scan_directory(root_dir='.'):
    """Scan directory recursively for files containing database references."""
    logger.info(f"Scanning directory {root_dir} for files with database references")
    
    updated_files = []
    
    # First update the config file specifically
    if update_config():
        updated_files.append('config.py')
    
    # Then scan all files for other references
    for path in Path(root_dir).rglob('*'):
        if path.is_file() and should_process_file(path):
            if process_file(path):
                updated_files.append(str(path))
    
    logger.info(f"Updated {len(updated_files)} files")
    for file in updated_files:
        logger.info(f" - {file}")
    
    return updated_files

def main():
    """Run the database reference update process."""
    logger.info("=== Updating database references to use Supabase ===")
    scan_directory()
    logger.info("=== Finished updating database references ===")

if __name__ == "__main__":
    main()