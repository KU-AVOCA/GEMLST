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
    aws_path = "/home/jovyan/work/AVOCA/GEM/Development/Data/PROMICE/output/"
    print("Using erda paths.")
elif a == "home": 
    imfolder = "/home/sirsimsius/Hentet/"
    aws_path = "/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/PROMICE/output/"
    print("Using home paths.")
else: print("Please enter 'erda' or 'home'.")

#%%

imfiles = sorted(Path(imfolder).glob("GEMLST_????????.tiff"))

aws_df = pd.read_csv(aws_path + "PROMICE_yearly_avg_positions.csv")
print(len(imfiles), "GEMLST files found in", imfolder)

output_csv = "lst_from_GEMLST_at_PROMICE_long.csv"

#%%
aws_pr_yr = aws_df.sort_values(by=['year', 'aws'])

#%%
# TRANSFORM AND ADD THE TRANSFORMED COORDINATES TO THE DF

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3413", always_xy=True)
x_3413, y_3413 = transformer.transform(aws_pr_yr['lon'].values, aws_pr_yr['lat'].values)

aws_pr_yr['x_3413'] = x_3413
aws_pr_yr['y_3413'] = y_3413


#%%
# Extract LST from GEMLST at PROMICE locations
# Goes through each file, extracts year from filename, filters the aws_pr_yr dataframe for that year, and 
# extracts the LST values at the transformed coordinates.

results = []

print("Commencing extraction")

for file in imfiles:
    with rio.open(file) as src:
        year = int(file.name.split('_')[1][:4])
        aws_pr_yr_year = aws_pr_yr[aws_pr_yr['year'] == year]
        # Read the raster data
        lst = src.read(1)
        qa = src.read(2)
        profile = src.profile

        row = {"date": file.name.split('_')[1][:-5]}

        x_3413 = aws_pr_yr_year['x_3413'].values
        y_3413 = aws_pr_yr_year['y_3413'].values
        for i, (x,y) in enumerate(zip(x_3413, y_3413)):
            try:
                # Convert geographic coordinates to pixel coordinates
                row_pix, col_pix = src.index(x, y)
                # Read 
                lst_value = lst[row_pix, col_pix]
                # qa_value = qa[row_pix, col_pix]
                row[aws_pr_yr_year.iloc[i]['aws']] = lst_value
            except IndexError:
                print(f"Coordinates ({x}, {y}) are out of bounds for file {file.name}.")

        results.append(row)

results_df = pd.DataFrame(results)

# convert 'date'
results_df['date'] = pd.to_datetime(results_df['date'], format='%Y%m%d')


#%% 
# CREATE LONG DATAFRAME AND EXPORT

# Unpivot the results_df to have a long format
results_df_long = results_df.melt(id_vars=['date'], var_name='aws', value_name='RS_LST')
results_df_long = results_df_long[results_df_long['RS_LST'].notnull()]

results_df_long.to_csv(output_csv, index=False)
print("Extracted LST saved")


#%% 
# MERGE WITH AWS SHEET

aws_sheet = "daily_prepped.csv"
gem_aws_data = pd.read_csv(os.path.join(aws_path, aws_sheet))
if a == "erda":
    rs_lst_path = "/home/jovyan/work/AVOCA/GEM/Development/Anlaysis/Validation_GEMLST/lst_from_GEMLST_at_PROMICE_long.csv"
elif a == "home":
    rs_lst_path = "/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Validation/lst_from_GEMLST_at_PROMICE_long.csv"
else: rs_lst_path = input("Please specify path to 'daily_prepped.csv' manually")

rs_lst = pd.read_csv(rs_lst_path)

validation_outputname = "validation_sheet_ice.csv"
validation_sheet_ice = gem_aws_data.merge(rs_lst, how = 'left', on = ['date', 'aws'])

validation_sheet_ice.to_csv(validation_outputname, index=False)

