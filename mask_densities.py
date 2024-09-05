import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import yaml

# Load the configuration file
with open("config.yaml", 'r') as stream:
    config = yaml.safe_load(stream)

# Hyperparameters
lame = config["lame"]  # Lame name
markers = config["markers"].values()  # List of markers

MALDI_PIXEL_LENGTH = config["MALDI_PIXEL_LENGTH"]  # MALDI pixel length in micrometers
IMAGE_PIXEL_LENGTH = config["IMAGE_PIXEL_LENGTH"]  # Image pixel length in micrometers

path = f"{config['path_to_data']}/{lame}/results"  # Path to the results folder

# Read the MALDI aligned pixels geojson pickle file
pixels_gdf = gpd.read_file(f"{path}/pixels_maldi_warped.geojson")

# Compute the geometry centroid of each pixel
pixels_gdf["centroid"] = pixels_gdf.geometry.centroid

# Transform the centroid to tuple
pixels_gdf["x_warped"] = pixels_gdf.centroid.x
pixels_gdf["y_warped"] = pixels_gdf.centroid.y


# Add the original pixel coordinates to the geodataframe
coord_scils = pd.read_csv(f"{config['path_to_data']}/{lame}/maldi/coord.csv",
                          skiprows=8,
                          sep=';')[["x", "y"]]  # Read the original pixels scils coordinates
coord_scils["y"] = coord_scils["y"].max() - coord_scils["y"]  # Invert the y axis
pixels_gdf["x_original"] = coord_scils.x  # Add the original x coordinates to the geodataframe
pixels_gdf["y_original"] = coord_scils.y  # Add the original y coordinates to the geodataframe

# Compute the half length of the square around the centroid in pixels
l = int((MALDI_PIXEL_LENGTH / IMAGE_PIXEL_LENGTH) / 2)

# Compute the density of each pixel
for marker in markers:
    mask = plt.imread(f"{path}/masks/{marker}_mask.png") > 0
    pixels_gdf[f"Density_{marker.split('_')[1]}"] = [np.mean(mask[int(y)-l:int(y)+l,
                                                                  int(x)-l:int(x)+l]) 
                                                     for x, y in zip(pixels_gdf.x_warped, pixels_gdf.y_warped)]

# Adjust the data types of the density columns
pixels_gdf = pixels_gdf.astype({f"Density_{marker.split('_')[1]}":'float32'
                                for marker in markers})

# Save the geodataframe to a pickle file
pixels_gdf.to_pickle(f"{path}/pixels_maldi_warped_density_gdf.pkl")

# Save a dataframe without the geometries
pixels_df = pd.DataFrame(pixels_gdf.drop(columns=["geometry", "centroid", "objectType"]))  # Remove the geometry columns
pixels_df = pixels_df.astype({'id':'int32'})  # Adjust the id data type to int32
pixels_df.to_csv(f"{path}/pixels_maldi_warped_density_df.csv", index=False)  # Save the dataframe to a csv file