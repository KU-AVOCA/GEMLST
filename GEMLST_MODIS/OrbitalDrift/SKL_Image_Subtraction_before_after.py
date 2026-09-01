#%% 
import rasterio as rio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#%%

file_before = "Acquisition_time_before_1month_median.tif"
file_after = "Acquisition_time_during_1month_median.tif"
path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/OD/"

with rio.open(path + file_before) as src:
    height, width = src.shape
    lst_height = height
    lst_width = width
    lst_transform = src.transform
    lst_crs = src.crs
    modbef = src.read(1)
    mydbef = src.read(2)

with rio.open(path + file_after) as src:
    modaft = src.read(1)
    mydaft = src.read(2)

mod = modaft - modbef
myd = mydaft - mydbef

plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.imshow(mod, cmap='RdBu', vmin=-1, vmax=1)
plt.colorbar(label='MODIS Acquisition Time Difference (days)')
plt.title('MODIS Acquisition Time Difference (After - Before)')

plt.subplot(1, 2, 2)
plt.imshow(myd, cmap='RdBu', vmin=-1, vmax=1)
plt.colorbar(label='MYD Acquisition Time Difference (days)')
plt.title('MYD Acquisition Time Difference (After - Before)')

#%%

# Calculate basic statistics for modbef
modbef_mean = np.nanmean(modbef)
modbef_median = np.nanmedian(modbef)
modbef_std = np.nanstd(modbef)

# Calculate basic statistics for mydbef
mydbef_mean = np.nanmean(mydbef)
mydbef_median = np.nanmedian(mydbef)
mydbef_std = np.nanstd(mydbef)

# Calculate basic statistics for modaft
modaft_mean = np.nanmean(modaft)
modaft_median = np.nanmedian(modaft)
modaft_std = np.nanstd(modaft)

# Calculate basic statistics for mydaft
mydaft_mean = np.nanmean(mydaft)
mydaft_median = np.nanmedian(mydaft)
mydaft_std = np.nanstd(mydaft)

# Print all
print("MODIS Before - Mean:", modbef_mean, "Median:", modbef_median, "Std Dev:", modbef_std)
print("MYD Before - Mean:", mydbef_mean, "Median:", mydbef_median, "Std Dev:", mydbef_std)
print("MODIS After - Mean:", modaft_mean, "Median:", modaft_median, "Std Dev:", modaft_std)
print("MYD After - Mean:", mydaft_mean, "Median:", mydaft_median, "Std Dev:", mydaft_std)

#%%
# Create new geotiff files from the Image subtraction 
output_file_mod = 'mod_subtraction_before_after.tif'
output_file_myd = 'myd_subtraction_before_after.tif'

with rio.open(output_file_mod, 'w', driver='GTiff', height=lst_height, width=lst_width, count=1, dtype=np.float32, crs=lst_crs, transform=lst_transform) as dst:
    dst.write(mod, 1)
with rio.open(output_file_myd, 'w', driver='GTiff', height=lst_height, width=lst_width, count=1, dtype=np.float32, crs=lst_crs, transform=lst_transform) as dst:
    dst.write(myd, 1)