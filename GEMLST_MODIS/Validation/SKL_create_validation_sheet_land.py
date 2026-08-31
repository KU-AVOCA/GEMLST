# %%
import rasterio as rio
import pandas as pd
import numpy as np
from pathlib import Path
from pyproj import Transformer
import os

#%%
# PARAMS

a = input("erda or home?")
if a == "erda":
    imfolder = "/home/jovyan/work/AVOCA/GEM/Production/Gapfilled/"
    aws_path = "/home/jovyan/work/AVOCA/GEM/Development/Data/GEM/"
    rs_lst_path = "/home/jovyan/work/AVOCA/GEM/Development/Anlaysis/Validation_GEMLST/lst_from_GEMLST_at_GEM_long.csv"
    print("Using erda paths.")
elif a == "home": 
    imfolder = "/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Validation/"
    aws_path = "/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Validation/"
    rs_lst_path = "/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Validation/lst_from_GEMLST_at_GEM_long.csv"
    print("Using home paths.")
else: print("Please enter 'erda' or 'home'.")

#%%

imfiles = sorted(Path(imfolder).glob("GEMLST_????????.tiff"))
sites = [
    {"id": "Kobbefjord_M500", "longitude": -51.37199020385742, "latitude": 64.12248229980469},
    {"id": "Disko_AWS2",     "longitude": -53.514129638671875, "latitude": 69.25348663330078},
    {"id": "Zackenberg_M2",  "longitude": -20.563194274902344, "latitude": 74.46549224853516},
    {"id": "Zackenberg_M3",  "longitude": -20.459354400634766, "latitude": 74.50310516357422},
    {"id": "Zackenberg_M4_30min", "longitude": -20.552143096923828, "latitude": 74.47307586669922},
]

aws_df = pd.DataFrame(sites)
print(len(imfiles), "GEMLST files found in", imfolder)

output_csv = "lst_from_GEMLST_at_GEM_longtest.csv"


#%%
# TRANSFORM AND EXTRACT

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3413", always_xy=True)
x_3413, y_3413 = transformer.transform(aws_df['longitude'].values, aws_df['latitude'].values)

results = []

for file in imfiles[:5]:
    with rio.open(file) as src:
        # Read the raster data
        lst = src.read(1)  # Assuming single band raster
        profile = src.profile

        row = {"Date": file.name.split('_')[1][:-5]}

        for i, (x,y) in enumerate(zip(x_3413, y_3413)):
            try:
                # Convert geographic coordinates to pixel coordinates
                row_pix, col_pix = src.index(x, y)
                # Read 
                lst_value = lst[row_pix, col_pix]
                row[aws_df.iloc[i]['id']] = lst_value
            except IndexError:
                print(f"Coordinates ({x}, {y}) are out of bounds for file {file.name}.")

        results.append(row)


#%% 
# CREATE LONG DATAFRAME AND EXPORT

# Create and restructure dataframe 
results_df = pd.DataFrame(results)

# convert the 'date' column to datetime format
results_df['Date'] = pd.to_datetime(results_df['Date'], format='%Y%m%d')

# Unpivot the results_df to have a long format
results_df_long = results_df.melt(id_vars=['Date'], var_name='aws', value_name='RS_LST')

results_df_long.to_csv(output_csv, index=False)
print("saved")


#%% 
# MERGE WITH AWS SHEET

aws_sheet = "aws_daily_temperature.csv"
gem_aws_data = pd.read_csv(os.path.join(aws_path, aws_sheet))
gem_aws_data = gem_aws_data[gem_aws_data['temperature'].notnull()]


rs_lst = pd.read_csv(rs_lst_path)
rs_lst["aws"] = rs_lst["aws"].replace({'Zackenberg_M4_30min' : 'Zackenberg_M4'})

validation_outputname = "validation_sheet_Landtest.csv"
validation_sheet_land = gem_aws_data.merge(rs_lst, how = 'left', on = ['Date', 'aws'])

validation_sheet_land.to_csv(validation_outputname, index=False)

