#%% 
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path

#%%
imfolder = "D:\Test_ERA5Land500m"
imfiles = sorted(Path(imfolder).rglob("*.nc"))
sites = [
    {"id": "Kobbefjord_M500", "longitude": -51.37199020385742, "latitude": 64.12248229980469},
    {"id": "Disko_AWS2",     "longitude": -53.514129638671875, "latitude": 69.25348663330078},
    {"id": "Zackenberg_M2",  "longitude": -20.563194274902344, "latitude": 74.46549224853516},
    {"id": "Zackenberg_M3",  "longitude": -20.459354400634766, "latitude": 74.50310516357422},
    {"id": "Zackenberg_M4_30min", "longitude": -20.552143096923828, "latitude": 74.47307586669922},
]

aws_df = pd.DataFrame(sites)

#%%
imfile = imfiles[0]

# Open the dataset
ds = xr.open_dataset(imfile)

# Extract the temperature data
t2m = ds['t2m']  # dims (time, zlev, Y, X)

# Get the 2D coordinate arrays
Y_2d = ds['Y'].values  # shape (Y, X)
X_2d = ds['X'].values  # shape (Y, X)

# Find nearest grid indices for each requested (lat, lon)
grid_indices = []
for lat, lon in zip(aws_df['latitude'].values, aws_df['longitude'].values):
    # Calculate the squared distance to find the nearest point
    dist2 = (Y_2d - lat) ** 2 + (X_2d - lon) ** 2
    # Find the 2D index of the minimum distance
    min_idx = np.unravel_index(dist2.argmin(), dist2.shape)
    grid_indices.append(min_idx)

# Extract temperature values for each site
temps_list = []
for y_idx, x_idx in grid_indices:
    # Extract temperature at this grid point: dims (time, zlev)
    temp_at_point = t2m[:, :, y_idx, x_idx]
    
    # If zlev is a singleton, drop it to get (time,)
    if 'zlev' in temp_at_point.dims and temp_at_point.sizes['zlev'] == 1:
        temp_at_point = temp_at_point.isel(zlev=0)
    
    temps_list.append(temp_at_point.values)

# Stack into a 2D array: shape (time, sites)
temps = np.column_stack(temps_list)

# Create DataFrame
if 'time' in t2m.dims:
    temps_df = pd.DataFrame(temps, index=t2m['time'].values, columns=aws_df['id'])
else:
    temps_df = pd.DataFrame([temps], columns=aws_df['id'])

ds.close()

# Convert temperature from Kelvin to Celsius
temps_df = temps_df - 273.15

# Check the resulting DataFrame
print(temps_df.head())
print("\nDataFrame shape:", temps_df.shape)
print("\nDataFrame info:")
print(temps_df.info())

# %%
