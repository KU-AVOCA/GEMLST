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
df_path = ('C:/Users/simon/OneDrive - University of Copenhagen/Documents/Arbeitsmappe/GEMLST/GEMLST/GEMLST_MODIS/Data/MODMYD_POI/') #
names = ['TerraD', 'TerraN', 'AquaD', 'AquaN', 'VIIRS_Day', 'VIIRS_Night']

for sname in names:
    file_path = os.path.join(df_path, f'GEMLST_{sname}_LST_POI_reduced.csv')
    # if path exists, load the dataset into a dataframe and assign it to a global variable named after the sensor
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        globals()[f'{sname}_df'] = df
        print(f'Loaded {sname} dataset with {len(df)} observations')
    else:
        print(f'File not found: {file_path}')

mappings = {
    'TerraD_df': {'MOD_LST_Day':'lst', 'MOD_QA_Day':'qa'},
    'TerraN_df': {'MOD_LST_Night':'lst', 'MOD_QA_Night':'qa'},
    'AquaD_df': {'MYD_LST_Day':'lst', 'MYD_QA_Day':'qa'},
    'AquaN_df': {'MYD_LST_Night':'lst', 'MYD_QA_Night':'qa'},
    'VIIRS_Day_df': {'VIIRS_LST_1KM_C':'lst', 'VIIRS_QC':'qa'},
    #'VIIRS_Night_df': {'VIIRS_LST_1KM_C':'lst', 'VIIRS_QC':'qa'}
}

for df, mapping in mappings.items():
    globals()[df].rename(columns=mapping, inplace=True)


#%%
# Create paired datasets for comparison 
# Join pairs: TerraN-AquaN, TerraD-AquaD, VIIRS_Day-TerraD, VIIRS_Day_AquaD, VIIRS_Night-TerraN, VIIRS_Night-AquaN

Terra_Aqua_N = pd.merge(TerraN_df, AquaN_df, on=['object_id', 'date', 'class'])
Terra_Aqua_D = pd.merge(TerraD_df, AquaD_df, on=['object_id', 'date', 'class'])
Terra_VIIRS_D = pd.merge(TerraD_df, VIIRS_Day_df, on=['object_id', 'date', 'class'])
Aqua_VIIRS_D = pd.merge(AquaD_df, VIIRS_Day_df, on=['object_id', 'date', 'class'])
TerraN_VIIRSD = pd.merge(TerraN_df, VIIRS_Day_df, on=['object_id', 'date', 'class'])
AquaN_VIIRSD = pd.merge(AquaN_df, VIIRS_Day_df, on=['object_id', 'date', 'class'])
# Terra_VIIRS_N = pd.merge(TerraN_df, VIIRS_Night_df, on=['object_id', 'date', 'class'])
# Aqua_VIIRS_N = pd.merge(AquaN_df, VIIRS_Night_df, on=['object_id', 'date', 'class'])


#%%
# DATA PREPARATION FUNCTIONS

# dtypes = {'Terra_LST_Day_C': 'float32', 'Aqua_LST_Day_C': 'float32', 'Terra_LST_Night_C': 'float32', 'Aqua_LST_Night_C': 'float32', 'class': 'category', 'object_id': 'int32'}

def filter_year(df, start_year=2002, end_year=2025):
    '''Extract year from date column and filter df for a time range. Default: 2002-2025'''
    df['year'] = pd.to_datetime(df['date']).dt.year
    df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    return df

def calc_diff(df):
    '''Calculate differences between sensors'''
    df['diff_lst'] = df['lst_x'] - df['lst_y']
    df['diff_time'] = df['time_x'] - df['time_y']
    return df

def split_df (df): 
    '''Split dataframe into day and night subsets'''
    df_land = df[df['class'] == 'land']
    df_ice = df[df['class'] == 'ice']  
    return df_land, df_ice

def prepare_data(df):
    '''Prepare data for analysis: filter years, calculate differences and split into land/ice subsets'''
    df = filter_year(df)
    df = calc_diff(df)
    df_land, df_ice = split_df(df)
    return df_land, df_ice


# ANALYSIS FUNCTIONS
def summarize(df): 
    '''Calculate summary statistics for each year'''
    summary = df.groupby('year').agg(
        n_obs=('diff_lst', 'count'),
        avg_diff_lst=('diff_lst', 'mean'),
        med_diff_lst=('diff_lst', 'median'),
        std_diff_lst=('diff_lst', 'std')
    ).reset_index()
    return summary

def compare_targetyear(df, tgt_year=2020):
    '''Compare target year to the years before (baseline) using t-test'''
    baseline = df[df['year'] < tgt_year]['diff_lst']
    target = df[df['year'] == tgt_year]['diff_lst']
    t_test = stats.ttest_ind(baseline, target, equal_var=False)
    t_statistic = f'{t_test.statistic:.2f}'
    p_value = f'{t_test.pvalue:.3f}'
    return t_statistic, p_value

def visualize(df):
    '''Visualize differences over time using boxplots'''
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='year', y='diff_lst', data=df, showfliers=False)
    plt.title('Cross-sensor difference in LST over time')
    plt.xlabel('Year')
    plt.ylabel('LST Difference (°C)')
    plt.show()

#%%
# Cross-sensor comparison: Terra vs Aqua

results_cross_sensor = {}

terra_aqua_n_land, terra_aqua_n_ice = prepare_data(Terra_Aqua_N)
terra_aqua_d_land, terra_aqua_d_ice = prepare_data(Terra_Aqua_D)
terra_viirs_d_land, terra_viirs_d_ice = prepare_data(Terra_VIIRS_D)
aqua_viirs_d_land, aqua_viirs_d_ice = prepare_data(Aqua_VIIRS_D)
terran_viirsd_land, terran_viirsd_ice = prepare_data(TerraN_VIIRSD)
aquan_viirsd_land, aquan_viirsd_ice = prepare_data(AquaN_VIIRSD) 

sensor_dict = {
    'Terra-Aqua Night Land': terra_aqua_n_land,
    'Terra-Aqua Night Ice': terra_aqua_n_ice,
    'Terra-Aqua Day Land': terra_aqua_d_land,
    'Terra-Aqua Day Ice': terra_aqua_d_ice,

    'Terra-VIIRS Day Land' : terra_viirs_d_land,
    'Terra-VIIRS Day Ice': terra_viirs_d_ice,
    'Aqua-VIIRS Day Land': aqua_viirs_d_land,
    'Aqua-VIIRS Day Ice': aqua_viirs_d_ice,

    'Terra-Night VIIRS Day Land': terran_viirsd_land,
    'Terra-Night VIIRS Day Ice': terran_viirsd_ice,
    'Aqua-Night VIIRS Day Land': aquan_viirsd_land,
    'Aqua-Night VIIRS Day Ice': aquan_viirsd_ice
}

for name, df in sensor_dict.items():
    t_statistic, p_value = compare_targetyear(df, 2020)
    results_cross_sensor[name] = {'t_statistic': t_statistic, 'p_value': p_value}

results_df = pd.DataFrame(results_cross_sensor)
print(results_df)

# t_statistic, p_value = compare_targetyear(terra_aqua_n_land, 2020)

# print(terra_aqua_n_land.head())
# summarize(terra_aqua_n_ice)
# compare_targetyear(terra_aqua_n_ice, 2020)
# visualize(terra_aqua_n_ice)

#%%
results_df.to_csv(os.path.join(df_path, 'cross_sensor_comparison_results.csv'), index=False)


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

# %%

test_df = pd.DataFrame({
    'Terra_LST_Day_C': np.arange(-5, 5, 1),
    'Aqua_LST_Day_C': np.arange(-3, 7, 1)})
test_df['diff_day'] = test_df['Terra_LST_Day_C'] - test_df['Aqua_LST_Day_C']
test_df['Terra_LST_K'] = test_df['Terra_LST_Day_C'] + 273.15
test_df['Aqua_LST_K'] = test_df['Aqua_LST_Day_C'] + 273.15
test_df['diff_day_K'] = test_df['Terra_LST_K'] - test_df['Aqua_LST_K']


test_df_filtered_new = test_df[(test_df['diff_day'].abs() / (0.5 * ((test_df['Terra_LST_Day_C'] + test_df['Aqua_LST_Day_C']).abs()))) > 1]
test_df_filtered_new_K = test_df[(test_df['diff_day_K'].abs() / (0.5 * ((test_df['Terra_LST_K'] + test_df['Aqua_LST_K']).abs()))) > 1]

print(test_df_filtered_new), print(test_df_filtered_new_K)



# %%
