"""
Script to update all existing packages that are missing procedure breakdown data.
This will use the intelligent procedure generator to create realistic breakdowns.
"""
import logging
from app import create_app, db
from sqlalchemy import text
from intelligent_procedure_generator import procedure_generator
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app instance
app = create_app()

def update_missing_procedure_breakdowns():
    """Update all packages that are missing procedure breakdown data."""
    with app.app_context():
        try:
            # Get all packages that are missing procedure breakdown
            missing_breakdown_sql = """
                SELECT id, title, category, actual_treatment_name, price_actual
                FROM packages 
                WHERE is_active = true 
                AND (procedure_breakdown IS NULL OR procedure_breakdown::text = '[]' OR procedure_breakdown::text = 'null')
                ORDER BY category, title
            """
            
            packages = db.session.execute(text(missing_breakdown_sql)).fetchall()
            logger.info(f"Found {len(packages)} packages missing procedure breakdown data")
            
            successful_updates = 0
            failed_updates = 0
            
            for package in packages:
                try:
                    package_id = package[0]
                    title = package[1]
                    category = package[2] or 'Aesthetic Medicine'
                    actual_treatment_name = package[3] or ''
                    price_actual = float(package[4]) if package[4] else 10000.0
                    
                    logger.info(f"Processing package {package_id}: {title}")
                    
                    # Generate procedure breakdown
                    procedure_breakdown = procedure_generator.generate_procedure_breakdown(
                        title=title,
                        category=category,
                        actual_treatment_name=actual_treatment_name,
                        package_price=price_actual
                    )
                    
                    # Update the package
                    update_sql = """
                        UPDATE packages 
                        SET procedure_breakdown = :procedure_breakdown
                        WHERE id = :package_id
                    """
                    
                    db.session.execute(text(update_sql), {
                        'procedure_breakdown': json.dumps(procedure_breakdown),
                        'package_id': package_id
                    })
                    
                    successful_updates += 1
                    logger.info(f"✅ Updated package {package_id}: {title}")
                    
                except Exception as e:
                    failed_updates += 1
                    logger.error(f"❌ Failed to update package {package_id}: {title} - Error: {e}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"""
            📊 Procedure Breakdown Update Summary:
            ✅ Successfully updated: {successful_updates} packages
            ❌ Failed updates: {failed_updates} packages
            🎯 Total processed: {len(packages)} packages
            """)
            
            # Verify the updates
            verify_sql = """
                SELECT COUNT(*) as remaining_missing
                FROM packages 
                WHERE is_active = true 
                AND (procedure_breakdown IS NULL OR procedure_breakdown::text = '[]' OR procedure_breakdown::text = 'null')
            """
            remaining = db.session.execute(text(verify_sql)).fetchone()
            logger.info(f"📈 Packages still missing procedure breakdown: {remaining[0]}")
            
            return successful_updates, failed_updates
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Critical error during batch update: {e}")
            raise e

def show_sample_updates():
    """Show a sample of the generated procedure breakdowns for review."""
    with app.app_context():
        try:
            # Get 5 sample packages that now have procedure breakdown
            sample_sql = """
                SELECT id, title, category, actual_treatment_name, procedure_breakdown
                FROM packages 
                WHERE is_active = true 
                AND procedure_breakdown IS NOT NULL 
                AND procedure_breakdown::text != '[]'
                ORDER BY id DESC
                LIMIT 5
            """
            
            samples = db.session.execute(text(sample_sql)).fetchall()
            
            logger.info("🔍 Sample procedure breakdowns generated:")
            for sample in samples:
                package_id = sample[0]
                title = sample[1]
                category = sample[2]
                breakdown = json.loads(sample[4])
                
                logger.info(f"\n📦 Package {package_id}: {title} ({category})")
                for i, component in enumerate(breakdown, 1):
                    logger.info(f"   {i}. {component.get('name', 'Unknown')}")
                    logger.info(f"      Price: ₹{component.get('price_actual', 0):,} → ₹{component.get('price_discounted', 0):,}")
                    logger.info(f"      Details: {component.get('details', 'N/A')}")
                
        except Exception as e:
            logger.error(f"Error showing samples: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting procedure breakdown update for missing packages...")
    
    try:
        successful, failed = update_missing_procedure_breakdowns()
        
        if successful > 0:
            logger.info("📝 Showing sample generated procedure breakdowns...")
            show_sample_updates()
        
        logger.info("✅ Procedure breakdown update completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Script failed: {e}")
        exit(1)