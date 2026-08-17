"""Extract MODIS Terra/Aqua day/night LST at POIs.

The output is split into four independent tables so downstream scripts can
join observations later by object_id and date.
"""

import ee


ee.Authenticate()
ee.Initialize(project='ee-ivanburgov666')


START_YEAR = 2002
END_YEAR = 2002
EXPORT_FOLDER = 'GEMLST_MODIS'
TILE_SCALE = 8
SCALE_M = 1000

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
      [-31.636966121354217, 83.7553561747887]]]
)

poi = ee.FeatureCollection('projects/ee-ivanburgov666/assets/randomGR5km_masked_260508')


def bitwise_extract(value, from_bit, to_bit):
    mask_size = ee.Number(1).add(to_bit).subtract(from_bit)
    mask = ee.Number(1).leftShift(mask_size).subtract(1)
    return value.rightShift(from_bit).bitwiseAnd(mask)


def mask_quality_daytime(image):
    qa = image.select('QC_Day')
    mask = (
        bitwise_extract(qa, 0, 1).lte(1)
        .And(bitwise_extract(qa, 2, 3).eq(0))
        .And(bitwise_extract(qa, 4, 5).eq(0))
        .And(bitwise_extract(qa, 6, 7).lte(1))
    )
    return image.updateMask(mask)


def mask_quality_nighttime(image):
    qa = image.select('QC_Night')
    mask = (
        bitwise_extract(qa, 0, 1).lte(1)
        .And(bitwise_extract(qa, 2, 3).eq(0))
        .And(bitwise_extract(qa, 4, 5).eq(0))
        .And(bitwise_extract(qa, 6, 7).lte(1))
    )
    return image.updateMask(mask)


def add_celsius_band(image, source_band, output_band):
    converted = image.select(source_band).multiply(0.02).subtract(273.15).rename(output_band)
    return image.addBands(converted)


def build_collection(dataset_id, source_band, qc_band, output_band, mask_fn):
    return (
        ee.ImageCollection(dataset_id)
        .select([source_band, qc_band])
        .filterBounds(greenland)
        .map(mask_fn)
        .map(lambda image: add_celsius_band(image, source_band, output_band))
        .select([output_band, qc_band])
    )


def prepare_image(image, prefix, value_band, qc_band):
    return (
        image.select([value_band, qc_band], [f'{prefix}_{value_band}', f'{prefix}_{qc_band}'])
        .set('date', image.date().format('YYYY-MM-dd'))
        .set('system:time_start', image.get('system:time_start'))
    )


def build_yearly_samples(year, dataset_id, prefix, source_band, qc_band, output_band, mask_fn):
    date_start = ee.Date.fromYMD(year, 1, 1)
    date_end = date_start.advance(1, 'year')

    collection = build_collection(dataset_id, source_band, qc_band, output_band, mask_fn)
    yearly_collection = collection.filterDate(date_start, date_end).map(
        lambda image: prepare_image(image, prefix, output_band, qc_band)
    )

    def sample_image(image):
        date = ee.String(image.get('date'))
        sampled = image.sampleRegions(
            collection=poi,
            properties=['object_id', 'class'],
            scale=SCALE_M,
            tileScale=TILE_SCALE,
            geometries=False,
        )
        return sampled.map(
            lambda feature: ee.Feature(feature).set(
                {
                    'date': date,
                    'sensor': prefix,
                }
            )
        )

    return ee.FeatureCollection(yearly_collection.map(sample_image).flatten())


def export_collection(collection, description):
    task = ee.batch.Export.table.toDrive(
        collection=collection,
        description=description,
        fileFormat='CSV',
        folder=EXPORT_FOLDER,
    )
    task.start()
    print(f'Started export task: {description}')


for year in range(START_YEAR, END_YEAR + 1):
    terra_day = build_yearly_samples(
        year,
        'MODIS/061/MOD11A1',
        'Terra_day',
        'LST_Day_1km',
        'QC_Day',
        'LST_Day_C',
        mask_quality_daytime,
    )
    terra_night = build_yearly_samples(
        year,
        'MODIS/061/MOD11A1',
        'Terra_night',
        'LST_Night_1km',
        'QC_Night',
        'LST_Night_C',
        mask_quality_nighttime,
    )
    aqua_day = build_yearly_samples(
        year,
        'MODIS/061/MYD11A1',
        'Aqua_day',
        'LST_Day_1km',
        'QC_Day',
        'LST_Day_C',
        mask_quality_daytime,
    )
    aqua_night = build_yearly_samples(
        year,
        'MODIS/061/MYD11A1',
        'Aqua_night',
        'LST_Night_1km',
        'QC_Night',
        'LST_Night_C',
        mask_quality_nighttime,
    )

    export_collection(terra_day, f'GEMLST_MODIS_Terra_day_POI_{year}')
    export_collection(terra_night, f'GEMLST_MODIS_Terra_night_POI_{year}')
    export_collection(aqua_day, f'GEMLST_MODIS_Aqua_day_POI_{year}')
    export_collection(aqua_night, f'GEMLST_MODIS_Aqua_night_POI_{year}')

print('All export tasks submitted.')