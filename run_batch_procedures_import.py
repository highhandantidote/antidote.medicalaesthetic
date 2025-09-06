"""
Run multiple batches of procedure imports in a sequence.
"""

import logging
import subprocess
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Number of batches to run
BATCH_COUNT = 5

def run_batch_imports():
    """Run multiple batches of procedure imports."""
    logging.info(f"Starting batch procedure import - will run {BATCH_COUNT} batches")
    
    for i in range(BATCH_COUNT):
        logging.info(f"Running batch {i+1}/{BATCH_COUNT}")
        
        try:
            # Run the import_procedures.py script
            result = subprocess.run(["python", "import_procedures.py"], 
                                   capture_output=True, text=True, check=True)
            
            # Log the output
            for line in result.stdout.split('\n'):
                if line.strip():
                    logging.info(f"Batch {i+1} output: {line}")
            
            # Check if all procedures have been imported
            if "All procedures have been imported" in result.stdout:
                logging.info("All procedures have been imported. Stopping batch import.")
                break
            
            # Add a short delay between batches to avoid overwhelming the database
            time.sleep(2)
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running batch {i+1}: {e}")
            logging.error(f"STDOUT: {e.stdout}")
            logging.error(f"STDERR: {e.stderr}")
            break
        except Exception as e:
            logging.error(f"Unexpected error in batch {i+1}: {e}")
            break
    
    logging.info("Batch import process complete")

def main():
    """Run the batch imports."""
    run_batch_imports()
    
    # Check final progress
    try:
        logging.info("Checking final import progress...")
        subprocess.run(["python", "check_import_progress.py"], check=True)
    except Exception as e:
        logging.error(f"Error checking progress: {e}")

if __name__ == "__main__":
    main()