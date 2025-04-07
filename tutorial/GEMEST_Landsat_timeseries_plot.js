/**
 * @file GEMEST_Landsat_timeseries_plot.js
 * @description This script extracts and visualizes time series of Landsat Land Surface Temperature (LST) 
 * from USGS Collection 2 data at a specific point location. It:
 * - Masks clouds and saturated pixels using QA bands
 * - Applies calibration to LST based on land cover types (land, ice, ocean) using GEMEST coefficients
 * - Aggregates observations to daily averages
 * - Exports the time series (celcius degress) as CSV to Google Drive
 * - Visualizes the original and calibrated temperature values on an interactive chart
 * 
 * The calibration coefficients are derived by comparing Landsat LST with in-situ measurements 
 * from the Greenland Ecosystem Monitoring (GEM) program. The script handles multiple Landsat 
 * sensors (TM4, TM5, ETM+, OLI, OLI-2) and combines them into a single collection.
 * 
 * @author Shunan Feng (shf@ign.ku.dk)
 */

/**
 * Initialize the map and set the region of interest (ROI).
 */

var roi = ee.Geometry.Point([-51.6787, 64.1902]); // longitude, latitude
Map.centerObject(roi, 8);
Map.addLayer(roi, {color: 'f8766d'}, 'ROI');
Map.setOptions('HYBRID');

// Enter the time of interest
var date_start = ee.Date.fromYMD(2000, 1, 1),
    date_end = ee.Date.fromYMD(2024, 12, 31);
  
var month_start = 5,
    month_end = 10;

var greenland_landmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                        .select('ocean_mask').eq(0).and(
                          ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                          .select('ice_mask').eq(0)); // 

var greenland_icemask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                        .select('ice_mask').eq(1);  
// var greenland_oceanmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
//                         .select('ocean_mask').eq(1); // ocean mask
/** 
 * prepare landsat image collection
 */
// Function to get and rename bands of interest from OLI.
function renameOli(img) {
  return img.select(
    ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'ST_B10', 'QA_PIXEL', 'QA_RADSAT'], // 'QA_PIXEL', 'QA_RADSAT'
    ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'ST_B10', 'QA_PIXEL', 'QA_RADSAT']);//'QA_PIXEL', 'QA_RADSAT';
}
// Function to get and rename bands of interest from ETM+, TM.
function renameEtm(img) {
  return img.select(
    ['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'ST_B6', 'QA_PIXEL', 'QA_RADSAT'], //#,   'QA_PIXEL', 'QA_RADSAT'
    ['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'ST_B10', 'QA_PIXEL', 'QA_RADSAT']); // #, 'QA_PIXEL', 'QA_RADSAT'
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
  var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  // var thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0).subtract(273.15);

  // Replace the original bands with the scaled ones and apply the masks.
  return image.addBands(opticalBands, null, true)
      // .addBands(thermalBands, null, true)
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
  var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  // var thermalBands = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15);

  // Replace the original bands with the scaled ones and apply the masks.
  return image.addBands(opticalBands, null, true)
      // .addBands(thermalBands, null, true)
      .updateMask(qaMask)
      .updateMask(saturationMask);
}

// Function to calibrate LST using different coefficients for different land cover types
function calibrateLST(image) {
  var lst = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15);
  
  // Apply land calibration: y = 0.8382798596053026*x + 1.9527861913159263
  var lst_land = lst.multiply(0.8382798596053026).add(1.9527861913159263)
            .updateMask(greenland_landmask).rename('ST_B10_land');
  
  // Apply ocean calibration: y = 0.7212493050563921*x + 1.4461030886482544
  var lst_ocean = lst.multiply(0.7212493050563921).add(1.4461030886482544);
  
  // For ice areas, keep the original values
  var lst_ice = lst.updateMask(greenland_icemask).rename('ST_B10_ice');
  
  // Combine the calibrated images
  var lst_calibrated = lst_ocean.where(greenland_landmask, lst_land)
                              .where(greenland_icemask, lst_ice);

  // Add the calibrated band to the image
  return image.addBands(lst_calibrated.rename('GEMEST_Landsat'))
              .addBands(lst.rename('LST_Original'));
}


var colFilter = ee.Filter.and(
    ee.Filter.bounds(roi),
    ee.Filter.date(date_start, date_end),
    ee.Filter.calendarRange(month_start, month_end, 'month')
  );
// Load Landsat surface reflectance data.
var oli2Col = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameOli)
    .map(maskL8sr)
    .map(calibrateLST);

var oliCol = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameOli)
    .map(maskL8sr)
    .map(calibrateLST);

var etmCol = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') 
    .filter(colFilter) 
    .filter(ee.Filter.calendarRange(1999, 2020, 'year')) // filter out L7 imagaes acquired after 2020 due to orbit drift
    .map(renameEtm)
    .map(maskL457sr)
    .map(calibrateLST); 

var tmCol = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameEtm)
    .map(maskL457sr)
    .map(calibrateLST);

var tm4Col = ee.ImageCollection('LANDSAT/LT04/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameEtm)
    .map(maskL457sr)
    .map(calibrateLST); 

var multiSat = oliCol.merge(etmCol).merge(tmCol).merge(tm4Col).merge(oli2Col);
var multiSat = multiSat.select(['GEMEST_Landsat', 'LST_Original']);

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
  var filtered = multiSat.filterDate(date, date.advance(dayNum,'day'));
  // Make the mosaic
  var image = ee.Image(
      filtered.mean().copyProperties(filtered.first()))
      .set({'system:index': date.format('yyyy_MM_dd')})
      .set('system:time_start', filtered.first().get('system:time_start'));

  // Add the mosaic to a list only if the collection has images
  return ee.List(ee.Algorithms.If(filtered.size(), newlist.add(image), newlist));
};

var daily_multiSat = ee.ImageCollection(ee.List(range.iterate(day_mosaics, ee.List([]))));


// Export the time series data to Google Drive
// Note: You can modify the export parameters as per your requirements
var allObs = daily_multiSat.map(function(image) {
  var obs = image.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: roi,
    scale: 30,
    maxPixels: 1e13
  });
  return image.set('GEMEST_Landsat', obs.get('GEMEST_Landsat'))
              .set('LST_Original', obs.get('LST_Original'))
              .set('system:time_start', image.get('system:time_start'));
}
);

var timeSeries = ee.Feature(null, allObs);

Export.table.toDrive({
  collection: allObs,
  description: 'GEMEST_Landsat_timeseries',
  folder: 'GEMEST_Landsat',
  fileFormat: 'CSV'
});

// Optional: Display the time series chart.
// Note: This may take a while to load depending on the number of images and may fail
// if the image collection is too large.
var chartAllObs = ui.Chart.feature.byFeature(allObs, 'system:time_start', ['GEMEST_Landsat', 'LST_Original'])
  .setChartType('ScatterChart')
  .setOptions({
    title: 'Time Series of GEMEST Landsat EST and Original LST',
    vAxis: {title: 'Surface Temperature (C)'},
    hAxis: {title: 'Date'},
    pointSize: 3,
    series: {
      0: {color: 'red', lineWidth: 0},
      1: {color: 'blue', lineWidth: 0}
    }
  });
print(chartAllObs);