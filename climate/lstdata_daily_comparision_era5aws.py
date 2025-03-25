#%% 
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns
# sns.set_theme(style="darkgrid", font_scale=1.5)

# #%% load data
# fileaws = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_temperature.csv'
# fileera5 = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/ERA5/GEM_AWS_ERA5Land.csv'

# dfaws = pd.read_csv(fileaws)
# dfera5 = pd.read_csv(fileera5)
# #%%
# dfera5['time'] = pd.to_datetime(dfera5['timestamp'], unit='ms')
# # %%
#%% 
def setup_plotting_style():
    """Set up the default plotting style."""
    sns.set_theme(style="darkgrid", font_scale=1.5)
def load_and_preprocess_data(aws_path, era5_path):
    """Load and preprocess AWS and ERA5 Land data."""
    # Load data
    aws_data = pd.read_csv(aws_path)
    era5_data = pd.read_csv(era5_path, usecols=['id', 'timestamp', 'skin_temperature', 'temperature_2m', 'temperature_of_snow_layer', 'soil_temperature_level_1'])
    era5_data['skin_temperature'] = era5_data['skin_temperature'] - 273.15
    era5_data['temperature_2m'] = era5_data['temperature_2m'] - 273.15
    era5_data['temperature_of_snow_layer'] = era5_data['temperature_of_snow_layer'] - 273.15
    era5_data['soil_temperature_level_1'] = era5_data['soil_temperature_level_1'] - 273.15

    # Process ERA5 Land data
    era5_data['Date'] = pd.to_datetime(era5_data['timestamp'], unit='ms')
    # era5_data['date'] = era5_data['Date']
    era5_data = era5_data.rename(columns={'id': 'aws'})
    
    # Process AWS data
    aws_data['Date'] = pd.to_datetime(aws_data['Date'])
    aws_data = aws_data.groupby([pd.Grouper(key='Date', freq='d'), 'aws']).mean().reset_index()
    
    # Merge data
    df = pd.merge_asof(
        aws_data.sort_values('Date'), 
        era5_data.sort_values('Date'), 
        on='Date', by='aws', direction='nearest', 
        allow_exact_matches=True, 
        # tolerance=pd.Timedelta(days=1)
    )
    
    # convert to daily average
    return df.dropna()

def create_overall_regression_plot(df, era5_variable='skin_temperature'):
    """Create overall regression plot comparing ERA5 Land and AWS temperatures."""
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Calculate regression statistics
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df[era5_variable], df['temperature']
    )
    
    # Create scatter plot with regression line
    sns.scatterplot(ax=ax, data=df, x=era5_variable, y='temperature', hue='aws', alpha=0.5)
    sns.regplot(ax=ax, data=df, x=era5_variable, y='temperature', 
                scatter=False, color='red')
    
    # Add 1:1 reference line
    min_val = min(df[era5_variable].min(), df['temperature'].min())
    max_val = max(df[era5_variable].max(), df['temperature'].max())
    ax.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
    
    # Customize plot
    ax.set_aspect('equal')
    plt.ylabel('AWS Temperature (°C)')
    plt.xlabel(f'ERA5 Land {era5_variable} (°C)')
    plt.title('ERA5 Land vs AWS Temperature Comparison')
    
    # Print statistics
    print(f"Regression Statistics:")
    print(f"Slope: {slope:.3f}")
    print(f"Intercept: {intercept:.3f}")
    print(f"R-value: {r_value:.3f}")
    print(f"R-squared: {r_value**2:.3f}")
    
    return fig

def create_station_subplots(df, era5_variable='skin_temperature'):
    """Create subplots for each AWS station."""
    unique_aws = df['aws'].unique()
    n_aws = len(unique_aws)
    n_cols = 3
    n_rows = (n_aws + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
    axes = axes.flatten()
    
    for idx, aws in enumerate(unique_aws):
        plot_single_station(df, aws, axes[idx], era5_variable)
    
    # Remove empty subplots
    for idx in range(len(unique_aws), len(axes)):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    return fig

def plot_single_station(df, aws, ax, era5_variable='skin_temperature'):
    """Plot regression for a single AWS station."""
    aws_data = df[df['aws'] == aws]
    
    # Calculate regression statistics
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        aws_data[era5_variable], aws_data['temperature']
    )
    
    # Create plots
    sns.scatterplot(data=aws_data, x=era5_variable, y='temperature', ax=ax, alpha=0.5)
    sns.regplot(data=aws_data, x=era5_variable, y='temperature', 
                scatter=False, color='red', ax=ax)
    
    # Add 1:1 line
    min_val = min(aws_data[era5_variable].min(), aws_data['temperature'].min())
    max_val = max(aws_data[era5_variable].max(), aws_data['temperature'].max())
    ax.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
    
    # Customize plot
    ax.set_title(f'AWS: {aws}')
    ax.set_xlabel(f'ERA5 Land {era5_variable} (°C)')
    ax.set_ylabel('AWS Temperature (°C)')
    ax.set_aspect('equal')
    
    # Print statistics
    print(f"\nStatistics for AWS {aws}:")
    print(f"Slope: {slope:.3f}")
    print(f"Intercept: {intercept:.3f}")
    print(f"R-value: {r_value:.3f}")
    print(f"R-squared: {r_value**2:.3f}")

def create_time_series_plots(df, era5_variable='skin_temperature'):
    """Create time series plots for each AWS station."""
    unique_aws = df['aws'].unique()
    n_aws = len(unique_aws)
    n_cols = 2  # Adjust as needed
    n_rows = (n_aws + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows), sharex=True)
    axes = axes.flatten()

    for idx, aws in enumerate(unique_aws):
        plot_time_series(df, aws, axes[idx], era5_variable)

    # Remove empty subplots
    for idx in range(len(unique_aws), len(axes)):
        fig.delaxes(axes[idx])

    plt.tight_layout()
    return fig

def plot_time_series(df, aws, ax, era5_variable='skin_temperature'):
    """Plot time series for a single AWS station."""
    aws_data = df[df['aws'] == aws].sort_values('Date')

    # Plot AWS data as a line
    ax.plot(aws_data['Date'], aws_data['temperature'], marker='', linestyle='-', color='blue', label='AWS Temperature')

    # Plot ERA5 Land data as scatter points
    ax.scatter(aws_data['Date'], aws_data[era5_variable], marker='o', color='red', label=f'ERA5 Land {era5_variable}', alpha=0.7)

    # Customize plot
    ax.set_title(f'AWS: {aws}')
    ax.set_ylabel('Temperature (°C)')
    ax.set_xlabel('Date')
    ax.legend()
    ax.grid(True)

#%%
def main():
    """Main function to run the analysis."""
    setup_plotting_style()
    
    # File paths
    aws_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_temperature.csv'
    era5_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/ERA5/GEM_AWS_ERA5LandDaily.csv'
    # aws_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/TOMST_temperature.csv'
    # era5_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/TOMST_AWS_LandsatLST.csv'

    # Load and process data
    df = load_and_preprocess_data(aws_path, era5_path)
    
    # Specify ERA5 variable for analysis
    era5_variable = 'temperature_2m'  # 'temperature_2m', 'skin_temperature', 'temperature_of_snow_layer', or 'soil_temperature_level_1'
    
    # Create plots
    create_overall_regression_plot(df, era5_variable)
    plt.show()
    
    create_station_subplots(df, era5_variable)
    plt.show()

    # Create time series plots
    time_series_fig = create_time_series_plots(df, era5_variable)
    plt.show()

if __name__ == "__main__":
    main()
# %%
