/*
This script extracts Landsat 8 LST data for GEM AWS stations.
It is not yet functional.
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
Map.addLayer(awsPoints, {color: 'red'}, 'AWS Points');

var date_start = ee.Date.fromYMD(2003, 1, 1),
    date_end = ee.Date.fromYMD(2024, 12, 31);

/*
prepare landsat image collection
*/
// link to the code that computes the Landsat LST
var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');
// link to the code that computes broad-band emissivity
var BBE = require('users/sofiaermida/landsat_smw_lst:modules/broadband_emiss.js');

// select region of interest, date range, and landsat satellite
var geometry = awsPoints;
var use_ndvi = true;

// compute the LST for each Landsat
var L9coll = LandsatLST.collection('L9', date_start, date_end, geometry, use_ndvi);
var L8coll = LandsatLST.collection('L8', date_start, date_end, geometry, use_ndvi);
var L7coll = LandsatLST.collection('L7', date_start, date_end, geometry, use_ndvi);
var L5coll = LandsatLST.collection('L5', date_start, date_end, geometry, use_ndvi);
var L4coll = LandsatLST.collection('L4', date_start, date_end, geometry, use_ndvi);

// compute broadband emissivity
L9coll = L9coll.map(BBE.addBand(true));
L8coll = L8coll.map(BBE.addBand(true));
L7coll = L7coll.map(BBE.addBand(true));
L5coll = L5coll.map(BBE.addBand(true));
L4coll = L4coll.map(BBE.addBand(true));


// get bands for each landsat in one collection
var getband = function(landsat, bandname){
  var wrap = function(image){
    return image.select(bandname).rename(bandname.concat('_').concat(landsat));
  };
  return wrap;
};
// merge all Landsat LST collections for the chart
var bandname = 'LST';
var LandsatColl = L8coll.map(getband('L8',bandname));
LandsatColl = LandsatColl.merge(L7coll.map(getband('L7',bandname)));
LandsatColl = LandsatColl.merge(L5coll.map(getband('L5',bandname)));
LandsatColl = LandsatColl.merge(L4coll.map(getband('L4',bandname)));
LandsatColl = LandsatColl.merge(L9coll.map(getband('L9',bandname)));

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

var pois = awsPoints.map(bufferPoints(30/2, true));
// print(pois)
var lstData = zonalStats(LandsatColl, pois, {
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