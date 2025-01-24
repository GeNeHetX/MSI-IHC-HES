#!/bin/bash

# Array of values
slides=("546332-17" "546332-26" "546332-38")

# Loop through slides
for slide in "${slides[@]}"; do
    echo "Processing slide $slide"

    # Replace the slide in the file
    sed -i "3s/.*/lame: $slide/" config.yaml
    sleep 2

    # Run the snakemake pipeline
    snakemake --cores 15 --use-singularity maldi_peaks
    sleep 60
done