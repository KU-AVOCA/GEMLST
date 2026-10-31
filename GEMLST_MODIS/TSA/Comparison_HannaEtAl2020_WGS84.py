#%%
import rasterio as rio
import numpy as np
from rasterio.enums import Resampling
from rasterio.plot import plotting_extent
from rasterio.warp import calculate_default_transform, reproject
import pandas as pd


#%%
# Import station coords. Keep the coordinates in their original EPSG:4326 CRS.
coords_csv = pd.read_csv('/home/sirsimsius/Dokumente/Arbeit/KU/Lit/Hanna_et_al_stations_coords_dmi.csv')

lon = coords_csv['lon'].values
lat = coords_csv['lat'].values

print(coords_csv)


#%%
# Import and reproject seasonal slopes from EPSG:3413 to EPSG:4326.
path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/djf_mam_jja_son/lst_trend_4seasons_quarters.tif"
with rio.open(path) as src:
    raster_crs = src.crs
    source_transform = src.transform

    if raster_crs != rio.crs.CRS.from_epsg(3413):
        raise ValueError(f"Expected the raster to use EPSG:3413, got {raster_crs}.")

    target_crs = rio.crs.CRS.from_epsg(4326)
    raster_transform, raster_width, raster_height = calculate_default_transform(
        raster_crs,
        target_crs,
        src.width,
        src.height,
        *src.bounds,
    )

    def reproject_band(band_number):
        source = src.read(band_number)
        destination = np.full(
            (raster_height, raster_width),
            np.nan,
            dtype=np.float32,
        )
        reproject(
            source=source,
            destination=destination,
            src_transform=source_transform,
            src_crs=raster_crs,
            dst_transform=raster_transform,
            dst_crs=target_crs,
            src_nodata=src.nodata,
            dst_nodata=np.nan,
            resampling=Resampling.nearest,
        )
        return destination

    mam = reproject_band(9)
    jja = reproject_band(10)
    son = reproject_band(11)
    djf = reproject_band(12)

# Hanna et al. used 19 years of data (2001-2019) for their analysis,
# so we multiply the slopes by 19 to get the total change over that period.
mam19 = mam * 19
jja19 = jja * 19
son19 = son * 19
djf19 = djf * 19

images = {'djf': djf19, 'mam': mam19, 'jja': jja19, 'son': son19}

#%%
results = []

# Read every reprojected image and extract values at the EPSG:4326 coordinates.
for img_name, img in images.items():
    row = {}
    for i, (x, y) in enumerate(zip(lon, lat)):
        try:
            row_pix, col_pix = rio.transform.rowcol(raster_transform, x, y)
            value = img[row_pix, col_pix]
            row['season'] = img_name
            row[coords_csv.iloc[i]['Stationsname']] = value
        except IndexError:
            print(f"Coordinates ({x}, {y}) are out of bounds for the image.")

    results.append(row)

results_df = pd.DataFrame(results).set_index('season').T.reset_index()
results_df = results_df.rename(columns={'index': 'Stationsname'})
print(results_df)

#%%
# Print the reprojected DJF image and the station coordinates.
import matplotlib.pyplot as plt
import cmcrameri.cm as cmc

fig, ax = plt.subplots(figsize=(10, 10))
ax.imshow(
    djf19,
    cmap=cmc.vik,
    vmin=-3,
    vmax=3,
    extent=plotting_extent(djf19, raster_transform),
    origin='upper',
)
ax.scatter(lon, lat, color='black', marker='o', label='Stations')
for i, station in enumerate(coords_csv['Stationsname']):
    ax.annotate(
        station,
        (lon[i], lat[i]),
        textcoords="offset points",
        xytext=(0, 10),
        ha='center',
        fontsize=8,
    )
ax.set_title('DJF Accumulated LST Change (2001-2019) with Station Locations')
ax.set_xlabel('Longitude (EPSG:4326)')
ax.set_ylabel('Latitude (EPSG:4326)')
ax.legend()
plt.show()
