#%%
import rasterio as rio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib as mpl
import seaborn as sns
from pyproj import Proj, Transformer

#%%
file = "lst_trend_4seasons_significant.tif"
path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/quarterly/"

with rio.open(path + file) as src:
    sslope = src.read(4)
    height, width = sslope.shape

    ### IDEA: Transform the image from EPSG:3413 to EPSG:4326 and save the y-coordinates so they can be shown as ticks in the following plt.
    transformer = Transformer.from_proj('EPSG:3413', 'EPSG:4326', always_xy=True)
    
    # Transform y-coordinates (latitudes) for each row
    y_coords_3413 = np.linspace(src.bounds.top, src.bounds.bottom, height)
    # Use left x coordinate for all points (we only care about y)
    x_const = np.full(height, src.bounds.left)
    lons, lats = transformer.transform(x_const, y_coords_3413)
    
    # Store latitude values for y-axis
    y_coords_4326 = lats


#%%
# sslope_1x = np.vsplit(sslope, 14)
# print(sslope_1x[0].shape)

# Remove NAs from all rows in the first split array
# sslope_x_nona = sslope_1x[0][~np.isnan(sslope_1x[0])]
# sslope_x_nona.shape


# Calculate the median of each row in the first split array
median_values = np.nanmedian(sslope, axis=1)
# print(f"Median values of the first split array: {median_values}")

#%%
#Print min and max values of the slope array
min_slope = np.nanmin(sslope)
max_slope = np.nanmax(sslope)
print(f"Minimum slope value: {min_slope}")
print(f"Maximum slope value: {max_slope}")



#%% 

# Create two plots side by side, one showing the slope image and the other showing the median values as a bar diagram

fig, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(6, 6),
    dpi=300,
    gridspec_kw={'width_ratios': [6, 4], 'wspace': 0},
    constrained_layout=True
)

# Show the slope image in the first subplot
cmap = ListedColormap(sns.color_palette("coolwarm", 256).as_hex())
im = ax1.imshow(sslope, cmap=cmap, vmin=-0.1, vmax=0.1)
cbar = plt.colorbar(im, ax=ax2, fraction=0.09, pad=0.03, extend='both', location='bottom')
cbar.set_label('°C yr-1', fontsize=8)
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


# Show the median values in the second subplot
norm = mpl.colors.Normalize(vmin=-0.1, vmax=0.1, clip=True)
bar_colors = cmap(norm(median_values))
ax2.barh(range(len(median_values)), width=median_values, height=2, color=bar_colors)
ax2.axvline(0, color='k', linewidth = 0.5)
ax2.set_xticks([])
ax2.set_yticks([])
ax2.invert_yaxis()
# ax2.set_xlabel('°C yr-1', fontsize=8)
# ax2.tick_params(labelsize=8)
ax2.set_ylim(len(median_values), 0)
# plt.tight_layout()
plt.savefig(f"median_slope_values.pdf", format='pdf', dpi=300)
plt.savefig("median_slope_values.png", format='png', dpi=300)

plt.show()

