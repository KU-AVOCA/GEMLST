/**
 * Initialize the map and set the region of interest (ROI).
 */
var roi_disko =  /* color: #ffc82d */ee.Geometry.Polygon(
    [[[-55.21736886745359, 70.38991670192887],
       [-55.21736886745359, 68.77328951286498],
       [-50.21858957057859, 68.77328951286498],
       [-50.21858957057859, 70.38991670192887]]],
    null, false);

var roi_kobbefjord = /* color: #00ffff */ee.Geometry.Polygon(
    [[[-52.26259158464628, 64.58707498802822],
        [-52.26259158464628, 63.641083335274274],
        [-50.13948367449003, 63.641083335274274],
        [-50.13948367449003, 64.58707498802822]]],
    null, false);

var roi_zackenberg = /* color: #bf04c2 */ee.Geometry.Polygon(
    [[[-23.250922828588923, 74.99849027993665],
        [-23.250922828588923, 73.81787607502739],
        [-18.241157203588923, 73.81787607502739],
        [-18.241157203588923, 74.99849027993665]]],
    null, false);
var roi = roi_disko; // change the region of interest (ROI) here
Map.centerObject(roi, 8);
var date_start = ee.Date.fromYMD(2019, 7, 1),
date_end = ee.Date.fromYMD(2019, 7, 10);

var greenland_landmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                    .select('ocean_mask').eq(0).and(
                      ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                      .select('ice_mask').eq(0)); // 

var greenland_icemask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                    .select('ice_mask').eq(1);  
var greenland_oceanmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                    .select('ocean_mask').eq(1); // ocean mask
/** 
* prepare image collection
*/
function renameS2(img) {
    return img.select(
      ['B4',  'B8',  'SCL', QA_BAND],
      ['Red', 'NIR', 'SCL', QA_BAND]
      //['B2',     'B3',      'B4',    'B8',    'B11',     'B12',     'QA60', 'SCL'],
      //['BlueS2', 'GreenS2', 'RedS2', 'NIRS2', 'SWIR1S2', 'SWIR2S2', 'QA60', 'SCL']
    );
  }

/**
 * Function to mask clouds using the Sentinel-2 QA band
 * @param {ee.Image} image Sentinel-2 image
 * @return {ee.Image} cloud masked Sentinel-2 image
 * archived after updating to Cloud Score+
 */
// function maskS2sr(image) {
//   var qa = image.select('QA60');

//   // Bits 10 and 11 are clouds and cirrus, respectively.
//   var cloudBitMask = 1 << 10;
//   var cirrusBitMask = 1 << 11;
//   // 1 is saturated or defective pixel
//   var not_saturated = image.select('SCL').neq(1);
//   // Both flags should be set to zero, indicating clear conditions.
//   var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
//       .and(qa.bitwiseAnd(cirrusBitMask).eq(0));

//   // return image.updateMask(mask).updateMask(not_saturated);
//   return image.updateMask(mask).updateMask(not_saturated).divide(10000);
// }

/**
 * Function to mask clouds using the Cloud Score+
 */
// Cloud Score+ image collection. Note Cloud Score+ is produced from Sentinel-2
// Level 1C data and can be applied to either L1C or L2A collections.

// Use 'cs' or 'cs_cdf', depending on your use case; see docs for guidance.
var QA_BAND = 'cs'; // I find'cs' is better than 'cs_cdf' because it is more robust but may mask out more clear pixels.

// The threshold for masking; values between 0.50 and 0.65 generally work well.
// Higher values will remove thin clouds, haze & cirrus shadows.
var CLEAR_THRESHOLD = 0.65;

function maskS2sr(image) {
  // 1 is saturated or defective pixel
  var not_saturated = image.select('SCL').neq(1);
  return image.updateMask(image.select(QA_BAND).gte(CLEAR_THRESHOLD))
              .updateMask(not_saturated)
              .updateMask(greenland_landmask)
              .divide(10000);
}

// calculate NDVI
function addNDVI(image) {
  var ndvi = image.normalizedDifference(['NIR', 'Red']).rename('NDVI');
  return image.addBands(ndvi);
}


var s2colFilter = ee.Filter.and(
ee.Filter.bounds(roi),
ee.Filter.date(date_start, date_end)
);

function prepS2(img) {
    var orig = img;
    img = renameS2(img);
    img = maskS2sr(img);
    img = addNDVI(img);

    return ee.Image(img.copyProperties(orig, orig.propertyNames()).set('SATELLITE', 'SENTINEL_2'));
  }
// Sentinel-2 surface reflectance data
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
              .filter(s2colFilter);
var s2Col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') 
              .filter(s2colFilter) 
              .linkCollection(csPlus, [QA_BAND])
              .map(prepS2)
              .select(['NDVI']); //# .select(['totalAlbedo']) or  .select(['visnirAlbedo'])

// convert to daily average
// Difference in days between start and finish
var diff = date_end.difference(date_start, 'day');

// Make a list of all dates
var dayNum = 1; // steps of day number
var range = ee.List.sequence(0, diff.subtract(1), dayNum).map(function(day){return date_start.advance(day,'day')});

// Function for iteration over the range of dates
var day_mosaics = function(date, newlist) {
// Cast
date = ee.Date(date);
newlist = ee.List(newlist);

// Filter collection between date and the next day
var filtered = s2Col.filterDate(date, date.advance(dayNum,'day'));
// Make the mosaic
var image = ee.Image(
  filtered.mean().copyProperties(filtered.first()))
  .set({'system:index': date.format('yyyy_MM_dd')})
  .set('system:time_start', filtered.first().get('system:time_start'));

// Add the mosaic to a list only if the collection has images
return ee.List(ee.Algorithms.If(filtered.size(), newlist.add(image), newlist));
};

// Create daily mosaics
var daily_multiSat_raw = ee.ImageCollection(ee.List(range.iterate(day_mosaics, ee.List([]))));

// Scale the NDVI values to Int16 to save space (multiply by 10000)
var daily_multiSat = daily_multiSat_raw.map(function(img) {
  return img.select('NDVI')
            .multiply(10000)
            .int16()
            .unmask(-32768)
            .set('system:time_start', img.get('system:time_start'))
            .set('system:index', img.get('system:index'));
});

// // Visualize the average NDVI for the region of interest
// var ndvi_avg = daily_multiSat.select('NDVI').mean().clip(roi);

// var palettes = require('users/gena/packages:palettes');
// // Using a green palette for NDVI visualization
// var visParam = {min: -10000, max: 10000, palette: palettes.colorbrewer.RdYlGn[11]};

// Map.addLayer(ndvi_avg, visParam, 'NDVI Average');

// // Create a color bar for the map
// var colorBar = ui.Thumbnail({
//     image: ee.Image.pixelLonLat().select(0),
//     params: {
//         bbox: [0, 0, 1, 0.1],
//         dimensions: '300x20',
//         format: 'png',
//         min: 0,
//         max: 1,
//         palette: visParam.palette
//     },
//     style: {position: 'bottom-right', margin: '0px 0px 30px 0px'}
// });

// // Create panel for colorbar legend
// var legendPanel = ui.Panel({
//     style: {
//         position: 'bottom-right',
//         padding: '8px 15px'
//     }
// });

// // Function to generate the legend
// function makeLegend() {
//     legendPanel.clear();

//     var legendTitle = ui.Label({
//         value: 'NDVI',
//         style: {
//             fontWeight: 'bold',
//             fontSize: '14px',
//             margin: '0 0 4px 0',
//             padding: '0'
//         }
//     });
//     legendPanel.add(legendTitle);

//     // Create and add the color bar
//     legendPanel.add(colorBar);

//     // Create min and max labels
//     var minMaxPanel = ui.Panel({
//         widgets: [
//             ui.Label(visParam.min, {margin: '4px 8px'}),
//             ui.Label(visParam.max, {margin: '4px 8px', textAlign: 'right', stretch: 'horizontal'})
//         ],
//         layout: ui.Panel.Layout.flow('horizontal')
//     });
//     legendPanel.add(minMaxPanel);

//     Map.add(legendPanel);
// }

// makeLegend();

// /**
//  * Expert the calibrated LST images to Google Drive.
//  */

// batch export image collection to Google Drive
var batch = require('users/fitoprincipe/geetools:batch');

batch.Download.ImageCollection.toDrive(daily_multiSat.select('NDVI'),
  'Disko',
  {scale: 10, 
   crs: 'EPSG:3413',
   region: roi, 
   type: 'int16',
   maxPixels: 1e13,
   name: 'GEMNDVI_Sentinel2_{system_date}'
  //  dateFormat: 'yyyy-MM-dd_HH-mm-ss',
  });