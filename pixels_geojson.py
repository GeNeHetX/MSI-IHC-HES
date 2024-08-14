# Libraries
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import os

# Functions
from utils import extract_contour, countour_to_geojson, align_coord_contour, coord_to_geojson

# Load the configuration file
with open('config.yaml', 'r') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# Hyperparameters
lame = config['lame']

path = f"{config['path_to_data']}/{lame}"

# Read the mis file
with open(f"{path}/maldi/mse.mis") as f:
    mis = f.read()

# Extract the x,y coordinates from the mis file
contour = extract_contour(mis)

# transform the coordinates to geojson
geojson_contour = countour_to_geojson(contour=contour,
                                      save=True,
                                      name=f"{path}/results/contour")

# Read the coordinates csv coming from SCiLS
coord_scils = pd.read_csv(f"{path}/maldi/coord.csv",
                          skiprows=8,
                          sep=';')

# Flip the y axis
coord_scils["y"] = coord_scils["y"].max() - coord_scils["y"]

# Align the MALDI-MSI spectrum x,y coordinates with the MALDI image contour
coord_maldi = align_coord_contour(coord=coord_scils[['x', 'y']].values,
                                  contour=contour,
                                  conserve_dimensions=False)

# Plot the MALDI-MSI spectrum x,y coordinates and the MALDI image contour
if config['plot_pixels_and_contour']:
    # Read the MALDI tif image
    img_maldi = plt.imread(f"{path}/images/alignment/MALDI.tif")

    # Create the results folder
    os.makedirs(f"{path}/results/figures", exist_ok=True)

    # Define the figure size
    figure_size = (img_maldi.shape[1] // config['plot_compression'], img_maldi.shape[0] // config['plot_compression'])

    # Visualize the MALDI-MSI spectrum x,y coordinates and the MALDI image contour on the MALDI image
    plt.figure(figsize=figure_size, tight_layout=True)
    plt.scatter(coord_maldi[:, 0], coord_maldi[:, 1], s=0.1, alpha=0.5, color='blue', label='Coordinates')
    plt.scatter(contour[:, 0], contour[:, 1], s=0.1, alpha=0.8, color='red', label='Contour')
    plt.imshow(img_maldi, cmap='gray', alpha=0.7)
    plt.axis('equal')
    plt.axis('off')
    plt.title('MALDI-MSI x,y coordinates and image contour')
    plt.legend()
    plt.savefig(f"{path}/results/figures/coord_maldi.png")
    plt.close()

# Transform the x,y coordinates into pixels in the form of geojson text
geojson = coord_to_geojson(x_coord=coord_maldi[:, 0],
                           y_coord=coord_maldi[:, 1],
                           save=True,
                           name=f"{path}/results/pixels_maldi")
