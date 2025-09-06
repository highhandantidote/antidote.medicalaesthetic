"""
Run multiple iterations of the single-thread process.
This script calls process_single_thread.py multiple times to add replies to threads.
"""
import os
import subprocess
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the number of iterations
MAX_ITERATIONS = 10  # Process 10 threads in total

def check_progress():
    """Check current progress using the status script."""
    result = subprocess.run(["python", "check_replies_status.py"], 
                          capture_output=True, text=True)
    # Look for a line like "Progress: 57% (71/125)"
    for line in result.stdout.split('\n'):
        if "Progress:" in line:
            logger.info(line.strip())
        if "Need" in line and "more threads" in line:
            needed_text = line.strip()
            # Extract the number
            try:
                needed = int(needed_text.split("Need ")[1].split(" more")[0])
                return needed
            except:
                pass
    return -1  # Error or unable to parse

def process_batch():
    """Process batch of individual threads."""
    logger.info(f"Starting batch process, max {MAX_ITERATIONS} iterations")
    
    # Initial progress check
    threads_needed = check_progress()
    
    if threads_needed <= 0:
        logger.info("✅ TASK ALREADY COMPLETE: At least 125 threads have 2-4 replies")
        return
    
    # Limit actual iterations to what's needed or MAX_ITERATIONS, whichever is less
    iterations = min(MAX_ITERATIONS, threads_needed)
    logger.info(f"Will process {iterations} threads")
    
    threads_processed = 0
    
    for i in range(iterations):
        logger.info(f"Running iteration {i+1}/{iterations}")
        
        # Run the single thread script
        start_time = time.time()
        result = subprocess.run(["python", "process_single_thread.py"], 
                              capture_output=True, text=True)
        end_time = time.time()
        
        # Check if it succeeded
        if result.returncode == 0:
            logger.info(f"Iteration {i+1} completed in {end_time - start_time:.2f} seconds")
            threads_processed += 1
        else:
            logger.error(f"Iteration {i+1} failed: {result.stderr}")
        
        # Check progress every few iterations
        if (i+1) % 5 == 0 or i == iterations-1:
            threads_needed = check_progress()
            if threads_needed <= 0:
                logger.info("✅ TASK COMPLETE: At least 125 threads have 2-4 replies")
                break
        
        # Small delay to avoid overwhelming the database
        time.sleep(1)
    
    # Final progress check
    threads_needed = check_progress()
    logger.info(f"Batch processing complete. Processed {threads_processed} threads")
    
    if threads_needed <= 0:
        logger.info("✅ TASK COMPLETE: At least 125 threads have 2-4 replies")
    else:
        logger.info(f"⏳ TASK IN PROGRESS: Need {threads_needed} more threads. Run this script again to continue.")

if __name__ == "__main__":
    process_batch()