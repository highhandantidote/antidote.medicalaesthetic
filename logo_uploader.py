"""
Logo Uploader Script for Antidote Platform

This script helps you replace the website logo with a new SVG file.
Run this script directly to upload a new logo file.
"""

import os
import shutil
import sys
from datetime import datetime

def upload_logo(logo_path):
    """
    Upload a new logo file to the static/images directory.
    
    Args:
        logo_path: Path to the new logo file
    """
    if not os.path.exists(logo_path):
        print(f"Error: File not found at {logo_path}")
        return False
    
    # Check if the file is an SVG
    file_ext = os.path.splitext(logo_path)[1].lower()
    valid_exts = ['.svg', '.png', '.jpg', '.jpeg']
    
    if file_ext not in valid_exts:
        print(f"Error: File must be one of these formats: {', '.join(valid_exts)}")
        return False
    
    # Destination folder
    dest_folder = os.path.join('static', 'images')
    
    # Ensure the destination folder exists
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    # Backup the current logo if it exists
    current_logo = os.path.join(dest_folder, 'antidote-logo-new.png')
    if os.path.exists(current_logo):
        backup_name = f'antidote-logo-backup-{datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        backup_path = os.path.join(dest_folder, backup_name)
        shutil.copy2(current_logo, backup_path)
        print(f"Backed up current logo to {backup_path}")
    
    # New logo filename
    new_logo_name = 'antidote-logo-new' + file_ext
    new_logo_path = os.path.join(dest_folder, new_logo_name)
    
    # Copy the new logo
    shutil.copy2(logo_path, new_logo_path)
    print(f"Successfully uploaded new logo to {new_logo_path}")
    
    # Update the template reference if needed
    if file_ext != '.png':
        print("\nIMPORTANT: Since your logo isn't a PNG, you need to update the template reference.")
        print("Open templates/base.html and find this line:")
        print('    <img src="{{ url_for(\'static\', filename=\'images/antidote-logo-new.png\') }}" alt="Antidote" height="60" class="me-2">')
        print("\nChange it to:")
        print(f'    <img src="{{ url_for(\'static\', filename=\'images/{new_logo_name}\') }}" alt="Antidote" height="60" class="me-2">')
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python logo_uploader.py path/to/your/logo.svg")
    else:
        upload_logo(sys.argv[1])