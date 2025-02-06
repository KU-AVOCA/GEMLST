'''
This script performs a linear regression-based calibration of Landsat Land Surface Temperature (LST) data using AWS (Automatic Weather Station) temperature measurements.

The script loads Landsat LST data and AWS temperature data, merges them based on date and AWS identifier, and then trains a linear regression model to predict AWS temperature 
from Landsat LST (ST_B10 band). The model is then used to calibrate the Landsat LST values.

The script includes the following steps:
1.  Data Loading: Loads Landsat LST and AWS temperature data from CSV files.
2.  Data Preprocessing:
    *   Converts date columns to datetime objects.
    *   Calculate the hourly average of AWS temperature data.
    *   Merges Landsat and AWS data based on date and AWS identifier, using a nearest-neighbor approach with a time tolerance (1h).
3.  Model Training:
    *   Splits the merged data into training (2/3) and testing (1/3) sets.
    *   Trains a linear regression model using the training data, with Landsat LST as the independent variable and AWS temperature as the dependent variable.
4.  Calibration and Evaluation:
    *   Applies the trained model to calibrate the Landsat LST values in the test dataset.
    *   Generates scatter plots comparing the original and calibrated Landsat LST values against the AWS temperature values for the test dataset.  Includes regression lines and 1:1 reference lines for visual assessment.
    *   Prints the coefficients, intercept, and R-squared value of the linear regression model.
5.  Full Dataset Calibration and Visualization:
    *   Applies the trained model to calibrate the Landsat LST values in the entire dataset.
    *   Generates scatter plots comparing the original and calibrated Landsat LST values against the AWS temperature values for each AWS station.  Includes regression lines and 1:1 reference lines for visual assessment.

Author: Shunan Feng (shf@ign.ku.dk)
'''
#%%
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
sns.set_theme(style="darkgrid", font_scale=1.5)

#%%    
# File paths
aws_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_temperature.csv'
landsat_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/GEM_AWS_LandsatLST.csv'

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

df = df.dropna()


#%% 
# Split data into training and testing sets (2/3 training, 1/3 testing)
train_df, test_df = train_test_split(df, test_size=0.33, random_state=42)

# --- Linear Regression Model ---
# Create linear regression object
model = LinearRegression()

# Train the model using the training sets
model.fit(train_df[['ST_B10']], train_df['temperature'])

# Make predictions using the testing set
temperature_pred = model.predict(test_df[['ST_B10']])

# The coefficients
print('Coefficients: ', model.coef_)
print('Intercept: ', model.intercept_)
print('R-squared: ', model.score(test_df[['ST_B10']], test_df['temperature']))


#%% Apply calibration to ST_B10 using the trained model coefficients
# Apply calibration to test dataset
test_df['ST_B10_calibrated'] = test_df['ST_B10'] * model.coef_[0] + model.intercept_

# Create comparison plot of original vs calibrated values
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# Add 1:1 reference line 
min_val = min(test_df['ST_B10'].min(), test_df['temperature'].min())
max_val = max(test_df['ST_B10'].max(), test_df['temperature'].max())

# Original ST_B10 plot
sns.scatterplot(ax=ax1, data=test_df, x='ST_B10', y='temperature', alpha=0.5)
sns.regplot(ax=ax1, data=test_df, x='ST_B10', y='temperature', scatter=False, color='red')
ax1.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
ax1.set_xlabel('Original Landsat LST (°C)')
ax1.set_ylabel('AWS Temperature (°C)')
ax1.set_title('Before Calibration (Test Data)')
ax1.set_aspect('equal')

# Calibrated ST_B10 plot
sns.scatterplot(ax=ax2, data=test_df, x='ST_B10_calibrated', y='temperature', alpha=0.5)
sns.regplot(ax=ax2, data=test_df, x='ST_B10_calibrated', y='temperature', scatter=False, color='red')
ax2.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
ax2.set_xlabel('Calibrated Landsat LST (°C)')
ax2.set_ylabel('AWS Temperature (°C)')
ax2.set_title('After Calibration (Test Data)')
ax2.set_aspect('equal')

plt.tight_layout()
plt.show()
# %%
# Apply calibration to the entire dataset
df['ST_B10_calibrated'] = df['ST_B10'] * model.coef_[0] + model.intercept_

# Group data by 'aws'
grouped = df.groupby('aws')

# Create a figure and a set of subplots
fig, axes = plt.subplots(len(grouped), 2, figsize=(20, 10*len(grouped)))

# Iterate over each group (each AWS)
for i, (aws_name, aws_data) in enumerate(grouped):
    # Add 1:1 reference line 
    min_val = min(aws_data['ST_B10'].min(), aws_data['temperature'].min())
    max_val = max(aws_data['ST_B10'].max(), aws_data['temperature'].max())

    # Original ST_B10 plot
    sns.scatterplot(ax=axes[i, 0], data=aws_data, x='ST_B10', y='temperature', alpha=0.5)
    sns.regplot(ax=axes[i, 0], data=aws_data, x='ST_B10', y='temperature', scatter=False, color='red')
    axes[i, 0].plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
    axes[i, 0].set_xlabel('Original Landsat LST (°C)')
    axes[i, 0].set_ylabel('AWS Temperature (°C)')
    axes[i, 0].set_title(f'Before Calibration - AWS: {aws_name}')
    axes[i, 0].set_aspect('equal')

    # Calibrated ST_B10 plot
    sns.scatterplot(ax=axes[i, 1], data=aws_data, x='ST_B10_calibrated', y='temperature', alpha=0.5)
    sns.regplot(ax=axes[i, 1], data=aws_data, x='ST_B10_calibrated', y='temperature', scatter=False, color='red')
    axes[i, 1].plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
    axes[i, 1].set_xlabel('Calibrated Landsat LST (°C)')
    axes[i, 1].set_ylabel('AWS Temperature (°C)')
    axes[i, 1].set_title(f'After Calibration - AWS: {aws_name}')
    axes[i, 1].set_aspect('equal')

plt.tight_layout()
plt.show()
# %%
