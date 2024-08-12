# Read the config file
configfile: "config.yaml"

# Rule all
rule all:
    input:
        f"{config['path_to_data']}/{config['lame']}/results/detected_peaks/peaks.yaml",
        f"{config['path_to_data']}/{config['lame']}/results/detected_peaks/peaks_per_feature.csv",
        f"{config['path_to_data']}/{config['lame']}/results/detected_peaks/peaks_profile.png",
        f"{config['path_to_data']}/{config['lame']}/results/detected_peaks/reduced_spectrum.pkl",
        f"{config['path_to_data']}/{config['lame']}/results/contour.geojson",
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi.geojson"
    shell:
        "echo 'All done!'"

# Build the singularity container for cardinal
rule cardinal_container:
    input: 
        "cardinal.def"
    output: 
        "cardinal.sif"
    shell: 
        "singularity build cardinal.sif cardinal.def"

# Build the singularity container for m2aia
rule m2aia_container:
    input: 
        "m2aia.def"
    output: 
        "m2aia.sif"
    shell: 
        "sudo singularity build m2aia.sif m2aia.def"

# Run the peak detection R script
rule maldi_proccess:
    input:
        "cardinal.sif",
        f"{config['path_to_data']}/{config['lame']}/maldi/mse.imzML",
        f"{config['path_to_data']}/{config['lame']}/maldi/mse.ibd"
    output: 
        directory(f"{config['path_to_data']}/{config['lame']}/results/mse_processed.imzML")
    singularity:
        "cardinal.sif"
    # resources:
    #     cores=24
    shell:
        f"Rscript maldi_proccess.R"

# Run the peak detection R script
rule maldi_peaks:
    input:
        "cardinal.sif",
        directory(f"{config['path_to_data']}/{config['lame']}/results/mse_processed.imzML")
    output: 
        directory(f"{config['path_to_data']}/{config['lame']}/results/mse_peaks.imzML")
    singularity:
        "cardinal.sif"
    # resources:
    #     cores=24
    shell:
        f"Rscript maldi_peaks.R"


# Run the pixel geojson generation python script
rule pixel_geojson:
    input:
        "m2aia.sif",
        f"{config['path_to_data']}/{config['lame']}/maldi/mse.mis",
        f"{config['path_to_data']}/{config['lame']}/maldi/coord.csv"
    output: 
        f"{config['path_to_data']}/{config['lame']}/results/contour.geojson",
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi.geojson"
    singularity:
        "m2aia.sif"
    script:
        "pixels_geojson.py"