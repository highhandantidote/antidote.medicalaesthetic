"""
Run multiple batches of procedure imports in sequence.
This script avoids using subprocess to prevent ptrace errors.
"""

import logging
import time
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Number of batches to run
BATCH_COUNT = 10

def run_multiple_batches():
    """Run multiple batches of procedure imports."""
    logging.info(f"Starting automated import for {BATCH_COUNT} batches")
    
    # Import the necessary modules
    sys.path.append(os.getcwd())
    from import_procedures import import_procedures_batch, main as import_proc_main
    from check_import_progress import check_progress
    
    for i in range(BATCH_COUNT):
        logging.info(f"Running batch {i+1} of {BATCH_COUNT}")
        
        # Run the import procedure
        import_proc_main()
        
        # Wait a bit between batches
        time.sleep(2)
    
    # Check final progress
    logging.info("Checking final import progress")
    body_parts, categories, procedures = check_progress()
    
    logging.info(f"Import complete. Now have {procedures} procedures in the database.")

if __name__ == "__main__":
    run_multiple_batches()