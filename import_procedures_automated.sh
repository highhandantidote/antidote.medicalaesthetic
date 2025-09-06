#!/bin/bash

# Import procedures in batches of 10
# This script will automatically continue from where it left off

CSV_PATH="attached_assets/procedure_details - Sheet1.csv"
BATCH_SIZE=10
TOTAL_ROWS=516  # Total number of procedures in CSV (excluding header)
CURRENT_ROW=20  # Start from where we left off

# Function to run the import and extract the next start row
run_import() {
    local start_row=$1
    echo "Running import from row $start_row..."
    python import_all_procedures.py --start $start_row --batch $BATCH_SIZE --csv "$CSV_PATH"
}

# Loop through batches until we've processed all rows
while [ $CURRENT_ROW -lt $TOTAL_ROWS ]; do
    run_import $CURRENT_ROW
    
    # Increment to the next batch
    CURRENT_ROW=$((CURRENT_ROW + BATCH_SIZE))
    
    echo "Completed batch. Next starting row: $CURRENT_ROW"
    echo "Progress: $((CURRENT_ROW * 100 / TOTAL_ROWS))% complete"
    
    # Sleep for a few seconds to avoid overwhelming the system
    echo "Sleeping for 3 seconds before next batch..."
    sleep 3
done

echo "Import process completed!"