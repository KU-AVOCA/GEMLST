# GEMNDVI (Greenland Ecosystem Monitoring Normalized Difference Vegetation Index)

[![DOI](https://zenodo.org/badge/924540924.svg)](https://doi.org/10.5281/zenodo.14802659)

## Table of Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [GEMNDVI_MODIS](#gemndvi_modis)
  - [Data Sources](#data-sources)
  - [Algorithm Workflow](#algorithm-workflow)
  - [Output Description](#output-description)
- [GEMNDVI_Sentinel2](#gemndvi_sentinel2)
  - [Data Sources](#data-sources-1)
  - [Algorithm Workflow](#algorithm-workflow-1)
  - [Output Description](#output-description-1)
- [Comments and Future plans](#comments-and-future-plans)
- [Author](#author)
- [Last Updated](#last-updated)

## Overview
GEMNDVI generates MODIS and Sentinel-2 based vegetation index products for Greenland. Two versions are available:
- GEMNDVI_MODIS: Daily vegetation index product using MODIS Terra and Aqua sensors (250m resolution) for land areas.
- GEMNDVI_Sentinel2: High-resolution vegetation index product using Sentinel-2 multispectral imagery (10m resolution) for detailed analysis of vegetated areas.

GEMNDVI_MODIS provides consistent long-term coverage (2000-present) with moderate spatial resolution, useful for tracking large-scale vegetation changes across Greenland's ice-free areas. An Earth Engine web app is available to visualize the daily NDVI dataset for Greenland - [GEMNDVI-MODIS-Viewer](https://ku-gem.projects.earthengine.app/view/gemndvimodis).

GEMNDVI_Sentinel2 offers high-resolution vegetation monitoring (2019-present) with advanced cloud masking using Cloud Score+ algorithms. The dataset is particularly useful for detailed vegetation analysis. Tiff images are generated for key study areas like Kobbefjord, Zackenberg, and Disko Island. An Earth Engine web app is also available to inspect and visualize the high-resolution NDVI dataset - [GEMNDVI-Sentinel2-Viewer](https://ku-gem.projects.earthengine.app/view/gemndvisentinel2).

## Requirements
- Google Earth Engine account
- Access to the following datasets:
  - `MODIS/061/MOD09GQ` (Terra Surface Reflectance)
  - `MODIS/061/MYD09GQ` (Aqua Surface Reflectance)
  - `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2 Surface Reflectance)
  - `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` (Cloud Score+ for Sentinel-2)
  - `OSU/GIMP/2000_ICE_OCEAN_MASK` (GIMP Mask)

# GEMNDVI_MODIS
## Data Sources
- **MODIS Terra & Aqua**: Primary surface reflectance measurements (250m resolution)
  - Daily observations from both sensors
  - Quality control based on QC_250m band
- **GIMP Mask**: Ice/ocean masking to isolate vegetated land areas

## Algorithm Workflow
1. **Data Preprocessing**
   - Apply quality control to MODIS Terra and Aqua data
   - Extract high-quality pixels using QC band bit information
   - Apply Greenland land mask (excluding ice and ocean areas)

2. **NDVI Calculation**
   - Calculate NDVI for MODIS Terra (MOD09GQ) using Red and NIR bands
   - Calculate NDVI for MODIS Aqua (MYD09GQ) using Red and NIR bands
   - Combine Terra and Aqua NDVI values through daily averaging

3. **Output Generation**
   - Create daily NDVI composites
   - Export calibrated NDVI maps in Greenland Polar Stereographic projection

## Output Description
The script [GEMNDVI_MODIS](GEMNDVI/GEMNDVI_MODIS.js) generates GeoTIFF files with the following attributes:
- **NDVI**: Normalized Difference Vegetation Index
  - Data exported as float values
  - Valid range (-1 to 1)
  - Nodata pixels are set to NaN

The output is available at 250m spatial resolution in EPSG:3413 projection (Greenland Polar Stereographic).

# GEMNDVI_Sentinel2
## Data Sources
- **Sentinel-2 MSI**: High-resolution multispectral imagery (10m resolution)
  - Red (Band 4) and NIR (Band 8) for NDVI calculation
  - Scene Classification Layer (SCL) for additional quality control
- **Cloud Score+**: Advanced cloud probability scores for cloud masking
- **GIMP Mask**: Ice/ocean masking to isolate vegetated land areas

## Algorithm Workflow
1. **Data Preprocessing**
   - Link Sentinel-2 images with Cloud Score+ data
   - Apply cloud masking using Cloud Score+ probability thresholds
   - Remove saturated or defective pixels using SCL band
   - Apply Greenland land mask (excluding ice and ocean areas)
   - Scale reflectance values to 0-1 range

2. **NDVI Calculation**
   - Calculate NDVI using Red (B4) and NIR (B8) bands
   - Create daily composites when multiple images are available

3. **Output Generation**
   - Scale NDVI values to int16 range (multiply by 10000)
   - Set nodata value to -32768
   - Export calibrated NDVI maps in Greenland Polar Stereographic projection.

## Output Description
The output from the script [GEMNDVI_Sentinel2](GEMNDVI/GEMNDVI_Sentinel2.js) is:
- **NDVI**: High-resolution (10m) vegetation index
  - Scaled to int16 range (-32768 to 32767)
  - Values must be divided by 10000 to get actual NDVI values (-1 to 1)
  - Nodata pixels are set to -32768

The output is available at 10m spatial resolution in EPSG:3413 projection (Greenland Polar Stereographic).
  
## Author
[Andreas Westergaard-Nielsen](mailto:awn@ign.ku.dk) and [Shunan Feng](mailto:shf@ign.ku.dk).

## Last Updated
2025-04-28