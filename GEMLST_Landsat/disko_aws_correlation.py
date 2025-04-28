"""
This script performs correlation analysis between Disko_AWS2 and other Disko AWS stations
(T1, T2, T3, T4). It includes functions for data loading, preprocessing, time-based matching,
and visualization, with a focus on regression analysis to assess the relationships
between ground temperature measurements at different Disko AWS stations.

The script generates overall regression plots and individual station subplots
to provide a comprehensive comparison.

Author: Shunan Feng
"""

#%%
import pandas as pd
import numpy as np
import seaborn as sns
from scipy import stats
import matplotlib.pyplot as plt

#%%
def setup_plotting_style():
    """Set up the default plotting style."""
    sns.set_theme(style="darkgrid", font_scale=1.5)

def load_and_preprocess_aws_data(aws_path):
    """
    Load and preprocess AWS temperature data.
    
    Parameters:
    -----------
    aws_path : str
        Path to the AWS temperature CSV file
        
    Returns:
    --------
    pandas.DataFrame
        Processed AWS data with consistent timestamps
    """
    # Load dataaaaaaaaaaaaa
    aws_data = pd.read_csv(aws_path)
    
    # Convert date to datetime
    aws_data['Date'] = pd.to_datetime(aws_data['Date'])
    
    # Filter only Disko stations
    disko_stations = ['Disko_AWS2', 'Disko_T1', 'Disko_T2', 'Disko_T3', 'Disko_T4']
    aws_data = aws_data[aws_data['aws'].isin(disko_stations)]
    
    return aws_data

def create_correlation_datasets(aws_data):
    """
    Create datasets for correlation analysis by matching timestamps.
    
    Parameters:
    -----------
    aws_data : pandas.DataFrame
        Processed AWS data
        
    Returns:
    --------
    dict
        Dictionary containing paired datasets for each T station vs AWS2
    """
    # Filter AWS2 data
    aws2_data = aws_data[aws_data['aws'] == 'Disko_AWS2']
    aws2_data = aws2_data.rename(columns={'temperature': 'AWS2_temperature'})
    aws2_data = aws2_data[['Date', 'AWS2_temperature']]
    
    correlation_datasets = {}
    
    # Match each T station with AWS2 by timestamp
    for station in ['Disko_T1', 'Disko_T2', 'Disko_T3', 'Disko_T4']:
        station_data = aws_data[aws_data['aws'] == station]
        station_data = station_data.rename(columns={'temperature': f'{station}_temperature'})
        station_data = station_data[['Date', f'{station}_temperature']]
        
        # Merge with AWS2 data on Date
        merged_data = pd.merge(
            aws2_data,
            station_data,
            on='Date',
            how='inner'  # Keep only matching timestamps
        )
        
        # Store in dictionary
        correlation_datasets[station] = merged_data
    
    return correlation_datasets

def create_overall_correlation_plot(correlation_datasets):
    """
    Create a combined plot showing all T stations vs AWS2.
    
    Parameters:
    -----------
    correlation_datasets : dict
        Dictionary of correlation datasets
        
    Returns:
    --------
    matplotlib.figure.Figure
        Figure containing the plot
    """
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Color map for different stations
    colors = {'Disko_T1': 'blue', 'Disko_T2': 'green', 
              'Disko_T3': 'red', 'Disko_T4': 'purple'}
    
    # Combined dataframe for statistics
    combined_df = pd.DataFrame()
    
    # Plot each station
    for station, data in correlation_datasets.items():
        x = data['AWS2_temperature']
        y = data[f'{station}_temperature']
        
        # Add data to combined dataframe
        station_df = data.copy()
        station_df['station'] = station
        combined_df = pd.concat([combined_df, station_df])
        
        # Calculate regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Plot scatterplot
        ax.scatter(x, y, label=f'{station} (r²={r_value**2:.2f})', 
                   color=colors[station], alpha=0.5)
        
        # Plot regression line
        x_range = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_range, intercept + slope * x_range, '--', color=colors[station])
        
        print(f"\nRegression for {station} vs AWS2:")
        print(f"Slope: {slope:.3f}")
        print(f"Intercept: {intercept:.3f}")
        print(f"R-value: {r_value:.3f}")
        print(f"R-squared: {r_value**2:.3f}")
    
    # Add 1:1 reference line
    min_val = combined_df[['AWS2_temperature'] + 
                          [f'{s}_temperature' for s in correlation_datasets.keys()]].min().min()
    max_val = combined_df[['AWS2_temperature'] + 
                          [f'{s}_temperature' for s in correlation_datasets.keys()]].max().max()
    ax.plot([min_val, max_val], [min_val, max_val], '-', color='gray', 
            alpha=0.8, label='1:1 line')
    
    # Customize plot
    ax.set_aspect('equal')
    ax.set_xlabel('Disko_AWS2 Temperature (°C)')
    ax.set_ylabel('T1-T4 Temperature (°C)')
    ax.set_title('Disko AWS2 vs. T1-T4 Temperature Comparison')
    ax.legend()
    ax.grid(True)
    
    plt.tight_layout()
    return fig

def create_individual_station_plots(correlation_datasets):
    """
    Create individual regression plots for each T station vs AWS2.
    
    Parameters:
    -----------
    correlation_datasets : dict
        Dictionary of correlation datasets
        
    Returns:
    --------
    matplotlib.figure.Figure
        Figure containing the subplots
    """
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    axes = axes.flatten()
    
    for idx, (station, data) in enumerate(correlation_datasets.items()):
        ax = axes[idx]
        
        # Get x and y data
        x = data['AWS2_temperature']
        y = data[f'{station}_temperature']
        
        # Calculate regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Create scatterplot with regression line
        sns.scatterplot(x=x, y=y, ax=ax, alpha=0.5)
        sns.regplot(x=x, y=y, scatter=False, color='red', ax=ax)
        
        # Add 1:1 reference line
        min_val = min(x.min(), y.min())
        max_val = max(x.max(), y.max())
        ax.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
        
        # Customize plot
        ax.set_aspect('equal')
        ax.set_title(f'{station} vs AWS2')
        ax.set_xlabel('Disko_AWS2 Temperature (°C)')
        ax.set_ylabel(f'{station} Temperature (°C)')
        
        # Add regression statistics as text
        stats_text = (f"Slope: {slope:.3f}\n"
                      f"Intercept: {intercept:.3f}\n"
                      f"R²: {r_value**2:.3f}")
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
                verticalalignment='top', bbox={'boxstyle': 'round', 'alpha': 0.5})
    
    plt.tight_layout()
    return fig

def create_time_series_plots(correlation_datasets):
    """
    Create time series plots showing AWS2 and each T station over time.
    
    Parameters:
    -----------
    correlation_datasets : dict
        Dictionary of correlation datasets
        
    Returns:
    --------
    matplotlib.figure.Figure
        Figure containing the subplots
    """
    # Create figure with subplots
    fig, axes = plt.subplots(4, 1, figsize=(15, 16), sharex=True)
    
    for idx, (station, data) in enumerate(correlation_datasets.items()):
        ax = axes[idx]
        
        # Sort data by date
        data = data.sort_values('Date')
        
        # Plot AWS2 data
        ax.plot(data['Date'], data['AWS2_temperature'], 
                color='black', label='Disko_AWS2')
        
        # Plot T station data
        ax.plot(data['Date'], data[f'{station}_temperature'], 
                color='red', label=station)
        
        # Calculate correlation
        r_value = np.corrcoef(data['AWS2_temperature'], data[f'{station}_temperature'])[0, 1]
        
        # Customize plot
        ax.set_title(f'{station} vs AWS2 (r={r_value:.3f})')
        ax.set_ylabel('Temperature (°C)')
        if idx == 3:  # Only add x-label to bottom subplot
            ax.set_xlabel('Date')
        ax.legend(loc='upper right')
        ax.grid(True)
    
    plt.tight_layout()
    return fig

#%%
def main():
    """Main function to run the analysis."""
    setup_plotting_style()
    
    # File path
    aws_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_temperature.csv'
    
    # Load and process AWS data
    aws_data = load_and_preprocess_aws_data(aws_path)
    
    # Create correlation datasets
    correlation_datasets = create_correlation_datasets(aws_data)
    
    # Create overall correlation plot
    fig1 = create_overall_correlation_plot(correlation_datasets)
    plt.figure(fig1.number)
    # plt.savefig('disko_aws_overall_correlation.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Create individual station plots
    fig2 = create_individual_station_plots(correlation_datasets)
    plt.figure(fig2.number)
    # plt.savefig('disko_aws_individual_correlations.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Create time series plots
    fig3 = create_time_series_plots(correlation_datasets)
    plt.figure(fig3.number)
    # plt.savefig('disko_aws_time_series.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    main()