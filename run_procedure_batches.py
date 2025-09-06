#!/usr/bin/env python3
"""
Script to run procedure addition in multiple batches.

This script executes add_procedures_small_batch.py repeatedly to add
all procedures while avoiding timeouts on Replit.
"""
import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
LOG_FILE = f"run_procedure_batches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BATCH_SCRIPT = "add_procedures_small_batch.py"
MAX_PROCEDURES_PER_RUN = 15
MAX_TOTAL_PROCEDURES = 100
BATCH_SIZE = 5

def run_batch(start_index=0):
    """Run a single batch of procedure additions."""
    logger.info(f"Running batch with start_index={start_index}")
    
    cmd = [
        "python3", BATCH_SCRIPT,
        "--start-index", str(start_index),
        "--batch-size", str(BATCH_SIZE),
        "--max-procedures", str(MAX_PROCEDURES_PER_RUN)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        logger.info(f"Batch completed: {output}")
        
        # Extract the next index
        for line in output.split('\n'):
            if line.startswith("NEXT_INDEX="):
                next_index = int(line.split("=")[1])
                return next_index
        
        logger.error("Could not find next index in output")
        return -1
    except subprocess.CalledProcessError as e:
        logger.error(f"Batch failed: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return -1
    except Exception as e:
        logger.error(f"Error running batch: {e}")
        return -1

def main():
    """Run batches until completion or reaching MAX_TOTAL_PROCEDURES."""
    logger.info("Starting procedure batch runner")
    
    start_index = 0
    total_added = 0
    batch_num = 1
    
    while start_index >= 0 and total_added < MAX_TOTAL_PROCEDURES:
        logger.info(f"Running batch {batch_num} (start_index={start_index})")
        next_index = run_batch(start_index)
        
        if next_index < 0:
            logger.info("All procedures added or batch failed")
            break
            
        procedures_added = next_index - start_index
        total_added += procedures_added
        
        logger.info(f"Batch {batch_num} added {procedures_added} procedures (total: {total_added})")
        
        start_index = next_index
        batch_num += 1
        
        if total_added >= MAX_TOTAL_PROCEDURES:
            logger.info(f"Reached maximum total procedures ({MAX_TOTAL_PROCEDURES})")
            break
    
    logger.info(f"Completed adding procedures. Total added: {total_added}")
    logger.info(f"Log saved to: {LOG_FILE}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())