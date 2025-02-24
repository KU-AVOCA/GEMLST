#%% load packages
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
#%%
filepath = "/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/CARRA/CARRA.grib"
ds = xr.open_dataset(filepath, engine='cfgrib', backend_kwargs={'indexpath': ''}, chunks='auto')


#%%
# output_path = "/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/CARRA/CARRA_grib2nc.nc"
# ds.to_netcdf(output_path)
#%%
def extract_carra_data(ds, aws_df):
    """
    Extract skin temperature time series for AWS locations.
    
    Parameters:
    -----------
    ds : xarray.Dataset
        CARRA dataset with skt variable
    aws_df : GeoDataFrame
        DataFrame containing AWS locations with 'lat', 'lon', and 'awsname' columns
    
    Returns:
    --------
    pandas.DataFrame
        Time series of skin temperature for each AWS location
    """
    # Initialize empty dictionary to store time series for each AWS
    skt_series = {}
    
    # Convert CARRA dataset to GeoDataFrame
    carra_points = ds.stack(point=('y', 'x')).reset_index('point')
    carra_points['lon'] = ds['longitude'].stack(point=('y', 'x'))
    carra_points['lat'] = ds['latitude'].stack(point=('y', 'x'))
    carra_points = carra_points.to_dataframe().reset_index()
    carra_points = gpd.GeoDataFrame(carra_points, geometry=gpd.points_from_xy(carra_points.lon, carra_points.lat), crs="EPSG:4326")
    
    # Extract time series for each AWS location
    for _, aws in aws_df.iterrows():
        # Find the nearest CARRA grid point
        tree = cKDTree(carra_points[['lat', 'lon']])
        _, index = tree.query([aws['lat'], aws['lon']])
        nearest_point = carra_points.iloc[index]
        
        # Select the nearest grid point from the original dataset
        ds_point = ds.sel(y=nearest_point['y'], x=nearest_point['x'])
        
        # Extract skt time series and name it with AWS name
        ts = ds_point['skt'].to_series()
        ts.name = aws['awsname']
        skt_series[aws['awsname']] = ts
        
        print(f"Extracted time series for {aws['awsname']}")
    
    # Combine all time series into a single DataFrame
    df = pd.DataFrame(skt_series)
    
    # Reset index to make time a column
    df = df.reset_index().rename(columns={'index': 'time'})
    
    return df

# Extract data
carra_data = extract_carra_data(ds, awslist)

# Save to CSV (optional)
output_path = "/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/CARRA/CARRA_aws_skt.csv"
carra_data.to_csv(output_path, index=False)

# %%
