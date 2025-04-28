/**
 * @file GEMEST_Landsat_GEEapp.js
 * @description This Earth Engine App visualizes and analyzes Landsat surface temperature data for Greenland, incorporating data harmonization, cloud masking, and calibration techniques.
 * It allows users to explore time series data, view temperature maps, and download data for specific locations and time periods.
 * The app integrates ArcticDEM for topographic context and provides tools for selecting date ranges and visualizing Landsat imagery.
 * 
 * The app is inspired by:
 * https://google.earthengine.app/view/ocean.
 * https://gis.stackexchange.com/questions/344680/exporting-image-from-app-side-using-google-earth-engine by Justin Braaten
 * https://developers.google.com/earth-engine/tutorials/community/landsat-etm-to-oli-harmonization by Justin Braaten 
 * 
 * Author Shunna Feng (shf@ign.ku.dk)
 */
/*


Shunna Feng (shunan.feng@envs.au.dk)
*/


/*
 * Map layer configuration
 */

var greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                        .select('ocean_mask').multiply(0).add(1); 
var greenland_landmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                        .select('ocean_mask').eq(0).and(
                          ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                          .select('ice_mask').eq(0)); // 

var greenland_icemask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                        .select('ice_mask').eq(1);  
// var greenland_oceanmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
//                         .select('ocean_mask').eq(1); // ocean mask
// Map.addLayer(greenlandmask, {min: 0, max: 1}, 'greenland mask');
// Map.addLayer(greenland_landmask, {min: 0, max: 1}, 'greenland land mask');
// Map.addLayer(greenland_icemask, {min: 0, max: 1}, 'greenland ice mask');
// Map.addLayer(greenland_oceanmask, {min: 0, max: 1}, 'greenland ocean mask');
var arcticDEM = ee.Image('UMN/PGC/ArcticDEM/V3/2m_mosaic').updateMask(greenlandmask);
var palettes = require('users/gena/packages:palettes');


var elevationVis = {
  min: -100.0,
  max: 3500.0,
  palette: palettes.cmocean.Ice[7] //['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']//palettes.cmocean.Ice[7]
};   
var arcticDEMgreenland = arcticDEM.visualize(elevationVis);//.updateMask(greenlandmask);
var demLayer = ui.Map.Layer(arcticDEMgreenland).setName('arctic dem');


/*
prepare harmonized satellite data
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




var date_start = ee.Date.fromYMD(1984, 1, 1),
    date_end = ee.Date(Date.now()),
    now = Date.now();
// palette ref: https://gist.github.com/jscarto/6cc7f547bb7d5d9acda51e5c15256b01
var surfTpallete = palettes.cmocean.Thermal[7];
var vis = {min: -20, max: 20, palette: surfTpallete};


// Create the main map and add arctic dem as base map.
var mapPanel = ui.Map();
mapPanel.setOptions('HYBRID').setControlVisibility(true);
var layers = mapPanel.layers();
layers.add(demLayer, 'arctic dem');


/*
 * Panel setup
 */

// Create a panel to hold title, intro text, chart and legend components.
var inspectorPanel = ui.Panel({style: {width: '30%'}});

// Create an intro panel with labels.
var intro = ui.Panel([
  ui.Label({
    value: 'GEMEST_Landsat - Time Series Inspector',
    style: {fontSize: '20px', fontWeight: 'bold'}
  }),
  ui.Label('Click a location to see its time series of temperature. This app shows both the original and calibrated Landsat surface temperature. '),
]);
inspectorPanel.add(intro);

// Create panels to hold lon/lat values.
var lon = ui.Label();
var lat = ui.Label();
inspectorPanel.add(ui.Panel([lon, lat], ui.Panel.Layout.flow('horizontal')));

// Add placeholders for the chart and legend.
inspectorPanel.add(ui.Label('[Chart]'));
inspectorPanel.add(ui.Label('[Legend]'));


/*
 * Chart setup
 */

// Generates a new time series chart of SST for the given coordinates.
var generateChart = function (coords) {
  // Update the lon/lat panel with values from the click event.
  lon.setValue('lon: ' + coords.lon.toFixed(4));
  lat.setValue('lat: ' + coords.lat.toFixed(4));

  // Add a dot for the point clicked on.
  var point = ee.Geometry.Point(coords.lon, coords.lat);
  var dot = ui.Map.Layer(point, {color: 'FF0000'}, 'clicked location');
  // Add the dot as the third layer, so it shows up on top of all layers.
  mapPanel.layers().set(3, dot);


  var colFilter = ee.Filter.and(
    ee.Filter.bounds(point),
    ee.Filter.date(date_start, date_end)
    // ee.Filter.calendarRange(6, 8, 'month')
  );
  

  
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
  var multiSat = oliCol.merge(etmCol).merge(tmCol).merge(tm4Col).merge(oli2Col);;
  
  // Make a chart from the time series.
  var geeChart = ui.Chart.image.series(multiSat.select('LST_Original', 'GEMEST_Landsat'), point, ee.Reducer.mean(), 90);
  geeChart.setChartType('ScatterChart');
  // Customize the chart.
  geeChart.setOptions({
    title: 'Temperature: time series',
    vAxis: {title: 'Temperature (°C)'},
    hAxis: {title: 'Date'},
    series: {
      0: {
        color: 'blue',
        lineWidth: 0,
        pointsVisible: true,
        pointSize: 2,
      },
      1: {
        color: 'red',
        lineWidth: 0,
        pointsVisible: true,
        pointSize: 2,
      },
    },
    legend: {position: 'right'},
  });
  // Add the chart at a fixed position, so that new charts overwrite older ones.
  inspectorPanel.widgets().set(2, geeChart);
};


/*
 * Legend setup
 */

// Creates a color bar thumbnail image for use in legend from the given color
// palette.
function makeColorBarParams(palette) {
  return {
    bbox: [0, 0, 1, 0.1],
    dimensions: '100x10',
    format: 'png',
    min: 0,
    max: 1,
    palette: palette,
  };
}

// Create the color bar for the legend.
var colorBar = ui.Thumbnail({
  image: ee.Image.pixelLonLat().select(0),
  params: makeColorBarParams(vis.palette),
  style: {stretch: 'horizontal', margin: '0px 8px', maxHeight: '24px'},
});
var colorBarDEM = ui.Thumbnail({
  image: ee.Image.pixelLonLat().select(0),
  params: makeColorBarParams(elevationVis.palette),
  style: {stretch: 'horizontal', margin: '0px 8px', maxHeight: '24px'},
});

// Create a panel with three numbers for the legend.
var legendLabels = ui.Panel({
  widgets: [
    ui.Label(vis.min, {margin: '4px 8px'}),
    ui.Label(
        ((vis.max + vis.min) / 2),
        {margin: '4px 8px', textAlign: 'center', stretch: 'horizontal'}),
    ui.Label(vis.max, {margin: '4px 8px'})
  ],
  layout: ui.Panel.Layout.flow('horizontal')
});
var legendLabelsDEM = ui.Panel({
  widgets: [
    ui.Label(elevationVis.min, {margin: '4px 8px'}),
    ui.Label(
        (elevationVis.max / 2),
        {margin: '4px 8px', textAlign: 'center', stretch: 'horizontal'}),
    ui.Label(elevationVis.max, {margin: '4px 8px'})
  ],
  layout: ui.Panel.Layout.flow('horizontal')
});

var legendTitle = ui.Label({
  value: 'Map Legend: Surface Temperature (°C)',
  style: {fontWeight: 'bold'}
});
var legendTitleDEM = ui.Label({
  value: 'Map Legend: DEM (m)',
  style: {fontWeight: 'bold'}
});

var legendPanel = ui.Panel([legendTitle, colorBar, legendLabels, legendTitleDEM, colorBarDEM, legendLabelsDEM]);
inspectorPanel.widgets().set(3, legendPanel);

/*
 * Map setup
 */

// Register a callback on the default map to be invoked when the map is clicked.
mapPanel.onClick(generateChart);

// Configure the map.
mapPanel.style().set('cursor', 'crosshair');


// Initialize with a test point.
var initialPoint = ee.Geometry.Point(-51.37199020385742, 64.12248229980469); // 'Kobbefjord_M500'
mapPanel.centerObject(initialPoint, 4);


/*
 * Initialize the app
 */

// Replace the root with a SplitPanel that contains the inspector and map.
ui.root.clear();
ui.root.add(ui.SplitPanel(inspectorPanel, mapPanel));
// ui.root.add(gifPanel);

generateChart({
  lon: initialPoint.coordinates().get(0).getInfo(),
  lat: initialPoint.coordinates().get(1).getInfo()
});


var dateIntro = ui.Panel([
  ui.Label({
    value: 'Map Viewer',
    style: {fontSize: '20px', fontWeight: 'bold'}
  }),
  ui.Label("Change date (YYYY-MM-DD) to load the n-week temperature and natural color composite mosaic for current map window. Increase the week number would include more images but may take longer time.")
]);
inspectorPanel.widgets().set(4, dateIntro);

// You can even add panels to other panels
var dropdownPanel = ui.Panel({
  layout: ui.Panel.Layout.flow('horizontal'),
});
inspectorPanel.widgets().set(5, dropdownPanel);

var yearSelector = ui.Select({
  placeholder: 'please wait..',
  });
var monthSelector = ui.Select({
  placeholder: 'please wait..',
  });
var daySelector = ui.Select({
  placeholder: 'please wait..',
  });
var weekSelector = ui.Select({
  placeholder: 'please wait..',
  });
var button = ui.Button('Load');
dropdownPanel.add(yearSelector);
dropdownPanel.add(monthSelector);
dropdownPanel.add(daySelector);
dropdownPanel.add(weekSelector);
dropdownPanel.add(button);
var urlLabel = ui.Label('Download', {shown: false});
dropdownPanel.add(urlLabel);

// Let's add a dropdown with the year month day and week
var years = ee.List.sequence( date_end.get('year'), date_start.get('year'), -1),
    months = ee.List.sequence(1, 12),
    days = ee.List.sequence(1, 31),
    weeks = ee.List.sequence(0.5, 4, 0.5);

// Dropdown items need to be strings
var yearStrings = years.map(function(year){
  return ee.Number(year).format('%04d');
});
var monthStrings = months.map(function(month){
  return ee.Number(month).format('%02d');
});
var dayStrings = days.map(function(day){
  return ee.Number(day).format('%02d');
});
var weekStrings = weeks.map(function(week){
  return ee.Number(week).format('%.1f');
});

// Evaluate the results and populate the dropdown
yearStrings.evaluate(function(yearList) {
  yearSelector.items().reset(yearList);
  yearSelector.setPlaceholder('select a year');
});

monthStrings.evaluate(function(monthList) {
  monthSelector.items().reset(monthList);
  monthSelector.setPlaceholder('select a month');
});

dayStrings.evaluate(function(dayList) {
  daySelector.items().reset(dayList);
  daySelector.setPlaceholder('select a day');
});

weekStrings.evaluate(function(weekList) {
  weekSelector.items().reset(weekList);
  weekSelector.setPlaceholder('select time step (week)');
});


// Define a function that triggers when any value is changed
var loadComposite = function() {
    var aoi = ee.Geometry.Rectangle(mapPanel.getBounds());
    var year = yearSelector.getValue(),
        month = monthSelector.getValue(),
        day = daySelector.getValue(),
        week = weekSelector.getValue();

    var startDate = ee.Date.fromYMD(
      ee.Number.parse(year), ee.Number.parse(month), ee.Number.parse(day));
    var endDate = startDate.advance(ee.Number.parse(week), 'week');

    var colFilter = ee.Filter.and(
      ee.Filter.bounds(aoi),
      ee.Filter.date(startDate, endDate)
      // ee.Filter.calendarRange(6, 8, 'month')
    );


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
                .filter(ee.Filter.calendarRange(1999, 2020, 'year')) // filter out L7 imagaes acquired after 2020 due to orbit drift
                .filter(colFilter) 
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
    // var multiSat = landsatCol.merge(s2Col).sort('system:time_start', true).map(imRangeFilter); // Sort chronologically in descending order.
    
    var imMean = multiSat.mean().updateMask(greenlandmask);

    var rgblayerName = year + '-' + month + '-' + day;
    var rgbComposite = imMean.visualize(
      {
        min: 0,
        max: 1,
        bands:['SR_B4', 'SR_B3', 'SR_B2']
      }
    );//.updateMask(greenlandmask);
    var rgbCompositeLayer = ui.Map.Layer(rgbComposite).setName(rgblayerName);
    mapPanel.layers().set(1, rgbCompositeLayer);

    var originalLST = imMean.select('LST_Original');
    var originalLSTLayerName = 'Original LST ' + year + '-' + month + '-' + day;
    var originalLSTComposite = originalLST.visualize(vis);
    var originalLSTCompositeLayer = ui.Map.Layer(originalLSTComposite).setName(originalLSTLayerName);
    mapPanel.layers().set(2, originalLSTCompositeLayer);

    var imgDownload = imMean.select('GEMEST_Landsat');
    var layerName = 'GEMEST_Landsat ' + year + '-' + month + '-' + day;
    var imgComposite = imgDownload.visualize(vis);//.updateMask(greenlandmask);
    var imgCompositeLayer = ui.Map.Layer(imgComposite).setName(layerName);
    // layers.add(imgCompositeLayer, layerName);
    mapPanel.layers().set(3, imgCompositeLayer);

    // Define a function to generate a download URL of the image for the
    // viewport region. 
//     function downloadImg(img) {
//       // var viewBounds = ee.Geometry.Rectangle(mapPanel.getBounds());
//       var downloadArgs = {
//         name: 'ee_ST_B10',
//         crs: 'EPSG:3857',
//         scale: 30,
//         region: aoi.toGeoJSONString()
//     };
//     var url = img.getDownloadURL(downloadArgs);
//     return url;
// }
// urlLabel.setUrl(downloadImg(imgDownload));
// urlLabel.style().set({shown: true});
};
button.onClick(loadComposite);


/*
add logo , ref: https://gis.stackexchange.com/questions/331842/adding-a-logo-to-a-panel-on-an-app-in-google-earth-engine
*/
var logo = ee.Image('projects/ku-gem/assets/GEM_Top-h100').visualize({
  bands:  ['b1', 'b2', 'b3'],
  min: 0,
  max: 255
  });
var thumb = ui.Thumbnail({
  image: logo,
  params: {
      dimensions: '516x100',
      format: 'png'
      },
  style: {height: '100/2px', width: '516/2px',padding :'0'}
  });
var logoPanel = ui.Panel(thumb, 'flow', {width: '300px'});
inspectorPanel.widgets().set(6, logoPanel);


var logoIntro = ui.Panel([
  ui.Label("The project is part of the Greenland Environmental Monitoring (GEM) program, funded by the Danish Ministry of Energy, Utilities and Climate. The project is hosted by the Department of Geosciences and Natural Resource Management, University of Copenhagen.  It is also supported by Villum Foundation (project No. 42069)."),
  ui.Label("https://g-e-m.dk/", {}, "https://g-e-m.dk/"),
  ui.Label("https://github.com/KU-AVOCA/GEMLST", {}, "https://github.com/KU-AVOCA/GEMLST"),
//   ui.Label("Feng, S., Cook, J. M., Anesio, A. M., Benning, L. G. and Tranter, M. (2023) “Long time series (1984–2020) of albedo variations on the Greenland ice sheet from harmonized Landsat and Sentinel 2 imagery,” Journal of Glaciology. Cambridge University Press, 69(277), pp. 1225–1240. doi: 10.1017/jog.2023.11.", {}, "https://doi.org/10.1017/jog.2023.11"),
//   ui.Label("Feng, S., Cook, J. M., Onuma, Y., Naegeli, K., Tan, W., Anesio, A. M., Benning, L. G., & Tranter, M. (2023). Remote sensing of ice albedo using harmonized Landsat and Sentinel 2 datasets: validation. International Journal of Remote Sensing, 00(00), 1–29. https://doi.org/10.1080/01431161.2023.2291000", {}, "https://doi.org/10.1080/01431161.2023.2291000")
]);
inspectorPanel.widgets().set(7, logoIntro);