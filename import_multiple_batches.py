"""
Import multiple batches of procedures consecutively.

This script runs the import process for multiple batches in a row, 
tracking progress and pausing between batches to avoid timeouts.
"""
import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('multi_batch_import.log')
    ]
)
logger = logging.getLogger(__name__)

def get_current_count():
    """Get the current count of procedures from the database."""
    try:
        # Run check_import_progress.py and capture its output
        result = subprocess.run(
            ['python', 'check_import_progress.py'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Parse the output to get the current count
        output_lines = result.stdout.splitlines()
        for line in output_lines:
            if "Procedures Imported:" in line:
                parts = line.split('/')
                if len(parts) >= 2:
                    count = parts[0].split(':')[1].strip()
                    return int(count)
        
        # If we couldn't parse the output, use a fallback method
        import psycopg2
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM procedures")
        count = cursor.fetchone()[0]
        conn.close()
        return count
        
    except Exception as e:
        logger.error(f"Error getting current count: {str(e)}")
        return -1

def run_batch(start_row, batch_size):
    """Run a single batch import."""
    try:
        logger.info(f"Starting batch import from row {start_row} with batch size {batch_size}")
        
        # Run the import script as a subprocess
        cmd = ['python', 'import_next_batch.py', '--start', str(start_row), '--batch', str(batch_size)]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Set a timeout (in seconds)
        timeout = 120
        start_time = time.time()
        
        # Monitor the process
        while process.poll() is None:
            # Check if timeout has been exceeded
            if time.time() - start_time > timeout:
                logger.warning(f"Batch import timed out after {timeout} seconds")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                return False
            
            # Sleep briefly to avoid high CPU usage
            time.sleep(0.5)
        
        # Check if process completed successfully
        if process.returncode == 0:
            logger.info(f"Batch import completed successfully")
            return True
        else:
            stderr = process.stderr.read()
            logger.error(f"Batch import failed with return code {process.returncode}: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running batch: {str(e)}")
        return False

def main():
    """Main entry point for the multi-batch import script."""
    parser = argparse.ArgumentParser(description='Import multiple batches of procedures')
    parser.add_argument('--start', type=int, help='Starting row (0-indexed)')
    parser.add_argument('--batch-size', type=int, default=15, help='Size of each batch')
    parser.add_argument('--num-batches', type=int, default=3, help='Number of batches to run')
    parser.add_argument('--pause', type=int, default=5, help='Seconds to pause between batches')
    args = parser.parse_args()
    
    # If no start row is provided, get the current count
    start_row = args.start
    if start_row is None:
        start_row = get_current_count()
        if start_row < 0:
            logger.error("Could not determine current count. Please specify a start row.")
            sys.exit(1)
    
    batch_size = args.batch_size
    num_batches = args.num_batches
    pause_seconds = args.pause
    
    logger.info(f"Starting multi-batch import from row {start_row}")
    logger.info(f"Will run {num_batches} batches of size {batch_size} with {pause_seconds}s pause between batches")
    
    start_time = time.time()
    successful_batches = 0
    
    for i in range(num_batches):
        current_start = start_row + (i * batch_size)
        logger.info(f"Running batch {i+1}/{num_batches} starting at row {current_start}")
        
        # Run the batch
        success = run_batch(current_start, batch_size)
        
        if success:
            successful_batches += 1
        else:
            logger.warning(f"Batch {i+1} encountered issues")
        
        # Pause between batches (except after the last one)
        if i < num_batches - 1:
            logger.info(f"Pausing for {pause_seconds} seconds before next batch...")
            time.sleep(pause_seconds)
    
    # Get final count
    end_count = get_current_count()
    
    # Calculate statistics
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    logger.info(f"Multi-batch import completed in {minutes}m {seconds}s")
    logger.info(f"Successful batches: {successful_batches}/{num_batches}")
    
    if end_count > 0:
        logger.info(f"Procedures count: {end_count}")
        
        # Calculate procedures per minute
        procedures_added = end_count - start_row
        if procedures_added > 0 and elapsed_time > 0:
            rate = procedures_added / (elapsed_time / 60)
            logger.info(f"Import rate: {rate:.2f} procedures/minute")
            
            # Estimate time to complete all imports
            total_procedures = 516  # Hardcoded total
            remaining = total_procedures - end_count
            if remaining > 0:
                est_minutes = remaining / rate
                est_hours = est_minutes / 60
                logger.info(f"Estimated time to complete all imports: {est_minutes:.2f} minutes ({est_hours:.2f} hours)")
    
    # Print next command to continue
    next_start = start_row + (successful_batches * batch_size)
    logger.info(f"To continue importing, run:")
    logger.info(f"python import_multiple_batches.py --start {next_start} --batch-size {batch_size} --num-batches {num_batches}")
    print(f"\nNext command to run: python import_multiple_batches.py --start {next_start} --batch-size {batch_size} --num-batches {num_batches}")

if __name__ == "__main__":
    main()