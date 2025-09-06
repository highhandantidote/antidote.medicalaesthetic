import gdown
import os

# Extract the file ID from the Google Drive link
file_id = "1lSR1IU1LGojniYyxDw4zPr9x-b1-63fJ"

# Set the output path
output_path = "static/images/svg/antidote-logo.svg"

# Make sure the directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Download the file using the file ID
url = f"https://drive.google.com/uc?id={file_id}"
gdown.download(url, output_path, quiet=False)

print(f"Downloaded logo to {output_path}")