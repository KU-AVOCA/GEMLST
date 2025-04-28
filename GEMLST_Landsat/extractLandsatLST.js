/*
This script extracts Landsat LST USGS products for GEM AWS stations.
*/

// a list of points for GEM AWS stations with temperature data
// var awsPoints = ee.FeatureCollection([
//     // Kobbefjord
//     ee.Feature(ee.Geometry.Point([-51.37199020385742, 64.12248229980469]), {
//         id: 'Kobbefjord_M500'
//     }),
    
//     // Disko
//     ee.Feature(ee.Geometry.Point([-53.479400634765625, 69.27300262451172]), {
//         id: 'Disko_T1'
//     }),
//     ee.Feature(ee.Geometry.Point([-53.43281936645508, 69.28909301757812]), {
//         id: 'Disko_T2'
//     }),
//     ee.Feature(ee.Geometry.Point([-53.45709991455078, 69.2767105102539]), {
//         id: 'Disko_T3'
//     }),
//     ee.Feature(ee.Geometry.Point([-53.49897003173828, 69.25126647949219]), {
//         id: 'Disko_T4'
//     }),
    
//     // Zackenberg
//     ee.Feature(ee.Geometry.Point([-20.563194274902344, 74.46549224853516]), {
//         id: 'Zackenberg_M2'
//     }),
//     ee.Feature(ee.Geometry.Point([-20.459354400634766, 74.50310516357422]), {
//         id: 'Zackenberg_M3'
//     }),
//     ee.Feature(ee.Geometry.Point([-20.552143096923828, 74.47307586669922]), {
//         id: 'Zackenberg_M4_30min'
//     })
// ]);
// a list of points for TOMST sensor locations
var awsPoints = ee.FeatureCollection([
  // TOMST2
  ee.Feature(ee.Geometry.Point([-53.51418, 69.25349]), {
      id: 'TOMST2',
      raw_identifier: 94204541
  }),
  // TOMST3
  ee.Feature(ee.Geometry.Point([-53.467324, 69.265525]), {
      id: 'TOMST3',
      raw_identifier: 94204542
  }),
  // TOMST-T2-15
  ee.Feature(ee.Geometry.Point([-53.4328202, 69.289089]), {
      id: 'TOMST-T2-15',
      raw_identifier: 94232447
  }),
  // TOMST4-15
  ee.Feature(ee.Geometry.Point([-53.45363, 69.27282]), {
      id: 'TOMST4-15',
      raw_identifier: 94232448
  }),
  // TOMST4-30
  ee.Feature(ee.Geometry.Point([-53.45363, 69.27282]), {
      id: 'TOMST4-30',
      raw_identifier: 94229981
  })
]);
Map.addLayer(awsPoints, {color: 'red'}, 'AWS Points');

var date_start = ee.Date.fromYMD(2020, 1, 1),
    date_end = ee.Date.fromYMD(2024, 12, 31);

/*
prepare landsat image collection
*/
// Function to get and rename bands of interest from OLI.
function renameOli(img) {
    return img.select(
      ['ST_B10', 'QA_PIXEL', 'QA_RADSAT'], // 'QA_PIXEL', 'QA_RADSAT'
      ['ST_B10', 'QA_PIXEL', 'QA_RADSAT']);//'QA_PIXEL', 'QA_RADSAT';
  }
  // Function to get and rename bands of interest from ETM+, TM.
  function renameEtm(img) {
    return img.select(
      ['ST_B6', 'QA_PIXEL', 'QA_RADSAT'], //#,   'QA_PIXEL', 'QA_RADSAT'
      ['ST_B10', 'QA_PIXEL', 'QA_RADSAT']); // #, 'QA_PIXEL', 'QA_RADSAT'
  }
  

/* 
Cloud mask for Landsat data based on fmask (QA_PIXEL) and saturation mask 
based on QA_RADSAT.
Cloud mask and saturation mask by sen2cor.
Codes provided by GEE official.
*/

// This example demonstrates the use of the Landsat 8 Collection 2, Level 2
// QA_PIXEL band (CFMask) to mask unwanted pixels.

function maskL8sr(image) {
  // Bit 0 - Fill
  // Bit 1 - Dilated Cloud
  // Bit 2 - Cirrus
  // Bit 3 - Cloud
  // Bit 4 - Cloud Shadow
  var qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0);
  var saturationMask = image.select('QA_RADSAT').eq(0);

  // Apply the scaling factors to the appropriate bands.
//   var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  var thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0).subtract(273.15);

  // Replace the original bands with the scaled ones and apply the masks.
  return image//.addBands(opticalBands, null, true)
      .addBands(thermalBands, null, true)
      .updateMask(qaMask)
      .updateMask(saturationMask);
}

// This example demonstrates the use of the Landsat 4, 5, 7 Collection 2,
// Level 2 QA_PIXEL band (CFMask) to mask unwanted pixels.

function maskL457sr(image) {
  // Bit 0 - Fill
  // Bit 1 - Dilated Cloud
  // Bit 2 - Unused
  // Bit 3 - Cloud
  // Bit 4 - Cloud Shadow
  var qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0);
  var saturationMask = image.select('QA_RADSAT').eq(0);

  // Apply the scaling factors to the appropriate bands.
//   var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  var thermalBands = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15);

  // Replace the original bands with the scaled ones and apply the masks.
  return image//.addBands(opticalBands, null, true)
      .addBands(thermalBands, null, true)
      .updateMask(qaMask)
      .updateMask(saturationMask);
}

var colFilter = ee.Filter.and(
    ee.Filter.bounds(awsPoints),
    ee.Filter.date(date_start, date_end)
    // ee.Filter.calendarRange(6, 8, 'month')
  );
// Load Landsat surface reflectance data.
var oli2Col = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameOli)
    .map(maskL8sr);

var oliCol = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameOli)
    .map(maskL8sr);

var etmCol = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') 
    .filter(colFilter) 
    .filter(ee.Filter.calendarRange(1999, 2020, 'year')) // filter out L7 imagaes acquired after 2020 due to orbit drift
    .map(renameEtm)
    .map(maskL457sr); 

var tmCol = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameEtm)
    .map(maskL457sr);

var tm4Col = ee.ImageCollection('LANDSAT/LT04/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameEtm)
    .map(maskL457sr); 

var multiSat = oliCol.merge(etmCol).merge(tmCol).merge(tm4Col).merge(oli2Col);

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
var lstData = zonalStats(multiSat, awsPoints, {
    reducer: ee.Reducer.mean(),
    scale: 30,
    crs: 'EPSG:3413',
    // bands: ['ST_B10'],
    // bandsRename: ['LST'],
    imgProps: ['system:index', 'system:time_start'],
    datetimeName: 'date',
    datetimeFormat: 'YYYY-MM-dd'
});

Export.table.toDrive({
    collection: lstData,
    description: 'GEM_AWS_LandsatLST',
    fileFormat: 'CSV',
    folder: 'gee'
});