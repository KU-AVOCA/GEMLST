# %%
# Import packages and initialize Earth Engine

import ee
import geemap
import pandas as pd
import numpy as np
# import numpy as np
# import os
# import seaborn as sns

ee.Authenticate()
ee.Initialize(project='ee-ivanburgov666')

# %%
greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK').select('ocean_mask').eq(0)

landmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK').select('ocean_mask').eq(0).And(ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK').select('ice_mask').eq(0))

icemask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK').select('ice_mask').eq(1)

greenland = ee.Geometry.Polygon(
    [[[-36.29516924635421, 83.70737243835941],
    [-51.85180987135421, 82.75597137647488],
    [-61.43188799635421, 81.99879137488564],
    [-74.08813799635422, 78.10103528196419],
    [-70.13305987135422, 75.65372336709613],
    [-61.08032549635421, 75.71891096312955],
    [-52.20337237135421, 60.9795530382023],
    [-43.41430987135421, 58.59235996703347],
    [-38.49243487135421, 64.70478286561182],
    [-19.771731746354217, 69.72271161037442],
    [-15.728762996354217, 76.0828635948066],
    [-15.904544246354217, 79.45091003031243],
    [-10.015872371354217, 81.62328742628017],
    [-26.627200496354217, 83.43179828852398],
    [-31.636966121354217, 83.7553561747887]]])

# create a vector of month time steps
months = np.arange(1, 2, 1) # last month not inclusive! # 1,13,1
date_start_initial = ee.Date('2020-01-01') # 1041

date_end_mod = ee.Date('2025-12-31') # Before orbital drift TERRA 2020-02-27
date_end_myd = ee.Date('2025-12-31') # Before orbital drift AQUA 2021-03-18

for s in months:

    adv=int(s-1)
    date_start = ee.Date(date_start_initial.advance(adv, 'month'))
    date_end = ee.Date(date_start.advance(1, 'month')) # month
    print(f'Processing month {s}: from {date_start.format("YYYY-MM-dd").getInfo()} to {date_end.format("YYYY-MM-dd").getInfo()}')

    # Use this for single days
    # adv=int(s-1)
    # date_start = ee.Date(date_start_initial.advance(adv, 'month'))
    # date_end = ee.Date(date_start.advance(1, 'day')) # month
    # print(f'Processing month {s}: from {date_start.format("YYYY-MM-dd").getInfo()} to {date_end.format("YYYY-MM-dd").getInfo()}')


    # %%

    lookup_ice = ee.FeatureCollection('projects/ee-ivanburgov666/assets/coefficients_ice_alle')
    lookup_land = ee.FeatureCollection('projects/ee-ivanburgov666/assets/coefficients_land_doublettes')


    # %%
    # Mask data based on quality flags

    def bitwiseExtract(input, fromBit, toBit):
        maskSize = ee.Number(1).add(toBit).subtract(fromBit)
        mask = ee.Number(1).leftShift(maskSize).subtract(1)
        return input.rightShift(fromBit).bitwiseAnd(mask)

    def maskQualityDaytime(image):
        qa = image.select('QC_Day')

        # Bits 0-"1": Mandatory QA flags
        # "0": LST produced, good quality, not necessary to examine more detailed QA
        # "1": LST produced, other quality, recommend examination of more detailed QA
        # "2": LST not produced due to cloud effects
        # "3": LST not produced primarily due to reasons other than cloud
        bits01Mask = bitwiseExtract(qa, 0, 1).lte(1); 
        # Bits 2-"3": Data quality flag
        # "0": Good data quality
        # "1": Other quality data
        # "2": TBD
        # "3": TBD
        bits23Mask = bitwiseExtract(qa, 2, 3).eq(0)
        # Bits 4-"5": Emissivity error flag
        # "0": Average emissivity error <= 0.01
        # "1": 0.01 < Average emissivity error <= 0.02
        # "2": 0.02 < Average emissivity error <= 0.04
        # "3": Average emissivity error > 0.04
        bits45Mask = bitwiseExtract(qa, 4, 5).eq(0)
        # Bit 6-"7": LST error flag
        # "0": Average LST error <= 1K
        # "1": Average LST error <= 2K
        # "2": Average LST error <= 3K
        # "3": Average LST error > 3K
        bit6Mask = bitwiseExtract(qa, 6, 7).lte(1)

        mask = bits01Mask.And(bits23Mask).And(bits45Mask).And(bit6Mask)

        return image.updateMask(mask)

    def maskQualityNighttime(image):
        qa = image.select('QC_Night')

        # Bits 0-"1": Mandatory QA flags
        # "0": LST produced, good quality, not necessary to examine more detailed QA
        # "1": LST produced, other quality, recommend examination of more detailed QA
        # "2": LST not produced due to cloud effects
        # "3": LST not produced primarily due to reasons other than cloud
        bits01Mask = bitwiseExtract(qa, 0, 1).lte(1); 
        # Bits 2-"3": Data quality flag
        # "0": Good data quality
        # "1": Other quality data
        # "2": TBD
        # "3": TBD
        bits23Mask = bitwiseExtract(qa, 2, 3).eq(0)
        # Bits 4-"5": Emissivity error flag
        # "0": Average emissivity error <= 0.01
        # "1": 0.01 < Average emissivity error <= 0.02
        # "2": 0.02 < Average emissivity error <= 0.04
        # "3": Average emissivity error > 0.04
        bits45Mask = bitwiseExtract(qa, 4, 5).eq(0)
        # Bit 6-"7": LST error flag
        # "0": Average LST error <= 1K
        # "1": Average LST error <= 2K
        # "2": Average LST error <= 3K
        # "3": Average LST error > 3K
        bit6Mask = bitwiseExtract(qa, 6, 7).lte(1)

        mask = bits01Mask.And(bits23Mask).And(bits45Mask).And(bit6Mask)

        return image.updateMask(mask)


    def maskJaxa(image):
        # '''Function to filter JAXA GCOM-C LST data based on quality flag.'''
        # qa = image.select('LST_QA_flag')
        # #0: water (land fraction = 0%)
        # #1: mostly water (0% < land fraction < 50%)
        # #2: mostly coastal (50% < land fraction < 100%) - included
        # #3: land (land fraction = 100%) - included
        # mask = qa.gt(1)
        return image.updateMask(icemask) 

    def maskViirs(image):
        '''Function to filter VIIRS LST data based on quality flag.'''
        qa = image.select('QC')
        bits01Mask = bitwiseExtract(qa, 0, 1).eq(0); 
        # Bits 0-1: Mandatory QA flags
        # 0: Pixel produced, good quality, no further QA info necessary
        # 1: Pixel produced but unreliable quality
        # 2: Pixel not produced due to cloud
        # 3: Pixel not produced due to reasons other than cloud

        bits23Mask = bitwiseExtract(qa, 2, 3).eq(0)
        # Bits 2-3: Data quality flag
        # 0: Good data quality of L1B bands 14, 15, 16
        # 1: Missing pixel
        # 2: Fairly calibrated
        # 3: Poorly calibrated, TES processing skipped

        bits45Mask = bitwiseExtract(qa, 4, 5).eq(0)
        # Bits 4-5: Cloud Flag
        # 0: Cloud-free
        # 1: Thin cirrus
        # 2: Pixel within 2 pixels of nearest cloud
        # 3: Cloudy pixels

        # Bits 6-7: Iterations
        # 0: Slow convergence
        # 1: Nominal
        # 2: Nominal
        # 3: Fast

        # Bits 8-9: Atmospheric Opacity
        # 0: ≥3 (Warm, humid air; or cold land)
        # 1: 0.2 - 0.3 (Nominal value)
        # 2: 0.1 - 0.2 (Nominal value)
        # 3: <0.1 (Dry, or high altitude pixel)

        # Bits 10-11: MMD
        # 0: >0.15 (Most silicate rocks)
        # 1: 0.1 - 0.15 (Rocks, sand, some soils)
        # 2: 0.03 - 0.1 (Mostly soils, mixed pixel)
        # 3: <0.03 (Vegetation, snow, water, ice, some soils)

        bit1213Mask = bitwiseExtract(qa, 12, 13).gte(2)
        # Bits 12-13: Emissivity accuracy
        # 0: >0.02 (Poor performance)
        # 1: 0.015 - 0.02 (Marginal performance)
        # 2: 0.01 - 0.015 (Good performance)
        # 3: <0.01 (Excellent performance)

        bit1415Mask = bitwiseExtract(qa, 14, 15).gte(2)
        # Bits 14-15: LST accuracy
        # 0: >2K (Poor performance)
        # 1: 1.5 - 2K (Marginal performance)
        # 2: 1 - 1.5K (Good performance)
        # 3: <1K (Excellent performance)
        
        mask = bits01Mask.And(bits23Mask).And(bits45Mask).And(bit1213Mask).And(bit1415Mask)
        return image.updateMask(mask)



    # %%
    # Functions for band selection and conversion

    # ERA5 (full scale)
    def era5_t2m(image):
        'ERA5 2m air temperature conversion'
        t2m = image.select('mean_2m_air_temperature').subtract(273.15).rename('ERA5_T2m')
        return image.addBands(t2m)

    # MODIS
    def lst_mod_day(image):
        'Terra Day band selection and conversion'
        lst_day = image.select('LST_Day_1km').multiply(0.02).subtract(273.15).rename('MOD_LST_Day')
        qa_day = image.select('QC_Day').rename('MOD_QA_Day')
        return image.addBands(lst_day).addBands(qa_day)

    def lst_mod_night(image):
        'Terra Night band selection and conversion'
        lst_night = image.select('LST_Night_1km').multiply(0.02).subtract(273.15).rename('MOD_LST_Night')
        qa_night = image.select('QC_Night').rename('MOD_QA_Night')
        return image.addBands(lst_night).addBands(qa_night)

    def lst_myd_day(image):
        'Aqua Day band selection and conversion'
        lst_day = image.select('LST_Day_1km').multiply(0.02).subtract(273.15).rename('MYD_LST_Day')
        qa_day = image.select('QC_Day').rename('MYD_QA_Day')
        return image.addBands(lst_day).addBands(qa_day)

    def lst_myd_night(image):
        'Aqua Night band selection and conversion'
        lst_night = image.select('LST_Night_1km').multiply(0.02).subtract(273.15).rename('MYD_LST_Night')
        qa_night = image.select('QC_Night').rename('MYD_QA_Night')
        return image.addBands(lst_night).addBands(qa_night)


    # JAXA
    def lst_jaxa_a(image):
        'JAXA GCOM-C band selection and conversion'
        lst_ave = image.select('LST_AVE').multiply(0.02).subtract(273.15).rename('JAXA_LST_A')
        qa_flag = image.select('LST_QA_flag')
        return image.addBands(lst_ave).addBands(qa_flag)

    def lst_jaxa_d(image):
        'JAXA GCOM-C band selection and conversion'
        lst_ave = image.select('LST_AVE').multiply(0.02).subtract(273.15).rename('JAXA_LST_D')
        qa_flag = image.select('LST_QA_flag')
        return image.addBands(lst_ave).addBands(qa_flag)


    # VIIRS 
    def lst_viirs_d(image):
        'VIIRS band selection and conversion'
        lst = image.select('LST_1KM').subtract(273.15).rename('VIIRS_LST_D')
        return image.addBands(lst)

    def lst_viirs_n(image):
        'VIIRS band selection and conversion'
        lst = image.select('LST_1KM').subtract(273.15).rename('VIIRS_LST_N')
        return image.addBands(lst)



    # Load MODIS Terra and Aqua data, apply quality control and conversion functions

    ERA5 = (
        ee.ImageCollection("ECMWF/ERA5/DAILY")
        .select(['mean_2m_air_temperature'])
        .filterDate(date_start, date_end)
        .filterBounds(greenland)
        .map(era5_t2m)
    )

    MOD11A1Daytime = (
        ee.ImageCollection('MODIS/061/MOD11A1')
        .select(['LST_Day_1km', 'QC_Day'])
        .filterDate(date_start, date_end)
        .filterDate(date_start, date_end_mod)
        .filterBounds(greenland)
        .map(maskQualityDaytime)
        .map(lst_mod_day)
    )

    MOD11A1Nighttime = (
        ee.ImageCollection('MODIS/061/MOD11A1')
        .select(['LST_Night_1km', 'QC_Night'])
        .filterDate(date_start, date_end)
        .filterDate(date_start, date_end_mod)
        .filterBounds(greenland)
        .map(maskQualityNighttime)
        .map(lst_mod_night)
    )

    MYD11A1Daytime = (
        ee.ImageCollection('MODIS/061/MYD11A1')
        .select(['LST_Day_1km', 'QC_Day'])
        .filterDate(date_start, date_end)
        .filterDate(date_start, date_end_myd)
        .filterBounds(greenland)
        .map(maskQualityDaytime)
        .map(lst_myd_day)
    )

    MYD11A1Nighttime = (
        ee.ImageCollection('MODIS/061/MYD11A1')
        .select(['LST_Night_1km', 'QC_Night'])
        .filterDate(date_start, date_end)
        .filterDate(date_start, date_end_myd)
        .filterBounds(greenland)
        .map(maskQualityNighttime)
        .map(lst_myd_night)
    )

    JAXA_A = (
        ee.ImageCollection('JAXA/GCOM-C/L3/LAND/LST/V3')
        .select(['LST_AVE', 'LST_QA_flag'])
        .filter(ee.Filter.eq('SATELLITE_DIRECTION', 'A')) # Filter for ascending (AM) overpasses
        .filter(ee.Filter.eq('PROCESSING_RESULT', 'Good')) 
        .filterDate(date_start, date_end)
        .filterBounds(greenland)
        .map(maskJaxa)
        .map(lst_jaxa_a)
    )

    JAXA_D = (
        ee.ImageCollection('JAXA/GCOM-C/L3/LAND/LST/V3')
        .select(['LST_AVE', 'LST_QA_flag'])
        .filter(ee.Filter.eq('SATELLITE_DIRECTION', 'D')) # Filter for descending (PM) overpasses
        .filter(ee.Filter.eq('PROCESSING_RESULT', 'Good')) 
        .filterDate(date_start, date_end)
        .filterBounds(greenland)
        .map(maskJaxa)
        .map(lst_jaxa_d)
    )


    VIIRS_Day = (
        ee.ImageCollection("NASA/VIIRS/002/VNP21A1D")
        .filterDate(date_start, date_end)
        .filterBounds(greenland)
        .map(maskViirs)
        .map(lst_viirs_d)
    )


    VIIRS_Night = (
        ee.ImageCollection("NASA/VIIRS/002/VNP21A1N") 
        .filterDate(date_start, date_end)
        .filterBounds(greenland)
        .map(maskViirs)
        .map(lst_viirs_n)
    )

    # %%
    # Create a common matching property ("date") on both collections, then link by that key.
    def add_date_prop(img):
        return img.set('date', ee.Date(img.get('system:time_start')).format('YYYY-MM-dd'))

    ERA5_by_date = ERA5.map(add_date_prop)
    MOD11A1Daytime_by_date = MOD11A1Daytime.map(add_date_prop)
    MOD11A1Nighttime_by_date = MOD11A1Nighttime.map(add_date_prop)
    MYD11A1Daytime_by_date = MYD11A1Daytime.map(add_date_prop)
    MYD11A1Nighttime_by_date = MYD11A1Nighttime.map(add_date_prop)
    JAXA_A_by_date = JAXA_A.map(add_date_prop)
    JAXA_D_by_date = JAXA_D.map(add_date_prop)
    VIIRS_Day_by_date = VIIRS_Day.map(add_date_prop)
    VIIRS_Night_by_date = VIIRS_Night.map(add_date_prop)

    sat_stack = (
        ERA5_by_date.select('ERA5_T2m')
        .linkCollection(
            MOD11A1Daytime_by_date.select('MOD_LST_Day'),
            linkedBands=['MOD_LST_Day'],
            linkedProperties=['system:time_start'],
            matchPropertyName='date'
        )
        .linkCollection(MOD11A1Nighttime_by_date.select('MOD_LST_Night'), linkedBands=['MOD_LST_Night'], linkedProperties=['system:time_start'], matchPropertyName='date')
        .linkCollection(MYD11A1Daytime_by_date.select('MYD_LST_Day'), linkedBands=['MYD_LST_Day'], linkedProperties=['system:time_start'], matchPropertyName='date')
        .linkCollection(MYD11A1Nighttime_by_date.select('MYD_LST_Night'), linkedBands=['MYD_LST_Night'], linkedProperties=['system:time_start'], matchPropertyName='date')
        .linkCollection(JAXA_A_by_date.select('JAXA_LST_A'), linkedBands=['JAXA_LST_A'], linkedProperties=['system:time_start'], matchPropertyName='date')
        .linkCollection(JAXA_D_by_date.select('JAXA_LST_D'), linkedBands=['JAXA_LST_D'], linkedProperties=['system:time_start'], matchPropertyName='date')
        .linkCollection(VIIRS_Day_by_date.select('VIIRS_LST_D'), linkedBands=['VIIRS_LST_D'], linkedProperties=['system:time_start'], matchPropertyName='date')
        .linkCollection(VIIRS_Night_by_date.select('VIIRS_LST_N'), linkedBands=['VIIRS_LST_N'], linkedProperties=['system:time_start'], matchPropertyName='date')
    )


    # %%
    # Calculate Availability Pattern
    def calculateAvailability(terra_day, terra_night, aqua_day, aqua_night, viirs_day, viirs_night, jaxa_a, jaxa_b):
        '''Calculates a unique pattern ID in bit format based on the availability of the sensors'''
        return (terra_day.mask().multiply(1)
            .add(terra_night.mask().multiply(2))
            .add(aqua_day.mask().multiply(4))
            .add(aqua_night.mask().multiply(8))
            .add(viirs_day.mask().multiply(16))
            .add(viirs_night.mask().multiply(32))
            .add(jaxa_a.mask().multiply(64))
            .add(jaxa_b.mask().multiply(128))
        )


    def applyCorrection(image):
        MODLST_DAY_avail = image.select('MOD_LST_Day')
        MODLST_NIGHT_avail = image.select('MOD_LST_Night')
        MYDLST_DAY_avail = image.select('MYD_LST_Day')
        MYDLST_NIGHT_avail = image.select('MYD_LST_Night')
        VIIRS_DAY_avail = image.select('VIIRS_LST_D')
        VIIRS_NIGHT_avail = image.select('VIIRS_LST_N')
        JAXA_A_avail = image.select('JAXA_LST_A')
        JAXA_D_avail = image.select('JAXA_LST_D')

        availPattern = calculateAvailability(
            MODLST_DAY_avail,
            MODLST_NIGHT_avail,
            MYDLST_DAY_avail,
            MYDLST_NIGHT_avail,
            VIIRS_DAY_avail,
            VIIRS_NIGHT_avail,
            JAXA_A_avail,
            JAXA_D_avail
        )

        availPatternUnique = availPattern.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=greenland,
            scale=1000,
            maxPixels=1e13,
            crs='EPSG:3413'
        )

        band_name = ee.String(availPattern.bandNames().get(0))
        hist_dict = ee.Dictionary(availPatternUnique.get(band_name))
        availPatternUniqueKeys = ee.List(hist_dict.keys()) \
            .map(lambda k: ee.Number.parse(k)) \
            .filter(ee.Filter.neq('item', 0))

        LSTimage = image.select(
            ['MOD_LST_Day', 'MOD_LST_Night', 'MYD_LST_Day', 'MYD_LST_Night', 'VIIRS_LST_D', 'VIIRS_LST_N', 'JAXA_LST_A', 'JAXA_LST_D']
        ).reduce(ee.Reducer.mean())

        def applyLandCoefficient(key, correctedLST):
            numericKey = ee.Number(key).toInt()
            coeff = lookup_land.filter(ee.Filter.eq('ID', numericKey)).first()
            intercept = ee.Number(coeff.get('intercept_before'))
            slope = ee.Number(coeff.get('coef_before'))

            patternMask = availPattern.eq(numericKey)
            calibratedLST_land = LSTimage.multiply(slope).add(intercept) \
                .updateMask(patternMask) \
                .unmask(0)

            return ee.Image(correctedLST).add(calibratedLST_land)

        def applyIceCoefficient(key, correctedLST):
            numericKey = ee.Number(key).toInt()
            coeff = lookup_ice.filter(ee.Filter.eq('ID', numericKey)).first()
            intercept = ee.Number(coeff.get('intercept_before'))
            slope = ee.Number(coeff.get('coef_before'))

            patternMask = availPattern.eq(numericKey)
            calibratedLST_ice = LSTimage.multiply(slope).add(intercept) \
                .updateMask(patternMask) \
                .unmask(0)

            return ee.Image(correctedLST).add(calibratedLST_ice)

        correctedLST_land = availPatternUniqueKeys.iterate(applyLandCoefficient, ee.Image(0))
        correctedLST_ice = availPatternUniqueKeys.iterate(applyIceCoefficient, ee.Image(0))

        below0 = ee.Image(correctedLST_ice).lte(0)
        correctedLST_ice = ee.Image(correctedLST_ice).updateMask(below0)

        correctedLST = ee.Image(correctedLST_land).updateMask(landmask).unmask(0).add(
            correctedLST_ice.updateMask(icemask).unmask(0)
        )

        return image.addBands([
            ee.Image(correctedLST).rename('Corrected_LST').updateMask(greenlandmask).toDouble(),
            availPattern.rename('Available_Pattern').updateMask(greenlandmask).toDouble()
        ])



    # %%
    corrected_collection = sat_stack.map(applyCorrection)



    # %%

    # Export each image in the corrected_collection to Google Drive
    col = corrected_collection.select(['Corrected_LST', 'Available_Pattern'])
    col_list = col.toList(col.size())
    n = col_list.size().getInfo()

    for i in range(n):
        img = ee.Image(col_list.get(i))
        idx = img.get('system:index').getInfo()
        desc = f'GEMLST_MODIS_{idx}'
        task = ee.batch.Export.image.toDrive(
            image=img,
            description=desc,
            folder='GEMLST_MODIS',
            fileNamePrefix=desc,
            scale=1000,
            region=greenland,
            crs='EPSG:3413',
            maxPixels=1e13
        )
        task.start()
        print(f'Started task: {desc}')

    print(f'Finished month {s}\n')

    # %%




# %%
