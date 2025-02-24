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
    'Kobbefjord_M500': {
        'lat': 64.12248229980469,
        'lon': -51.37199020385742,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/2_Kobbefjord/3_ClimateData/M500_10.17897_7MSK-4190/M500_10.17897_7MSK-4190_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'SurfaceTemperature (°C)'
    },
    'Disko_T1': {
        'lat': 69.27300262451172,
        'lon': -53.479400634765625,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/T1-Temperature_125m_10.17897_ZHA1-YC59/T1-Temperature_125m_10.17897_ZHA1-YC59_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground surface temperature_°C'
    },
    'Disko_T2': {
        'lat': 69.28909301757812,
        'lon': -53.43281936645508,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/T2-Temperature_830m_10.17897_1QY7-Q102/T2-Temperature_830m_10.17897_1QY7-Q102_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground surface temperature_°C'
    },
    'Disko_T3': {
        'lat': 69.2767105102539,
        'lon': -53.45709991455078,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/T3-Temperature_400m_10.17897_CFES-BX22/T3-Temperature_400m_10.17897_CFES-BX22_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground surface temperature_°C'
    },
    'Disko_T4': {
        'lat': 69.25126647949219,
        'lon': -53.49897003173828,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/T4-Temperature_1m_10.17897_QDGE-TH28/T4-Temperature_1m_10.17897_QDGE-TH28_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground surface temperature_°C'
    },
    'Disko_AWS2': {
        'lat': 69.25348663330078,
        'lon': -53.514129638671875, 
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/3_Disko/1_ClimateData/AWS2-Meteorology_10.17897_CSZT-F010/AWS2-Meteorology_10.17897_CSZT-F010_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC-3',
        'temp_var': 'Ground temperature_°C'
    },
    'Zackenberg_M2': {
        'lat': 74.46549224853516,
        'lon': -20.563194274902344,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/4_Zackenberg/1_ClimateData/M2_10.17897_7WAM-6143/M2_10.17897_7WAM-6143_data.txt',
        'temp_unit': 'kelvin',
        'time_zone': 'UTC',
        'temp_var': 'Temp ground °K'
    },
    'Zackenberg_M3': {
        'lat': 74.50310516357422,
        'lon': -20.459354400634766,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/4_Zackenberg/1_ClimateData/M3_10.17897_7JXY-VX51/M3_10.17897_7JXY-VX51_data.txt',
        'temp_unit': 'kelvin',
        'time_zone': 'UTC',
        'temp_var': 'Temp ground °K'
    },
    'Zackenberg_M4': {
        'lat': 74.47307586669922,
        'lon': -20.552143096923828,
        'filepath': '/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/4_Zackenberg/1_ClimateData/M4_30min_10.17897_ZNKG-K687/M4_30min_10.17897_ZNKG-K687_data.txt',
        'temp_unit': 'celcius',
        'time_zone': 'UTC',
        'temp_var': 'Surface temperature avg °C'
    }
}
# Convert AWS dictionary to DataFrame
awslist = pd.DataFrame.from_dict(awslist, orient='index')
awslist = awslist.reset_index().rename(columns={'index': 'aws'})
awslist['date_start'] = pd.to_datetime('')
awslist['date_end'] = pd.to_datetime('')
# Export the AWS list to a CSV file
awslist.to_csv('/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/AWS/aws_stations.csv', index=False)
# %% check the date range of each AWS station and save the
#  temperature to a new CSV file.
for i in range(awslist.shape[0]):
    print(f'Processing {awslist.loc[i, "aws"]}...')
    # read selected columns from the AWS data file
    # Try reading with 'Time' column first, if not available, try 'Time (UTC-3)'
    try:
        df = pd.read_csv(awslist.loc[i, 'filepath'], delimiter='\t', usecols=['Date', awslist.loc[i, 'temp_var'], 'Time'])
    except ValueError:
        df = pd.read_csv(awslist.loc[i, 'filepath'], delimiter='\t', usecols=['Date', awslist.loc[i, 'temp_var'], 'Time (UTC-3)'])
        df = df.rename(columns={'Time (UTC-3)': 'Time'})
    df['Date'] = pd.to_datetime(df['Date'])
    # Parse the time string and combine with date, adjusting for timezone
    df['Time'] = pd.to_datetime(df['Time'], format='mixed').dt.time
    # Drop rows with NaN or NaT values
    df = df.dropna(subset=['Date', awslist.loc[i, 'temp_var'], 'Time'])
    df['datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
    if awslist.loc[i, 'time_zone'] == 'UTC-3':
        df['datetime'] = df['datetime'] + pd.Timedelta(hours=3)
    df['Date'] = df['datetime']
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
        df.to_csv('/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_temperature.csv', mode='w', header=True, index=False)
    else:
        df.to_csv('/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_temperature.csv', mode='a', header=False, index=False)

print('Done!')
awslist.to_csv('/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/Landsat_LST/data/aws_stations.csv', index=False, mode='w')
# %%
