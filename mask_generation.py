import numpy as np
import matplotlib.pyplot as plt
import PIL
from PIL import Image
from skimage import io
from skimage.filters import threshold_isodata
import yaml
import os

# Increase the limit of allowed images size
PIL.Image.MAX_IMAGE_PIXELS = 10e10

# Load the configuration file
with open("config.yaml", 'r') as stream:
    config = yaml.safe_load(stream)

# Hyperparameters
lame = config["lame"]
compression = config["compression"]
markers = config["markers"]

# Define the path to the masks and the QP projects
path = f"{config['path_to_data']}/{lame}/results/masks"
path_qp = f"{config['path_to_qp_projects']}/{lame}/export"

# Extract the original width of the image
with Image.open(f"{config['path_to_data']}/{lame}/results/images_aligned/HES.ome.tiff") as slide:
    original_width = slide.size[0]

# Create the directory if it does not exist
os.makedirs(path, exist_ok=True)

for marker in markers:
    # Check if the mask already exists
    if os.path.exists(f"{path}/{marker}_mask.png") and os.path.exists(f"{path}/{marker}_mask_compressed_{compression}.png"):
        print(f"{marker} mask already exists")
    else:
        print(f"Creating {marker} mask")
        
        # Determine the number of tiles
        num_of_tiles = len([tile for tile in os.listdir(path_qp) if marker in tile])

        # Read first channel of one of the tile images
        tile = io.imread(f"{path_qp}/{marker}_mask_{num_of_tiles//2}_of_{num_of_tiles}.png")[:, :, 1]

        # Compute isodata threshold 
        thresh = threshold_isodata(tile)

        # Repeat the process on all the tiles if the threshold does not isolate the signal
        k = 0
        while (tile < thresh).mean() == 0:
            k += 1
            # Raise an error if the threshold does not isolate the signal for all the tiles
            if k > num_of_tiles:
                raise ValueError(f"Marker {marker} threshold does not isolate the signal for all the tiles")
            tile = io.imread(f"{path_qp}/{marker}_mask_{k}_of_{num_of_tiles}.png")[:, :, 1]
            thresh = threshold_isodata(tile)

        # Clear tile and mask to free memory
        del tile

        # Create a generator of all tiles as binary masks
        masks = ((io.imread(f"{path_qp}/{marker}_mask_{i}_of_{num_of_tiles}.png")[:, :, 1] < thresh) for i in range(1, num_of_tiles+1))

        # Stack all the masks horizontally to create a single mask
        mask = np.hstack([mask for mask in masks])

        # Complete the mask to meet the original image size
        mask = np.pad(mask, ((0, 0), (0, original_width - mask.shape[1])), mode='edge')

        # Save the mask
        PIL.Image.fromarray(mask).save(f"{path}/{marker}_mask.png")

        # Compres or cut the mask to a smaller size
        mask_small = mask[::compression, ::compression]

        # Save the small mask
        PIL.Image.fromarray(mask_small).save(f"{path}/{marker}_mask_compressed_{compression}.png")

        # Print the density of the mask
        print(f"Density: {mask.mean()}")