# GEM Remote Sensing Products

[![DOI](https://zenodo.org/badge/924540924.svg)](https://doi.org/10.5281/zenodo.14802659)

## Overview

This repository contains remote sensing products developed for the Greenland Ecosystem Monitoring (GEM) program. The products include surface temperature and vegetation indices derived from various satellite sensors, covering the entire Greenland.

Currently, the repository contains two main product lines:

1. **GEMLST** - Greenland Ecosystem Monitoring Land Surface Temperature
2. **GEMNDVI** - Greenland Ecosystem Monitoring Normalized Difference Vegetation Index

## Product Descriptions

### GEMLST

GEMLST provides calibrated land surface temperature datasets for Greenland with two main variations:
- **GEMLST_MODIS**: Daily 1km resolution product combining MODIS Terra/Aqua and ERA5-Land data
- **GEMLST_Landsat**: High-resolution (30m) calibrated product for both land and water surfaces

For detailed information, see the [GEMLST README](GEMLST.md).

### GEMNDVI

GEMNDVI provides vegetation index datasets for Greenland's ice-free areas with two main variations:
- **GEMNDVI_MODIS**: Daily 250m resolution product combining MODIS Terra and Aqua data
- **GEMNDVI_Sentinel2**: High-resolution (10m) product using Sentinel-2 imagery with Cloud Score+

For detailed information, see the [GEMNDVI README](GEMNDVI.md).

## Web Applications

All products are available through interactive Google Earth Engine web applications:

- [GEMLST-MODIS](https://ku-gem.projects.earthengine.app/view/gemlst-viewer) - Visualize daily land surface temperature
- [GEMEST_Landsat](https://ku-gem.projects.earthengine.app/view/gemestlandsat) - Explore high-resolution land surface temperature
- [GEMNDVI-MODIS-Viewer](https://ku-gem.projects.earthengine.app/view/gemndvimodis) - Visualize daily vegetation index
- [GEMNDVI-Sentinel2-Viewer](https://ku-gem.projects.earthengine.app/view/gemndvisentinel2) - Explore high-resolution vegetation index


## Key Study Areas

The products have been extensively tested and validated at key Greenland Ecosystem Monitoring sites:
- Kobbefjord (Southwest Greenland)
- Zackenberg (Northeast Greenland)
- Disko Island (West Greenland)

## Authors

[Andreas Westergaard-Nielsen](mailto:awn@ign.ku.dk) and [Shunan Feng](mailto:shf@ign.ku.dk).

## Acknowledgments

This work is part of the Greenland Ecosystem Monitoring (GEM) program, funded by the Danish Ministry of Energy, Utilities and Climate. The project is hosted by the Department of Geosciences and Natural Resource Management, University of Copenhagen. It is also supported by Villum Foundation (project No. 42069).

## Links

- [GEM Program](https://g-e-m.dk/)
- [GitHub Repository](https://github.com/KU-AVOCA/GEMLST)

## Last Updated
2025-04-28