#!/usr/bin/env python3
"""
Run all seeding operations in the correct order using optimized batch processing.

This script will:
1. Seed a test user
2. Seed 117 procedures in small batches
3. Seed 6 community threads with specific distribution in small batches
4. Verify seeding completion

The optimized approach avoids database timeouts by using small transaction batches.
"""
import os
import sys
import logging
import subprocess
import time
from datetime import datetime

# Configure logging
LOG_FILE = f"optimized_seeding_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name, max_retries=2, retry_delay=5):
    """
    Run a Python script and return success/failure.
    Includes retry logic for handling transient failures.
    """
    logger.info(f"Running {script_name}...")
    retries = 0
    
    while retries <= max_retries:
        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, script_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5-minute timeout
            )
            elapsed_time = time.time() - start_time
            
            logger.info(f"Output from {script_name}:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Errors/warnings from {script_name}:\n{result.stderr}")
            
            logger.info(f"{script_name} completed successfully in {elapsed_time:.2f} seconds")
            return True
        
        except subprocess.TimeoutExpired:
            logger.error(f"{script_name} timed out after 300 seconds")
            retries += 1
            if retries <= max_retries:
                logger.info(f"Retrying in {retry_delay} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logger.error(f"Max retries exceeded for {script_name}")
                return False
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running {script_name}:")
            logger.error(f"Exit code: {e.returncode}")
            logger.error(f"Output: {e.stdout}")
            logger.error(f"Error: {e.stderr}")
            
            retries += 1
            if retries <= max_retries:
                logger.info(f"Retrying in {retry_delay} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logger.error(f"Max retries exceeded for {script_name}")
                return False
        
        except Exception as e:
            logger.error(f"Unexpected error running {script_name}: {str(e)}")
            return False

def check_database():
    """Run database status check and return success/failure."""
    logger.info("Checking database status...")
    try:
        result = subprocess.run(
            [sys.executable, "check_db_status.py"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if we have the expected number of procedures and threads
        proc_complete = "117/117" in result.stdout
        thread_complete = "6/6" in result.stdout
        
        if proc_complete and thread_complete:
            logger.info("Database seeding is complete")
            return True
        else:
            logger.warning("Database seeding is incomplete")
            return False
    
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return False

def main():
    """Run all seeding scripts in order with optimized batching."""
    logger.info("Starting optimized community analytics dashboard seeding process...")
    start_time = time.time()
    
    # Step 1: Seed test user
    if not run_script("seed_minimal_user.py"):
        logger.error("Failed to seed test user. Aborting.")
        return 1
    
    # Step 2: Seed procedures with batching
    logger.info("Starting procedure seeding with batch processing...")
    if not run_script("seed_procedures_batch.py"):
        logger.error("Failed to seed procedures with batch processing. Aborting.")
        return 1
    
    # Step 3: Seed community threads with batching
    logger.info("Starting community thread seeding with batch processing...")
    if not run_script("seed_community_threads_batch.py"):
        logger.error("Failed to seed community threads with batch processing. Aborting.")
        return 1
    
    # Step 4: Verify database status
    if check_database():
        logger.info("Database verification successful!")
    else:
        logger.warning("Database verification showed incomplete seeding. Check the logs for details.")
    
    elapsed_time = time.time() - start_time
    logger.info(f"All seeding operations completed in {elapsed_time:.2f} seconds!")
    logger.info("Community analytics dashboard is ready to use.")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())