# GEMLST (Greenland Ecosystem Monitoring Land Surface Temperature)

## Overview
GEMLST generates a daily gapless land surface temperature dataset for Greenland by combining MODIS and ERA5-Land data. It handles common challenges like cloud cover and data gaps through a sophisticated calibration approach.

## Requirements
- Google Earth Engine account
- Access to the following datasets:
  - MODIS/061/MOD11A1 (Terra LST)
  - MODIS/061/MYD11A1 (Aqua LST) 
  - ECMWF/ERA5_LAND/HOURLY
  - OSU/GIMP/2000_ICE_OCEAN_MASK

## Data Sources
- **MODIS Terra & Aqua**: Primary LST measurements (1km resolution)
  - Day and night observations
  - Quality control based on QC bands
- **ERA5-Land**: 
  - Surface net solar radiation (calibration)
  - Skin temperature (gap-filling)
- **GIMP Mask**: Ice/ocean masking

## Algorithm Workflow
1. **Data Preprocessing**
   - Apply quality control to MODIS data
   - Convert units to Celsius
   - Apply Greenland ice mask

2. **LST Calibration**
   - Determine data availability pattern
   - Apply calibration coefficients based on:
     - Available MODIS observations
     - Surface net solar radiation
   - Fill gaps using ERA5-Land data

3. **Output Generation**
   - Create daily composites
   - Export calibrated LST maps

## Output Description
The script generates GeoTIFF files with two bands:
1. **Corrected_LST**: Calibrated land surface temperature (°C)
2. **Available_Pattern**: Data source flag:
 The flag uses a binary system to represent data availability from 5 different sources:
    - Binary to Decimal Example:
    - MODIS Terra Day   = 1000 (binary) = 8 (decimal)
    - MODIS Terra Night = 0100 (binary) = 4 (decimal) 
    - MODIS Aqua Day    = 0010 (binary) = 2 (decimal)
    - MODIS Aqua Night  = 0001 (binary) = 1 (decimal)
    - ERA5-Land         = 0000 (binary) = 0 (decimal)
    
For example, a flag value of 15 indicates that all 4 MODIS data sources are available.

    | Flag Value | Binary | Available Data               |
    |------------|--------|------------------------------|
    | 15         | 1111   | All 4 MODIS data available   |
    | 8          | 1000   | Only Terra Day               |
    | 12         | 1100   | Terra Day + Terra Night      |
    | 10         | 1010   | Terra Day + Aqua Day         |
    | 0          | 0000   | No data (uses ERA5)          |

## Usage
1. Open code editor in Google Earth Engine and copy the script from [GreenlandSurfTGEE.js](GreenlandSurfTGEE.js).
2. Set your desired time period:
```javascript
var startDate = ee.Date.fromYMD(2024, 1, 1);
var endDate = ee.Date.fromYMD(2024, 1, 31);
```

Finally, [GEMLST.js](GEMLST.js) deploys the script into an Earth Engine web app, which allows users to interact with the script and view the daily gapless surface temperature dataset for Greenland.
(Currently not available due to limitations to generate the time series chart in the Earth Engine web app.)
## Author
Shunan Feng (shf@ign.ku.dk)

## Last Updated
2025-01-30