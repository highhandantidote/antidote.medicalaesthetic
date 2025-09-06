"""
Bulk clinic upload script that directly creates clinics and assigns them to users.

This script reads clinic data from a CSV file and creates:
1. User accounts for clinic owners
2. Clinic records linked to those users
3. Proper slug generation and data validation

CSV Format Required:
clinic_name,contact_person,email,phone,address,city,state,pincode,website,specialties,description,password

Usage: python bulk_clinic_upload.py clinics.csv
"""

import csv
import sys
import os
from datetime import datetime
import re
import logging
from werkzeug.security import generate_password_hash
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using DATABASE_URL."""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def generate_slug(name):
    """Generate a URL-friendly slug from clinic name."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug[:100]  # Limit length

def user_exists(conn, email):
    """Check if user with email already exists."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        return None

def clinic_exists(conn, email):
    """Check if clinic with email already exists."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clinics WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error checking clinic existence: {e}")
        return None

def create_user_account(conn, name, email, phone_number, password=None):
    """Create a user account for clinic owner."""
    try:
        cursor = conn.cursor()
        
        # Use provided password or generate default
        if not password:
            password = "clinic123"  # Default password - should be changed
        
        password_hash = generate_password_hash(password)
        
        # Insert user with provided phone number
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, phone_number, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (name, email, password_hash, 'clinic', phone_number, datetime.utcnow()))
        
        user_id = cursor.fetchone()[0]
        cursor.close()
        
        logger.info(f"Created user account for {name} (ID: {user_id})")
        return user_id
        
    except Exception as e:
        logger.error(f"Error creating user account for {email}: {e}")
        return None

def create_clinic_record(conn, user_id, clinic_data):
    """Create clinic record linked to user."""
    try:
        cursor = conn.cursor()
        
        # Generate unique slug
        base_slug = generate_slug(clinic_data['clinic_name'])
        slug = base_slug
        counter = 1
        
        # Ensure slug uniqueness
        while True:
            cursor.execute("SELECT id FROM clinics WHERE slug = %s", (slug,))
            if not cursor.fetchone():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Parse specialties
        specialties = [s.strip() for s in clinic_data.get('specialties', '').split(',') if s.strip()]
        
        # Insert clinic
        cursor.execute("""
            INSERT INTO clinics (
                owner_user_id, name, slug, address, city, state, pincode,
                contact_number, email, website, description, specialties,
                is_approved, verification_status, verification_date,
                credit_balance, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            user_id,
            clinic_data['clinic_name'],
            slug,
            clinic_data['address'],
            clinic_data['city'],
            clinic_data['state'],
            clinic_data.get('pincode', ''),
            clinic_data['phone'],
            clinic_data['email'],
            clinic_data.get('website', ''),
            clinic_data.get('description', ''),
            specialties,
            True,  # Auto-approve bulk uploaded clinics
            'approved',
            datetime.utcnow(),
            100,  # Starting credit balance
            datetime.utcnow()
        ))
        
        clinic_id = cursor.fetchone()[0]
        cursor.close()
        
        logger.info(f"Created clinic: {clinic_data['clinic_name']} (ID: {clinic_id})")
        return clinic_id
        
    except Exception as e:
        logger.error(f"Error creating clinic for {clinic_data.get('clinic_name', 'Unknown')}: {e}")
        return None

def process_csv_file(csv_file_path):
    """Process CSV file and create clinics with user accounts."""
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return
    
    try:
        conn = get_db_connection()
        success_count = 0
        error_count = 0
        errors = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            # Validate required columns
            required_columns = ['clinic_name', 'contact_person', 'email', 'phone', 'address', 'city', 'state']
            missing_columns = [col for col in required_columns if col not in csv_reader.fieldnames]
            
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # Validate required fields
                    missing_fields = [field for field in required_columns if not row.get(field, '').strip()]
                    if missing_fields:
                        error_msg = f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}"
                        errors.append(error_msg)
                        error_count += 1
                        continue
                    
                    email = row['email'].strip().lower()
                    
                    # Check if user already exists
                    existing_user_id = user_exists(conn, email)
                    if existing_user_id:
                        logger.warning(f"Row {row_num}: User with email {email} already exists")
                        
                        # Check if clinic also exists
                        if clinic_exists(conn, email):
                            error_msg = f"Row {row_num}: Clinic with email {email} already exists"
                            errors.append(error_msg)
                            error_count += 1
                            continue
                        else:
                            # Use existing user account
                            user_id = existing_user_id
                    else:
                        # Create new user account
                        user_id = create_user_account(
                            conn,
                            row['contact_person'].strip(),
                            email,
                            row['phone'].strip(),
                            row.get('password', '').strip()
                        )
                        
                        if not user_id:
                            error_msg = f"Row {row_num}: Failed to create user account"
                            errors.append(error_msg)
                            error_count += 1
                            continue
                    
                    # Create clinic record
                    clinic_id = create_clinic_record(conn, user_id, row)
                    
                    if clinic_id:
                        success_count += 1
                        logger.info(f"✅ Successfully processed row {row_num}: {row['clinic_name']}")
                    else:
                        error_msg = f"Row {row_num}: Failed to create clinic record"
                        errors.append(error_msg)
                        error_count += 1
                
                except Exception as e:
                    error_msg = f"Row {row_num}: Unexpected error - {str(e)}"
                    errors.append(error_msg)
                    error_count += 1
                    logger.error(error_msg)
                    continue
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("BULK CLINIC UPLOAD SUMMARY")
        logger.info("="*50)
        logger.info(f"✅ Successfully created: {success_count} clinics")
        logger.info(f"❌ Errors encountered: {error_count}")
        
        if errors:
            logger.info("\nERROR DETAILS:")
            for error in errors[:10]:  # Show first 10 errors
                logger.info(f"  • {error}")
            if len(errors) > 10:
                logger.info(f"  ... and {len(errors) - 10} more errors")
        
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def create_sample_csv():
    """Create a sample CSV file with proper format."""
    sample_data = [
        {
            'clinic_name': 'Elite Cosmetic Center',
            'contact_person': 'Dr. Priya Sharma',
            'email': 'info@elitecosmetic.com',
            'phone': '+919876543210',
            'address': '123 MG Road, Bangalore',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'pincode': '560001',
            'website': 'https://elitecosmetic.com',
            'specialties': 'Rhinoplasty, Breast Augmentation, Liposuction',
            'description': 'Premier cosmetic surgery clinic with 15+ years experience',
            'password': 'secure123'
        },
        {
            'clinic_name': 'Mumbai Aesthetic Clinic',
            'contact_person': 'Dr. Rajesh Khanna',
            'email': 'contact@mumbaiaesthetic.com',
            'phone': '+919876543211',
            'address': '456 Linking Road, Bandra West',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400050',
            'website': 'https://mumbaiaesthetic.com',
            'specialties': 'Botox, Fillers, Laser Treatment',
            'description': 'Modern aesthetic treatments in the heart of Mumbai',
            'password': 'clinic456'
        }
    ]
    
    with open('sample_clinics.csv', 'w', newline='', encoding='utf-8') as file:
        fieldnames = list(sample_data[0].keys())
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)
    
    logger.info("Created sample_clinics.csv with example data")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        logger.info("Usage: python bulk_clinic_upload.py <csv_file_path>")
        logger.info("Or: python bulk_clinic_upload.py --create-sample")
        return
    
    if sys.argv[1] == '--create-sample':
        create_sample_csv()
        return
    
    csv_file_path = sys.argv[1]
    process_csv_file(csv_file_path)

if __name__ == "__main__":
    main()