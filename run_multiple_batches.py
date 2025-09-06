"""
Run multiple batches of procedure imports in a sequence.
This script avoids using subprocess to prevent timeouts.
"""

import logging
import os
import sys
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Progress tracking file
PROGRESS_FILE = 'import_progress.json'

def load_progress():
    """Load the current import progress."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"last_index": 0, "completed": False}
    return {"last_index": 0, "completed": False}

def save_progress(index, completed=False):
    """Save the current import progress."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({"last_index": index, "completed": completed}, f)

def run_single_batch(start_idx):
    """Run a single batch starting from the given index."""
    import import_remaining_procedures as imp
    
    # Get missing procedures
    missing = imp.find_missing_procedures()
    if not missing:
        logging.info("No missing procedures found.")
        save_progress(0, True)
        return True, 0
    
    # Calculate batch range
    batch_size = imp.BATCH_SIZE
    end_idx = min(start_idx + batch_size, len(missing))
    
    if start_idx >= len(missing):
        logging.info("All procedures imported.")
        save_progress(0, True)
        return True, 0
    
    # Run import for this batch
    batch = missing[start_idx:end_idx]
    added_count = 0
    
    logging.info(f"Processing procedures {start_idx+1} to {end_idx} of {len(missing)}")
    
    conn = imp.get_db_connection()
    if conn:
        try:
            for proc in batch:
                if imp.import_procedure(conn, proc):
                    added_count += 1
        finally:
            conn.close()
    
    # Update progress
    logging.info(f"Imported {added_count} procedures in this batch")
    logging.info(f"Overall progress: {end_idx}/{len(missing)}")
    
    save_progress(end_idx)
    
    # Check if all imported
    completed = end_idx >= len(missing)
    if completed:
        logging.info("All procedures have been imported.")
        save_progress(0, True)
    
    return completed, added_count

def main():
    """Run imports in batches, resuming from last saved progress."""
    logging.info("Starting multiple batch imports...")
    
    # Get the last saved progress
    progress = load_progress()
    if progress["completed"]:
        logging.info("Import is already completed according to progress file.")
        return
    
    # Start from last save point
    start_idx = progress["last_index"]
    logging.info(f"Resuming from index {start_idx}")
    
    # Run one batch
    completed, added = run_single_batch(start_idx)
    
    logging.info(f"Batch import complete. Added {added} procedures.")
    if completed:
        logging.info("All procedures have been imported.")

if __name__ == "__main__":
    main()