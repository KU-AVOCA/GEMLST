#%% 
import os
import glob
import geopandas as gpd
import xarray as xr
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
#%% aws coordinates
awslist = {
    'Kobbefjord_M500': {
        'lat': 64.12248229980469,
        'lon': -51.37199020385742,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/2_Kobbefjord/3_ClimateData/M500_10.17897_7MSK-4190/M500_10.17897_7MSK-4190_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'SurfaceTemperature (°C)'
    },
    'Disko_T1': {
        'lat': 69.27300262451172,
        'lon': -53.479400634765625,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/T1-Temperature_125m_10.17897_ZHA1-YC59/T1-Temperature_125m_10.17897_ZHA1-YC59_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground surface temperature_°C'
    },
    'Disko_T2': {
        'lat': 69.28909301757812,
        'lon': -53.43281936645508,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/T2-Temperature_830m_10.17897_1QY7-Q102/T2-Temperature_830m_10.17897_1QY7-Q102_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground surface temperature_°C'
    },
    'Disko_T3': {
        'lat': 69.2767105102539,
        'lon': -53.45709991455078,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/T3-Temperature_400m_10.17897_CFES-BX22/T3-Temperature_400m_10.17897_CFES-BX22_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground surface temperature_°C'
    },
    'Disko_T4': {
        'lat': 69.25126647949219,
        'lon': -53.49897003173828,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/T4-Temperature_1m_10.17897_QDGE-TH28/T4-Temperature_1m_10.17897_QDGE-TH28_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground surface temperature_°C'
    },
    'Disko_AWS2': {
        'lat': 69.25348663330078,
        'lon': -53.514129638671875, 
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/AWS2-Meteorology_10.17897_CSZT-F010/AWS2-Meteorology_10.17897_CSZT-F010_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground temperature_°C'
    },
    'Zackenberg_M2': {
        'lat': 74.46549224853516,
        'lon': -20.563194274902344,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/4_Zackenberg/1_ClimateData/M2_10.17897_7WAM-6143/M2_10.17897_7WAM-6143_data.txt',
        'temp_unit': 'kelvin',
        'time_zone': 'UTC',
        'temp_var': 'Temp ground °K'
    },
    'Zackenberg_M3': {
        'lat': 74.50310516357422,
        'lon': -20.459354400634766,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/4_Zackenberg/1_ClimateData/M3_10.17897_7JXY-VX51/M3_10.17897_7JXY-VX51_data.txt',
        'temp_unit': 'kelvin',
        'time_zone': 'UTC',
        'temp_var': 'Temp ground °K'
    },
    'Zackenberg_M4': {
        'lat': 74.47307586669922,
        'lon': -20.552143096923828,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/4_Zackenberg/1_ClimateData/M4_30min_10.17897_ZNKG-K687/M4_30min_10.17897_ZNKG-K687_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC',
        'temp_var': 'Surface temperature avg °C'
    }
}
awslist = gpd.GeoDataFrame(awslist).T
awslist.index.name = 'awsname'
awslist = awslist.reset_index()
awslist['geometry'] = gpd.points_from_xy(awslist.lon, awslist.lat)

#%% load ERA5 data
imfolder = "/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/ERA5/JAXA/untar"
imfile = "DI30m/t2m/t2m_elvcorr_2024_daily.nc"
ds = xr.open_dataset(os.path.join(imfolder, imfile))

# First, print the structure of your dataset to understand its dimensions and coordinates
print("Dataset dimensions:", ds.dims)
print("Dataset coordinates:", list(ds.coords))

# Function to find nearest grid point indices (not coordinate values)
def find_nearest_grid_indices(ds, lat, lon):
    # Get grid coordinates
    xx = ds.X.values
    yy = ds.Y.values
    
    # Find nearest grid indices
    x_idx = np.abs(xx - lon).argmin()  # Note: using lon for X
    y_idx = np.abs(yy - lat).argmin()  # Note: using lat for Y
    
    return x_idx, y_idx

# Extract for each AWS station
aws_ts_dict = {}

for idx, aws in awslist.iterrows():
    aws_name = aws['awsname']
    print(f"Processing {aws_name}...")
    
    try:
        # Find nearest grid point indices
        x_idx, y_idx = find_nearest_grid_indices(ds, aws.lat, aws.lon)
        
        # Get the actual coordinate values for reference
        nearest_x = ds.X.values[x_idx]
        nearest_y = ds.Y.values[y_idx]
        print(f"For {aws_name}, nearest grid point: X={nearest_x}, Y={nearest_y}")
        
        # Extract temperature using isel (index-based selection)
        temp_values = []
        for time_idx, time_step in enumerate(ds.time.values):
            temp = ds.isel(time=time_idx, X=x_idx, Y=y_idx, zlev=0).t2m.values.item()
            temp_values.append(temp)
        
        # Create time series for the AWS
        aws_ts = pd.Series(temp_values, index=ds.time.values, name=aws_name)
        aws_ts_dict[aws_name] = aws_ts
        
        print(f"Successfully extracted {len(aws_ts)} temperature values for {aws_name}")
    
    except Exception as e:
        print(f"Error processing {aws_name}: {e}")

# Combine all time series into a DataFrame
aws_ts_df = pd.DataFrame(aws_ts_dict)

# Save to CSV
output_path = "/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/ERA5/era5_aws_t2m.csv"
aws_ts_df.to_csv(output_path)
print(f"Saved time series data to {output_path}")

# %%
