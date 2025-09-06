#!/bin/bash

# First, clear existing doctor data
echo "Clearing existing doctor data..."
python clear_doctors.py

if [ $? -ne 0 ]; then
    echo "Error clearing doctor data. Exiting."
    exit 1
fi

# Create default avatar
echo "Creating default doctor avatar..."
python create_default_avatar.py

if [ $? -ne 0 ]; then
    echo "Error creating default avatar. Exiting."
    exit 1
fi

# Run batch import in a loop
start_index=0
total_done=0
max_batches=12  # Maximum number of batches to process (12 batches x 10 doctors = ~120 doctors)

for i in $(seq 1 $max_batches); do
    echo "Running batch $i (starting at index $start_index)..."
    
    # Run the batch import and capture output
    output=$(python import_doctors_batch.py $start_index)
    status=$?
    
    if [ $status -ne 0 ]; then
        echo "Error in batch $i. Exiting."
        exit 1
    fi
    
    # Extract next index from output
    next_index=$(echo "$output" | grep "NEXT_INDEX=" | cut -d= -f2)
    
    if [ -z "$next_index" ]; then
        echo "Could not determine next index. Batch processing may be complete."
        break
    fi
    
    # Count docs added in this batch
    docs_added=$((next_index - start_index))
    total_done=$((total_done + docs_added))
    echo "Added $docs_added doctors in this batch. Total so far: $total_done"
    
    # Update start index for next batch
    start_index=$next_index
    
    # If next index is the same as current, we're done
    if [ $next_index -eq $start_index ]; then
        echo "No more doctors to process."
        break
    fi
    
    # Brief pause to let the system breathe
    sleep 1
done

echo "Doctor import complete. Total doctors imported: $total_done"