#%%

# Notes: 
# - four plots for each season with significant sen's slopes
# - lin slope, intercept, p-value (suppl. fig), tau-b


#%%
import rasterio as rio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import cmcrameri.cm as cmc
from matplotlib_scalebar.scalebar import ScaleBar

import geopandas as gpd

#%%
# Import Seasonal Images 

# Greenland mask
with rio.open("/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/Masks/Greenlandmask.tif") as mask_src:
    mask = mask_src.read(1)

with rio.open("/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/Masks/Icemask.tif") as ice_src:
    ice_mask = ice_src.read(1)
    land_mask = np.where((ice_mask == 0) & (mask == 1), 1, 0)  


# Significant slopes per season
path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/djf_mam_jja_son/lst_trend_4seasons_quarters.tif"

with rio.open(path) as src:
    mam_pval = src.read(5)
    jja_pval = src.read(6)
    son_pval = src.read(7)
    djf_pval = src.read(8)

    mam_img = src.read(9)
    jja_img = src.read(10)
    son_img = src.read(11)
    djf_img = src.read(12)

mam_sig = np.where(mam_pval < 0.05, mam_img, np.nan)
jja_sig = np.where(jja_pval < 0.05, jja_img, np.nan)
son_sig = np.where(son_pval < 0.05, son_img, np.nan)
djf_sig = np.where(djf_pval < 0.05, djf_img, np.nan)

annual_path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/djf_mam_jja_son/lst_trend_4seasons.tif"
with rio.open(annual_path) as annual_src:
    annual = annual_src.read(6)

#TCC
path2 = path = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/djf_mam_jja_son/tcc_trend_4seasons_quarters_significant.tif"
with rio.open(path2) as tcc_src:
    mam_sig_tcc = tcc_src.read(1)
    jja_sig_tcc = tcc_src.read(2)
    son_sig_tcc = tcc_src.read(3)
    djf_sig_tcc = tcc_src.read(4)

path3 = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/djf_mam_jja_son/tcc_trend_4seasons_significant.tif"
with rio.open(path3) as tcc_src:
    ann_sig_tcc = tcc_src.read(4)


#%%
print(f'man_min: {np.nanmin(mam_sig)}, mam_max: {np.nanmax(mam_sig)}')
print(f'jja_min: {np.nanmin(jja_sig)}, jja_max: {np.nanmax(jja_sig)}')
print(f'son_min: {np.nanmin(son_sig)}, son_max: {np.nanmax(son_sig)}')
print(f'djf_min: {np.nanmin(djf_sig)}, djf_max: {np.nanmax(djf_sig)}')

print(f'mam_min_tcc: {np.nanmin(mam_sig_tcc)}, mam_max_tcc: {np.nanmax(mam_sig_tcc)}'
      f'jja_min_tcc: {np.nanmin(jja_sig_tcc)}, jja_max_tcc: {np.nanmax(jja_sig_tcc)}'
      f'son_min_tcc: {np.nanmin(son_sig_tcc)}, son_max_tcc: {np.nanmax(son_sig_tcc)}'
      f'djf_min_tcc: {np.nanmin(djf_sig_tcc)}, djf_max_tcc: {np.nanmax(djf_sig_tcc)}')



#%%
fig, (ax1, ax2, ax3, ax4) = plt.subplots(
    1, 4,
    figsize=(8, 4),

    dpi=300,
    gridspec_kw={'width_ratios': [2.5, 2.5, 2.5, 2.5], 'wspace': 0},
    constrained_layout=True
)

mask_cmap1 = mpl.colors.ListedColormap(['white', 'lightgray'])
ax1.imshow(land_mask, cmap=mask_cmap1)
ax2.imshow(land_mask, cmap=mask_cmap1)
ax3.imshow(land_mask, cmap=mask_cmap1)
ax4.imshow(land_mask, cmap=mask_cmap1)

# ax1.contour(mask, levels=[0.1], colors='black', linewidths=0.1, alpha=0.8)
# ax2.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
# ax3.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
# ax4.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
# ax1.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
# ax2.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
# ax3.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
# ax4.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)

ax1.imshow(mam_sig, cmap=cmc.vik, vmin=-0.2, vmax=0.2)
ax2.imshow(jja_sig, cmap=cmc.vik, vmin=-0.2, vmax=0.2)
ax3.imshow(son_sig, cmap=cmc.vik, vmin=-0.2, vmax=0.2)
ax4.imshow(djf_sig, cmap=cmc.vik, vmin=-0.2, vmax=0.2)

ax1.set_xticks([])
ax1.set_yticks([])
ax2.set_xticks([])
ax2.set_yticks([])
ax3.set_xticks([])
ax3.set_yticks([])
ax4.set_xticks([])
ax4.set_yticks([])

ax1.set_xlabel('MAM', fontsize=10)
ax2.set_xlabel('JJA', fontsize=10)
ax3.set_xlabel('SON', fontsize=10)
ax4.set_xlabel('DJF', fontsize=10)

# Add scalebar
scalebar = ScaleBar(1, units='km', dimension='si-length', location='lower right', scale_loc='bottom', height_fraction=0.02, border_pad=0.5, box_alpha=0.5, color='black', font_properties={'size': 8}, fixed_value=300)
ax4.add_artist(scalebar)

# add colorbar to the right of the last subplot
cbar = plt.colorbar(ax4.imshow(djf_sig, cmap=cmc.vik, vmin=-0.2, vmax=0.2), ax=ax4, fraction=0.09, pad=0.03, extend='both', location='right')
cbar.set_label('Median Slope (°C yr$^{⁻1}$)', fontsize=10)

plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_seasons.pdf", format='pdf', dpi=300)
plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_seasons.png", format='png', dpi=300)

plt.show()






#%% 

# TCC PLOTS

fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(
    1, 5,
    figsize=(9, 3.4),

    dpi=300,
    gridspec_kw={'width_ratios': [2, 2, 2, 2, 2], 'wspace': 0},
    constrained_layout=True
)

clr = cmc.batlow

mask_cmap1 = mpl.colors.ListedColormap(['white', 'lightgray'])
ax1.imshow(land_mask, cmap=mask_cmap1)
ax2.imshow(land_mask, cmap=mask_cmap1)
ax3.imshow(land_mask, cmap=mask_cmap1)
ax4.imshow(land_mask, cmap=mask_cmap1)
ax5.imshow(land_mask, cmap=mask_cmap1)

# ax1.contour(mask, levels=[0.1], colors='black', linewidths=0.1, alpha=0.8)
# ax2.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
# ax3.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
# ax4.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
# ax1.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
# ax2.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
# ax3.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
# ax4.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)

ax1.imshow(mam_sig_tcc, cmap=clr, vmin=-0.5, vmax=0.5)
ax2.imshow(jja_sig_tcc, cmap=clr, vmin=-0.5, vmax=0.5)
ax3.imshow(son_sig_tcc, cmap=clr, vmin=-0.5, vmax=0.5)
ax4.imshow(djf_sig_tcc, cmap=clr, vmin=-0.5, vmax=0.5)
ax5.imshow(ann_sig_tcc, cmap=clr, vmin=-0.5, vmax=0.5)

ax1.set_xticks([])
ax1.set_yticks([])
ax2.set_xticks([])
ax2.set_yticks([])
ax3.set_xticks([])
ax3.set_yticks([])
ax4.set_xticks([])
ax4.set_yticks([])
ax5.set_xticks([])
ax5.set_yticks([])

ax1.set_xlabel('MAM', fontsize=10)
ax2.set_xlabel('JJA', fontsize=10)
ax3.set_xlabel('SON', fontsize=10)
ax4.set_xlabel('DJF', fontsize=10)
ax5.set_xlabel('Annual', fontsize=10)

# Add scalebar
scalebar = ScaleBar(1, units='km', dimension='si-length', location='lower right', scale_loc='bottom', height_fraction=0.02, border_pad=0.5, box_alpha=0.5, color='black', font_properties={'size': 8}, fixed_value=300)
ax5.add_artist(scalebar)

# add colorbar to the right of the last subplot
cbar = plt.colorbar(ax5.imshow(ann_sig_tcc, cmap=clr, vmin=-0.5, vmax=0.5), ax=ax5, fraction=0.09, pad=0.03, extend='both', location='right')
cbar.set_label('Median Slope (% yr$^{⁻1}$)', fontsize=10)

plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_seasons_tcc.pdf", format='pdf', dpi=300)
plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_seasons_tcc.png", format='png', dpi=300)

plt.show()



#%%

# Test plots for monthly trends - significant and unsignificant

monthly_unsignificant = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/py_stats.seasonalkendal/lst_trend_monthly_seasonal.tif"
monthly_significant = "/home/sirsimsius/Dokumente/Arbeit/KU/GIS/Output_Trends/py_stats.seasonalkendal/lst_trend_monthly_seasonal_significant.tif"

clr = cmc.vik

# Read bands from the monthly trend images
with rio.open(monthly_unsignificant) as src:
    # Band names
    band_names = [f"Band {i+1}" for i in range(src.count)]
    print("Band names:", band_names)

with rio.open(monthly_unsignificant) as src:
    jan_img = src.read(1)
    feb_img = src.read(2)
    mar_img = src.read(3)
    apr_img = src.read(4)
    may_img = src.read(5)
    jun_img = src.read(6)
    jul_img = src.read(7)
    aug_img = src.read(8)
    sep_img = src.read(9)
    oct_img = src.read(10)
    nov_img = src.read(11)
    dec_img = src.read(12)

# Plotting the monthly trends in the same way as the seasonal trends, with significant and unsignificant slopes, can be done similarly to the previous plots. You can create subplots for each month and apply the same masking and color mapping techniques.
fig, axes = plt.subplots(3, 4, figsize=(9, 12), dpi=300, constrained_layout=False)
monthly_images = [jan_img, feb_img, mar_img, apr_img, may_img, jun_img, jul_img, aug_img, sep_img, oct_img, nov_img, dec_img]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

for i, (img, name) in enumerate(zip(monthly_images, month_names)):
    row = i // 4
    col = i % 4
    axes[row, col].imshow(img, cmap=clr, vmin=-1, vmax=1)
    axes[row, col].set_xlabel(name, fontsize=10)
    axes[row, col].set_xticks([])
    axes[row, col].set_yticks([])

# Add a colorbar to the right of the last subplot
cbar = plt.colorbar(axes[2, 3].imshow(dec_img, cmap=clr, vmin=-1, vmax=1), ax=axes[:, 3], fraction=0.02, pad=0.01, extend='both', location='right')
cbar.set_label('Trend direction and strength (tau-b)', fontsize=10)

plt.show()

#%%
#%%
fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(
    1, 5,
    figsize=(10, 4),

    dpi=300,
    gridspec_kw={'width_ratios': [2, 2, 2, 2, 2], 'wspace': 0},
    constrained_layout=True
)

mask_cmap1 = mpl.colors.ListedColormap(['white', 'lightgray'])
ax1.imshow(land_mask, cmap=mask_cmap1)
ax2.imshow(land_mask, cmap=mask_cmap1)
ax3.imshow(land_mask, cmap=mask_cmap1)
ax4.imshow(land_mask, cmap=mask_cmap1)
ax5.imshow(land_mask, cmap=mask_cmap1)

ax1.imshow(mam_img, cmap=cmc.vik, vmin=-0.2, vmax=0.2)
ax2.imshow(jja_img, cmap=cmc.vik, vmin=-0.2, vmax=0.2)
ax3.imshow(son_img, cmap=cmc.vik, vmin=-0.2, vmax=0.2)
ax4.imshow(djf_img, cmap=cmc.vik, vmin=-0.2, vmax=0.2)
im = ax5.imshow(annual, cmap=cmc.vik, vmin=-0.2, vmax=0.2)

ax1.set_xticks([])
ax1.set_yticks([])
ax2.set_xticks([])
ax2.set_yticks([])
ax3.set_xticks([])
ax3.set_yticks([])
ax4.set_xticks([])
ax4.set_yticks([])
ax5.set_xticks([])
ax5.set_yticks([])

ax1.set_xlabel('MAM', fontsize=10)
ax2.set_xlabel('JJA', fontsize=10)
ax3.set_xlabel('SON', fontsize=10)
ax4.set_xlabel('DJF', fontsize=10)
ax5.set_xlabel('Annual', fontsize=10)

# Add scalebar
scalebar = ScaleBar(1, units='km', dimension='si-length', location='lower right', scale_loc='bottom', height_fraction=0.02, border_pad=0.5, box_alpha=0.5, color='black', font_properties={'size': 8}, fixed_value=300)
ax5.add_artist(scalebar)

# add colorbar to the right of the last subplot
cbar = plt.colorbar(im, ax=ax5, fraction=0.09, pad=0.03, extend='both', location='right')
cbar.set_label('Median Slope (°C yr$^{-1}$) incl. insignificant areas', fontsize=10)

plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_inclInsignificant.pdf", format='pdf', dpi=300)
plt.savefig("/home/sirsimsius/Dokumente/Arbeit/KU/Graphs/Publish/TrendAnalysis/sslope_inclInsignificant.png", format='png', dpi=300)

plt.show()