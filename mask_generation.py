import numpy as np
import xgboost as xgb
import PIL
from PIL import Image
from skimage import io, morphology
from skimage.filters import threshold_isodata
from tqdm import tqdm
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

# Loop over all the markers
for model, marker in markers.items():
    
    # Check if the mask already exists
    if os.path.exists(f"{path}/{marker}_mask.png") and os.path.exists(f"{path}/{marker}_mask_compressed.png"):
        print(f"{marker} mask already exists")
    
    # If model starts with "qupath", then we need to extract the masks from the QP project
    elif model.startswith("qupath"):
        print(f"Creating {marker} mask from QuPath project")
        
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
        print(f"Saving the {marker}_mask")
        PIL.Image.fromarray(mask).save(f"{path}/{marker}_mask.png")

        # Compres or cut the mask to a smaller size
        mask_small = mask[::compression, ::compression]

        # Save the small mask
        PIL.Image.fromarray(mask_small).save(f"{path}/{marker}_mask_compressed.png")

        # Print the density of the mask
        print(f"Density = {mask.mean()}")
    
    # If model starts with "xgboost", then we need to apply XGBoost model on the image
    elif model.startswith("xgboost"):
        print(f"Creating {marker} mask from its XGBoost model")

        # Load the model file
        model = xgb.Booster()
        model.load_model(f"models/xgboost_{marker.split('_')[1]}.model")

        # Set the model to use GPU
        model.set_param({'device':'gpu'})

        # Load the model parameters
        with open(f"models/xgboost_{marker.split('_')[1]}.yaml", "r") as f:
            model_params = yaml.safe_load(f)

        # Extract the model parameters
        threshold = model_params["threshold"]
        min_size = model_params["min_size"]

        # Cut the image into vertical tiles
        img_tiles = np.array_split(ary=io.imread(f"{config['path_to_data']}/{lame}/results/images_aligned/{marker.split('_')[0]}.ome.tiff"), 
                                   indices_or_sections=100,
                                   axis=1)
        
        # Apply the model to each image tile
        mask_tiles = []
        print("Processing the tiles")
        for i, img_tile in tqdm(enumerate(img_tiles)):
            # Transform the image into a 2D matrix
            dtest = xgb.DMatrix(img_tile.reshape(-1, 3))

            # Predict the mask
            preds = model.predict(dtest)

            # Append the mask to the mask_tiles list
            mask_tiles.append(preds.reshape(img_tile.shape[:2]) > threshold)

        # Concatenate the mask tiles into a single mask
        mask = np.concatenate(mask_tiles, axis=1)

        # Clean the mask
        print(f"Cleaning the {marker}_mask")
        mask_clean = morphology.remove_small_objects(mask, min_size=min_size)

        # Print the density of the mask
        print(f"Density before cleaning = {mask.mean()}")
        print(f"Density after  cleaning = {mask_clean.mean()}")

        # Save the cleaned mask and compressed version of it
        print(f"Saving the {marker}_mask")
        PIL.Image.fromarray(mask_clean).save(f"{config['path_to_data']}/{lame}/results/masks/{marker}_mask.png")
        PIL.Image.fromarray(mask_clean[::compression, ::compression]).save(f"{config['path_to_data']}/{lame}/results/masks/{marker}_mask_compressed.png")

    # Raise an error if the model is not recognized
    else:
        raise ValueError(f"Model {model} not recognized")