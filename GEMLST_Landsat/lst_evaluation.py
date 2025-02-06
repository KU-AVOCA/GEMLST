'''
"""
This script performs an evaluation of Landsat Land Surface Temperature (LST) data
by comparing it with in-situ temperature measurements from Automatic Weather Stations (AWS).
It includes functions for data loading, preprocessing, merging, and visualization,
with a focus on regression analysis to assess the relationship between Landsat LST
and AWS temperatures.
The script generates overall regression plots and individual station subplots
to provide a comprehensive comparison.

Author: Shunan Feng
"""

'''
#%%
import pandas as pd
import seaborn as sns
from scipy import stats
import matplotlib.pyplot as plt

#%% 
def setup_plotting_style():
    """Set up the default plotting style."""
    sns.set_theme(style="darkgrid", font_scale=1.5)

def load_and_preprocess_data(aws_path, landsat_path):
    """Load and preprocess AWS and Landsat data."""
    # Load data
    aws_data = pd.read_csv(aws_path)
    landsat_data = pd.read_csv(landsat_path)
    
    # Process Landsat data
    landsat_data['Date'] = pd.to_datetime(landsat_data['system:time_start'], unit='ms')
    landsat_data['date'] = landsat_data['Date']
    landsat_data = landsat_data.rename(columns={'id': 'aws'})
    
    # Process AWS data
    aws_data['Date'] = pd.to_datetime(aws_data['Date'])
    aws_data['time'] = aws_data['Date'].dt.floor('h')
    aws_data = aws_data.groupby(['time', 'aws']).mean().reset_index()
    
    # Merge data
    df = pd.merge_asof(
        aws_data.sort_values('Date'), 
        landsat_data.sort_values('Date'), 
        on='Date', by='aws', direction='nearest', 
        allow_exact_matches=False, 
        tolerance=pd.Timedelta(hours=1)
    )
    
    return df.dropna()

def create_overall_regression_plot(df):
    """Create overall regression plot comparing Landsat and AWS temperatures."""
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Calculate regression statistics
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df['ST_B10'], df['temperature']
    )
    
    # Create scatter plot with regression line
    sns.scatterplot(ax=ax, data=df, x='ST_B10', y='temperature', hue='aws', alpha=0.5)
    sns.regplot(ax=ax, data=df, x='ST_B10', y='temperature', 
                scatter=False, color='red')
    
    # Add 1:1 reference line
    min_val = min(df['ST_B10'].min(), df['temperature'].min())
    max_val = max(df['ST_B10'].max(), df['temperature'].max())
    ax.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
    
    # Customize plot
    ax.set_aspect('equal')
    plt.ylabel('AWS Temperature (°C)')
    plt.xlabel('Landsat LST (°C)')
    plt.title('Landsat vs AWS Temperature Comparison')
    
    # Print statistics
    print(f"Regression Statistics:")
    print(f"Slope: {slope:.3f}")
    print(f"Intercept: {intercept:.3f}")
    print(f"R-value: {r_value:.3f}")
    print(f"R-squared: {r_value**2:.3f}")
    
    return fig

def create_station_subplots(df):
    """Create subplots for each AWS station."""
    unique_aws = df['aws'].unique()
    n_aws = len(unique_aws)
    n_cols = 3
    n_rows = (n_aws + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
    axes = axes.flatten()
    
    for idx, aws in enumerate(unique_aws):
        plot_single_station(df, aws, axes[idx])
    
    # Remove empty subplots
    for idx in range(len(unique_aws), len(axes)):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    return fig

def plot_single_station(df, aws, ax):
    """Plot regression for a single AWS station."""
    aws_data = df[df['aws'] == aws]
    
    # Calculate regression statistics
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        aws_data['ST_B10'], aws_data['temperature']
    )
    
    # Create plots
    sns.scatterplot(data=aws_data, x='ST_B10', y='temperature', ax=ax, alpha=0.5)
    sns.regplot(data=aws_data, x='ST_B10', y='temperature', 
                scatter=False, color='red', ax=ax)
    
    # Add 1:1 line
    min_val = min(aws_data['ST_B10'].min(), aws_data['temperature'].min())
    max_val = max(aws_data['ST_B10'].max(), aws_data['temperature'].max())
    ax.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
    
    # Customize plot
    ax.set_title(f'AWS: {aws}')
    ax.set_xlabel('Landsat LST (°C)')
    ax.set_ylabel('AWS Temperature (°C)')
    ax.set_aspect('equal')
    
    # Print statistics
    print(f"\nStatistics for AWS {aws}:")
    print(f"Slope: {slope:.3f}")
    print(f"Intercept: {intercept:.3f}")
    print(f"R-value: {r_value:.3f}")
    print(f"R-squared: {r_value**2:.3f}")

def main():
    """Main function to run the analysis."""
    setup_plotting_style()
    
    # File paths
    aws_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_temperature.csv'
    landsat_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/GEM_AWS_LandsatLST.csv'
    
    # Load and process data
    df = load_and_preprocess_data(aws_path, landsat_path)
    
    # Create plots
    create_overall_regression_plot(df)
    plt.show()
    
    create_station_subplots(df)
    plt.show()

if __name__ == "__main__":
    main()

# %%
