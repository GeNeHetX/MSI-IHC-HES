library(Cardinal)
library(yaml)

# Read the hyperparameters from the config file
config <- read_yaml("config.yaml")

# Path to the data and results
path <- sprintf("%s/%s", config$path_to_data, config$lame)

# Load the processed data as an imzML file
mse_processed <- readMSIData(sprintf("%s/results/mse_processed.imzML", path))

# Detect the peaks
mse_peaks <- mse_processed |>
  peakProcess(method = config$peak_pick_method,
              SNR = config$signal_to_noise,
              tolerance = config$peak_pick_tolerance,
              units = config$units,
              filterFreq = config$filtered_frequency,
              BPPARAM = MulticoreParam())

# Save the detected peaks
writeMSIData(mse_peaks,
             sprintf("%s/results/mse_peaks.imzML", path))

# Extract the spectra
spectrum <- spectra(mse_peaks)

# Rename the rows
rownames(spectrum) <- mz(mse_peaks)

# Rotate the spectrum matrix so that the m/z values are the features
spectrum <- t(spectrum)

# Save the spectrum matrix as a CSV file
write.csv(as.matrix(spectrum),
          sprintf("%s/results/mse_peaks.csv", path))

# Create the directory for the figures if it does not exist
dir.create(sprintf("%s/results/figures", path), showWarnings = FALSE)

# Save the plot
png(filename = sprintf("%s/results/figures/mse_peaks.png", path),
    width = 2000,
    height = 500)
plot(mse_peaks)
dev.off()