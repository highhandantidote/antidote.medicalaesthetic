#!/usr/bin/env python3
"""
Minimal test script for AI recommendations with expanded dataset.
"""
import sys
from app import create_app
from models import Procedure

def main():
    """Run the minimal test script."""
    print("Starting minimal recommendation test...")
    
    # Create the application context
    app = create_app()
    
    with app.app_context():
        try:
            # Count procedures
            count = Procedure.query.count()
            print(f"Found {count} procedures in the database")
            
            # Get a specific procedure by ID
            # Use ID 1 which should exist if any procedures exist
            procedure = Procedure.query.get(1)
            
            if procedure:
                print(f"Found procedure: {procedure.procedure_name}")
                print(f"Body part: {procedure.body_part}")
                print(f"Category: {procedure.category.name if procedure.category else 'None'}")
            else:
                print("Procedure with ID 1 not found.")
                
        except Exception as e:
            print(f"Error in testing: {str(e)}")
            return 1
            
    return 0

if __name__ == "__main__":
    sys.exit(main())