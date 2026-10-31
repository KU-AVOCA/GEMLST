#%% 
import rasterio as rio
import numpy as np
from rasterio.plot import show
import pandas as pd
from pyproj import Transformer


#%%
# Import station coords 
coords_csv = pd.read_csv('/home/sirsimsius/Dokumente/Arbeit/KU/Lit/Hanna_et_al_stations_coords_dmi.csv')

# TRANSFORM AND ADD THE TRANSFORMED COORDINATES TO THE DF
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3413", always_xy=True)
x_3413, y_3413 = transformer.transform(coords_csv['lon'].values, coords_csv['lat'].values)

coords_csv['x_3413'] = x_3413
coords_csv['y_3413'] = y_3413

print(coords_csv)


#%%
# Import and prepare seasonal slopes from GEMLST trend analysis 
path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/djf_mam_jja_son/lst_trend_4seasons_quarters.tif"
with rio.open(path) as src: 
    
    # Read the data
    mam = src.read(9)
    jja = src.read(10)
    son = src.read(11)
    djf = src.read(12)
    raster_transform = src.transform
    raster_crs = src.crs
    if raster_crs != rio.crs.CRS.from_epsg(3413):
        raise ValueError(f"Expected the raster to use EPSG:3413, got {raster_crs}.")

# Hanna et al. used 19 years of data (2001-2019) for their analysis, 
# so we multiply the slopes by 19 to get the total change over that period.
mam19 = mam*19
jja19 = jja*19
son19 = son*19
djf19 = djf*19

images = {'djf': djf19, 'mam': mam19, 'jja': jja19, 'son': son19}

#%%
x_3413 = coords_csv['x_3413'].values
y_3413 = coords_csv['y_3413'].values

results = []

# Read every accumulated image and extract the values at the transformed coordinates
for img_name, img in images.items():
    row = {}
    for i, (x,y) in enumerate(zip(x_3413, y_3413)):
        try:
            # Convert geographic coordinates to pixel coordinates
            row_pix, col_pix = rio.transform.rowcol(raster_transform, x, y)
            # Read the value from the image
            value = img[row_pix, col_pix]
            row['season'] = img_name
            row[coords_csv.iloc[i]['Stationsname']] = value
        except IndexError:
            print(f"Coordinates ({x}, {y}) are out of bounds for the image.")

    results.append(row)

results_df = pd.DataFrame(results).set_index('season').T.reset_index()
results_df = results_df.rename(columns={'index': 'Stationsname'})
# results_df.columns.name = None
# results_df.columns = ['Stationsname', 'DJF', 'MAM', 'JJA', 'SON']
print(results_df)

#%%
# print the djf image and all the station coordinates on top of it
import matplotlib.pyplot as plt
import cmcrameri.cm as cmc

fig, ax = plt.subplots(figsize=(10, 10))

# Show the DJF image
ax.imshow(djf19, cmap=cmc.vik, vmin= -3, vmax=3, extent=rio.plot.plotting_extent(djf19, raster_transform), origin='upper')
# Plot the station coordinates
plt.scatter(x_3413, y_3413, color='black', marker='o', label='Stations')
# Annotate the stations with their names
for i, station in enumerate(coords_csv['Stationsname']):
    plt.annotate(station, (x_3413[i], y_3413[i]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
plt.title('DJF Accumulated LST Change (2001-2019) with Station Locations')
plt.xlabel('X (EPSG:3413)')
plt.ylabel('Y (EPSG:3413)')
plt.legend()
plt.show()