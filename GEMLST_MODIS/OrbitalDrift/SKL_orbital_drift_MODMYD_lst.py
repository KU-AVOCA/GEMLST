#%% 
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
# from pylr2.regress2 import regress2
from sklearn.metrics import mean_squared_error #, r2_score

#%%
df_path = ('C:/Users/simon/OneDrive - University of Copenhagen/Documents/Arbeitsmappe/GEMLST/GEMLST/GEMLST_MODIS/Data/MODMYD_POI/')
file_path = os.path.join(df_path, f'GEMLST_MODIS_LST_POI_2004_new.csv')
df = pd.read_csv(file_path)

#%%

### Import dataframes and calc cross sensor differences
df_path = ('C:/Users/simon/OneDrive - University of Copenhagen/Documents/Arbeitsmappe/GEMLST/GEMLST/GEMLST_MODIS/Data/MODMYD_POI/')

start_year = 2000
end_year = 2019

yr_range = np.arange(start_year, end_year + 1)

lst_land_day = []
lst_ice_day = []
lst_land_night = []
lst_ice_night = []

dtypes = {'Terra_LST_Day_C': 'float32', 'Aqua_LST_Day_C': 'float32', 'Terra_LST_Night_C': 'float32', 'Aqua_LST_Night_C': 'float32', 'class': 'category', 'object_id': 'int32'}

def calc_diff(df):
    '''Calculate differences between Terra and Aqua LST for day and night'''
    df['diff_day'] = df['Terra_LST_Day_C'] - df['Aqua_LST_Day_C']
    df['diff_night'] = df['Terra_LST_Night_C'] - df['Aqua_LST_Night_C']
    return df

def split_df (df): 
    '''Split dataframe into day and night subsets'''
    df_land = df[df['class'] == 'land']
    df_ice = df[df['class'] == 'ice']  
    df_land_day = df_land[['object_id','date','Terra_LST_Day_C', 'Aqua_LST_Day_C', 'diff_day', 'year', 'class']]
    df_ice_day = df_ice[['object_id','date','Terra_LST_Day_C', 'Aqua_LST_Day_C', 'diff_day', 'year', 'class']]
    df_land_night = df_land[['object_id','date','Terra_LST_Night_C', 'Aqua_LST_Night_C', 'diff_night', 'year', 'class']]
    df_ice_night = df_ice[['object_id','date','Terra_LST_Night_C', 'Aqua_LST_Night_C', 'diff_night', 'year', 'class']]
    return df_land_day, df_ice_day, df_land_night, df_ice_night

def noise_filter_day(df):
    '''Remove paired pixel values where absolute differences exceed the mean of their absolute values'''
    df_filtered = df[(df['diff_day'].abs() <= 0.5 * ((df['Terra_LST_Day_C'] + df['Aqua_LST_Day_C']).abs()))]
    return df_filtered

def noise_filter_night(df):
    '''Remove paired pixel values where absolute differences exceed half the sum of their absolute values'''
    df_filtered = df[(df['diff_night'].abs() <= 0.5 * ((df['Terra_LST_Night_C'] + df['Aqua_LST_Night_C']).abs()))]
    return df_filtered

def load_yearly_data(year):
    '''Load yearly data and apply functions'''
    file_path = os.path.join(df_path, f'GEMLST_MODIS_LST_POI_{year}_new.csv')
    df = pd.read_csv(file_path, dtype=dtypes)
    df = calc_diff(df)
    df['year'] = int(year)
    df_land_day, df_ice_day, df_land_night, df_ice_night = split_df(df)
    df_land_day, df_ice_day = noise_filter_day(df_land_day), noise_filter_day(df_ice_day)
    df_land_night, df_ice_night = noise_filter_night(df_land_night), noise_filter_night(df_ice_night)
    return df_land_day, df_ice_day, df_land_night, df_ice_night

for year in yr_range:
    '''Loop through years and pass the prepped dataframes to global variables'''
    df_land_day, df_ice_day, df_land_night, df_ice_night = load_yearly_data(year)
    lst_land_day.append(df_land_day)
    lst_ice_day.append(df_ice_day)
    lst_land_night.append(df_land_night)
    lst_ice_night.append(df_ice_night)

lst_land_day = pd.concat(lst_land_day, ignore_index=True)
lst_ice_day = pd.concat(lst_ice_day, ignore_index=True)
lst_land_night = pd.concat(lst_land_night, ignore_index=True)
lst_ice_night = pd.concat(lst_ice_night, ignore_index=True)

print(f'Number of observations in land day dataset: {len(lst_land_day)}')
print(f'Number of observations in ice day dataset: {len(lst_ice_day)}')
print(f'Number of observations in land night dataset: {len(lst_land_night)}')
print(f'Number of observations in ice night dataset: {len(lst_ice_night)}')


#%%

### Perform orbital cross sensor drift analysis
summary_land_day = (
    lst_land_day.groupby('year').agg(
        n_obs=('diff_day', 'count'),
        avg_diff_day=('diff_day', 'mean'),
        med_diff_day=('diff_day', 'median'),
        std_diff_day=('diff_day', 'std')
    )
    .reset_index()
)

summary_ice_day = (
    lst_ice_day.groupby('year').agg(
        n_obs=('diff_day', 'count'),
        avg_diff_day=('diff_day', 'mean'),
        med_diff_day=('diff_day', 'median'),
        std_diff_day=('diff_day', 'std')
    )
    .reset_index()
)

summary_land_night = (
    lst_land_night.groupby('year').agg(
        n_obs=('diff_night', 'count'),
        avg_diff_night=('diff_night', 'mean'),
        med_diff_night=('diff_night', 'median'),
        std_diff_night=('diff_night', 'std')
    )
    .reset_index()
)

summary_ice_night = (
    lst_ice_night.groupby('year').agg(
        n_obs=('diff_night', 'count'),
        avg_diff_night=('diff_night', 'mean'),
        med_diff_night=('diff_night', 'median'),
        std_diff_night=('diff_night', 'std')
    )
    .reset_index()
)

print(summary_land_day)
print(summary_ice_day)
print(summary_land_night)
print(summary_ice_night)

# Export summary tables to CSV
# summary_land_day.to_csv(os.path.join(df_path, 'summary_land_day.csv'), index=False)
# summary_ice_day.to_csv(os.path.join(df_path, 'summary_ice_day.csv'), index=False)
# summary_land_night.to_csv(os.path.join(df_path, 'summary_land_night.csv'), index=False)
# summary_ice_night.to_csv(os.path.join(df_path, 'summary_ice_night.csv'), index=False)


#%%
baseline_land_day = lst_land_day[lst_land_day['year'] < 2020]['diff_day'].median()
baseline_ice_day = lst_ice_day[lst_ice_day['year'] < 2020]['diff_day'].median()
baseline_land_night = lst_land_night[lst_land_night['year'] < 2020]['diff_night'].median()
baseline_ice_night = lst_ice_night[lst_ice_night['year'] < 2020]['diff_night'].median()
target_land_day = lst_land_day[lst_land_day['year'] == 2020]['diff_day'].median()
target_ice_day = lst_ice_day[lst_ice_day['year'] == 2020]['diff_day'].median()
target_land_night = lst_land_night[lst_land_night['year'] == 2020]['diff_night'].median()
target_ice_night = lst_ice_night[lst_ice_night['year'] == 2020]['diff_night'].median()
print(f'Baseline cross-sensor difference in Day LST on GrIS (median of pre-2020 years): {baseline_ice_day:.2f} °C')
print(f'Baseline cross-sensor difference in Night LST on GrIS(median of pre-2020 years): {baseline_ice_night:.2f} °C')
print(f'Baseline cross-sensor difference in Day LST on land (median of pre-2020 years): {baseline_land_day:.2f} °C')
print(f'Baseline cross-sensor difference in Night LST on land (median of pre-2020 years): {baseline_land_night:.2f} °C')
print(f'Cross-sensor median difference in Day LST for 2020 - GrIS: {target_ice_day:.2f} °C')
print(f'Cross-sensor median difference in Night LST for 2020 - GrIS: {target_ice_night:.2f} °C')
print(f'Cross-sensor median difference in Day LST for 2020 - Land: {target_land_day:.2f} °C')
print(f'Cross-sensor median difference in Night LST for 2020 - Land: {target_land_night:.2f} °C')


before_2020_day_land = lst_land_day[lst_land_day['year'] < 2020]['diff_day']
during_od_day_land = lst_land_day[lst_land_day['year'] == 2020]['diff_day']
before_2020_night_land = lst_land_night[lst_land_night['year'] < 2020]['diff_night']
during_od_night_land = lst_land_night[lst_land_night['year'] == 2020]['diff_night']
before_2020_day_ice = lst_ice_day[lst_ice_day['year'] < 2020]['diff_day']
during_od_day_ice = lst_ice_day[lst_ice_day['year'] == 2020]['diff_day']
before_2020_night_ice = lst_ice_night[lst_ice_night['year'] < 2020]['diff_night']
during_od_night_ice = lst_ice_night[lst_ice_night['year'] == 2020]['diff_night']


# Test if the variances of the two groups are equal using Levene's test
levene_test_day_land = stats.levene(before_2020_day_land, during_od_day_land)
print(f'Levene’s test for Day LST differences on land: statistic = {levene_test_day_land.statistic:.2f}, p-value = {levene_test_day_land.pvalue:.4f}')
levene_test_night_land = stats.levene(before_2020_night_land, during_od_night_land)
print(f'Levene’s test for Night LST differences on land: statistic = {levene_test_night_land.statistic:.2f}, p-value = {levene_test_night_land.pvalue:.4f}')
levene_test_day_ice = stats.levene(before_2020_day_ice, during_od_day_ice)
print(f'Levene’s test for Day LST differences on GrIS: statistic = {levene_test_day_ice.statistic:.2f}, p-value = {levene_test_day_ice.pvalue:.4f}')
levene_test_night_ice = stats.levene(before_2020_night_ice, during_od_night_ice)
print(f'Levene’s test for Night LST differences on GrIS: statistic = {levene_test_night_ice.statistic:.2f}, p-value = {levene_test_night_ice.pvalue:.4f}')
    # Different variances. 

result_ttest_day_land = stats.ttest_ind(before_2020_day_land, during_od_day_land, equal_var=False)
print(f'T-test for Day LST differences on land: t-statistic = {result_ttest_day_land.statistic:.2f}, p-value = {result_ttest_day_land.pvalue:.4f}')

result_ttest_night_land = stats.ttest_ind(before_2020_night_land, during_od_night_land, equal_var=False)
print(f'T-test for Night LST differences on land: t-statistic = {result_ttest_night_land.statistic:.2f}, p-value = {result_ttest_night_land.pvalue:.4f}')

result_ttest_day_ice = stats.ttest_ind(before_2020_day_ice, during_od_day_ice, equal_var=False)
print(f'T-test for Day LST differences on GrIS: t-statistic = {result_ttest_day_ice.statistic:.2f}, p-value = {result_ttest_day_ice.pvalue:.4f}')

result_ttest_night_ice = stats.ttest_ind(before_2020_night_ice, during_od_night_ice, equal_var=False)
print(f'T-test for Night LST differences on GrIS: t-statistic = {result_ttest_night_ice.statistic:.2f}, p-value = {result_ttest_night_ice.pvalue:.4f}')

#%% 

### Visualize cross sensor differences over time DAY

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

sns.set_style('whitegrid')

sns.boxplot(ax=ax1, x='year', y='diff_day', data=lst_land_day, color='pink', showfliers=False)
ax1.set_title('Cross-sensor difference in Day LST')
ax1.set_xlabel(f'Year')
ax1.set_ylabel('LST Difference on Land (°C)')


### Visualize cross sensor differences over time day ice
sns.boxplot(ax=ax2, x='year', y='diff_day', data=lst_ice_day, color='lightblue', showfliers=False)
ax2.set_xlabel(f'Year')
ax2.set_ylabel('LST Difference on GrIS (°C)')
plt.show()
# OBS: 2002 has a distinctively different variation than the rest and should evt. be excluded from the baseline calculation!

#%% 

### Visualize cross sensor differences over time NIGHT

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

sns.set_style('whitegrid')

sns.boxplot(ax=ax1, x='year', y='diff_night', data=lst_land_night, color='pink', showfliers=False)
ax1.set_title('Cross-sensor difference in Night LST')
ax1.set_xlabel(f'Year')
ax1.set_ylabel('LST Difference on Land (°C)')


### Visualize cross sensor differences over time day ice
sns.boxplot(ax=ax2, x='year', y='diff_night', data=lst_ice_night, color='lightblue', showfliers=False)
ax2.set_xlabel(f'Year')
ax2.set_ylabel('LST Difference on GrIS (°C)')
plt.show()
# %%


for yr in yr_range:

    baseline = lst_land_day[lst_land_day['year'] != yr]['diff_day']
    focus = lst_land_day[lst_land_day['year'] == yr]['diff_day']
    t_test = stats.ttest_ind(baseline, focus, equal_var=False)
    print(f'Significance test {yr}')
    if t_test.pvalue < 0.05:
        print(f'\tLST_Land_Day: t-statistic = {t_test.statistic:.2f}, p-value = {t_test.pvalue:.4f}')

    baseline = lst_land_night[lst_land_night['year'] != yr]['diff_night']
    focus = lst_land_night[lst_land_night['year'] == yr]['diff_night']
    t_test = stats.ttest_ind(baseline, focus, equal_var=False)
    if t_test.pvalue < 0.05:
        print(f'\tLST_Land_Night: t-statistic = {t_test.statistic:.2f}, p-value = {t_test.pvalue:.4f}')

    baseline = lst_ice_day[lst_ice_day['year'] != yr]['diff_day']
    focus = lst_ice_day[lst_ice_day['year'] == yr]['diff_day']
    t_test = stats.ttest_ind(baseline, focus, equal_var=False)
    if t_test.pvalue < 0.05:
        print(f'\tLST_Ice_Day: t-statistic = {t_test.statistic:.2f}, p-value = {t_test.pvalue:.4f}')

    baseline = lst_ice_night[lst_ice_night['year'] != yr]['diff_night']
    focus = lst_ice_night[lst_ice_night['year'] == yr]['diff_night']
    t_test = stats.ttest_ind(baseline, focus, equal_var=False)
    if t_test.pvalue < 0.05:
        print(f'\tLST_Ice_Night: t-statistic = {t_test.statistic:.2f}, p-value = {t_test.pvalue:.4f}')


#%%

# Suggested changes: 
# Split analysis for ice / land - still significant
# Compare data to other reference data (VIIRS) 

