#!/usr/bin/env python3
"""
Restore Database Script

This script restores essential data to the Antidote database.
It runs all the necessary data import scripts in the proper order.
"""

import os
import logging
import importlib
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Run a script by importing and calling its main function."""
    logger.info(f"Running {script_name}...")
    try:
        # Try to import and run the script
        module = importlib.import_module(script_name)
        if hasattr(module, 'main'):
            result = module.main()
            logger.info(f"Completed {script_name} with result: {result}")
            return True
        else:
            logger.error(f"Script {script_name} has no main() function")
            return False
    except ImportError as e:
        logger.error(f"Failed to import {script_name}: {str(e)}")
        # Try running as a subprocess
        try:
            result = subprocess.run(['python', f'{script_name}.py'], check=True)
            logger.info(f"Completed {script_name} as subprocess with exit code: {result.returncode}")
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run {script_name} as subprocess: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        return False

def restore_database():
    """Restore the database by running import scripts in sequence."""
    logger.info("Starting database restoration...")
    
    # Scripts to run in order
    scripts = [
        # Add essential foundation data
        "add_essential_procedures",  # Adds body parts, categories, and procedures
        "add_fixed_doctors",         # Adds a set of doctors
        
        # Add education modules if needed
        "add_education_module",
        
        # Add banners
        "add_all_banners",
        
        # Add ratings to doctors
        "add_doctor_ratings"
    ]
    
    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
        else:
            logger.warning(f"Script {script} did not complete successfully")
    
    logger.info(f"Database restoration completed. {success_count}/{len(scripts)} scripts successful.")
    return success_count == len(scripts)

if __name__ == "__main__":
    restore_database()