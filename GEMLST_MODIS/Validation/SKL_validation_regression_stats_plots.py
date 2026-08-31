#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
import cmocean
from matplotlib.ticker import MultipleLocator


#%%

land = pd.read_csv("validation_sheet_Land.csv")
land = land[land['RS_LST'].notnull() & land['temperature'].notnull()]
ice = pd.read_csv("validation_sheet_ice.csv")
ice = ice[ice['RS_LST'].notnull() & ice['t_surf'].notnull()]

## Prepare ice table
# Harmonize ice df to use defined functions. 
ice = ice.rename(columns={'t_surf': 'temperature'})
# Filter out the stations that performed insufficiently in the calibration process (R2 < 0.8)
cal_stations = ['HUM', 'NAE', 'NEM', 'TUN', 'NAU', 'EGP', 'CEN', 'KPC_U', 'KPC_L', 'THU_U', 'CP1', 'THU_L2', 'THU_L', 'NSE', 'DY2', 'SCO_U', 'SDL', 'SWC', 'JAR', 'UPE_U', 'SDM', 'KAN_L', 'KAN_U', 'KAN_M', 'WEG_L']
ice = ice[ice['aws'].isin(cal_stations)]

#%%

def return_stats(df):
    # Regression model
    model = LinearRegression()
    model.fit(df[['RS_LST']], df[['temperature']])
    model.predict(df[['RS_LST']])

    r2 = round(model.score(df[['RS_LST']], df[['temperature']]), 2)
    coef = model.coef_[0][0]
    intercept = model.intercept_[0]

    # Calculate RMSE
    rmse = ((df['RS_LST'] - df['temperature']) ** 2).mean() ** 0.5

    s1 = f'No. of observations: {len(df)} \nSlope: {coef:.3f} \nIntercept: {intercept:.3f} \nR2: {r2} \nRMSE: {rmse:.2f} °C'
    
    # Print model summary
    # print(f"Model Summary:\nNo. of observations: {len(df)}\nCoefficients: {model.coef_}\nIntercept: {model.intercept_}\nR2: {r2}\nRMSE: {rmse:.2f} °C\n")
    
    return s1

print(f'land: \n{return_stats(land)}\n\nice: \n{return_stats(ice)}')

#%%

### GRAPHICAL VISUALIZATION ###

### LAND PLOTS ###

def viz(df, stats):
    '''Visualise input dataset and stats. Input: df (DataFrame), stats (string)'''

    # Set ax limits
    min_val = -60
    max_val = 20

    font = {#'family': 'serif',
            'color':  'navy',
            'weight': 'normal',
            'size': 8,
            }
    
    bbox = dict(
        boxstyle='square', 
        fc='whitesmoke', 
        ec='navy', 
        alpha=0.5)

    # Create comparison plot of original vs calibrated values
    fig, ax = plt.subplots(figsize=(5, 4), dpi=300)

    # Add 1:1 reference line 
    min_val = min(df['RS_LST'].min(), df['temperature'].min())
    max_val = max(df['RS_LST'].max(), df['temperature'].max())

    # 2d HISTOGRAM PLOTS
    # Original est_temp plot
    hist = sns.histplot(ax=ax, data=df, x='RS_LST', y='temperature', bins=60, discrete=True, cbar=True, cmap=cmocean.cm.thermal, cbar_kws={'label': 'Count', 'fraction': 0.05, 'pad': 0.02})
    hist.collections[0].colorbar.ax.tick_params(labelsize=8)
    hist.collections[0].colorbar.set_label('Count', fontsize=8)
    sns.regplot(ax=ax, data=df, x='RS_LST', y='temperature', scatter=False, color='gold')
    ax.plot([min_val, max_val], [min_val, max_val], '--', color='cyan', alpha=0.8)
    ax.text(0.01, 0.813, stats, fontdict=font, bbox=bbox, transform=ax.transAxes, horizontalalignment='left')
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ax.xaxis.set_major_locator(MultipleLocator(20))
    ax.yaxis.set_major_locator(MultipleLocator(20))
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    ax.set_xlabel('GEMLST (°C)', fontsize=8)
    ax.set_ylabel('AWS Temperature (°C)', fontsize=8)
    ax.set_aspect('equal')

    plt.tight_layout()

    # Save the fugure as vector pdf 
    plt.savefig(f"validation_stats_plot_land.pdf", format='pdf', dpi=300)
    plt.show()
    plt.close(fig)

stats_land = return_stats(land)
viz(land, stats_land)


#%%
### ICE PLOTS ###

def viz(df, stats):
    '''Visualise input dataset and stats. Input: df (DataFrame), stats (string)'''

    # Set ax limits
    min_val = -60
    max_val = 20

    font = {#'family': 'serif',
            'color':  'navy',
            'weight': 'normal',
            'size': 8,
            }
    
    bbox = dict(
        boxstyle='square', 
        fc='whitesmoke', 
        ec='navy', 
        alpha=0.5)

    # Create comparison plot of original vs calibrated values
    fig, ax = plt.subplots(figsize=(5, 4), dpi=300)


    # Add 1:1 reference line 
    # min_val = min(df['RS_LST'].min(), df['temperature'].min())
    # max_val = max(df['RS_LST'].max(), df['temperature'].max())

    # 2d HISTOGRAM PLOTS
    # Original est_temp plot
    hist = sns.histplot(ax=ax, data=df, x='RS_LST', y='temperature', bins=60, discrete=True, cbar=True, vmax=1000, cmap=cmocean.cm.thermal, cbar_kws={'label': 'Count', 'fraction': 0.05, 'pad': 0.02, 'extend': 'max'})
    hist.collections[0].colorbar.ax.tick_params(labelsize=8)
    hist.collections[0].colorbar.set_label('Count', fontsize=8)
    sns.regplot(ax=ax, data=df, x='RS_LST', y='temperature', scatter=False, color='gold')
    ax.plot([min_val, max_val], [min_val, max_val], '--', color='cyan', alpha=0.8)
    ax.text(0.01, 0.811, stats, fontdict=font, bbox=bbox, transform=ax.transAxes, horizontalalignment='left')
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ax.xaxis.set_major_locator(MultipleLocator(20))
    ax.yaxis.set_major_locator(MultipleLocator(20))
    ax.set_xlabel('GEMLST (°C)', fontsize=8)
    ax.set_ylabel('AWS Temperature (°C)', fontsize=8)
    ax.set_aspect('equal')

    plt.tight_layout()

    # Save the fugure as vector pdf 
    plt.savefig(f"validation_stats_plot_ice.pdf", format='pdf', dpi=300)
    plt.show()
    plt.close(fig)

stats_ice = return_stats(ice)
viz(ice, stats_ice)

# For large amounts of data, consider a 2d hist, kernel density or vaex plot
# https://seaborn.pydata.org/generated/seaborn.kdeplot.html
# https://seaborn.pydata.org/generated/seaborn.histplot.html
# https://vaex.io/docs/index.html

#%%

len(ice['aws'].unique())

