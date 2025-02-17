"""
This script preprocesses Automatic Weather Station (AWS) data from various locations,
extracts temperature information, and compiles it into a single CSV file.
The script performs the following steps:
1.  **Defines AWS Locations and Metadata:**
    -   A dictionary `awslist` stores metadata for each AWS, including:
        -   Latitude and longitude coordinates.
        -   Filepath to the AWS data file.
        -   Temperature unit ('celcius' or 'kelvin').
        -   Time zone ('UTC-3' or 'UTC').
        -   Name of the temperature variable in the data file.
2.  **Reads and Preprocesses AWS Data:**
    -   Iterates through each AWS in the `awslist`.
    -   Reads the AWS data file using pandas, selecting 'Date', 'Time', and the temperature variable.
    -   Handles variations in time column naming ('Time' or 'Time (UTC-3)').
    -   Converts 'Date' and 'Time' columns to datetime objects, combining them into a single 'datetime' column.
    -   Adjusts the 'datetime' column for time zone differences (UTC-3).
    -   Converts temperature from Kelvin to Celsius if necessary.
    -   Removes rows with missing temperature values or unrealistic temperature values (<-100°C).
    -   Determines the start and end dates of the data for each AWS.
3.  **Resamples and Exports Data:**
    -   Adds the AWS name as a column to the DataFrame.
    -   Resamples the data to hourly averages.
    -   Appends the processed data to a master CSV file (`aws_temperature.csv`).
4.  **Saves AWS Metadata:**
    -   Saves the `awslist` DataFrame, including the start and end dates of each AWS, to a CSV file (`aws_stations.csv`).
The script assumes that the AWS data files are tab-separated and contain columns for 'Date', 'Time' (or 'Time (UTC-3)'),
and a temperature variable as specified in the `awslist` dictionary.

Author: Shunan Feng (shf@ign.ku.dk)
"""


#%% import libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(style="darkgrid", font_scale=1.5)

#%% list of AWS locations and coordinates
awslist = {
    'TOMST2': {
        'lat': 69.25349,
        'lon': -53.51418,
        'filepath': '94204541',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'T2'
    },
    'TOMST3': {
        'lat': 69.265525,
        'lon': -53.467324,
        'filepath': '94204542',
        'temp_unit': 'celcius', 
        'time_zone': 'UTC-3',
        'temp_var': 'T2'
    },
    'TOMST-T2-15': {
        'lat': 69.289089,
        'lon': -53.4328202,
        'filepath': '94232447',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3', 
        'temp_var': 'T2'
    },
    'TOMST4-15': {
        'lat': 69.27282,
        'lon': -53.45363,
        'filepath': '94232448',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'T2'
    },
    'TOMST4-30': {
        'lat': 69.27282,
        'lon': -53.45363,
        'filepath': '94232449',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'T2'
    }
}
# Convert AWS dictionary to DataFrame
awslist = pd.DataFrame.from_dict(awslist, orient='index')
awslist = awslist.reset_index().rename(columns={'index': 'aws'})
awslist['date_start'] = pd.to_datetime('')
awslist['date_end'] = pd.to_datetime('')

filepath = '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/5_Østerlien/SoilTemp2.0_data-submission_template_long_multisensor_logger_separated-timeseries_CS2024_Preliminary.xlsx'
# %% check the date range of each AWS station and save the
#  temperature to a new CSV file.
for i in range(awslist.shape[0]):
    print(f'Processing {awslist.loc[i, "aws"]}...')
    # read selected columns from the AWS data file
    df = pd.read_excel(filepath, sheet_name=awslist.loc[i, 'filepath'], usecols=['Time', awslist.loc[i, 'temp_var']])
    # Parse the time string and combine with date, adjusting for timezone
    df['Date'] = pd.to_datetime(df['Time'].astype(str), format='mixed')
    # Drop rows with NaN or NaT values
    df = df.dropna(subset=['Date', awslist.loc[i, 'temp_var'], 'Time'])
    if awslist.loc[i, 'time_zone'] == 'UTC-3':
        df['Date'] = df['Date'] + pd.Timedelta(hours=3)
    df = df.rename(columns={awslist.loc[i, 'temp_var']: 'temperature'})
    # Check if the temperature unit is in kelvin
    if awslist.loc[i, 'temp_unit'] == 'kelvin':
        df['temperature'] = df['temperature'] - 273.15
    # Drop rows with unrealistic temperature values (< -100)
    df = df[df['temperature'] > -100]
    # Check the date range
    awslist.loc[i, 'date_start'] = df['Date'].min()
    awslist.loc[i, 'date_end'] = df['Date'].max()
    print(f'Date range: {awslist.loc[i, "date_start"]} to {awslist.loc[i, "date_end"]}')
    
    # Add AWS name and prepare for export
    df['aws'] = awslist.loc[i, 'aws']
    df = df[['Date', 'temperature', 'aws']]  # Select only needed columns
    # Resample to hourly averages
    df = df.set_index('Date').resample('h').agg({
        'temperature': 'mean',
        'aws': 'first'
    }).reset_index()
    
    # Export the data
    if i == 0:
        df.to_csv('/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/TOMST_temperature.csv', mode='w', header=True, index=False)
    else:
        df.to_csv('/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/TOMST_temperature.csv', mode='a', header=False, index=False)

print('Done!')
awslist.to_csv('/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/TOMST_stations.csv', index=False, mode='w')
# %%
