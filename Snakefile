# Read the config file
configfile: "config.yaml"


#####################
## MALDI-MSI peaks ##
#####################

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
        "singularity build m2aia.sif m2aia.def"

# Run the peak detection R script
rule maldi_proccess:
    input:
        "cardinal.sif",
        f"{config['path_to_data']}/{config['lame']}/maldi/mse.imzML",
        f"{config['path_to_data']}/{config['lame']}/maldi/mse.ibd"
    output: 
        f"{config['path_to_data']}/{config['lame']}/results/mse_processed.imzML/mse_processed.imzML",
        f"{config['path_to_data']}/{config['lame']}/results/mse_processed.imzML/mse_processed.ibd"
    singularity:
        "cardinal.sif"
    shell:
        "Rscript maldi_proccess.R"

# Run the peak detection R script
rule maldi_peaks:
    input:
        "cardinal.sif",
        f"{config['path_to_data']}/{config['lame']}/results/mse_processed.imzML/mse_processed.imzML",
        f"{config['path_to_data']}/{config['lame']}/results/mse_processed.imzML/mse_processed.ibd"
    output: 
        f"{config['path_to_data']}/{config['lame']}/results/mse_peaks.imzML/mse_peaks.imzML",
        f"{config['path_to_data']}/{config['lame']}/results/mse_peaks.imzML/mse_peaks.ibd",

    singularity:
        "cardinal.sif"
    shell:
        "Rscript maldi_peaks.R"


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



###############
## Alignment ##
###############

# Rule all
rule alignment:
    input:
        f"{config['path_to_data']}/{config['lame']}/results/images_aligned/HES.ome.tiff",
        f"{config['path_to_data']}/{config['lame']}/results/images_aligned/MALDI.ome.tiff",
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi_warped.geojson"
    shell:
        "echo 'Alignment done!'"

# Build the singularity container for VALIS
rule valis_container:
    output: 
        "valis.sif"
    shell: 
        f"singularity build valis.sif docker://cdgatenbee/valis-wsi:{config['valis_version']}"


# Run the images alignment python script
rule align_images:
    input:
        "valis.sif",
        f"{config['path_to_data']}/{config['lame']}/images/alignment/HES.svs",
        f"{config['path_to_data']}/{config['lame']}/images/alignment/MALDI.tif"
    output: 
        f"{config['path_to_data']}/{config['lame']}/results/images_aligned/HES.ome.tiff",
        f"{config['path_to_data']}/{config['lame']}/results/images_aligned/MALDI.ome.tiff"
    singularity:
        "valis.sif"
    script:
        "images_alignment.py"


# Run the annotation transfer python script
rule annotation_transfer:
    input:
        "valis.sif",
        f"{config['path_to_data']}/{config['lame']}/images/annotation/HES.svs",
        f"{config['path_to_data']}/{config['lame']}/images/annotation/MALDI.tif",
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi.geojson"
    output: 
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi_warped.geojson"
    singularity:
        "valis.sif"
    script:
        "annotation_transfer.py"



##################
## Mask density ##
##################

rule densities:
    input:
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi_warped_density_gdf.pkl",
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi_warped_density_df.csv"      
    shell:
        "echo 'Mask density done!'"


# Run the mask generation python script
rule mask_generation:
    input:
        "m2aia.sif",
        expand("{path_to_qp_projects}/{lame}/export/",
               path_to_qp_projects=config['path_to_qp_projects'],
               lame=config['lame'])
    output: 
        expand("{path_to_data}/{lame}/results/masks/{marker}_mask.png",
               path_to_data=config['path_to_data'],
               lame=config['lame'],
               marker=config['markers'])
    singularity:
        "m2aia.sif"
    script:
        "mask_generation.py"


# Run the mask density python script
rule mask_densities:
    input:
        "m2aia.sif",
        expand("{path_to_data}/{lame}/results/masks/{marker}_mask.png",
               path_to_data=config['path_to_data'],
               lame=config['lame'],
               marker=config['markers']),
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi_warped.geojson",
        f"{config['path_to_data']}/{config['lame']}/maldi/coord.csv"
    output: 
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi_warped_density_gdf.pkl",
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi_warped_density_df.csv"
    singularity:
        "m2aia.sif"
    script:
        "mask_densities.py"


# Run the setter R script to set the densities in the imzML file
rule maldi_densities:
    input:
        f"{config['path_to_data']}/{config['lame']}/results/mse_peaks.imzML/mse_peaks.imzML",
        f"{config['path_to_data']}/{config['lame']}/results/mse_peaks.imzML/mse_peaks.ibd",
        f"{config['path_to_data']}/{config['lame']}/results/pixels_maldi_warped_density_df.csv"
    output: 
        f"{config['path_to_data']}/{config['lame']}/results/mse_densities.imzML/mse_densities.imzML",
        f"{config['path_to_data']}/{config['lame']}/results/mse_densities.imzML/mse_densities.ibd"
    singularity:
        "cardinal.sif"
    shell:
        "Rscript imzml_setter.R"