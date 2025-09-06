#!/usr/bin/env python3
"""
Force regenerate procedure breakdowns for packages using generic templates.
"""
import json
import logging
from main import app
from models import Package, db
from intelligent_procedure_generator import procedure_generator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_regenerate_generic_breakdowns():
    """Force regenerate procedure breakdowns for packages using generic 'Professional Treatment Session' templates."""
    with app.app_context():
        logger.info("🚀 Starting force regeneration of generic procedure breakdowns...")
        
        # Get all packages with generic breakdowns
        all_packages = Package.query.filter(Package.procedure_breakdown.isnot(None)).all()
        
        generic_packages = []
        for package in all_packages:
            if package.procedure_breakdown:
                breakdown_text = json.dumps(package.procedure_breakdown) if isinstance(package.procedure_breakdown, list) else str(package.procedure_breakdown)
                if 'Professional Treatment Session' in breakdown_text or 'Customized aesthetic treatment' in breakdown_text:
                    generic_packages.append(package)
        
        logger.info(f"Found {len(generic_packages)} packages with generic breakdowns")
        
        success_count = 0
        error_count = 0
        
        for package in generic_packages:
            try:
                logger.info(f"🔄 Regenerating breakdown for: {package.title} (ID: {package.id})")
                
                # Generate new breakdown
                new_breakdown = procedure_generator.generate_procedure_breakdown(
                    title=package.title,
                    category=package.category or "aesthetic medicine",
                    actual_treatment_name=package.actual_treatment_name or "",
                    package_price=float(package.price_discounted) if package.price_discounted else None
                )
                
                # Update package
                package.procedure_breakdown = new_breakdown
                db.session.add(package)
                
                logger.info(f"✅ Updated breakdown for {package.title}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to update {package.title}: {e}")
                error_count += 1
        
        # Commit all changes
        try:
            db.session.commit()
            logger.info(f"💾 Successfully committed {success_count} package updates")
        except Exception as e:
            logger.error(f"❌ Failed to commit changes: {e}")
            db.session.rollback()
            return
        
        logger.info(f"""
        📊 Force Regeneration Summary:
        ✅ Successfully updated: {success_count} packages
        ❌ Failed updates: {error_count} packages
        🎯 Total processed: {len(generic_packages)} packages
        """)
        
        # Check for remaining generic packages
        remaining_generic = 0
        updated_packages = Package.query.filter(Package.procedure_breakdown.isnot(None)).all()
        for package in updated_packages:
            if package.procedure_breakdown:
                breakdown_text = json.dumps(package.procedure_breakdown) if isinstance(package.procedure_breakdown, list) else str(package.procedure_breakdown)
                if 'Professional Treatment Session' in breakdown_text or 'Customized aesthetic treatment' in breakdown_text:
                    remaining_generic += 1
        
        logger.info(f"📈 Packages still with generic breakdowns: {remaining_generic}")
        logger.info("✅ Force regeneration completed successfully!")

if __name__ == "__main__":
    force_regenerate_generic_breakdowns()