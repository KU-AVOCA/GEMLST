/**
 * @file GEMEST_Landsat.js
 * @description This script calibrates Landsat Land Surface Temperature (LST) products from USGS Collection 2 and displays the results.
 * It supports masking clouds and saturated pixels using QA bands, applies a calibration to the LST band, and visualizes both original and calibrated LST.
 * The calibration coefficients are derived by comparing Landsat LST with in-situ measurements from the Greenland Ecosystem Monitoring (GEM) program.
 * The script also includes functionality for batch exporting the calibrated images to Google Drive.
 */

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
 * prepare landsat image collection
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
  // var thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0).subtract(273.15);

  // Replace the original bands with the scaled ones and apply the masks.
  return image//.addBands(opticalBands, null, true)
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
//   var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  // var thermalBands = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15);

  // Replace the original bands with the scaled ones and apply the masks.
  return image//.addBands(opticalBands, null, true)
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
  var lst_ocean = lst.multiply(0.7212493050563921).add(1.4461030886482544)
             .updateMask(greenland_oceanmask).rename('ST_B10_ocean');
  
  // For ice areas, keep the original values
  var lst_ice = lst.updateMask(greenland_icemask).rename('ST_B10_ice');
  
  // Combine the calibrated images
  var lst_calibrated = lst_land.unmask().add(lst_ocean.unmask()).add(lst_ice.unmask());
  
  // Add the calibrated band to the image
  return image.addBands(lst_calibrated.rename('GEMEST_Landsat'))
              .addBands(lst, null, true);
}


var colFilter = ee.Filter.and(
    ee.Filter.bounds(roi),
    ee.Filter.date(date_start, date_end)
    // ee.Filter.calendarRange(6, 8, 'month')
  );
// Load Landsat surface reflectance data.
var oli2Col = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameOli)
    .map(calibrateLST)
    .map(maskL8sr);

var oliCol = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameOli)
    .map(calibrateLST)
    .map(maskL8sr);

var etmCol = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') 
    .filter(colFilter) 
    .filter(ee.Filter.calendarRange(1999, 2020, 'year')) // filter out L7 imagaes acquired after 2020 due to orbit drift
    .map(renameEtm)
    .map(calibrateLST)
    .map(maskL457sr); 

var tmCol = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameEtm)
    .map(calibrateLST)
    .map(maskL457sr);

var tm4Col = ee.ImageCollection('LANDSAT/LT04/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameEtm)
    .map(calibrateLST)
    .map(maskL457sr); 

var multiSat = oliCol.merge(etmCol).merge(tmCol).merge(tm4Col).merge(oli2Col);

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

// Convert celcius to kelvin and then convert it back to how the data was stored in landsat 
// plus 273.15 and then subtract 149 and then divide by 0.00341802 
//  
function convertToLandsat(image) {
    var lst = image.select('GEMEST_Landsat');
    var lst_kelvin = lst.add(273.15);
    var lst_origional = lst_kelvin.subtract(149).divide(0.00341802);
    return image.addBands(lst_origional.rename('GEMEST_Landsat_uint16'));
}

daily_multiSat = daily_multiSat.map(convertToLandsat);

// optional feature: visualize the average LST for the region of interest 
// and compare the original and calibrated LST images
var temp_origional = multiSat.select('ST_B10').mean().clip(roi);
var temp_calibrated = multiSat.select('GEMEST_Landsat').mean().clip(roi);

var palettes = require('users/gena/packages:palettes');
var surfTpallete = palettes.cmocean.Thermal[7];
var visParam = {min: -20, max: 20, palette: surfTpallete};

Map.addLayer(temp_origional, visParam, 'LST_Origional');
Map.addLayer(temp_calibrated, visParam, 'GEMEST_Landsat');

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

// // Add a title to the colorbar
// var colorBarTitle = ui.Label({
//     value: 'LST (°C)',
//     style: {
//         position: 'bottom-right',
//         fontSize: '12px',
//         margin: '0px 0px 0px 0px',
//         textAlign: 'center',
//         stretch: 'horizontal'
//     }
// });

// // Create panel for colorbar legend
// var legendPanel = ui.Panel({
//   style: {
//     position: 'bottom-right',
//     padding: '8px 15px'
//   }
// });

// // Function to generate the legend
// function makeLegend() {
//   legendPanel.clear();

//   var legendTitle = ui.Label({
//     value: 'LST (°C)',
//     style: {
//       fontWeight: 'bold',
//       fontSize: '14px',
//       margin: '0 0 4px 0',
//       padding: '0'
//     }
//   });
//   legendPanel.add(legendTitle);

//   // Create and add the color bar
//   legendPanel.add(colorBar);

//   // Create min and max labels
//   var minMaxPanel = ui.Panel({
//     widgets: [
//       ui.Label(visParam.min, {margin: '4px 8px'}),
//       ui.Label(visParam.max, {margin: '4px 8px', textAlign: 'right', stretch: 'horizontal'})
//     ],
//     layout: ui.Panel.Layout.flow('horizontal')
//   });
//   legendPanel.add(minMaxPanel);

//   Map.add(legendPanel);
// }

// makeLegend();

// /**
//  * Expert the calibrated LST images to Google Drive.
//  */

// // batch export image collection to Google Drive
// var batch = require('users/fitoprincipe/geetools:batch');

// batch.Download.ImageCollection.toDrive(daily_multiSat.select('GEMEST_Landsat_uint16'),
//   'disko',
//   {scale: 30, 
//    crs: 'EPSG:3413',
//    region: roi, 
//    type: 'uint16',
//    maxPixels: 1e13,
//    name: 'GEMEST_Landsat_{system_date}'
//   //  dateFormat: 'yyyy-MM-dd_HH-mm-ss',
//   });