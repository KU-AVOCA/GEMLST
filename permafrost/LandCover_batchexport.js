/**
 * @file GEMLST_Landsat.js
 * @description This script calibrates Landsat Land Surface Temperature (LST) products from USGS Collection 2 and displays the results.
 * It supports masking clouds and saturated pixels using QA bands, applies a calibration to the LST band, and visualizes both original and calibrated LST.
 * The calibration coefficients are derived by comparing Landsat LST with in-situ measurements from the Greenland Ecosystem Monitoring (GEM) program.
 * The script also includes functionality for batch exporting the calibrated images to Google Drive.
 */

/**
 * Initialize the map and set the region of interest (ROI).
 */
var roi_disko =  /* color: #ffc82d */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[-53.57472811076303, 69.30723867672772],
          [-53.57472811076303, 69.248442318855],
          [-53.388647178145845, 69.248442318855],
          [-53.388647178145845, 69.30723867672772]]], null, false);
    // ee.Geometry.Polygon(
    //     [[[-55.21736886745359, 70.38991670192887],
    //        [-55.21736886745359, 68.77328951286498],
    //        [-50.21858957057859, 68.77328951286498],
    //        [-50.21858957057859, 70.38991670192887]]],
    //     null, false);
var roi_nuuk = 
    /* color: #00ffff */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[-51.755927822081134, 64.2062739921684],
          [-51.755927822081134, 64.12982994345987],
          [-51.547874233213946, 64.12982994345987],
          [-51.547874233213946, 64.2062739921684]]], null, false);

var roi_kobbefjord = 
    /* color: #00ffff */
    ee.Geometry.Polygon(
      [[[-51.46882937761503, 64.15257227061342],
        [-51.46882937761503, 64.10328366450781],
        [-51.33047030779081, 64.10328366450781],
        [-51.33047030779081, 64.15257227061342]]], null, false);
    // ee.Geometry.Polygon(
    //     [[[-52.26259158464628, 64.58707498802822],
    //         [-52.26259158464628, 63.641083335274274],
    //         [-50.13948367449003, 63.641083335274274],
    //         [-50.13948367449003, 64.58707498802822]]],
    //     null, false);

var roi_zackenberg = 
    /* color: #bf04c2 */
    ee.Geometry.Polygon(
      [[[-20.693887208214505, 74.52438752652616],
        [-20.693887208214505, 74.44006793415453],
        [-20.345757935753568, 74.44006793415453],
        [-20.345757935753568, 74.52438752652616]]], null, false);
    // ee.Geometry.Polygon(
        // [[[-23.250922828588923, 74.99849027993665],
        //     [-23.250922828588923, 73.81787607502739],
        //     [-18.241157203588923, 73.81787607502739],
        //     [-18.241157203588923, 74.99849027993665]]],
        // null, false);
var roi_kangerlussuaq = 
    /* color: #d63000 */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
        [[[-51.0002231147376, 67.08758222848459],
          [-51.0002231147376, 66.9002674050274],
          [-50.4124545600501, 66.9002674050274],
          [-50.4124545600501, 67.08758222848459]]], null, false);
    // ee.Geometry.Polygon(
    //     [[[-51.71364779735479, 67.14232235561316],
    //       [-51.71364779735479, 66.80714970994468],
    //       [-49.97506137157354, 66.80714970994468],
    //       [-49.97506137157354, 67.14232235561316]]], null, false);      
var roi_ilulissat = 
    /* color: #98ff00 */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
      [[[-51.15236795689255, 69.27335679481543],
        [-51.15236795689255, 69.17007514175228],
        [-50.84818399693161, 69.17007514175228],
        [-50.84818399693161, 69.27335679481543]]], null, false);
    // ee.Geometry.Polygon(
    //     [[[-51.15061125721688, 69.35254431730108],
    //       [-51.15061125721688, 69.04825211416775],
    //       [-50.23874602284188, 69.04825211416775],
    //       [-50.23874602284188, 69.35254431730108]]], null, false);    
var roi_qaanaaq =
  /* color: #0b4a8b */
  /* displayProperties: [
    {
      "type": "rectangle"
    }
  ] */
    ee.Geometry.Polygon(
      [[[-69.61569384963421, 77.53364115602874],
        [-69.61569384963421, 77.45379447077481],
        [-68.76425341994671, 77.45379447077481],
        [-68.76425341994671, 77.53364115602874]]], null, false);    
var roi_aasiaat = 
    /* color: #ffc82d */
    /* displayProperties: [
      {
        "type": "rectangle"
      }
    ] */
    ee.Geometry.Polygon(
      [[[-52.92938230523308, 68.72729236156103],
        [-52.92938230523308, 68.68627444980157],
        [-52.70828245171745, 68.68627444980157],
        [-52.70828245171745, 68.72729236156103]]], null, false);
var roi = roi_disko; // change the region of interest (ROI) here
var roi_name = 'disko'; // change the name of the ROI here
Map.centerObject(roi, 8);
var date_start = ee.Date.fromYMD(2019, 7, 1),
    date_end = ee.Date.fromYMD(2019, 7, 31);

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
  var thermalBands = image.select('ST_B10').updateMask(qaMask).updateMask(saturationMask);

  // Replace the original bands with the scaled ones and apply the masks.
  return image//.addBands(opticalBands, null, true)
      .addBands(thermalBands.rename('LandsatLST'), null, true);
      // .updateMask(qaMask)
      // .updateMask(saturationMask);
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
  var thermalBands = image.select('ST_B10').updateMask(qaMask).updateMask(saturationMask);

  // Replace the original bands with the scaled ones and apply the masks.
  return image//.addBands(opticalBands, null, true)
      .addBands(thermalBands.rename('LandsatLST'), null, true);
      // .updateMask(qaMask)
      // .updateMask(saturationMask);
}

// calibration: Coefficients:  0.75508115, Intercept:  1.229782776404388
// function calibrateLST(image) {
//     var lst = image.select('ST_B10');
//     var lst_calibrated = lst.multiply(0.75508115).add(1.229782776404388);
//     return image.addBands(lst_calibrated.rename('GEMLST_Landsat'));
// }

var colFilter = ee.Filter.and(
    ee.Filter.bounds(roi),
    ee.Filter.date(date_start, date_end)
    // ee.Filter.calendarRange(6, 8, 'month')
  );
// Load Landsat surface reflectance data.
var oli2Col = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameOli)
    .map(maskL8sr)
    .select('LandsatLST');
    // .map(calibrateLST);

var oliCol = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameOli)
    .map(maskL8sr)
    .select('LandsatLST');
    // .map(calibrateLST);

var etmCol = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') 
    .filter(colFilter) 
    .filter(ee.Filter.calendarRange(1999, 2020, 'year')) // filter out L7 imagaes acquired after 2020 due to orbit drift
    .map(renameEtm)
    .map(maskL457sr)
    .select('LandsatLST');
    // .map(calibrateLST); 

var tmCol = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameEtm)
    .map(maskL457sr)
    .select('LandsatLST');
    // .map(calibrateLST);

var tm4Col = ee.ImageCollection('LANDSAT/LT04/C02/T1_L2') 
    .filter(colFilter) 
    .map(renameEtm)
    .map(maskL457sr)
    .select('LandsatLST');
    // .map(calibrateLST); 

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
// function convertToLandsat(image) {
//     var lst = image.select('GEMLST_Landsat');
//     var lst_kelvin = lst.add(273.15);
//     var lst_origional = lst_kelvin.subtract(149).divide(0.00341802);
//     return image.addBands(lst_origional.rename('GEMLST_Landsat_uint16'));
// }

// daily_multiSat = daily_multiSat.map(convertToLandsat);

// optional feature: visualize the average LST for the region of interest 
// and compare the original and calibrated LST images
// var temp_origional = multiSat.select('ST_B10').mean().clip(roi);
// var temp_calibrated = multiSat.select('GEMLST_Landsat').mean().clip(roi);

// var palettes = require('users/gena/packages:palettes');
// var surfTpallete = palettes.cmocean.Thermal[7];
// var visParam = {min: -20, max: 20, palette: surfTpallete};

// Map.addLayer(temp_origional, visParam, 'LST_Origional');
// Map.addLayer(temp_calibrated, visParam, 'GEMLST_Landsat');

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

/**
 * Expert the calibrated LST images to Google Drive.
 */

// batch export image collection to Google Drive
var batch = require('users/fitoprincipe/geetools:batch');

batch.Download.ImageCollection.toDrive(daily_multiSat.select('LandsatLST'),
  roi_name,
  {scale: 30, 
   crs: 'EPSG:3413',
   region: roi, 
   type: 'uint16',
   maxPixels: 1e13,
   name: 'GEMLST_Landsat_{system_date}'
  //  dateFormat: 'yyyy-MM-dd_HH-mm-ss',
  });