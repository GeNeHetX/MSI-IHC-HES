from valis import registration
import yaml

# Load the configuration file
with open("config.yaml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# Hyperparameters
lame = config["lame"]  # Name of the lame
path = f"{config['path_to_data']}/{lame}"  # Path to the data


# Images directory to be aligned including the reference
slide_src_dir = f"{path}/images/alignment"
# Alignment results directory
results_dst_dir = f"{path}/results/alignment"
# Directory of the resulted aligned images
registered_slide_dst_dir = f"{path}/results/images_aligned"
# The reference image to which all the images will be aligned
reference_slide = config["reference_slide"]

# Create a Valis object and use it to register the slides in slide_src_dir
registrar = registration.Valis(src_dir=slide_src_dir,
                               dst_dir=results_dst_dir,
                               reference_img_f=reference_slide,
                               align_to_reference=config["align_to_reference"])

# Apply the alignment on the slides in slide_src_dir
rigid_registrar, non_rigid_registrar, error_df = registrar.register()

# Save all registered slides as ome.tiff
registrar.warp_and_save_slides(registered_slide_dst_dir,
                               crop=config["crop"])

# Kill the JVM
registration.kill_jvm()