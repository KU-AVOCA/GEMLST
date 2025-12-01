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
