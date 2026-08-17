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
### PARAMETERS ### 
start_year = 2002
end_year = 2020

tgt_year = 2020 # Target year for comparison 
before = False # Whether to compare the tgt_year to the year before (yr<tgt_year) or all other years (yr!=tgt_year).

#%%
### CREATE PAIRED DATASETS FOR COMPARISON ###
# Join pairs: TerraN-AquaN, TerraD-AquaD, VIIRS_Day-TerraD, VIIRS_Day_AquaD, VIIRS_Night-TerraN, VIIRS_Night-AquaN

Terra_Aqua_N = pd.merge(TerraN_df, AquaN_df, on=['object_id', 'date', 'class'])
Terra_Aqua_D = pd.merge(TerraD_df, AquaD_df, on=['object_id', 'date', 'class'])
Terra_VIIRS_D = pd.merge(TerraD_df, VIIRS_Day_df, on=['object_id', 'date', 'class'])
Aqua_VIIRS_D = pd.merge(AquaD_df, VIIRS_Day_df, on=['object_id', 'date', 'class'])
TerraN_VIIRSD = pd.merge(TerraN_df, VIIRS_Day_df, on=['object_id', 'date', 'class'])
AquaN_VIIRSD = pd.merge(AquaN_df, VIIRS_Day_df, on=['object_id', 'date', 'class'])
# Terra_VIIRS_N = pd.merge(TerraN_df, VIIRS_Night_df, on=['object_id', 'date', 'class'])
# Aqua_VIIRS_N = pd.merge(AquaN_df, VIIRS_Night_df, on=['object_id', 'date', 'class'])

sensor_dict = {
    'Terra-Aqua Night': Terra_Aqua_N,
    'Terra-Aqua Day': Terra_Aqua_D,

    'Terra-VIIRS Day': Terra_VIIRS_D,
    'Aqua-VIIRS Day': Aqua_VIIRS_D,

    'Terra-Night VIIRS Day': TerraN_VIIRSD,
    'Aqua-Night VIIRS Day': AquaN_VIIRSD
}


#%%
# DATA PREPARATION FUNCTIONS
def filter_year(df, start_year, end_year):
    '''Extract year from date column and filter df for a time range.'''
    df['year'] = pd.to_datetime(df['date']).dt.year
    df_filtered = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    return df_filtered

def calc_diff(df):
    '''Calculate differences between sensors'''
    df['diff_lst'] = df['lst_x'] - df['lst_y']
    df['diff_time'] = df['time_x'] - df['time_y']
    return df

def prepare_data(df):
    '''Prepare data for analysis: filter years, calculate differences, select columns'''
    df = df.copy()  # Single copy at the start of the pipeline
    df['year'] = pd.to_datetime(df['date']).dt.year
    df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    df['diff_lst'] = df['lst_x'] - df['lst_y']
    df['diff_time'] = df['time_x'] - df['time_y']
    return df

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
    df = df.reset_index(drop=True)
    grouped_poi = df.groupby(by=['object_id'])[['diff_lst', 'diff_time']].mean().reset_index()
    return grouped_poi

def prepare_ttest(df, before = True, tgt_year=2020):
    '''Prepare dataframe for paired ttest. Splits into baseline and targetyear (default = 2020).
    Choose whether the baseline should include only years before the target year (default) or all other years. 
    Groups by POI and calculates mean difference per POI for LST and overfly time. Then merges the data into a single dataframe, 
    keeping only rows for POI that have observations in both baseline and targetyear.'''

    # Prepare data
    df_prepared = prepare_data(df)
    
    # Select relevant columns
    df_prepared.drop(columns=['lst_x', 'qa_x', 'time_x', 'lst_y', 'qa_y', 'time_y'], inplace=True)

    # Split into baseline and target year. Choose whether the baseline should include only years before the target year (default) or all other years.
    if before:
        baseline = df_prepared[df_prepared['year'] < tgt_year]
    else:
        baseline = df_prepared[df_prepared['year'] != tgt_year]
    target = df_prepared[df_prepared['year'] == tgt_year]

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
### Cross-sensor comparison: Terra vs Aqua
# Compare 2020 to the years before

results_cross_sensor = {}

for name, df in sensor_dict.items():
    df_prepared = prepare_ttest(df, before=True, tgt_year=2020)
    result_lst, result_time = perform_ttest(df_prepared)
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


#%%
results_df.to_csv(os.path.join(df_path, 'cross_sensor_comparison_results.csv'), index=True)

# %%
### Perform the ttest for every year in yr_range against the baseline of all other years, separately for each sensor pair and for day and night. Print the results in a readable format, only if the p-value is below 0.05.

yr_range = range(start_year, end_year + 1)

for name, df in sensor_dict.items():
    print(f'\n{name} comparison:')
    for yr in yr_range:
        df_prepared = prepare_ttest(df, before=False, tgt_year=yr)
        ttest_lst, ttest_time = perform_ttest(df_prepared)
        if ttest_lst.pvalue < 0.05:
            print(f'\tLST: Year {yr} vs baseline: t-statistic = {ttest_lst.statistic:.2f}, p-value = {ttest_lst.pvalue:.4f}')
        if ttest_time.pvalue < 0.05:
            print(f'\tTime: Year {yr} vs baseline: t-statistic = {ttest_time.statistic:.2f}, p-value = {ttest_time.pvalue:.4f}')



#%%
