#%% 
import os
from duckdb import df
from duckdb import df
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
# from pylr2.regress2 import regress2
from sklearn.metrics import mean_squared_error #, r2_score

#%%

### Import dataframes and calc cross sensor differences
df_path = ('C:\\Users\\simon\\OneDrive - University of Copenhagen\\Documents\\Arbeitsmappe\\GEMLST\\Test')

start_year = 2002
end_year = 2005

range = np.arange(start_year, end_year + 1)

all_dfs = []

dtypes = {'Terra_LST_Day_C': 'float32', 'Aqua_LST_Day_C': 'float32', 'Terra_LST_Night_C': 'float32', 'Aqua_LST_Night_C': 'float32'}

def calc_diff(df):
    '''Calculate differences between Terra and Aqua LST for day and night'''
    df['diff_day'] = df['Terra_LST_Day_C'] - df['Aqua_LST_Day_C']
    df['diff_night'] = df['Terra_LST_Night_C'] - df['Aqua_LST_Night_C']
    return df

def load_yearly_data(year):
    '''Load yearly data and add columns for differences'''
    file_path = os.path.join(df_path, f'GEMLST_MODIS_LST_POI_{year}.csv')
    df = pd.read_csv(file_path, dtype=dtypes)
    df = calc_diff(df)
    df['year'] = int(year)
    return df

for year in range:
    '''Loop through years and pass the prepped dataframes to global variables'''
    all_dfs.append(load_yearly_data(year))

all_dfs = pd.concat(all_dfs, ignore_index=True)


#%%

### Perform orbital cross sensor drift analysis
summary_stats = (
    all_dfs.groupby('year').agg(
        n_obs=('diff_day', 'count'),
        avg_diff_day=('diff_day', 'mean'),
        med_diff_day=('diff_day', 'median'),
        std_diff_day=('diff_day', 'std'),
        avg_diff_night=('diff_night', 'mean'),
        med_diff_night=('diff_night', 'median'),
        std_diff_night=('diff_night', 'std')
    )
    .reset_index()
)

print(summary_stats)



#%% 

# ### Visualize cross sensor differences over time
sns.set_style('whitegrid')
plt.figure(figsize=(12, 6))

sns.boxplot(x='year', y='diff_day', data=all_dfs, color='pink', showfliers=False)
plt.xlabel(f'Year')
plt.ylabel('Difference in Day LST (°C)')
plt.show()