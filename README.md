# GEMLST
Greenland Ecosystem Monitoring - Greenland Surface Temperature Gapless Dataset

This script creates a daily gapless surface temperature dataset for Greenland using MODIS Terra, MODIS Aqua, and ERA5 Land data. It calibrates the temperature data using a set of coefficients and the surface net solar radiation data from ERA5 Land, and fills gaps in the MODIS LST data using ERA5 Land skin temperature data.

## Steps

### 1. Define the Region of Interest, Mask, and Time Period
- **Region of Interest**: Defined as a polygon covering Greenland.
- **Mask**: Applied to exclude ocean areas using the 'OSU/GIMP/2000_ICE_OCEAN_MASK' dataset.
- **Time Period**: Set from January 1, 2024, to January 31, 2024. Or you can set your own time period.

### 2. Load MODIS Terra and Aqua LST Data
- **Load Data**: Load the MODIS Terra and Aqua Land Surface Temperature (LST) data.
- **Quality Control**: Apply a quality control function to filter out low-quality data based on the QC_Day band.

### 3. Apply Quality Control to the LST Data
- **Quality Control Function**: A function to extract and apply quality control based on specific bits in the QC_Day and QC_Night bands.

### 4. Calibrate the LST Data Using ERA5 Land Data
- **Calibration**: Calibrate the LST data using coefficients and surface net solar radiation data from ERA5 Land.

### 5. Fill Gaps in the LST Data Using ERA5 Land Skin Temperature Data
- **Gap Filling**: Fill gaps in the MODIS LST data using ERA5 Land skin temperature data.

### 6. Generate the Final Gapless Surface Temperature Dataset
- **Final Dataset**: Generate the final gapless surface temperature dataset by combining the calibrated LST data and the gap-filled data.

### 7. Export the Final Dataset to Google Drive
- **Export**: Export the final dataset to Google Drive for further analysis and use.

## Author
Shunan Feng (shf@ign.ku.dk)

## Last Updated
2025-01-30