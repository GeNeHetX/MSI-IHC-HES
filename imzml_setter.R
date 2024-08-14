library(Cardinal)
library(yaml)

# Read the hyperparameters from the config file
config <- read_yaml("config.yaml")

# Path to the data and results
path <- sprintf("%s/%s", config$path_to_data, config$lame)

# Load the detected peaks
mse_peaks <- readMSIData(sprintf("%s/results/mse_peaks.imzML", path))

# Rename the run factor with the name of the lame
mse_peaks$run <- factor(mse_peaks$run,
                        levels = unique(mse_peaks$run),
                        labels = config$lame)

# Set the centroided flag to TRUE
centroided(mse_peaks) <- TRUE

# Load the IHC pixels features densities
ihc_df <- read.csv(sprintf("%s/results/pixels_maldi_warped_density_df.csv", path))

# Add the IHC features to the mse_peaks object
for (feature in colnames(ihc_df)[2:length(ihc_df)]) {
  mse_peaks[[feature]] <- ihc_df[[feature]]
}

# Save the detected peaks with the IHC features
writeMSIData(mse_peaks,
             sprintf("%s/results/mse_densities.imzML", path))