#!/bin/bash

# Shell script to run multiple batches of procedure imports

echo "Starting procedure imports in batch mode"
echo "========================================"

# Number of batches to run
BATCH_COUNT=10

for i in $(seq 1 $BATCH_COUNT); do
    echo "Running batch $i of $BATCH_COUNT"
    python import_procedures.py
    
    # Add a short delay between batches
    sleep 2
done

echo "========================================"
echo "Checking final progress"
python check_import_progress.py

echo "Import batches complete"