#%%
#%%
import rasterio as rio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import cmcrameri.cm as cmc

#%%
# Import Seasonal Images 

# Greenland mask
with rio.open("/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/Masks/Greenlandmask.tif") as mask_src:
    mask = mask_src.read(1)

with rio.open("/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/Masks/Icemask.tif") as ice_src:
    ice_mask = ice_src.read(1)


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

#%%
print(f'man_min: {np.nanmin(mam_sig)}, mam_max: {np.nanmax(mam_sig)}')
print(f'jja_min: {np.nanmin(jja_sig)}, jja_max: {np.nanmax(jja_sig)}')
print(f'son_min: {np.nanmin(son_sig)}, son_max: {np.nanmax(son_sig)}')
print(f'djf_min: {np.nanmin(djf_sig)}, djf_max: {np.nanmax(djf_sig)}')


#%%
fig, (ax1, ax2, ax3, ax4) = plt.subplots(
    1, 4,
    figsize=(12, 6),
    dpi=300,
    gridspec_kw={'width_ratios': [2.5, 2.5, 2.5, 2.5], 'wspace': 0},
    constrained_layout=True
)

ax1.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
ax2.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
ax3.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
ax4.contour(mask, levels=[0.5], colors='black', linewidths=0.1, alpha=0.8)
ax1.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
ax2.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
ax3.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)
ax4.contour(ice_mask, levels=[0.5], colors='grey', linewidths=0.1, alpha=0.8)

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

ax1.set_xlabel('MAM', fontsize=12)
ax2.set_xlabel('JJA', fontsize=12)
ax3.set_xlabel('SON', fontsize=12)
ax4.set_xlabel('DJF', fontsize=12)

# add colorbar to the right of the last subplot
cbar = plt.colorbar(ax4.imshow(djf_sig, cmap=cmc.vik, vmin=-0.2, vmax=0.2), ax=ax4, fraction=0.09, pad=0.03, extend='both', location='right')
cbar.set_label('Median Slope (°C $yr^⁻1$)', fontsize=12)

plt.show()