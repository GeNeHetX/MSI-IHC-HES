#!/bin/bash

# Array of values
slides=("13AG06573-10" "13AG06573-18" "13AG06746-19" "13AG06746-22" "13AG06746-27" "14AG03250-32" "14AG03681-25" "14AG03681-31" "14AG06301-08" "14AG06301-09")

# Loop through slides
for slide in "${slides[@]}"; do
    echo "Processing slide $slide"

    # Replace the slide in the file
    sed -i "3s/.*/lame: $slide/" config.yaml
    sleep 2

    # Run the snakemake pipeline
    snakemake --use-singularity mask_generation
    sleep 60
done