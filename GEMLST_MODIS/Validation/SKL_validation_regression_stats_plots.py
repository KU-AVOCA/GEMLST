#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
import cmocean

#%%

land = pd.read_csv("validation_sheet_Land.csv")
land = land[land['RS_LST'].notnull() & land['temperature'].notnull()]


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

return_stats(land)

#%%
    ### GRAPHICAL VISUALIZATION ###

    # Add 1:1 reference line 
    # min_val = -75print(len(land), len(land_nona), "rows with non-null RS_LST and temperature values.")
    # max_val = 15

def viz(df, stats):
    '''Visualise input dataset and stats. Input: df (DataFrame), stats (string)'''

    font = {'family': 'serif',
            'color':  'navy',
            'weight': 'normal',
            'size': 9,
            }
    
    bbox = dict(
        boxstyle='square', 
        fc='whitesmoke', 
        ec='navy', 
        alpha=0.5)

    # Create comparison plot of original vs calibrated values
    fig, ax = plt.subplots(figsize=(8, 6))

    # Add 1:1 reference line 
    min_val = min(df['RS_LST'].min(), df['temperature'].min())
    max_val = max(df['RS_LST'].max(), df['temperature'].max())

    # 2d HISTOGRAM PLOTS
    # Original est_temp plot
    sns.histplot(ax=ax, data=df, x='RS_LST', y='temperature', bins=60, discrete=True, cbar=True, cmap=cmocean.cm.thermal, cbar_kws={'label': 'Count'})
    sns.regplot(ax=ax, data=df, x='RS_LST', y='temperature', scatter=False, color='gold')
    ax.plot([min_val, max_val], [min_val, max_val], '--', color='cyan', alpha=0.8)
    ax.text(0.008, 0.866, stats, fontdict=font, bbox=bbox, transform=ax.transAxes, horizontalalignment='left')
    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ax.set_xlabel('GEMLST (°C)')
    ax.set_ylabel('AWS Temperature (°C)')
    ax.set_aspect('equal')

    plt.tight_layout()

    # Save the fugure as vector pdf 
    # plt.savefig("validation_stats_plot_Land.pdf", format='pdf', dpi=300)
    plt.show()
    plt.close(fig)

stats = return_stats(land)

viz(land, stats)

# For large amounts of data, consider a 2d hist, kernel density or vaex plot
# https://seaborn.pydata.org/generated/seaborn.kdeplot.html
# https://seaborn.pydata.org/generated/seaborn.histplot.html
# https://vaex.io/docs/index.html

