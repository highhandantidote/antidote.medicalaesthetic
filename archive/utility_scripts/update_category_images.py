"""
Update category images from CSV file with Google Drive URLs.

This script reads a CSV file containing category names, body part names, and Google Drive image URLs,
then updates the corresponding categories in the database with the new image URLs.
"""

import csv
import os
import psycopg2
from urllib.parse import urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not found")
    
    return psycopg2.connect(database_url)

def validate_google_drive_url(url):
    """Validate and convert Google Drive URL to direct access format if needed."""
    if not url or not url.strip():
        return None
    
    # If it's already in the correct format, return as is
    if 'drive.google.com/uc?id=' in url:
        return url.strip()
    
    # If it's in the sharing format, extract the file ID and convert
    if 'drive.google.com/file/d/' in url:
        try:
            # Extract file ID from sharing URL
            file_id = url.split('/file/d/')[1].split('/')[0]
            return f"https://drive.google.com/uc?id={file_id}"
        except IndexError:
            logger.warning(f"Could not extract file ID from URL: {url}")
            return url.strip()
    
    # Return the URL as is if it's not a Google Drive URL
    return url.strip()

def update_category_images_from_csv(csv_file_path):
    """Update category images from CSV file."""
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return False
    
    conn = get_db_connection()
    updated_count = 0
    error_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            # Read CSV file
            csv_reader = csv.DictReader(file)
            
            # Check which format is being used
            fieldnames = csv_reader.fieldnames or []
            
            if 'body_part_name' in fieldnames:
                # Full format: category_name, body_part_name, image_url
                required_columns = ['category_name', 'body_part_name', 'image_url']
                use_simplified_format = False
            else:
                # Simplified format: category_name, image_url
                required_columns = ['category_name', 'image_url']
                use_simplified_format = True
            
            if not all(col in fieldnames for col in required_columns):
                logger.error(f"CSV file must contain columns: {', '.join(required_columns)}")
                logger.error(f"Found columns: {', '.join(fieldnames)}")
                return False
            
            logger.info(f"Using {'simplified' if use_simplified_format else 'full'} CSV format")
            
            with conn.cursor() as cursor:
                for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
                    category_name = row['category_name'].strip()
                    image_url = row['image_url'].strip()
                    
                    if not category_name:
                        logger.warning(f"Row {row_num}: Missing category_name")
                        error_count += 1
                        continue
                    
                    # Validate and format the Google Drive URL
                    formatted_url = validate_google_drive_url(image_url)
                    
                    if not formatted_url:
                        logger.warning(f"Row {row_num}: Empty or invalid image URL for {category_name}")
                        error_count += 1
                        continue
                    
                    try:
                        if use_simplified_format:
                            # Find the category by name only (automatically map to body part)
                            cursor.execute("""
                                SELECT c.id, c.name, bp.name as body_part_name
                                FROM categories c
                                JOIN body_parts bp ON c.body_part_id = bp.id
                                WHERE LOWER(c.name) = LOWER(%s)
                            """, (category_name,))
                        else:
                            # Find the category by name and body part
                            body_part_name = row['body_part_name'].strip()
                            if not body_part_name:
                                logger.warning(f"Row {row_num}: Missing body_part_name")
                                error_count += 1
                                continue
                            
                            cursor.execute("""
                                SELECT c.id, c.name, bp.name as body_part_name
                                FROM categories c
                                JOIN body_parts bp ON c.body_part_id = bp.id
                                WHERE LOWER(c.name) = LOWER(%s) AND LOWER(bp.name) = LOWER(%s)
                            """, (category_name, body_part_name))
                        
                        category = cursor.fetchone()
                        
                        if not category:
                            if use_simplified_format:
                                logger.warning(f"Row {row_num}: Category '{category_name}' not found")
                            else:
                                body_part_name = row['body_part_name'].strip()
                                logger.warning(f"Row {row_num}: Category '{category_name}' in body part '{body_part_name}' not found")
                            error_count += 1
                            continue
                        
                        category_id = category[0]
                        found_body_part = category[2]
                        
                        # Update the category with the new image URL
                        cursor.execute("""
                            UPDATE categories 
                            SET image_url = %s 
                            WHERE id = %s
                        """, (formatted_url, category_id))
                        
                        logger.info(f"Row {row_num}: Updated '{category_name}' ({found_body_part}) with image URL")
                        updated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Row {row_num}: Error updating {category_name}: {str(e)}")
                        error_count += 1
                        continue
                
                # Commit all changes
                conn.commit()
                
    except Exception as e:
        conn.rollback()
        logger.error(f"Error processing CSV file: {str(e)}")
        return False
    finally:
        conn.close()
    
    # Print summary
    logger.info(f"\n=== UPDATE SUMMARY ===")
    logger.info(f"Successfully updated: {updated_count} categories")
    logger.info(f"Errors encountered: {error_count}")
    logger.info(f"Total processed: {updated_count + error_count}")
    
    return updated_count > 0

def get_categories_without_images():
    """Get a list of categories that don't have images."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.name, bp.name as body_part_name, c.image_url
                FROM categories c
                JOIN body_parts bp ON c.body_part_id = bp.id
                WHERE c.image_url IS NULL OR c.image_url = ''
                ORDER BY bp.name, c.name
            """)
            
            categories = cursor.fetchall()
            
            if categories:
                logger.info(f"\nCategories without images ({len(categories)}):")
                for cat_name, bp_name, img_url in categories:
                    logger.info(f"  - {cat_name} ({bp_name})")
            else:
                logger.info("All categories have images!")
                
            return categories
            
    except Exception as e:
        logger.error(f"Error getting categories without images: {str(e)}")
        return []
    finally:
        conn.close()

def main():
    """Main function to update category images."""
    logger.info("Category Image Update Script")
    logger.info("=" * 40)
    
    # Check if CSV file is provided as argument
    import sys
    if len(sys.argv) < 2:
        logger.info("Usage: python update_category_images.py <csv_file_path>")
        logger.info("\nExample CSV format:")
        logger.info("category_name,body_part_name,image_url")
        logger.info("Rhinoplasty,Face,https://drive.google.com/uc?id=1ABC123XYZ")
        logger.info("Breast Augmentation,Breasts,https://drive.google.com/uc?id=1DEF456ABC")
        
        # Show categories without images
        get_categories_without_images()
        return
    
    csv_file_path = sys.argv[1]
    
    logger.info(f"Updating category images from: {csv_file_path}")
    
    # Update categories from CSV
    success = update_category_images_from_csv(csv_file_path)
    
    if success:
        logger.info("✅ Category images updated successfully!")
        
        # Show remaining categories without images
        logger.info("\nChecking for remaining categories without images...")
        get_categories_without_images()
    else:
        logger.error("❌ Failed to update category images")

if __name__ == "__main__":
    main()