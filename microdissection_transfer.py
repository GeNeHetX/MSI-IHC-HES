from valis import registration
import json
import yaml
import os

# Load the configuration file
with open("config.yaml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# Hyperparameters
lame = config["lame"]  # Name of the lame
path = f"{config['path_to_data']}/{lame}"  # Path to the data

# Get the list of microdissections
microdissections = [dir.split('_')[1] for dir in os.listdir(f"{path}/images") if "MDNF" in dir]

for microdissection in microdissections:
    
    # Annotation and target images directory
    slide_src_dir = f"{path}/images/annotation_{microdissection}"
    # Alignment results directory
    results_dst_dir = f"{path}/results/annotation_{microdissection}"
    # The target image to which the features will be aligned
    target_img_f = f"{path}/images/annotation_{microdissection}/HES.svs"
    # The annotation image at which the original features are aligned
    annotation_img_f = f"{path}/images/annotation_{microdissection}/{microdissection}_HES.svs"
    # The original features as geojson file
    annotation_geojson_f = f"{path}/images/annotation_{microdissection}/{microdissection}_HES.geojson"
    # The warped features aligned to the target image as geojson file
    warped_geojson_annotation_f = f"{path}/results/{microdissection}_{config['warped_microdissection_file']}"

    # Create a Valis object and use the target_img_file as reference
    registrar = registration.Valis(src_dir=slide_src_dir,
                                   dst_dir=results_dst_dir,
                                   reference_img_f=target_img_f,
                                   align_to_reference=config["align_to_reference"])

    # Apply the registration
    rigid_registrar, non_rigid_registrar, error_df = registrar.register()

    # Register the annotation source slide from the microdissection image
    annotation_source_slide = registrar.get_slide(src_f=annotation_img_f)
    # Register the annotation target slide from the HES.svs image
    target_slide = registrar.get_slide(src_f=target_img_f)

    # Transfer the annotation from microdissection image to HES.svs using the pixels.geojson file
    warped_geojson = annotation_source_slide.warp_geojson_from_to(geojson_f=annotation_geojson_f,
                                                                  to_slide_obj=target_slide,
                                                                  non_rigid=config["microdissection_non_rigid"])

    # Save annotation as warped_pixels in the form geojson file, that can be dragged and dropped into QuPath
    with open(warped_geojson_annotation_f, 'w') as f:
        json.dump(warped_geojson, f)