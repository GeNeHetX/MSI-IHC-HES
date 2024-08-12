library(Cardinal)
library(yaml)

# Read the hyperparameters from the config file
config <- read_yaml("config.yaml")

# Path to the data and results
path <- sprintf("%s/%s", config$path_to_data, config$lame)

# Read the imzML + ibd object
mse <- readMSIData(sprintf("%s/maldi/mse.imzML", path))

# # Compute the mean intensity of each m/z value
# mse <- mse |>
#   summarizeFeatures(stat = c(Mean = "mean"),
#                     BPPARAM = MulticoreParam())

# Normalize the data and reduce the baseline
mse_processed <- mse |>
  normalize(method = config$normalization_method) |>  # Normalize the data
  reduceBaseline(method = config$base_line_method) |>  # Reduce the baseline
  process(BPPARAM = MulticoreParam())

# # Compute the mean intensity of each m/z value in the processed data
# mse_processed <- mse_processed |>
#   summarizeFeatures(stat = c(Mean_proc = "mean"),
#                     BPPARAM = MulticoreParam())

# Create the directory for the figures if it does not exist
dir.create(sprintf("%s/results", path), showWarnings = FALSE)

# Save the processed data
writeMSIData(mse_processed,
             file = sprintf("%s/results/mse_processed.imzML", path))