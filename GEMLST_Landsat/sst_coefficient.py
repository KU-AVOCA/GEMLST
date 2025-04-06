'''
This script performs a linear regression-based calibration of Landsat Land Surface Temperature (LST) data using AWS (Automatic Weather Station) temperature measurements.

The script loads Landsat LST data and AWS temperature data, merges them based on date and AWS identifier, and then trains a linear regression model to predict AWS temperature 
from Landsat LST (LandsatSST band). The model is then used to calibrate the Landsat LST values.

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
file_path = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/Sea/OceanSurfaceTemp_Landsat0.csv'

# Load data
df = pd.read_csv(file_path)

df = df.dropna()
sns.regplot(data=df, x='LandsatSST', y='Temp')
# sns.scatterplot(data=df, x='LandsatSST', y='Temp', hue='Depth')
# remove one obvious outlier when LandsatSST < -15
df = df[df['LandsatSST'] > -10]

fig, ax = plt.subplots(figsize=(10, 10))
sns.scatterplot(ax=ax, data=df, x='LandsatSST', y='Temp')
sns.regplot(ax=ax, data=df, x='LandsatSST', y='Temp', scatter=False, color='red')
ax.plot([df['LandsatSST'].min(), df['LandsatSST'].max()], [df['LandsatSST'].min(), df['LandsatSST'].max()], '--', color='gray', alpha=0.8)
ax.set_xlabel('Landsat SST (°C)')
ax.set_ylabel('In situ Temperature (°C)')
ax.set_title('All Data')
ax.set_aspect('equal')
plt.show()
#%% 
# Split data into training and testing sets (2/3 training, 1/3 testing)
train_df, test_df = train_test_split(df, test_size=0.33, random_state=42)

# --- Linear Regression Model ---
# Create linear regression object
model = LinearRegression()

# Train the model using the training sets
model.fit(train_df[['LandsatSST']], train_df['Temp'])

# Make predictions using the testing set
temperature_pred = model.predict(test_df[['LandsatSST']])

# The coefficients
print('Coefficients: ', model.coef_)
print('Intercept: ', model.intercept_)
print('R-squared: ', model.score(test_df[['LandsatSST']], test_df['Temp']))


#%% Apply calibration to LandsatSST using the trained model coefficients
# Apply calibration to test dataset
test_df['LandsatSST_calibrated'] = test_df['LandsatSST'] * model.coef_[0] + model.intercept_

# Create comparison plot of original vs calibrated values
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

# Add 1:1 reference line 
min_val = min(test_df['LandsatSST'].min(), test_df['Temp'].min())
max_val = max(test_df['LandsatSST'].max(), test_df['Temp'].max())

# Original LandsatSST plot
sns.scatterplot(ax=ax1, data=test_df, x='LandsatSST', y='Temp', alpha=0.5)
sns.regplot(ax=ax1, data=test_df, x='LandsatSST', y='Temp', scatter=False, color='red')
ax1.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
ax1.set_xlabel('Original Landsat LandsatSST (°C)')
ax1.set_ylabel('In situ Temperature (°C)')
ax1.set_title('Before Calibration (Test Data)')
ax1.set_aspect('equal')

# Calibrated LandsatSST plot
sns.scatterplot(ax=ax2, data=test_df, x='LandsatSST_calibrated', y='Temp', alpha=0.5)
sns.regplot(ax=ax2, data=test_df, x='LandsatSST_calibrated', y='Temp', scatter=False, color='red')
ax2.plot([min_val, max_val], [min_val, max_val], '--', color='gray', alpha=0.8)
ax2.set_xlabel('Calibrated Landsat LST (°C)')
ax2.set_ylabel('In Situ Temperature (°C)')
ax2.set_title('After Calibration (Test Data)')
ax2.set_aspect('equal')

plt.tight_layout()
plt.show()

# %%
# Save calibration model parameters to a file
model_params = {
    'coefficient': model.coef_[0],
    'intercept': model.intercept_,
    'r_squared': model.score(test_df[['LandsatSST']], test_df['Temp'])
}

pd.DataFrame([model_params]).to_csv('landsat_SSTcalibration_parameters.txt', index=False)
print("\nCalibration model parameters saved to 'landsat_SSTcalibration_parameters.txt'")

# %%
