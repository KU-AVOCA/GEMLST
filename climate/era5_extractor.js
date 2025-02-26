/*
This script extracts ERA5 Land data for GEM AWS stations.
*/

// a list of points for GEM AWS stations with temperature data
var awsPoints = ee.FeatureCollection([
    // Kobbefjord
    ee.Feature(ee.Geometry.Point([-51.37199020385742, 64.12248229980469]), {
        id: 'Kobbefjord_M500'
    }),
    
    // Disko
    ee.Feature(ee.Geometry.Point([-53.479400634765625, 69.27300262451172]), {
        id: 'Disko_T1'
    }),
    ee.Feature(ee.Geometry.Point([-53.43281936645508, 69.28909301757812]), {
        id: 'Disko_T2'
    }),
    ee.Feature(ee.Geometry.Point([-53.45709991455078, 69.2767105102539]), {
        id: 'Disko_T3'
    }),
    ee.Feature(ee.Geometry.Point([-53.49897003173828, 69.25126647949219]), {
        id: 'Disko_T4'
    }),
    ee.Feature(ee.Geometry.Point([-53.514129638671875, 69.25348663330078]), {
        id: 'Disko_AWS2'
    }),
    
    // Zackenberg
    ee.Feature(ee.Geometry.Point([-20.563194274902344, 74.46549224853516]), {
        id: 'Zackenberg_M2'
    }),
    ee.Feature(ee.Geometry.Point([-20.459354400634766, 74.50310516357422]), {
        id: 'Zackenberg_M3'
    }),
    ee.Feature(ee.Geometry.Point([-20.552143096923828, 74.47307586669922]), {
        id: 'Zackenberg_M4_30min'
    })
]);
// a list of points for TOMST sensor locations
// var awsPoints = ee.FeatureCollection([
//   // TOMST2
//   ee.Feature(ee.Geometry.Point([-53.51418, 69.25349]), {
//       id: 'TOMST2',
//       raw_identifier: 94204541
//   }),
//   // TOMST3
//   ee.Feature(ee.Geometry.Point([-53.467324, 69.265525]), {
//       id: 'TOMST3',
//       raw_identifier: 94204542
//   }),
//   // TOMST-T2-15
//   ee.Feature(ee.Geometry.Point([-53.4328202, 69.289089]), {
//       id: 'TOMST-T2-15',
//       raw_identifier: 94232447
//   }),
//   // TOMST4-15
//   ee.Feature(ee.Geometry.Point([-53.45363, 69.27282]), {
//       id: 'TOMST4-15',
//       raw_identifier: 94232448
//   }),
//   // TOMST4-30
//   ee.Feature(ee.Geometry.Point([-53.45363, 69.27282]), {
//       id: 'TOMST4-30',
//       raw_identifier: 94229981
//   })
// ]);
Map.addLayer(awsPoints, {color: 'red'}, 'AWS Points');

var date_start = ee.Date.fromYMD(2000, 1, 1),
    date_end = ee.Date.fromYMD(2024, 12, 31);

var ERA5Land = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    .select(
      ['skin_temperature', 'temperature_2m', 'soil_temperature_level_1', 'temperature_of_snow_layer',
        'surface_net_solar_radiation_sum', 'snow_albedo', 'snow_cover', 'snow_density', 'snow_depth',
        'forecast_albedo'
      ]
    )// .select('surface_net_solar_radiation', 'skin_temperature')
    .filterDate(date_start, date_end)
    .filterBounds(awsPoints);
/* extract LST data for each AWS station  
Reference: https://developers.google.com/earth-engine/tutorials/community/extract-raster-values-for-points
*/
function bufferPoints(radius, bounds) {
  return function(pt) {
    pt = ee.Feature(pt);
    return bounds ? pt.buffer(radius).bounds() : pt.buffer(radius);
  };
}

function zonalStats(ic, fc, params) {
  // Initialize internal params dictionary.
  var _params = {
    reducer: ee.Reducer.mean(),
    scale: null,
    crs: null,
    bands: null,
    bandsRename: null,
    imgProps: null,
    imgPropsRename: null,
    datetimeName: 'datetime',
    datetimeFormat: 'YYYY-MM-dd HH:mm:ss'
  };

  // Replace initialized params with provided params.
  if (params) {
    for (var param in params) {
      _params[param] = params[param] || _params[param];
    }
  }

  // Set default parameters based on an image representative.
  var imgRep = ic.first();
  var nonSystemImgProps = ee.Feature(null)
    .copyProperties(imgRep).propertyNames();
  if (!_params.bands) _params.bands = imgRep.bandNames();
  if (!_params.bandsRename) _params.bandsRename = _params.bands;
  if (!_params.imgProps) _params.imgProps = nonSystemImgProps;
  if (!_params.imgPropsRename) _params.imgPropsRename = _params.imgProps;

  // Map the reduceRegions function over the image collection.
  var results = ic.map(function(img) {
    // Select bands (optionally rename), set a datetime & timestamp property.
    img = ee.Image(img.select(_params.bands, _params.bandsRename))
      .set(_params.datetimeName, img.date().format(_params.datetimeFormat))
      .set('timestamp', img.get('system:time_start'));

    // Define final image property dictionary to set in output features.
    var propsFrom = ee.List(_params.imgProps)
      .cat(ee.List([_params.datetimeName, 'timestamp']));
    var propsTo = ee.List(_params.imgPropsRename)
      .cat(ee.List([_params.datetimeName, 'timestamp']));
    var imgProps = img.toDictionary(propsFrom).rename(propsFrom, propsTo);

    // Subset points that intersect the given image.
    var fcSub = fc.filterBounds(img.geometry());

    // Reduce the image by regions.
    return img.reduceRegions({
      collection: fcSub,
      reducer: _params.reducer,
      scale: _params.scale,
      crs: _params.crs
    })
    // Add metadata to each feature.
    .map(function(f) {
      return f.set(imgProps).set('sampleID', f.get('name'));
    });
  }).flatten().filter(ee.Filter.notNull(_params.bandsRename));

  return results;
}

// var pois = awsPoints.map(bufferPoints(30/2, true));
// print(pois)
var lstData = zonalStats(ERA5Land, awsPoints, {
    reducer: ee.Reducer.mean(),
    scale: 30,
    crs: 'EPSG:3413',
    // bands: ['ST_B10'],
    // bandsRename: ['LST'],
    // imgProps: ['system:index', 'system:time_start'],
    datetimeName: 'date',
    datetimeFormat: 'YYYY-MM-dd'
});

Export.table.toDrive({
    collection: lstData,
    description: 'GEM_AWS_ERA5Land',
    fileFormat: 'CSV',
    folder: 'gee'
});