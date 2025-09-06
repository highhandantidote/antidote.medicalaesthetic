#!/usr/bin/env python3
"""
Update .env file with properly encoded Supabase connection string.

This script:
1. Takes Supabase connection details from user input
2. Properly URL-encodes the password to handle special characters
3. Updates the .env file with the new DATABASE_URL
"""
import os
import sys
import urllib.parse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_current_db_url():
    """Get the current DATABASE_URL from .env file."""
    try:
        env_path = Path('.env')
        if not env_path.exists():
            logger.error(".env file not found")
            return None
            
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            if line.startswith('DATABASE_URL='):
                return line.strip().split('=', 1)[1].strip("'").strip('"')
                
        logger.warning("DATABASE_URL not found in .env file")
        return None
    except Exception as e:
        logger.error(f"Error reading .env file: {str(e)}")
        return None

def create_supabase_connection_string(host, password, port=5432, database="postgres", user="postgres"):
    """Create a Supabase connection string with properly encoded password."""
    try:
        # URL-encode the password to handle special characters
        encoded_password = urllib.parse.quote_plus(password)
        
        # Build connection string
        conn_str = f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"
        
        return conn_str
    except Exception as e:
        logger.error(f"Error creating connection string: {str(e)}")
        return None

def update_env_file(new_db_url):
    """Update the .env file with the new DATABASE_URL."""
    try:
        env_path = Path('.env')
        if not env_path.exists():
            logger.error(".env file not found")
            return False
            
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Create backup of original .env file
        backup_path = Path('.env.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        logger.info(f"Created backup of .env file at {backup_path}")
            
        # Update DATABASE_URL line
        found = False
        for i, line in enumerate(lines):
            if line.startswith('DATABASE_URL='):
                lines[i] = f'DATABASE_URL={new_db_url}\n'
                found = True
                break
                
        # If DATABASE_URL not found, add it
        if not found:
            lines.append(f'\nDATABASE_URL={new_db_url}\n')
            
        # Write updated .env file
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        logger.info("Updated .env file with new DATABASE_URL")
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        return False

def main():
    """Main function to run the .env update script."""
    logger.info("=== Updating .env file for Supabase connection ===")
    
    # Get current DATABASE_URL
    current_db_url = get_current_db_url()
    if current_db_url:
        logger.info(f"Current DATABASE_URL: {current_db_url[:20]}...")
    
    # Get Supabase connection details
    print("\nPlease enter your Supabase connection details:")
    host = input("Host (e.g., db.asgwdfirkanaaswobuj.supabase.co): ")
    password = input("Password: ")
    
    # Optional parameters with defaults
    port = input("Port (default: 5432): ") or "5432"
    database = input("Database (default: postgres): ") or "postgres"
    user = input("User (default: postgres): ") or "postgres"
    
    # Create connection string
    conn_str = create_supabase_connection_string(
        host=host,
        password=password,
        port=int(port),
        database=database,
        user=user
    )
    
    if not conn_str:
        logger.error("Failed to create connection string")
        return 1
        
    logger.info(f"New connection string: {conn_str[:20]}...")
    
    # Confirm update
    confirm = input("\nUpdate .env file with new connection string? (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Operation cancelled")
        return 0
    
    # Update .env file
    success = update_env_file(conn_str)
    
    if success:
        logger.info("=== .env file updated successfully ===")
        logger.info("Your application is now configured to use Supabase")
        logger.info("Restart your application for changes to take effect")
        return 0
    else:
        logger.error("=== Failed to update .env file ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())