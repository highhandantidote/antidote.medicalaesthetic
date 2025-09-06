"""
Download and update the Antidote logo from Google Drive.
This script properly extracts the file ID and downloads the logo.
"""

import gdown
import os
import shutil
from datetime import datetime

def download_and_update_logo():
    """Download logo from Google Drive and update the website."""
    
    # Extract file ID from the Google Drive URL
    # URL: https://drive.google.com/file/d/1pFlfdxKERkNHN4_BuiULNxwhspm8JJDp/view?usp=sharing
    file_id = "1pFlfdxKERkNHN4_BuiULNxwhspm8JJDp"
    
    # Set up paths
    temp_download_path = "temp_logo_download"
    static_images_dir = "static/images"
    
    # Make sure directories exist
    os.makedirs(static_images_dir, exist_ok=True)
    
    print("Downloading logo from Google Drive...")
    
    try:
        # Download the file using gdown
        download_url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(download_url, temp_download_path, quiet=False)
        
        print(f"Successfully downloaded logo to {temp_download_path}")
        
        # Check what type of file we got
        if os.path.exists(temp_download_path):
            # Get file size to verify download
            file_size = os.path.getsize(temp_download_path)
            print(f"Downloaded file size: {file_size} bytes")
            
            # Backup current logo if it exists
            current_logo = os.path.join(static_images_dir, "antidote-logo-new.png")
            if os.path.exists(current_logo):
                backup_name = f"antidote-logo-backup-{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                backup_path = os.path.join(static_images_dir, backup_name)
                shutil.copy2(current_logo, backup_path)
                print(f"Backed up current logo to {backup_path}")
            
            # Try to determine file type and copy to appropriate location
            # Since Google Drive doesn't preserve extension, we'll assume it's a PNG
            new_logo_path = os.path.join(static_images_dir, "antidote-logo-new.png")
            shutil.copy2(temp_download_path, new_logo_path)
            print(f"Updated logo at {new_logo_path}")
            
            # Clean up temp file
            os.remove(temp_download_path)
            print("Cleaned up temporary download file")
            
            return True
            
        else:
            print("Error: Download failed - file not found")
            return False
            
    except Exception as e:
        print(f"Error downloading logo: {str(e)}")
        print("This might be due to permissions or the file not being publicly accessible.")
        return False

if __name__ == "__main__":
    success = download_and_update_logo()
    if success:
        print("\n✅ Logo update completed successfully!")
        print("The new logo should now appear on your website.")
    else:
        print("\n❌ Logo update failed.")
        print("Please check that the Google Drive file is publicly accessible.")