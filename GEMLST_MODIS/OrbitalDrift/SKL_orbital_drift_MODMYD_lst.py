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
df_path = ('C:/Users/simon/OneDrive - University of Copenhagen/Documents/Arbeitsmappe/GEMLST/GEMLST/GEMLST_MODIS/Data/MODMYD_POI/')

start_year = 2003
end_year = 2024

range = np.arange(start_year, end_year + 1)

lst_day = []
lst_night = []

dtypes = {'Terra_LST_Day_C': 'float32', 'Aqua_LST_Day_C': 'float32', 'Terra_LST_Night_C': 'float32', 'Aqua_LST_Night_C': 'float32'}

def calc_diff(df):
    '''Calculate differences between Terra and Aqua LST for day and night'''
    df['diff_day'] = df['Terra_LST_Day_C'] - df['Aqua_LST_Day_C']
    df['diff_night'] = df['Terra_LST_Night_C'] - df['Aqua_LST_Night_C']
    return df

def split_df (df): 
    '''Split dataframe into day and night subsets'''
    df_day = df[['poi_id','date','Terra_LST_Day_C', 'Aqua_LST_Day_C', 'diff_day', 'year']]
    df_night = df[['poi_id','date','Terra_LST_Night_C', 'Aqua_LST_Night_C', 'diff_night', 'year']]
    return df_day, df_night

def noise_filter(df):
    '''Remove paired pixel values where absolute differences exceed half the sum of their absolute values'''
    df_filtered = df[(df.iloc[:, 4].abs() <= 0.5 * ((df.iloc[:, 2] + df.iloc[:, 3]).abs()))]
    return df_filtered

def load_yearly_data(year):
    '''Load yearly data and apply functions'''
    file_path = os.path.join(df_path, f'GEMLST_MODIS_LST_POI_{year}.csv')
    df = pd.read_csv(file_path, dtype=dtypes)
    df = calc_diff(df)
    df['year'] = int(year)
    df_day, df_night = split_df(df)
    df_day, df_night = noise_filter(df_day), noise_filter(df_night)
    return df_day, df_night

for year in range:
    '''Loop through years and pass the prepped dataframes to global variables'''
    df_day, df_night = load_yearly_data(year)
    lst_day.append(df_day)
    lst_night.append(df_night)

lst_day = pd.concat(lst_day, ignore_index=True)
lst_night = pd.concat(lst_night, ignore_index=True)

print(f'Number of observations in day dataset: {len(lst_day)}')
print(f'Number of observations in night dataset: {len(lst_night)}')


#%%

### Perform orbital cross sensor drift analysis
summary_day = (
    lst_day.groupby('year').agg(
        n_obs=('diff_day', 'count'),
        avg_diff_day=('diff_day', 'mean'),
        med_diff_day=('diff_day', 'median'),
        std_diff_day=('diff_day', 'std')
    )
    .reset_index()
)

summary_night = (
    lst_night.groupby('year').agg(
        n_obs=('diff_night', 'count'),
        avg_diff_night=('diff_night', 'mean'),
        med_diff_night=('diff_night', 'median'),
        std_diff_night=('diff_night', 'std')
    )
    .reset_index()
)

print(summary_day)
print(summary_night)

# Export summary tables to CSV
# summary_day.to_csv(os.path.join(df_path, 'summary_day.csv'), index=False)
# summary_night.to_csv(os.path.join(df_path, 'summary_night.csv'), index=False)


#%%
baseline_day = lst_day[lst_day['year'] < 2020]['diff_day'].median()
baseline_night = lst_night[lst_night['year'] < 2020]['diff_night'].median()
target_day = lst_day[lst_day['year'] == 2020]['diff_day'].median()
target_night = lst_night[lst_night['year'] == 2020]['diff_night'].median()
print(f'Baseline cross-sensor difference in Day LST (median of pre-2020 years): {baseline_day:.2f} °C')
print(f'Baseline cross-sensor difference in Night LST (median of pre-2020 years): {baseline_night:.2f} °C')
print(f'Cross-sensor median difference in Day LST for 2020: {target_day:.2f} °C')
print(f'Cross-sensor median difference in Night LST for 2020: {target_night:.2f} °C')

before_2020_day = lst_day[lst_day['year'] < 2020]['diff_day']
during_od_day = lst_day[lst_day['year'] == 2020]['diff_day']
before_2020_night = lst_night[lst_night['year'] < 2020]['diff_night']
during_od_night = lst_night[lst_night['year'] == 2020]['diff_night']

# Test if the variances of the two groups are equal using Levene's test
levene_test = stats.levene(before_2020_day, during_od_day)
print(f'Levene’s test for Day LST differences: statistic = {levene_test.statistic:.2f}, p-value = {levene_test.pvalue:.4f}')
levene_test_night = stats.levene(before_2020_night, during_od_night)
print(f'Levene’s test for Night LST differences: statistic = {levene_test_night.statistic:.2f}, p-value = {levene_test_night.pvalue:.4f}')
    # Different variances. 

result_ttest = stats.ttest_ind(before_2020_day, during_od_day, equal_var=False)
print(f'T-test for Day LST differences: t-statistic = {result_ttest.statistic:.2f}, p-value = {result_ttest.pvalue:.4f}')

result_ttest_night = stats.ttest_ind(before_2020_night, during_od_night, equal_var=False)
print(f'T-test for Night LST differences: t-statistic = {result_ttest_night.statistic:.2f}, p-value = {result_ttest_night.pvalue:.4f}')

#%% 

### Visualize cross sensor differences over time
sns.set_style('whitegrid')
plt.figure(figsize=(12, 6))

sns.boxplot(x='year', y='diff_day', data=lst_day, color='pink', showfliers=False)
plt.title('Cross-sensor difference in Day LST')
plt.xlabel(f'Year')
plt.ylabel('Difference in Day LST (°C)')
plt.show()

# OBS: 2002 has a distinctively different variation than the rest and should evt. be excluded from the baseline calculation!

#%% 

### Visualize cross sensor differences over time
sns.set_style('whitegrid')
plt.figure(figsize=(12, 6))

sns.boxplot(x='year', y='diff_night', data=lst_night, color='lightblue', showfliers=False)
plt.title('Cross-sensor difference in Night LST')
plt.xlabel(f'Year')
plt.ylabel('Difference in Night LST (°C)')
plt.show()
# %%

# Suggested changes: 
# Split analysis for ice / land 
# Compare data to other reference data (VIIRS) 