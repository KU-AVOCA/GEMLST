'''
This script performs a linear regression-based calibration of ERA5 air temperature data using AWS (Automatic Weather Station) 
temperature measurements.

The script loads ERA5 data and AWS temperature data, merges them based on date and AWS identifier, and then trains 
a linear regression model to predict AWS temperature from ERA5 air temperature. The model is then used to calibrate 
the ERA5 values.

The script includes the following steps:
1.  Data Loading: Loads ERA5 and AWS temperature data from CSV files.
2.  Data Preprocessing:
    *   Converts date columns to datetime objects.
    *   Calculate the daily average of AWS temperature data.
    *   Merges ERA5 and AWS data based on date and AWS identifier.
3.  Model Training:
    *   Splits the merged data into training (2/3) and testing (1/3) sets.
    *   Trains a linear regression model using the training data, with ERA5 temperature as the independent variable 
        and AWS temperature as the dependent variable.
4.  Calibration and Evaluation:
    *   Applies the trained model to calibrate the ERA5 temperature values in the test dataset.
    *   Generates scatter plots comparing the original and calibrated ERA5 values against the AWS temperature values 
        for the test dataset. Includes regression lines and 1:1 reference lines for visual assessment.
    *   Prints the coefficients, intercept, and R-squared value of the linear regression model.
5.  Full Dataset Calibration and Visualization:
    *   Applies the trained model to calibrate the ERA5 temperature values in the entire dataset.
    *   Generates scatter plots comparing the original and calibrated ERA5 values against the AWS temperature values 
        for each AWS station. Includes regression lines and 1:1 reference lines for visual assessment.

Author: Shunan Feng (shf@ign.ku.dk)
'''
#%%
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Set plotting style
sns.set_theme(style="darkgrid", font_scale=1.5)

# File paths
aws_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_temperature.csv'
era5_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/ERA5/JAXA/aws_airtemp_era5land.csv'

# Load data
aws_data = pd.read_csv(aws_path)
era5_data = pd.read_csv(era5_path)

# Process ERA5 data
era5_data['Date'] = pd.to_datetime(era5_data['imtime'])
era5_data = era5_data.rename(columns={'awsname': 'aws'})


# Convert ERA5 temperature from Kelvin to Celsius if needed
if era5_data['airtemp'].max() > 100:  # Simple check if temp is in Kelvin
    era5_data['airtemp'] = era5_data['airtemp'] - 273.15  # Convert to Celsius

# Process AWS data
aws_data['Date'] = pd.to_datetime(aws_data['Date'])
aws_data = aws_data.groupby([pd.Grouper(key='Date', freq='d'), 'aws']).mean().reset_index()

# Merge data
df = pd.merge_asof(
    aws_data.sort_values('Date'), 
    era5_data.sort_values('Date'), 
    on='Date', by='aws', direction='nearest', 
    allow_exact_matches=True,
    tolerance=pd.Timedelta(days=1)
)
df = df[df['Date'].dt.year != 2018]
df = df.dropna()

# Split data into training and testing sets (2/3 training, 1/3 testing)
train_df, test_df = train_test_split(df, test_size=0.33, random_state=42)

# --- Linear Regression Model ---
# Create linear regression object
model = LinearRegression()

# Train the model using the training sets
model.fit(train_df[['airtemp']], train_df['temperature'])

# Make predictions using the testing set
temperature_pred = model.predict(test_df[['airtemp']])

# The coefficients
print('Coefficients: ', model.coef_)
print('Intercept: ', model.intercept_)
print('R-squared: ', model.score(test_df[['airtemp']], test_df['temperature']))
print('RMSE: ', np.sqrt(np.mean((test_df['temperature'] - temperature_pred)**2)))

# Apply calibration to ERA5 temperature using the trained model coefficients
# Apply calibration to test dataset
test_df['airtemp_calibrated'] = test_df['airtemp'] * model.coef_[0] + model.intercept_

# Create comparison plot of original vs calibrated values
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# Add 1:1 reference line 
min_val = min(test_df['airtemp'].min(), test_df['temperature'].min())
max_val = max(test_df['airtemp'].max(), test_df['temperature'].max())

# Calculate statistics for original data
original_slope, original_intercept, original_r, original_p, original_stderr = stats.linregress(test_df['airtemp'], test_df['temperature'])
original_r2 = original_r**2
n_obs = len(test_df)

# Original ERA5 temperature plot
sns.scatterplot(ax=ax1, data=test_df, x='airtemp', y='temperature', alpha=0.5)
sns.regplot(ax=ax1, data=test_df, x='airtemp', y='temperature', scatter=False, color='red')
ax1.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
ax1.set_xlabel('Original ERA5 Air Temperature (°C)')
ax1.set_ylabel('AWS Temperature (°C)')
ax1.set_title('Before Calibration (Test Data)')
ax1.set_aspect('equal')

# Add statistics text to original plot
ax1.text(0.05, 0.95, f'$R^2$: {original_r2:.4f}\nn: {n_obs}\np-value: {original_p:.4f}\nSlope: {original_slope:.4f}\nIntercept: {original_intercept:.4f}', 
         transform=ax1.transAxes,  verticalalignment='top', 
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Calculate statistics for calibrated data
cal_slope, cal_intercept, cal_r, cal_p, cal_stderr = stats.linregress(test_df['airtemp_calibrated'], test_df['temperature'])
cal_r2 = cal_r**2

# Calibrated ERA5 temperature plot
sns.scatterplot(ax=ax2, data=test_df, x='airtemp_calibrated', y='temperature', alpha=0.5)
sns.regplot(ax=ax2, data=test_df, x='airtemp_calibrated', y='temperature', scatter=False, color='red')
ax2.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
ax2.set_xlabel('Calibrated ERA5 Air Temperature (°C)')
ax2.set_ylabel('AWS Temperature (°C)')
ax2.set_title('After Calibration (Test Data)')
ax2.set_aspect('equal')

# Add statistics text to calibrated plot
ax2.text(0.05, 0.95, f'$R^2$: {cal_r2:.4f}\nn: {n_obs}\np-value: {cal_p:.4f}\nSlope: {cal_slope:.4f}\nIntercept: {cal_intercept:.4f}', 
         transform=ax2.transAxes, verticalalignment='top', 
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig('era5_calibration_test_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

# Apply calibration to the entire dataset
df['airtemp_calibrated'] = df['airtemp'] * model.coef_[0] + model.intercept_

# Group data by 'aws'
grouped = df.groupby('aws')

# Create a figure and a set of subplots
fig, axes = plt.subplots(len(grouped), 2, figsize=(20, 10*len(grouped)))

# Iterate over each group (each AWS)
for i, (aws_name, aws_data) in enumerate(grouped):
    # Add 1:1 reference line 
    min_val = min(aws_data['airtemp'].min(), aws_data['temperature'].min())
    max_val = max(aws_data['airtemp'].max(), aws_data['temperature'].max())

    # Original ERA5 temperature plot
    sns.scatterplot(ax=axes[i, 0], data=aws_data, x='airtemp', y='temperature', alpha=0.5)
    sns.regplot(ax=axes[i, 0], data=aws_data, x='airtemp', y='temperature', scatter=False, color='red')
    axes[i, 0].plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
    axes[i, 0].set_xlabel('Original ERA5 Air Temperature (°C)')
    axes[i, 0].set_ylabel('AWS Temperature (°C)')
    axes[i, 0].set_title(f'Before Calibration - AWS: {aws_name}')
    axes[i, 0].set_aspect('equal')

    # Calibrated ERA5 temperature plot
    sns.scatterplot(ax=axes[i, 1], data=aws_data, x='airtemp_calibrated', y='temperature', alpha=0.5)
    sns.regplot(ax=axes[i, 1], data=aws_data, x='airtemp_calibrated', y='temperature', scatter=False, color='red')
    axes[i, 1].plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
    axes[i, 1].set_xlabel('Calibrated ERA5 Air Temperature (°C)')
    axes[i, 1].set_ylabel('AWS Temperature (°C)')
    axes[i, 1].set_title(f'After Calibration - AWS: {aws_name}')
    axes[i, 1].set_aspect('equal')

plt.tight_layout()
# plt.savefig('era5_calibration_by_station.png', dpi=300, bbox_inches='tight')
plt.show()

# Calculate and print statistics for each AWS station
for aws_name, aws_data in grouped:
    original_r2 = np.corrcoef(aws_data['airtemp'], aws_data['temperature'])[0, 1]**2
    calibrated_r2 = np.corrcoef(aws_data['airtemp_calibrated'], aws_data['temperature'])[0, 1]**2
    
    original_rmse = np.sqrt(np.mean((aws_data['temperature'] - aws_data['airtemp'])**2))
    calibrated_rmse = np.sqrt(np.mean((aws_data['temperature'] - aws_data['airtemp_calibrated'])**2))
    
    print(f"\nStatistics for {aws_name}:")
    print(f"  Original R²: {original_r2:.3f}")
    print(f"  Calibrated R²: {calibrated_r2:.3f}")
    print(f"  Original RMSE: {original_rmse:.3f}°C")
    print(f"  Calibrated RMSE: {calibrated_rmse:.3f}°C")
    print(f"  Improvement: {(1 - calibrated_rmse/original_rmse) * 100:.1f}%")

# Save calibration model parameters to a file
model_params = {
    'coefficient': model.coef_[0],
    'intercept': model.intercept_,
    'r_squared': model.score(test_df[['airtemp']], test_df['temperature'])
}

pd.DataFrame([model_params]).to_csv('era5_calibration_parameters.txt', index=False)
print("\nCalibration model parameters saved to 'era5_calibration_parameters.txt'")