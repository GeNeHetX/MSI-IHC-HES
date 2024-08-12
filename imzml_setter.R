library(Cardinal)
library(yaml)

# Read the hyperparameters from the config file
config <- read_yaml("config.yaml")

# Path to the data and results
path <- sprintf("%s/%s", config$path_to_data, config$lame)

# Load the detected peaks
mse_peaks <- readMSIData(sprintf("%s/results/mse_peaks.imzML", path))

# Load the IHC pixels features densities
ihc <- read.csv(sprintf("%s/results/pixels_maldi_warped_density_df.csv", path))

# Add the ihc features to the mse_peaks object
for (feature in colnames(ihc)[2:length(ihc)]) {
  mse_peaks[[feature]] <- ihc[[feature]]
}

# Save the detected peaks with the IHC features
writeMSIData(mse_peaks,
             sprintf("%s/results/mse_peaks.imzML", path))