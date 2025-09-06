#!/usr/bin/env python3
"""
Restore clinic contact numbers from CSV files to fix data corruption.
"""
import csv
import logging
from sqlalchemy import text
from models import db
from app import create_app
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def restore_contacts_from_csv(csv_file_path, city_name):
    """Restore contact numbers for a specific city from CSV file"""
    if not os.path.exists(csv_file_path):
        logger.warning(f"CSV file not found: {csv_file_path}")
        return 0
    
    updated_count = 0
    logger.info(f"Processing {csv_file_path} for {city_name}")
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                name = row.get('name', '').strip()
                contact_number = row.get('contact_number', '').strip()
                
                if not name:
                    continue
                
                # Update clinic if contact number is provided in CSV
                if contact_number:
                    try:
                        result = db.session.execute(text("""
                            UPDATE clinics 
                            SET contact_number = :contact_number
                            WHERE name = :name 
                            AND (contact_number IS NULL OR contact_number = '')
                        """), {
                            'contact_number': contact_number,
                            'name': name
                        })
                        
                        if result.rowcount > 0:
                            updated_count += 1
                            logger.info(f"✅ Restored contact for: {name[:50]}... -> {contact_number}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error updating {name}: {e}")
                        continue
            
            db.session.commit()
            logger.info(f"✅ {city_name}: Updated {updated_count} clinics with contact numbers")
            
    except Exception as e:
        logger.error(f"❌ Error processing {csv_file_path}: {e}")
        db.session.rollback()
        return 0
    
    return updated_count

def main():
    """Main function to restore all clinic contacts"""
    app = create_app()
    with app.app_context():
        logger.info("🔧 Starting clinic contact restoration process...")
        
        # CSV files to process
        csv_files = [
        ('hyderabad_clinics.csv', 'Hyderabad'),
        ('mumbai_clinics.csv', 'Mumbai'),
        ('bengaluru_clinics.csv', 'Bengaluru'),
        ('chennai_clinics.csv', 'Chennai'),
        ('delhi_clinics.csv', 'Delhi'),
        ('gurugram_clinics.csv', 'Gurugram'),
        ('kolkata_clinics.csv', 'Kolkata'),
        ('jaipur_clinics.csv', 'Jaipur'),
            ('ahmedabad_clinics.csv', 'Ahmedabad')
        ]
        
        total_restored = 0
        
        for csv_file, city in csv_files:
            count = restore_contacts_from_csv(csv_file, city)
            total_restored += count
        
        logger.info(f"🎉 RESTORATION COMPLETE: {total_restored} clinics restored with contact numbers")
        
        # Show current status
        result = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_clinics,
                COUNT(CASE WHEN contact_number IS NOT NULL AND contact_number != '' THEN 1 END) as with_contact,
                COUNT(CASE WHEN contact_number IS NULL OR contact_number = '' THEN 1 END) as missing_contact
            FROM clinics
        """)).fetchone()
        
        logger.info(f"📊 CURRENT STATUS:")
        logger.info(f"   Total clinics: {result.total_clinics}")
        logger.info(f"   With contact numbers: {result.with_contact}")
        logger.info(f"   Still missing: {result.missing_contact}")

if __name__ == '__main__':
    main()