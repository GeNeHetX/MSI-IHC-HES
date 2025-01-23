#!/bin/bash

# Array of values
values=("543933-23" "543933-24" "544085-12" "544085-14" "544085-17")

# Loop through each value
for value in "${values[@]}"; do
    echo "Processing value $value"

    # Replace the value in the file
    sed -i "3s/.*/lame: $value/" config.yaml

    # Sleep for 2 second
    sleep 2

    # Run the snakemake pipeline
    snakemake --use-singularity maldi_peaks

    # Sleep for 2 second
    sleep 2
done