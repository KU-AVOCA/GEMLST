# Add VIIRS and cloud filters, then download again, also for MODIS


# %%
# Import packages and initialize Earth Engine

import ee
import geemap

ee.Authenticate()
ee.Initialize(project='ee-ivanburgov666')

# %%
START_YEAR = 2004
END_YEAR = 2025 # 2002 already downloaded
EXPORT_FOLDER = 'GEMLST_MODIS'
TILE_SCALE = 8
SCALE_M = 1000

greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK').select('ocean_mask').eq(0)
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

poi = ee.FeatureCollection("projects/ee-ivanburgov666/assets/randomGR5km_masked_260508")


# %%
# Load MODIS Terra and Aqua data and convert LST from Kelvin scale to Celsius.
def lst_conversion_day(image):
    lst_day = image.select('LST_Day_1km').multiply(0.02).subtract(273.15).rename('LST_Day_C')
    return image.addBands(lst_day)


def lst_conversion_night(image):
    lst_night = image.select('LST_Night_1km').multiply(0.02).subtract(273.15).rename('LST_Night_C')
    return image.addBands(lst_night)

# Bitwise QA filter
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


def get_day_collection(dataset_id, date_start, date_end):
    return (
        ee.ImageCollection(dataset_id)
        .select(['LST_Day_1km', 'QC_Day'])
        .filterDate(date_start, date_end)
        .filterBounds(greenland)
        .map(maskQualityDaytime)
        .map(lst_conversion_day)
        .select(['LST_Day_C', 'QC_Day'])
    )


def get_night_collection(dataset_id, date_start, date_end):
    return (
        ee.ImageCollection(dataset_id)
        .select(['LST_Night_1km', 'QC_Night'])
        .filterDate(date_start, date_end)
        .filterBounds(greenland)
        .map(maskQualityNighttime)
        .map(lst_conversion_night)
        .select(['LST_Night_C', 'QC_Night'])
    )

def add_poi_id(feature):
    poi_id = feature.get('object_id')
    cls = feature.get('class')
    return ee.Feature(feature).set({'object_id': poi_id, 'class': cls})


poi_with_id = poi.map(add_poi_id)

def prepare_collection_for_join(collection, prefix, bands):
    def rename_and_tag(img):
        renamed = img.select(
            bands,
            [f'{prefix}_{band}' for band in bands],
        )
        return renamed.set('date', img.date().format('YYYY-MM-dd')).set('system:time_start', img.get('system:time_start'))

    return collection.map(rename_and_tag)


def extract_collection_at_poi(collection):
    def sample_image(img):
        date = ee.String(img.get('date'))
        sampled = img.sampleRegions(
            collection=poi_with_id,
            properties=['object_id', 'class'],
            scale=SCALE_M,
            tileScale=TILE_SCALE,
            geometries=False,
        )
        return sampled.map(
            lambda f: ee.Feature(f).set(
                {
                    'object_id': f.get('object_id'),
                    'class': f.get('class'),
                    'date': date,
                    'sample_key': ee.String(f.get('object_id')).cat('_').cat(ee.String(f.get('class'))).cat('_').cat(date),
                }
            )
        )

    return ee.FeatureCollection(collection.map(sample_image).flatten())


def merge_feature_join(joined_feature, match_property):
    primary = ee.Feature(joined_feature)
    matched = primary.get(match_property)

    return ee.Feature(
        ee.Algorithms.If(
            matched,
            primary.copyProperties(ee.Feature(matched), ee.Feature(matched).propertyNames()),
            primary,
        )
    )


def outer_join_feature_collections(primary, secondary, match_property):
    key_filter = ee.Filter.equals(leftField='sample_key', rightField='sample_key')
    joined = ee.Join.saveFirst(match_property).apply(primary, secondary, key_filter)
    primary_joined = ee.FeatureCollection(joined.map(lambda f: merge_feature_join(f, match_property)))
    secondary_only = ee.FeatureCollection(ee.Join.inverted().apply(secondary, primary, key_filter))
    return primary_joined.merge(secondary_only)


def build_sensor_collection_for_year(year, dataset_id, prefix):
    date_start = ee.Date.fromYMD(year, 1, 1)
    date_end = date_start.advance(1, 'year')

    day_collection = prepare_collection_for_join(
        get_day_collection(dataset_id, date_start, date_end),
        prefix,
        ['LST_Day_C', 'QC_Day'],
    )
    night_collection = prepare_collection_for_join(
        get_night_collection(dataset_id, date_start, date_end),
        prefix,
        ['LST_Night_C', 'QC_Night'],
    )

    day_samples = extract_collection_at_poi(day_collection)
    night_samples = extract_collection_at_poi(night_collection)

    return outer_join_feature_collections(day_samples, night_samples, f'{prefix}_night_match')


def build_paired_collection_for_year(year):
    terra = build_sensor_collection_for_year(year, 'MODIS/061/MOD11A1', 'Terra')
    aqua = build_sensor_collection_for_year(year, 'MODIS/061/MYD11A1', 'Aqua')

    return outer_join_feature_collections(terra, aqua, 'aqua_match')


def export_year(year):
    paired_collection = build_paired_collection_for_year(year)
    all_samples = paired_collection

    description = f'GEMLST_MODIS_LST_POI_{year}_new'
    selectors = [
        'object_id',
        'class',
        'date',
        'Terra_LST_Day_C',
        'Terra_LST_Night_C',
        'Terra_QC_Day',
        'Terra_QC_Night',
        'Aqua_LST_Day_C',
        'Aqua_LST_Night_C',
        'Aqua_QC_Day',
        'Aqua_QC_Night',
    ]

    task = ee.batch.Export.table.toDrive(
        collection=all_samples,
        description=description,
        fileFormat='CSV',
        folder=EXPORT_FOLDER,
        selectors=selectors,
    )
    task.start()
    print(f'Started export task: {description}')


for year in range(START_YEAR, END_YEAR + 1):
    export_year(year)
print('All yearly export tasks submitted.')






