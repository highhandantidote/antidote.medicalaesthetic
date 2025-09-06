#!/usr/bin/env python3
"""
Run data import scripts in sequence.

This script runs the data import scripts in the correct order:
1. Import body parts
2. Import categories
3. Import procedures
4. Import doctors
5. Associate doctors with procedures

This ensures the proper dependency order is maintained.
"""

import logging
import sys
import time

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   handlers=[
                       logging.FileHandler("import_log.txt"),
                       logging.StreamHandler(sys.stdout)
                   ])
logger = logging.getLogger(__name__)

def run_import_script(step, module_name):
    """Run an import script and handle errors."""
    try:
        logger.info(f"Step {step}: Running {module_name}")
        
        # Import the module dynamically
        module = __import__(module_name)
        
        # For modules with multiple functions, determine which function to call
        if module_name == 'import_body_parts':
            result = module.import_body_parts()
        elif module_name == 'import_categories':
            result = module.import_categories()
        elif module_name == 'import_procedures':
            result = module.import_procedures(batch_size=10)
        elif module_name == 'import_doctors':
            result = module.import_doctors(batch_size=5)
            if result:
                # If doctors were imported, associate them with procedures
                logger.info("Associating doctors with procedures...")
                result = module.associate_doctors_with_procedures(batch_size=5)
        
        if result:
            logger.info(f"Step {step}: {module_name} completed successfully")
        else:
            logger.error(f"Step {step}: {module_name} failed")
            return False
        
        # Add delay between steps to avoid database locks
        time.sleep(1)
        return True
    except Exception as e:
        logger.error(f"Error in {module_name}: {str(e)}")
        return False

def main():
    """Run the data import scripts in sequence."""
    start_time = time.time()
    logger.info("Starting data import sequence")
    
    # Define the import steps
    steps = [
        (1, "import_body_parts"),
        (2, "import_categories"),
        (3, "import_procedures"),
        (4, "import_doctors")
    ]
    
    # Run the imports
    for step_num, module_name in steps:
        success = run_import_script(step_num, module_name)
        if not success:
            logger.error(f"Import sequence stopped at step {step_num}: {module_name}")
            return False
    
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Data import completed in {duration:.2f} seconds")
    return True

if __name__ == "__main__":
    main()