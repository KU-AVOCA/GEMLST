//ee.ImageCollection("LANDSAT/COMPOSITES/C02/T1_L2_8DAY_NDVI")

// 1. Load the Landsat 8/9 surface reflectance product (T1_L2_8DAY_NDVI)
// Here we assume you are using Landsat 8 or 9. Adjust according to the product you need.
var startDate = ee.Date.fromYMD(2007,6,9); // Start date
var endDate = ee.Date.fromYMD(2007,6,20); // End date
var geometry = 
    /* color: #d63000 */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[-52.99454267793822, 69.5474455706429],
          [-52.99454267793822, 69.42231416752831],
          [-52.320256789266345, 69.42231416752831],
          [-52.320256789266345, 69.5474455706429]]], null, false);
var roi = geometry; // Define your region of interest (roi) here

var landsatNdvi = ee.ImageCollection("LANDSAT/COMPOSITES/C02/T1_L2_8DAY_NDVI")
    .filterBounds(geometry)  // Filter by your area of interest
    .filterDate(startDate, endDate)  // Filter by date range
    .select('NDVI');  // Select the NDVI band


// 2. Convert image collection to collection of daily average    
var diff = endDate.difference(startDate, 'day');

// Make a list of all dates
var dayNum = 1; // steps of day number
var range = ee.List.sequence(0, diff.subtract(1), dayNum).map(function(day){return startDate.advance(day,'day')});

// Function for iteration over the range of dates
var day_mosaics = function(date, newlist) {
  // Cast
  date = ee.Date(date);
  newlist = ee.List(newlist);

  // Filter collection between date and the next day
  var filtered = landsatNdvi.filterDate(date, date.advance(dayNum,'day'));
  // Make the mosaic and clip it to the region of interest
  var image = ee.Image(
      filtered.mean().clip(roi).copyProperties(filtered.first()))
      .set({'system:index': date.format('yyyy_MM_dd')})
      .set('system:time_start', filtered.first().get('system:time_start'));

  // Add the mosaic to a list only if the collection has images
  return ee.List(ee.Algorithms.If(filtered.size(), newlist.add(image), newlist));
};

var daily_NDVI = ee.ImageCollection(ee.List(range.iterate(day_mosaics, ee.List([]))));

// 3. Batch export the daily NDVI images to Google Drive
var batch = require('users/fitoprincipe/geetools:batch');

batch.Download.ImageCollection.toDrive(
    daily_NDVI,
    'foldername', // Replace with your desired folder name
    {
        scale: 30,
        region: roi,
        crs: 'EPSG:4326',
        maxPixels: 1e13,
        name: 'Landsat_NDVI_{system_date}',
        type: 'double'
    });

// // Select each scene from the image collection
// var image = landsatNdvi.first()

// // 3. Clip the NDVI image using the shapefile
// var clippedNDVI = image.clip(geometry);

// 4. Export the clipped NDVI to Google Drive as a GeoTIFF
// Export.image.toDrive({
//   image: clippedNDVI,
//   description: 'clipped_ndvi_landsat',  // Export task name
//   folder: 'EarthEngineExports',  // Optional folder name in Google Drive
//   fileNamePrefix: 'clipped_ndvi_landsat2007_june1-10', // File prefix
//   region: geometry,  // Clip region based on your shapefile
//   scale: 30,  // Set the scale to match Landsat (30 meters per pixel)
//   crs: 'EPSG:4326', // Coordinate Reference System (WGS84)
//   fileFormat: 'GeoTIFF' // Export format as GeoTIFF
// });
