# The script extracts temperature data from ERA5 Land NetCDF files at the locations 
# of PROMICE AWS stations for a specific time range. 
# It reads the ERA5 files, identifies the nearest grid points to the PROMICE station locations, 
# and saves the extracted temperature data into a CSV file. 

# MAKE SURE TO ADJUST THE DATE RANGE MANUALLY BOTH IN THE MARKERS FOR ERA5 FILES!

#%% 
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path

#%% IMPORT DATA

# ERA5 Data: 
imfolder = "/media/sirsimsius/WD3TB/ERA5Land500m/t2m/"
imfiles = sorted(Path(imfolder).glob("*.nc"))

# PROMICE DATA (dataset of each PROMICE aws' yearly averaged position, cols: aws, year, lat, lon)
path = "/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/PROMICE/output/PROMICE_yearly_avg_positions.csv" ## UPDATE
promice_df = pd.read_csv(path)
promice_dict = promice_df.set_index(['aws', 'year'])[['lat', 'lon']].to_dict('index')

station_list = promice_df['aws'].unique()
# print(station_list)


#%% DEFINE THE TIME RANGE OF INTEREST AND SELECT FILES

# gather and sort all NetCDF files under imfolder
imfiles = sorted(Path(imfolder).rglob("*.nc"))

# markers (adjust if you need case-insensitive match or different substrings)
start_marker = "t2m_elvcorr_2007_d232.nc" # 20.08.2007 (= first PROMICE OBS)
end_marker = "t2m_elvcorr_2011_d365.nc" # 31.12.2024

# find first index containing the start marker and last index containing the end marker
start_idx = next((i for i, p in enumerate(imfiles) if start_marker in p.name), None)
end_idx = next((i for i, p in enumerate(imfiles) if end_marker in p.name), None)

if start_idx is None:
    raise FileNotFoundError(f"No file containing '{start_marker}' found under {imfolder}")
if end_idx is None:
    raise FileNotFoundError(f"No file containing '{end_marker}' found under {imfolder}")
if end_idx < start_idx:
    raise ValueError(f"End file '{end_marker}' appears before start file '{start_marker}' in sorted file order")

# slice inclusive range
imfiles = imfiles[start_idx:end_idx + 1]

#%% EXTRACT AND CREATE CSV

### Initialize an empty csv file to store results
csv_path = "/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/ERA5/t2m_at_PROMICE_test2007.csv"
final_df = pd.DataFrame(columns=station_list)


### LOOP THROUGH FILES AND EXTRACT DATA
for imfile in imfiles:

    print(imfile.name)

    # Open the dataset
    ds = xr.open_dataset(imfile)

    # Extract the temperature data
    t2m = ds['t2m']  # dims (time, zlev, Y, X)

    # Get the 2D coordinate arrays
    Y_2d = ds['Y'].values  # shape (Y, X)
    X_2d = ds['X'].values  # shape (Y, X)

    # Extract time information from the filename (format: "t2m_elvcorr_2007_d232.nc")
    date_str = imfile.stem.split('_')[-1].replace('d', '') 
    year = int(imfile.stem.split('_')[2])
    date = pd.to_datetime(f"{year}-{date_str}", format="%Y-%j") # Convert to datetime

    # Create list of stations for this year
    stations_this_year = [aws for (aws, yr) in promice_dict.keys() if yr == year]

    # Create empty arrays for this years data
    temps_list = []
    for aws in station_list: 
        if aws in stations_this_year:
            lat, lon = promice_dict[(aws, year)]['lat'], promice_dict[(aws, year)]['lon']
            # Calculate the squared distance to find the nearest point
            dist2 = (Y_2d - lat) ** 2 + (X_2d - lon) ** 2
            # Find the 2D index of the minimum distance
            y_idx, x_idx = np.unravel_index(dist2.argmin(), dist2.shape)
            # Extract temperature at this grid point: dims (time, zlev)
            temp_at_point = t2m[:, :, y_idx, x_idx].values
            temps_list.append(temp_at_point[0,0])
        else: 
            # Append NaN values for stations not present this year
            temps_list.append(np.nan) # Fill with NaN if station not present this year

    temps_list = [t-273.15 if not np.isnan(t) else np.nan for t in temps_list] # Convert from Kelvin to Celsius
    temps_df = pd.DataFrame([temps_list], index=[date], columns=station_list)

    final_df = pd.concat([final_df, temps_df])

    ds.close()

final_df.to_csv(csv_path)
# %%
