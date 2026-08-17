#%% 
import pandas as pd
import numpy as np

#%%
ds = pd.read_csv('/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/data4simon/aws_temperature.csv')

print(ds.head())

# %%

grouped_ds = ds.groupby(by='aws')['Date'].nunique()
print(grouped_ds)

#%%
dp = pd.read_csv('/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/PROMICE/output/daily_prepped.csv')
grouped_dp = dp.groupby(by='aws')['date'].nunique()
# grouped_dp.to_csv('/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/PROMICE/output/daily_prepped_first_date.csv')
print(grouped_dp)

#%%
s_meta = pd.read_csv('/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/PROMICE/AWS_sites_metadata.csv')
sunique = s_meta.groupby('location_type')['site_id'].nunique()
print(sunique)

#%%
pos = pd.read_csv('/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/PROMICE/output/PROMICE_yearly_avg_positions.csv')
grouped_pos = pos.groupby(by='aws').first()[['lat', 'lon']]
grouped_pos.to_csv('/home/sirsimsius/Dokumente/Arbeit/KU/GEMLST/GEMLST_MODIS/Data/PROMICE/output/latlontable.csv')
print(grouped_pos)

#%%
tdf = pd.DataFrame({'Source': ['GEM', 'PROMICE', 'MODIS(NASA Terra)', 'MODIS(NASA Aqua)', "VIIRS(NASA S-NPP)", "SGLI(JAXA GCOM-C)", "ERA5-Land"], 'Start': ['2003-08-05', '2007-08-23', '2000-02-24', '2002-07-04', '2011-11-21', '2018-02-17', '1950'], 'End': ['2025-12-31', '2025-12-31', '2020-02-27', '2021-03-18', '2025-12-31', '2025-12-31', '2025']})
print(tdf)