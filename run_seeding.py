#!/usr/bin/env python3
"""
Run all seeding operations in the correct order to prepare the community analytics dashboard.
This script will:
1. Seed a test user
2. Seed 117 procedures
3. Seed 6 community threads with specific distribution
"""
import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
LOG_FILE = f"seeding_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Run a Python script and return success/failure."""
    logger.info(f"Running {script_name}...")
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Output from {script_name}:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Errors/warnings from {script_name}:\n{result.stderr}")
        logger.info(f"{script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}:")
        logger.error(f"Exit code: {e.returncode}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False

def main():
    """Run all seeding scripts in order."""
    logger.info("Starting community analytics dashboard seeding process...")
    
    # Step 1: Seed test user
    if not run_script("seed_minimal_user.py"):
        logger.error("Failed to seed test user. Aborting.")
        return 1
    
    # Step 2: Seed procedures
    if not run_script("seed_procedures.py"):
        logger.error("Failed to seed procedures. Aborting.")
        return 1
    
    # Step 3: Seed community threads
    if not run_script("seed_community_threads_updated.py"):
        logger.error("Failed to seed community threads. Aborting.")
        return 1
    
    logger.info("All seeding operations completed successfully!")
    logger.info("Community analytics dashboard is ready to use.")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())