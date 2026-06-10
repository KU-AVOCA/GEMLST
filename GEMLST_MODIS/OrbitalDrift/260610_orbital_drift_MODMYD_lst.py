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
    'AquaN_df': {'MYD_LST_Night':'lst', 'MYD_QA_Night':'qa'},
    'AquaD_df': {'MYD_LST_Day':'lst', 'MYD_QA_Day':'qa'},
    'AquaN_df': {'MYD_LST_Night':'lst', 'MYD_QA_Night':'qa'},
    'VIIRS_Day_df': {'VIIRS_LST_1KM_C':'lst', 'VIIRS_QC':'qa'},
    # 'VIIRS_Night_df': {'VIIRS_LST_1KM_C':'lst', 'VIIRS_QC':'qa'}
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

def prepare_data(df):
    '''Prepare data for analysis: filter years, calculate differences, select columns'''
    df = filter_year(df)
    df = calc_diff(df)
    return df


#%%
# ANALYSIS FUNCTIONS
def summarize(df): 
    '''Calculate summary statistics for each year'''
    df = prepare_data(df)
    summary = df.groupby('year').agg(
        n_obs=('diff_lst', 'count'),
        avg_diff_lst=('diff_lst', 'mean'),
        med_diff_lst=('diff_lst', 'median'),
        std_diff_lst=('diff_lst', 'std')
    ).reset_index()
    return summary

def calc_poi_avg(df):
    '''Group by object_id and calculate mean difference per POI'''
    df.reset_index(inplace=True)
    grouped_poi = df.groupby(by=['object_id'])[['diff_lst', 'diff_time']].mean().reset_index()
    return grouped_poi

def prepare_ttest(df, tgt_year=2020):
    '''Prepare dataframe for paired ttest. Splits into baseline and targetyear (default = 2020), groups by POI and calculates mean difference per POI for LST and overfly time. Then merges the data into a single dataframe, keeping only rows for POI that have observations in both baseline and targetyear.'''
    # Prepare data
    df = prepare_data(df)
    
    # Select relevant columns
    df.drop(columns=['lst_x', 'qa_x', 'time_x', 'lst_y', 'qa_y', 'time_y'], inplace=True)

    # Split into baseline and target year
    baseline = df[df['year'] < tgt_year]
    target = df[df['year'] == tgt_year]

    # Group on POI level and calculate mean difference per POI for LST and overfly time
    bl_grp, tgt_grp = calc_poi_avg(baseline), calc_poi_avg(target)

    # Merge 
    merged_df = pd.merge(bl_grp, tgt_grp, on='object_id', suffixes=('_baseline', '_target'), how='inner')
    
    return merged_df

def perform_ttest(df):
    '''Perform paired t-test on the differences in LST between baseline and target year.'''
    ttest_lst_results = stats.ttest_rel(df['diff_lst_baseline'], df['diff_lst_target'], nan_policy='raise')
    ttest_time_results = stats.ttest_rel(df['diff_time_baseline'], df['diff_time_target'], nan_policy='raise')
    return ttest_lst_results, ttest_time_results

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

terra_aqua_n = prepare_ttest(Terra_Aqua_N)
terra_aqua_d = prepare_ttest(Terra_Aqua_D)
terra_viirs_d = prepare_ttest(Terra_VIIRS_D)
aqua_viirs_d = prepare_ttest(Aqua_VIIRS_D)
terran_viirsd = prepare_ttest(TerraN_VIIRSD)
aquan_viirsd = prepare_ttest(AquaN_VIIRSD) 

sensor_dict = {
    'Terra-Aqua Night': terra_aqua_n,
    'Terra-Aqua Day': terra_aqua_d,

    'Terra-VIIRS Day': terra_viirs_d,
    'Aqua-VIIRS Day': aqua_viirs_d,

    'Terra-Night VIIRS Day': terran_viirsd,
    'Aqua-Night VIIRS Day': aquan_viirsd
}

for name, df in sensor_dict.items():
    result_lst, result_time = perform_ttest(df)
    # Add a row for each sensor comparison, with columns for t-statistic and p-value for both LST and time differences to the results dictionary
    results_cross_sensor.update({
        name: {
            't_statistic_lst': f'{result_lst.statistic:.2f}',
            'p_value_lst': f'{result_lst.pvalue:.3f}',
            't_statistic_time': f'{result_time.statistic:.2f}',
            'p_value_time': f'{result_time.pvalue:.3f}'
        }
    })

results_df = pd.DataFrame(results_cross_sensor)
print(results_df)

# t_statistic, p_value = compare_targetyear(terra_aqua_n_land, 2020)

# print(terra_aqua_n_land.head())
# summarize(terra_aqua_n_ice)
# compare_targetyear(terra_aqua_n_ice, 2020)
# visualize(terra_aqua_n_ice)

#%%
results_df.to_csv(os.path.join(df_path, 'cross_sensor_comparison_results.csv'), index=True)

#%% 

# ### Visualize cross sensor differences over time DAY

# fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

# sns.set_style('whitegrid')

# sns.boxplot(ax=ax1, x='year', y='diff_day', data=lst_land_day, color='pink', showfliers=False)
# ax1.set_title('Cross-sensor difference in Day LST')
# ax1.set_xlabel(f'Year')
# ax1.set_ylabel('LST Difference on Land (°C)')


# ### Visualize cross sensor differences over time day ice
# sns.boxplot(ax=ax2, x='year', y='diff_day', data=lst_ice_day, color='lightblue', showfliers=False)
# ax2.set_xlabel(f'Year')
# ax2.set_ylabel('LST Difference on GrIS (°C)')
# plt.show()
# # OBS: 2002 has a distinctively different variation than the rest and should evt. be excluded from the baseline calculation!

# #%% 

# ### Visualize cross sensor differences over time NIGHT

# fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

# sns.set_style('whitegrid')

# sns.boxplot(ax=ax1, x='year', y='diff_night', data=lst_land_night, color='pink', showfliers=False)
# ax1.set_title('Cross-sensor difference in Night LST')
# ax1.set_xlabel(f'Year')
# ax1.set_ylabel('LST Difference on Land (°C)')


# ### Visualize cross sensor differences over time day ice
# sns.boxplot(ax=ax2, x='year', y='diff_night', data=lst_ice_night, color='lightblue', showfliers=False)
# ax2.set_xlabel(f'Year')
# ax2.set_ylabel('LST Difference on GrIS (°C)')
# plt.show()
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
