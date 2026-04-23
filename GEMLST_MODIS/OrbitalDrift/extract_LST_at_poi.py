# %%
# Import packages and initialize Earth Engine

import ee
import geemap

geemap.ee_initialize()

# %%
START_YEAR = 2000
END_YEAR = 2024
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

poi = ee.FeatureCollection("projects/ee-ivanburgov666/assets/randomGR5km_masked_260423")


# %%
# Load MODIS Terra and Aqua data and convert LST from Kelvin scale to Celsius.
def lst_conversion(image):
    lst_night = image.select('LST_Night_1km').multiply(0.02).subtract(273.15).rename('LST_Night_C')
    lst_day = image.select('LST_Day_1km').multiply(0.02).subtract(273.15).rename('LST_Day_C')
    return image.addBands(lst_night).addBands(lst_day)


def get_collection(dataset_id, date_start, date_end):
    return (
        ee.ImageCollection(dataset_id)
        .select(['LST_Night_1km', 'QC_Night', 'LST_Day_1km', 'QC_Day'])
        .filterDate(date_start, date_end)
        .filterBounds(greenland)
        .map(lst_conversion)
        .select(['LST_Night_C', 'QC_Night', 'LST_Day_C', 'QC_Day'])
    )

def add_poi_id(feature):
    poi_id = feature.get('system:index')
    return ee.Feature(feature).set({'poi_id': poi_id, 'system:index': poi_id})


poi_with_id = poi.map(add_poi_id)


def prepare_collection_for_join(collection, prefix):
    def rename_and_tag(img):
        renamed = img.select(
            ['LST_Day_C', 'LST_Night_C', 'QC_Day', 'QC_Night'],
            [f'{prefix}_LST_Day_C', f'{prefix}_LST_Night_C', f'{prefix}_QC_Day', f'{prefix}_QC_Night'],
        )
        return renamed.set('date', img.date().format('YYYY-MM-dd')).set('system:time_start', img.get('system:time_start'))

    return collection.map(rename_and_tag)

def merge_joined_pair(joined_feature):
    primary = ee.Image(joined_feature.get('primary'))
    secondary = ee.Image(joined_feature.get('secondary'))
    return ee.Image.cat(primary, secondary).set('date', primary.get('date')).set('system:time_start', primary.get('system:time_start'))


def extract_collection_at_poi(collection):
    def sample_image(img):
        date = ee.String(img.get('date'))
        sampled = img.sampleRegions(
            collection=poi_with_id,
            properties=['system:index', 'poi_id'],
            scale=SCALE_M,
            tileScale=TILE_SCALE,
            geometries=False,
        )
        return sampled.map(
            lambda f: ee.Feature(f).set(
                {
                    'poi_id': f.get('poi_id'),
                    'date': date,
                }
            )
        )

    return ee.FeatureCollection(collection.map(sample_image).flatten())


def build_paired_collection_for_year(year):
    date_start = ee.Date.fromYMD(year, 1, 1)
    date_end = date_start.advance(1, 'year')

    terra = get_collection('MODIS/061/MOD11A1', date_start, date_end)
    aqua = get_collection('MODIS/061/MYD11A1', date_start, date_end)

    terra_for_join = prepare_collection_for_join(terra, 'Terra')
    aqua_for_join = prepare_collection_for_join(aqua, 'Aqua')

    time_filter = ee.Filter.equals(leftField='system:time_start', rightField='system:time_start')
    joined = ee.Join.inner().apply(terra_for_join, aqua_for_join, time_filter)

    return ee.ImageCollection(joined.map(merge_joined_pair))


def export_year(year):
    paired_collection = build_paired_collection_for_year(year)
    all_samples = extract_collection_at_poi(paired_collection)

    description = f'GEMLST_MODIS_LST_POI_{year}'
    selectors = [
        'poi_id',
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






