#%%

import rasterio as rio
import matplotlib.pyplot as plt
import os 
from pathlib import Path


#%%

path = 'home/johvan/work/AVOCA/GEM/Development/Anlaysis/TSA/monthly_lst'

imfiles = [f for f in os.listdir(path) if f.startswith('GEMLST_monthly_') & f.endswith('.tiff')]

with rio.open(path + imfiles[0]) as src:
    agg = src.read(1)  

for imfile in imfiles:
    with rio.open(path + imfile) as src:
        data = src.read(1)
        agg += data

avg_img = agg/len(imfiles)

#%%


#%%
plt.imshow(avg_img)
plt.axis('off')
plt.colorbar()
plt.show()

