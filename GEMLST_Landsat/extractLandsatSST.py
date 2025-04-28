


'''
# extractLandsatSST.py
This script extracts Sea Surface Temperature (SST) values from Landsat satellite imagery
at specific locations and times defined in a CSV file and compares them with in-situ measurements.
## Functionality
- Reads a CSV file containing in-situ ocean temperature measurements with location, date, and ID
- Creates a unique identifier for each measurement
- Extracts Landsat SST values for each location and date by:
    - Applying cloud masking to Landsat imagery
    - Scaling thermal bands to temperature values
    - Standardizing band names across different Landsat sensors (4, 5, 7, 8, 9)
    - Calculating mean SST values when multiple images exist for a date
- Converts Landsat temperatures from Kelvin to Celsius
- Saves the original data with added Landsat SST values to a new CSV file

## Processing Steps
1. Load and prepare input CSV data
2. For each row in the dataset:
     - Create a point geometry at the specified coordinates
     - Filter Landsat collections by date and location
     - Apply cloud masking and band scaling 
     - Extract SST values at the specified point
     - Convert temperature from Kelvin to Celsius
     - Store the result in the dataframe
3. Save the updated dataframe with Landsat SST values to a new CSV file'
'''
#%%
import pandas as pd
import ee
import geemap
import numpy as np
# %%
csvpath = "/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/Sea/OceanSurfaceTemp.csv"
df = pd.read_csv(csvpath)
df['Date'] = pd.to_datetime(df['Date'])
df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
df['unique_id'] = df['Dataset'] + '_' + df['ID'].astype(str) + '_' + df['Date']
df['LandsatSST'] = np.nan
# %%
Map = geemap.Map()
Map

#%% functions 
def maskL8sr(image):
    """
    Apply cloud masking to Landsat 8/9 imagery using the QA_PIXEL band.
    
    Parameters:
        image (ee.Image): Landsat image to mask
        
    Returns:
        ee.Image: Cloud-masked image with properly scaled band values
    """
    # Get the QA band for cloud masking
    qaMask = image.select('QA_PIXEL').bitwiseAnd(int('11111', 2)).eq(0)
    saturationMask = image.select('QA_RADSAT').eq(0)  # Mask saturated pixels
    
    # Apply scaling factors to convert DN to reflectance or temperature 
    # opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2).updateMask(qaMask).updateMask(saturationMask)
    thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0).updateMask(qaMask).updateMask(saturationMask)

    # Return the masked and scaled image
    return image.addBands(thermalBands, None, True)

# the Landsat 4, 5, 7 Collection 2
def maskL457sr(image):
  # Bit 0 - Fill
  # Bit 1 - Dilated Cloud
  # Bit 2 - Unused
  # Bit 3 - Cloud
  # Bit 4 - Cloud Shadow
  qaMask = image.select('QA_PIXEL').bitwiseAnd(int('11111', 2)).eq(0)
  saturationMask = image.select('QA_RADSAT').eq(0)

  # Apply the scaling factors to the appropriate bands.
  # opticalBands = image.select('SR_B.')
  # opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
  thermalBand = image.select('ST_B6').multiply(0.00341802).add(149.0).updateMask(qaMask).updateMask(saturationMask)

  # Replace the original bands with the scaled ones and apply the masks.
  return image.addBands(thermalBand, None, True)

def renameOli(img):
    """
    Rename Landsat 8/9 bands to standardized names for easier processing.
    
    Parameters:
        img (ee.Image): Landsat image with original band names
        
    Returns:
        ee.Image: Image with renamed bands
    """
    return img.select(
        ['ST_B10',   'QA_PIXEL', 'QA_RADSAT'],
        ['SST',      'QA_PIXEL', 'QA_RADSAT']
    )
# Function to get and rename bands of interest from ETM+, TM.
def renameEtm(img):
  return img.select(
    ['ST_B6', 'QA_PIXEL', 'QA_RADSAT'], #,   'QA_PIXEL', 'QA_RADSAT'
    ['SST',   'QA_PIXEL', 'QA_RADSAT']) #, 'QA_PIXEL', 'QA_RADSAT'

def prepOli(img):
    """
    Prepare Landsat 8/9 imagery by applying cloud mask and renaming bands.
    
    Parameters:
        img (ee.Image): Raw Landsat image
        
    Returns:
        ee.Image: Processed image with cloud masking and standardized band names
    """
    orig = img
    img = maskL8sr(img)  # Apply cloud masking
    img = renameOli(img)  # Rename bands to standardized names

    # Preserve original metadata
    return ee.Image(img.copyProperties(orig, orig.propertyNames()))

def prepEtm(img):
    """
    Prepare Landsat 4/5/7 imagery by applying cloud mask and renaming bands.
    
    Parameters:
        img (ee.Image): Raw Landsat image
        
    Returns:
        ee.Image: Processed image with cloud masking and standardized band names
    """
    orig = img
    img = maskL457sr(img)  # Apply cloud masking
    img = renameEtm(img)  # Rename bands to standardized names

    # Preserve original metadata
    return ee.Image(img.copyProperties(orig, orig.propertyNames()))

def ee_array_to_df(arr, list_of_bands):
    """Transforms client-side ee.Image.getRegion array to pandas.DataFrame."""
    df = pd.DataFrame(arr)

    # Rearrange the header.
    headers = df.iloc[0]
    df = pd.DataFrame(df.values[1:], columns=headers)

    # Remove rows without data inside.
    df = df[['longitude', 'latitude', 'time', *list_of_bands]]

    # Convert the data to numeric values.
    for band in list_of_bands:
        df[band] = pd.to_numeric(df[band], errors='coerce')

    # Convert the time field into a datetime.
    # df['datetime'] = pd.to_datetime(df['time'], unit='ms')

    # Keep the columns of interest.
    df = df[['time', 'longitude', 'latitude', *list_of_bands]]

    return df
# %%
for i in range(0, len(df)):
    print(f"Processing {i+1}/{len(df)}: {df.iloc[i]['unique_id']}")
    
    poi = ee.Geometry.Point(df.iloc[i]['Lon'], df.iloc[i]['Lat'])
    # Map.addLayer(poi, {}, df.iloc[i]['unique_id'])

    # Extract date components
    date_str = df.iloc[i]['Date']
    year, month, day = date_str.split('-')
    year = int(year)
    month = int(month)
    day = int(day)

    day_step = 0
    # Create ee.Date object for filtering with ±8 days window
    start_date = ee.Date.fromYMD(year, month, day).advance(-1 * day_step, 'day')
    end_date = ee.Date.fromYMD(year, month, day).advance(day_step + 1, 'day')
    print(f"Processing data for: {year}-{month}-{day}")

    # Create filter for image collection
    colFilter = ee.Filter.And(
        ee.Filter.bounds(poi), 
        ee.Filter.date(start_date, end_date)
    )

    oliCol = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filter(colFilter) \
            .map(prepOli) 
    oli2Col = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
            .filter(colFilter) \
            .map(prepOli)
    etmCol = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
            .filter(colFilter) \
            .map(prepEtm)
    tmCol = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') \
            .filter(colFilter) \
            .map(prepEtm)
    # Combine all collections
    landsatCol = oliCol.merge(oli2Col).merge(etmCol).merge(tmCol)
    if landsatCol.size().getInfo() == 0:
        print("No images found for this date.")
        continue

    # extract the data
    list_of_bands = ['SST']
    arr = landsatCol.getRegion(poi, 30).getInfo()
    df_arr = ee_array_to_df(arr, list_of_bands)
    
    # add SST to the df
    df.at[i, 'LandsatSST'] = df_arr['SST'].mean() - 273.15
    # print the result
    print(f"SST is : {df.iloc[i]['Temp']}")
    print(f"Landsat SST is : {df.iloc[i]['LandsatSST']}")
    
# %%
csvNewpath = f"/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/Sea/OceanSurfaceTemp_Landsat{day_step}.csv"
df.to_csv(csvNewpath, index=False)
# %%
