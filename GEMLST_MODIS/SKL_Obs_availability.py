#%%
import pandas as pd
import numpy as np
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
sns.set_theme(style="darkgrid", font_scale=1.5)

#%%
sheet = pd.read_csv('./Data/Availability_pattern_sensors.csv')
patterns = pd.DataFrame(sheet)

#%%








#%%

coefficients = {
    # MODLST_Day: 1, MODLST_Night: 0, MYDLST_Day: 0, MYDLST_Night: 0
    8 : {'intercept': -1.34695967294259,  'Slope': 0.918214355203352, SW_netx: 4.53098106772407E-08,  obs_avail_flag:8},
    # MODLST_Day: 0, MODLST_Night: 0, MYDLST_Day: 1, MYDLST_Night: 0
    2 : {intercept: -2.72772961154428,  Tx: 0.864013566310192, SW_netx: -3.35940233622233E-08, obs_avail_flag:2},
    # MODLST_Day: 0, MODLST_Night: 1, MYDLST_Day: 0, MYDLST_Night: 0
    4 : {intercept: -0.482353446197247, Tx: 0.9232805167859,   SW_netx: 6.28895745791016E-07,  obs_avail_flag:4},
    # MODLST_Day: 0, MODLST_Night: 0, MYDLST_Day: 0, MYDLST_Night: 1
    1 : {intercept: -0.784992834128613, Tx: 0.906590788274843, SW_netx: 1.03669127251288E-06,  obs_avail_flag:1},
    # MODLST_Day: 1, MODLST_Night: 0, MYDLST_Day: 1, MYDLST_Night: 0
    10: {intercept: -1.87107581116087,  Tx: 0.905781514375017, SW_netx: -6.98570333719986E-08, obs_avail_flag:10},
    # MODLST_Day: 1, MODLST_Night: 1, MYDLST_Day: 0, MYDLST_Night: 0
    12: {intercept: -0.0945029361445182,Tx: 0.984136140624823, SW_netx: 6.02125454340973E-08,  obs_avail_flag:12},
    # MODLST_Day: 1, MODLST_Night: 0, MYDLST_Day: 0, MYDLST_Night: 1
    9 : {intercept:  -0.284975970024893,Tx: 0.972507056820705, SW_netx:  2.90972229423868E-07, obs_avail_flag:9},
    # MODLST_Day: 0, MODLST_Night: 1, MYDLST_Day: 1, MYDLST_Night: 0
    6 : {intercept: -0.644606390843865, Tx: 0.971834024884555, SW_netx: -7.48746592128951E-08, obs_avail_flag:6},
    # MODLST_Day: 0, MODLST_Night: 0, MYDLST_Day: 1, MYDLST_Night: 1
    3 : {intercept: -0.631502973964556, Tx: 0.976195873933907, SW_netx: 8.5668092908308E-08,   obs_avail_flag:3},
    # MODLST_Day: 0, MODLST_Night: 1, MYDLST_Day: 0, MYDLST_Night: 1
    5 : {intercept: 0.13822534121047,   Tx: 0.972898933945562, SW_netx: 6.07908419848783E-07,  obs_avail_flag:5},
    # MODLST_Day: 1, MODLST_Night: 1, MYDLST_Day: 1, MYDLST_Night: 0
    14: {intercept: -0.669653995793039, Tx: 0.970568958538719, SW_netx: -1.11444153642164E-07, obs_avail_flag:14},
    # MODLST_Day: 1, MODLST_Night: 1, MYDLST_Day: 0, MYDLST_Night: 1
    13: {intercept: 0.2080247987705,    Tx: 0.998557440221747, SW_netx: 2.29617740169069E-07,  obs_avail_flag:13},
    # MODLST_Day: 1, MODLST_Night: 0, MYDLST_Day: 1, MYDLST_Night: 1
    11: {intercept: -0.710224635510656, Tx: 0.969619217974844, SW_netx: 1.17703947635499E-08,  obs_avail_flag:11},
    # MODLST_Day: 0, MODLST_Night: 1, MYDLST_Day: 1, MYDLST_Night: 1
    7 : {intercept: -0.0074406421379301,Tx: 1.00258673602663,  SW_netx: 8.30382103055948E-08,  obs_avail_flag:7},
    # MODLST_Day: 1, MODLST_Night: 1, MYDLST_Day: 1, MYDLST_Night: 1
    15: {intercept: -0.155889791750814, Tx: 0.996384902208461, SW_netx: 2.61860711397444E-09,  obs_avail_flag:15}
}

# 3.2 Calculate Availability Pattern
def calculate_availability(aqua_day, aqua_night, terra_day, terra_night, viirs_day, viirs_night, jaxa_a, jaxa_b):
    return (aqua_day.mask().multiply(1)
        .add(aqua_night.mask().multiply(2))
        .add(terra_day.mask().multiply(4))
        .add(terra_night.mask().multiply(8))
        .add(viirs_day.mask().multiply(16))
        .add(viirs_night.mask().multiply(32))
        .add(jaxa_a.mask().multiply(64))
        .add(jaxa_b.mask().multiply(128))
    )

#%%
