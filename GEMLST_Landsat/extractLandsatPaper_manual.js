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
// var geometry = awsPoints.filterMetadata('id', 'equals', 'Kobbefjord_M500').geometry().buffer(30);
// var geometry = awsPoints.filterMetadata('id', 'equals', 'Disko_T1').geometry().buffer(30);
// var geometry = awsPoints.filterMetadata('id', 'equals', 'Disko_T2').geometry().buffer(30);
// var geometry = awsPoints.filterMetadata('id', 'equals', 'Disko_T3').geometry().buffer(30);
// var geometry = awsPoints.filterMetadata('id', 'equals', 'Disko_T4').geometry().buffer(30);
// var geometry = awsPoints.filterMetadata('id', 'equals', 'Zackenberg_M2').geometry().buffer(30);
// var geometry = awsPoints.filterMetadata('id', 'equals', 'Zackenberg_M3').geometry().buffer(30);
// var geometry = awsPoints.filterMetadata('id', 'equals', 'Zackenberg_M4_30min').geometry().buffer(30);
var site = ee.Geometry.Point([-53.479400634765625, 69.27300262451172]);
var geometry = site.buffer(30);
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
var LandsatColl = L8coll.map(getband('Landsat',bandname));
LandsatColl = LandsatColl.merge(L7coll.map(getband('Landsat',bandname)));
LandsatColl = LandsatColl.merge(L5coll.map(getband('Landsat',bandname)));
LandsatColl = LandsatColl.merge(L4coll.map(getband('Landsat',bandname)));
LandsatColl = LandsatColl.merge(L9coll.map(getband('Landsat',bandname)));

var TimeSeries = ui.Chart.image.series(
  LandsatColl, geometry, ee.Reducer.mean(), 30, 'system:time_start')
      .setChartType('ScatterChart')
      .setOptions({
        vAxis: {title: bandname},
        lineWidth: 1,
        pointSize: 4
});
print(TimeSeries);