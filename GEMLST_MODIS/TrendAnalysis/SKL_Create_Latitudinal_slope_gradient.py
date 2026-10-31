#%% 

### TREND ANALYSIS PLOTS PART 1 ###

#1: OVERALL SEN'S SLOPE INKL. LONGITUDUNAL GRADIENT

#2: ACCUMULATED SEN'S SLOPE (SUPPL. FIG) INKL. GEOGRAPHIC REFERENCE (ZONES)

#%%
import rasterio as rio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib as mpl
import seaborn as sns
from pyproj import Proj, Transformer
import cmcrameri.cm as cmc
from cmcrameri import show_cmaps
from matplotlib_scalebar.scalebar import ScaleBar
import geopandas as gpd

#%%
file = "lst_trend_4seasons.tif"
path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/djf_mam_jja_son/"

with rio.open(path + file) as src:
    sslope = src.read(6)
    mk_pval = src.read(5)
    height, width = sslope.shape
    raster_extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)
    raster_crs = src.crs

    significant_slope = np.where(mk_pval < 0.05, sslope, np.nan)

    ### IDEA: Transform the image from EPSG:3413 to EPSG:4326 and save the y-coordinates so they can be shown as ticks in the following plt.
    transformer = Transformer.from_proj('EPSG:3413', 'EPSG:4326', always_xy=True)
    
    # Transform y-coordinates (latitudes) for each row
    y_coords_3413 = np.linspace(src.bounds.top, src.bounds.bottom, height)
    # Use left x coordinate for all points (we only care about y)
    x_const = np.full(height, src.bounds.left)
    lons, lats = transformer.transform(x_const, y_coords_3413)
    
    # Store latitude values for y-axis
    y_coords_4326 = lats


with rio.open("/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/Masks/Greenlandmask.tif") as mask_src:
    mask = mask_src.read(1)

with rio.open("/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/Masks/Icemask.tif") as ice_src:
    ice_mask = ice_src.read(1)
    land_mask = np.where((ice_mask == 0) & (mask == 1), 1, 0)  

significant_slope26 = significant_slope*25.75 # The entire collection covers 25.75 seasonal circles (years), as 2000 has -1 season. Multiply the annual slope with this factor. 

median_values = np.nanmedian(significant_slope, axis=1)
# print(f"Median values of the first split array: {median_values}")

#%%
# Export the accumulated slope image as a GeoTIFF
output_file = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/AccumulatedSlope/accumulated_slope_2575.tiff"
# with rio.open(output_file, 'w', driver='GTiff', height=height, width=width, count=1, dtype=significant_slope26.dtype, crs=raster_crs, transform=src.transform) as dst:
#     dst.write(significant_slope26, 1)
#     dst.set_band_description(1, "Sslope_x_25.57")
    


#%%
#Print min and max values of the slope array

min_slope = np.nanmin(significant_slope)
max_slope = np.nanmax(significant_slope)
print(f"Minimum significant slope value: {min_slope}")
print(f"Maximum significant slope value: {max_slope}")

min_slope = np.nanmin(significant_slope26)
max_slope = np.nanmax(significant_slope26)
avg_slope = np.nanmean(significant_slope26)
sdt_slope = np.nanstd(significant_slope26)
print(f"Minimum slope value (25x): {min_slope}")
print(f"Maximum slope value (25x): {max_slope}")
print(f"Average slope value (25x): {avg_slope}")
print(f"Standard deviation of slope value (25x): {sdt_slope}")


#%% 

### PLOT: SSLOPE/YR WITH LATITUDINAL GRADIENT (FIGURE 1) ###
# Create two plots side by side, one showing the slope image and the other showing the median values as a bar diagram

fig, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(4, 4),
    dpi=300,
    gridspec_kw={'width_ratios': [6, 4], 'wspace': 0},
    constrained_layout=True
)

mask_cmap1 = mpl.colors.ListedColormap(['white', 'lightgray'])

ax1.imshow(land_mask, cmap=mask_cmap1)
# ax1.contour(mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
# ax1.contour(ice_mask, levels=[0.1], colors='grey', linewidths=0.1, alpha=0.8)

cmap = cmc.vik
im = ax1.imshow(significant_slope, cmap=cmap, vmin=-0.1, vmax=0.1)
cbar = plt.colorbar(im, ax=ax2, fraction=0.09, pad=0.03, extend='both', location='bottom')
cbar.set_label('Median slope (°C yr$^{⁻1}$)', fontsize=8)
cbar.ax.tick_params(labelsize=8, rotation=0)

# Print lat coords on y-axis - every 10 degrees
lat_min, lat_max = np.nanmin(y_coords_4326), np.nanmax(y_coords_4326)
# Create tick positions at every 10 degrees
tick_lats = np.arange(np.ceil(lat_min/10)*10, np.floor(lat_max/10)*10 + 1, 10)
# Find row indices closest to these latitudes
tick_indices = [np.argmin(np.abs(y_coords_4326 - lat)) for lat in tick_lats]
tick_labels = [f"{lat:.0f}° N" for lat in tick_lats]
ax1.set_yticks(tick_indices)
ax1.set_yticklabels(tick_labels, fontsize=8)
ax1.yaxis.set_label_position("left")
ax1.yaxis.tick_left()
ax1.set_xticks([])
scalebar = ScaleBar(1, units='km', dimension='si-length', location='lower right', scale_loc='bottom', length_fraction=0.25, height_fraction=0.04, border_pad=0.5, box_alpha=0.5, color='black', font_properties={'size': 8}, fixed_value=300, fixed_units='km')
ax1.add_artist(scalebar)


# Show the median values in the second subplot
norm = mpl.colors.Normalize(vmin=-0.1, vmax=0.1, clip=True)
bar_colors = cmap(norm(median_values))
ax2.barh(range(len(median_values)), width=median_values, height=2, color=bar_colors)
ax2.axvline(0, color='k', linewidth = 0.5)
ax2.set_xticks([])
ax2.set_yticks([])
ax2.invert_yaxis()
ax2.tick_params(labelsize=8)
ax2.set_ylim(len(median_values), 0)
# plt.tight_layout()
plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_lat_gradient.pdf", format='pdf', dpi=300)
plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_lat_gradient.png", format='png', dpi=300)

plt.show()





#%%

### PLOT: ACCUMULATED SLOPE (FIGURE 2) ###

fig, ax = plt.subplots(
    figsize=(4, 4),
    dpi=300
)

mask_cmap1 = mpl.colors.ListedColormap(['white', 'lightgray'])
ax.imshow(land_mask, cmap=mask_cmap1, extent=raster_extent, origin='upper')
# ax.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
# ax.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)

# Add a shapefile of regional zones to the plot
shp = gpd.read_file('/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Zones/Shapefiles/Zones_polyg.shp')
shp = shp.to_crs(raster_crs)
shp.boundary.plot(ax=ax, color='black', linewidth=0.5)

cmap = cmc.vik
im3 = ax.imshow(
    significant_slope26,
    cmap=cmap,
    vmin=-3,
    vmax=3,
    extent=raster_extent,
    origin='upper'
)
cbar = plt.colorbar(im3, ax=ax, fraction=0.09, pad=0.03, aspect=40, extend='both', location='right')
cbar.set_label('Temperature trend 2000 - 2025 (°C)', fontsize=8)
ax.set_xlim(raster_extent[0], raster_extent[1])
ax.set_ylim(raster_extent[2], raster_extent[3])
ax.set_xticks([])
ax.set_yticks([])

# Add the shapefile and labels for the zones from the attribute table of the shapefile
for idx, row in shp.iterrows():
    ax.annotate(text=row['Zone'], xy=(row.geometry.centroid.x, row.geometry.centroid.y), ha='center', va='center_baseline', fontsize=7, color='black')
    # ax.plot(row.geometry.centroid.x, row.geometry.centroid.y, marker='o', markersize=2, color='black')
    
scalebar = ScaleBar(1, units='km', dimension='si-length', location='lower right', scale_loc='bottom', border_pad=0.5, box_alpha=0.5, color='black', font_properties={'size': 8}, fixed_value=300, fixed_units='km')
ax.add_artist(scalebar)

# plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/accumulated_slope.pdf", format='pdf', dpi=300)
# plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/accumulated_slope.png", format='png', dpi=300)
plt.show()







#%%

##3 PLOT: FIGURE 1 AND 2 COMBINED (FIGURE 3) ###

fig = plt.figure(figsize=(7, 4), dpi=300, constrained_layout=True)
grid = fig.add_gridspec(
    1,
    3,
    width_ratios=[6, 4, 6],
    wspace=0
)
ax1 = fig.add_subplot(grid[0, 0])
ax2 = fig.add_subplot(grid[0, 1])
ax3 = fig.add_subplot(grid[0, 2])

mask_cmap1 = mpl.colors.ListedColormap(['white', 'lightgray'])
cmap = cmc.vik



# AX1: SLOPE IMAGE WITH LATITUDE TICKS 
ax1.imshow(land_mask, cmap=mask_cmap1)
im = ax1.imshow(significant_slope, cmap=cmap, vmin=-0.1, vmax=0.1)

lat_min, lat_max = np.nanmin(y_coords_4326), np.nanmax(y_coords_4326) # Print lat coords on y-axis - every 10 degrees
tick_lats = np.arange(np.ceil(lat_min/10)*10, np.floor(lat_max/10)*10 + 1, 10) # Create tick positions at every 10 degrees
tick_indices = [np.argmin(np.abs(y_coords_4326 - lat)) for lat in tick_lats] # Find row indices closest to these latitudes
tick_labels = [f"{lat:.0f}° N" for lat in tick_lats]

ax1.set_yticks(tick_indices)
ax1.set_yticklabels(tick_labels, fontsize=8)
ax1.yaxis.set_label_position("left")
ax1.yaxis.tick_left()
ax1.set_xticks([])

scalebar = ScaleBar(1, units='km', dimension='si-length', location='lower right', scale_loc='bottom', border_pad=0.5, box_alpha=0.5, color='black', font_properties={'size': 8}, fixed_value=300, fixed_units='km')
ax1.add_artist(scalebar)



# AX2: MEDIAN VALUES AS BAR DIAGRAM
# Show the median values in the second subplot
norm = mpl.colors.Normalize(vmin=-0.1, vmax=0.1, clip=True)
bar_colors = cmap(norm(median_values))
ax2.barh(range(len(median_values)), width=median_values, height=2, color=bar_colors)
ax2.axvline(0, color='k', linewidth = 0.5)
ax2.set_xticks([])
ax2.set_yticks([])
ax2.invert_yaxis()
ax2.tick_params(labelsize=8)
ax2.set_ylim(len(median_values), 0)
cbar = plt.colorbar(im, ax=ax2, fraction=0.09, pad=0.03, extend='both', location='bottom')
cbar.set_label('Median slope (°C yr$^{⁻1}$)', fontsize=8)
cbar.ax.tick_params(labelsize=8, rotation=0)


# AX3: ACCUMULATED SLOPE IMAGE WITH ZONES
ax3.imshow(land_mask, cmap=mask_cmap1, extent=raster_extent, origin='upper')
shp = gpd.read_file('/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Zones/Shapefiles/Zones_polyg.shp')
shp = shp.to_crs(raster_crs)
shp.boundary.plot(ax=ax3, color='black', linewidth=0.5)
im3 = ax3.imshow(
    significant_slope26,
    cmap=cmap,
    vmin=-3,
    vmax=3,
    extent=raster_extent,
    origin='upper'
)
cbar2 = plt.colorbar(im3, ax=ax3, fraction=0.09, pad=0.03, aspect=40, extend='both', location='right')
cbar2.set_label('Temperature trend 2000 - 2025 (°C)', fontsize=8)
ax3.set_xlim(raster_extent[0], raster_extent[1])
ax3.set_ylim(raster_extent[2], raster_extent[3])
ax3.set_xticks([])
ax3.set_yticks([])

# Add the shapefile and labels for the zones from the attribute table of the shapefile
for idx, row in shp.iterrows():
    ax3.annotate(text=row['Zone'], xy=(row.geometry.centroid.x, row.geometry.centroid.y), ha='center', va='center_baseline', fontsize=7, color='black')
    # ax.plot(row.geometry.centroid.x, row.geometry.centroid.y, marker='o', markersize=2, color='black')
    

# Compact the horizontal layout without changing subplot heights.
fig.canvas.draw()

def shift_axis(axis, shift_x):
    position = axis.get_position()
    axis.set_position([
        position.x0 + shift_x,
        position.y0,
        position.width,
        position.height
    ])

left_shift = -0.03
shift_axis(ax2, left_shift)
shift_axis(cbar.ax, left_shift)
shift_axis(ax3, left_shift)
shift_axis(cbar2.ax, left_shift)

ax1_position = ax1.get_position()
ax2_position = ax2.get_position()
gap = 0.000
ax1.set_position([
    ax2_position.x0 - gap - ax1_position.width,
    ax1_position.y0,
    ax1_position.width,
    ax1_position.height
])

ax3_position = ax3.get_position()
ax3_gap = 0.05
ax3_shift = ax2_position.x1 + ax3_gap - ax3_position.x0
shift_axis(ax3, ax3_shift)
shift_axis(cbar2.ax, ax3_shift)

cbar2_position = cbar2.ax.get_position()
ax3_position = ax3.get_position()
cbar2.ax.set_position([
    cbar2_position.x0,
    ax3_position.y0,
    cbar2_position.width,
    ax3_position.height
])


plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_lat_gradient_accumulated.pdf", format='pdf', dpi=300)
plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_lat_gradient_accumulated.png", format='png', dpi=300)

plt.show()




