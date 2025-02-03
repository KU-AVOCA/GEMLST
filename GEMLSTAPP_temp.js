/*
This is a GEE app for visualizing the Greenalnd Ecosystem Monitoring (GEM) Landsat Surface Temperature (LST) data.

Shunan Feng (shf@ign.ku.dk)
*/


/*
 * Map layer configuration
 */

var greenland = ee.Geometry.Polygon([
  [[-74.0, 83.0], [-74.0, 59.0], 
   [-11.0, 59.0], [-11.0, 83.0], [-74.0, 83.0]]
]);
var greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK').select('ocean_mask').eq(0);
var arcticDEM = ee.Image('UMN/PGC/ArcticDEM/V3/2m_mosaic').updateMask(greenlandmask);
var palettes = require('users/gena/packages:palettes');

var elevationVis = {
  min: 0.0,
  max: 3500.0,
  palette: palettes.cmocean.Ice[7] //['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']//palettes.cmocean.Ice[7]
};    
var arcticDEMgreenland = arcticDEM.visualize(elevationVis);
var demLayer = ui.Map.Layer(arcticDEMgreenland).setName('arctic dem');// base map

/*
prepare GEM-LST data
*/

// 1. Set the date range and visualization parameters
var date_start = ee.Date.fromYMD(2000, 1, 1),
    date_end = ee.Date(Date.now());
// palette ref: https://gist.github.com/jscarto/6cc7f547bb7d5d9acda51e5c15256b01
var surfTpallete = palettes.cmocean.Thermal[7];
var vis = {min: -20, max: 20, palette: surfTpallete};

// 2. Functions to load and preprocess MODIS Terra and Aqua LST data
// 2.1 Quality Control Function 
// ref: https://gis.stackexchange.com/a/360887
function bitwiseExtract(input, fromBit, toBit) {
  var maskSize = ee.Number(1).add(toBit).subtract(fromBit);
  var mask = ee.Number(1).leftShift(maskSize).subtract(1);
  return input.rightShift(fromBit).bitwiseAnd(mask);
}

function maskQualityDaytime(image) {
    var qa = image.select('QC_Day');

    // Bits 0-1: Mandatory QA flags
    // 0: LST produced, good quality, not necessary to examine more detailed QA
    // 1: LST produced, other quality, recommend examination of more detailed QA
    // 2: LST not produced due to cloud effects
    // 3: LST not produced primarily due to reasons other than cloud
    // var bits01Mask = bitwiseExtract(qa, 0, 1).eq(0);
    var bits01Mask = bitwiseExtract(qa, 0, 1).lte(1); // if other quality is allowed
    // Bits 2-3: Data quality flag
    // 0: Good data quality
    // 1: Other quality data
    // 2: TBD
    // 3: TBD
    var bits23Mask = bitwiseExtract(qa, 2, 3).eq(0);
    // Bits 4-5: Emissivity error flag
    // 0: Average emissivity error <= 0.01
    // 1: 0.01 < Average emissivity error <= 0.02
    // 2: 0.02 < Average emissivity error <= 0.04
    // 3: Average emissivity error > 0.04
    var bits45Mask = bitwiseExtract(qa, 4, 5).eq(0);
    // Bit 6-7: LST error flag
    // 0: Average LST error <= 1K
    // 1: Average LST error <= 2K
    // 2: Average LST error <= 3K
    // 3: Average LST error > 3K
    var bit6Mask = bitwiseExtract(qa, 6, 7).eq(0);

    var mask = bits01Mask.and(bits23Mask).and(bits45Mask).and(bit6Mask);

    return image.updateMask(mask);
}

function maskQualityNighttime(image) {
    var qa = image.select('QC_Night');

    // Bits 0-1: Mandatory QA flags
    // 0: LST produced, good quality, not necessary to examine more detailed QA
    // 1: LST produced, other quality, recommend examination of more detailed QA
    // 2: LST not produced due to cloud effects
    // 3: LST not produced primarily due to reasons other than cloud
    // var bits01Mask = bitwiseExtract(qa, 0, 1).eq(0);
    var bits01Mask = bitwiseExtract(qa, 0, 1).lte(1); // if other quality is allowed
    // Bits 2-3: Data quality flag
    // 0: Good data quality
    // 1: Other quality data
    // 2: TBD
    // 3: TBD
    var bits23Mask = bitwiseExtract(qa, 2, 3).eq(0);
    // Bits 4-5: Emissivity error flag
    // 0: Average emissivity error <= 0.01
    // 1: 0.01 < Average emissivity error <= 0.02
    // 2: 0.02 < Average emissivity error <= 0.04
    // 3: Average emissivity error > 0.04
    var bits45Mask = bitwiseExtract(qa, 4, 5).eq(0);
    // Bit 6-7: LST error flag
    // 0: Average LST error <= 1K
    // 1: Average LST error <= 2K
    // 2: Average LST error <= 3K
    // 3: Average LST error > 3K
    var bit6Mask = bitwiseExtract(qa, 6, 7).eq(0);

    var mask = bits01Mask.and(bits23Mask).and(bits45Mask).and(bit6Mask);

    return image.updateMask(mask);
}
// 2.2 Coefficients for calbrating and calculating the final LST
// Each obs_avail_flag is a unique combination of MODIS Terra and Aqua LST availability
// The availablity is noted in the comments of the coefficients, where 0 is not available and 1 is available
var coefficients = {
    // MODLST_Day: 1, MODLST_Night: 0, MYDLST_Day: 0, MYDLST_Night: 0
    8 : {intercept: -1.34695967294259,  Tx: 0.918214355203352, SW_netx: 4.53098106772407E-08,  obs_avail_flag:8},
    // MODLST_Day: 0, MODLST_Night: 0, MYDLST_Day: 1, MYDLST_Night: 0
    2 : {intercept: -2.72772961154428,  Tx: 0.864013566310192, SW_netx: -3.35940233622233E-08, obs_avail_flag:2},
    // MODLST_Day: 0, MODLST_Night: 1, MYDLST_Day: 0, MYDLST_Night: 0
    4 : {intercept: -0.482353446197247, Tx: 0.9232805167859,   SW_netx: 6.28895745791016E-07,  obs_avail_flag:4},
    // MODLST_Day: 0, MODLST_Night: 0, MYDLST_Day: 0, MYDLST_Night: 1
    1 : {intercept: -0.784992834128613, Tx: 0.906590788274843, SW_netx: 1.03669127251288E-06,  obs_avail_flag:1},
    // MODLST_Day: 1, MODLST_Night: 0, MYDLST_Day: 1, MYDLST_Night: 0
    10: {intercept: -1.87107581116087,  Tx: 0.905781514375017, SW_netx: -6.98570333719986E-08, obs_avail_flag:10},
    // MODLST_Day: 1, MODLST_Night: 1, MYDLST_Day: 0, MYDLST_Night: 0
    12: {intercept: -0.0945029361445182,Tx: 0.984136140624823, SW_netx: 6.02125454340973E-08,  obs_avail_flag:12},
    // MODLST_Day: 1, MODLST_Night: 0, MYDLST_Day: 0, MYDLST_Night: 1
    9 : {intercept:  -0.284975970024893,Tx: 0.972507056820705, SW_netx:  2.90972229423868E-07, obs_avail_flag:9},
    // MODLST_Day: 0, MODLST_Night: 1, MYDLST_Day: 1, MYDLST_Night: 0
    6 : {intercept: -0.644606390843865, Tx: 0.971834024884555, SW_netx: -7.48746592128951E-08, obs_avail_flag:6},
    // MODLST_Day: 0, MODLST_Night: 0, MYDLST_Day: 1, MYDLST_Night: 1
    3 : {intercept: -0.631502973964556, Tx: 0.976195873933907, SW_netx: 8.5668092908308E-08,   obs_avail_flag:3},
    // MODLST_Day: 0, MODLST_Night: 1, MYDLST_Day: 0, MYDLST_Night: 1
    5 : {intercept: 0.13822534121047,   Tx: 0.972898933945562, SW_netx: 6.07908419848783E-07,  obs_avail_flag:5},
    // MODLST_Day: 1, MODLST_Night: 1, MYDLST_Day: 1, MYDLST_Night: 0
    14: {intercept: -0.669653995793039, Tx: 0.970568958538719, SW_netx: -1.11444153642164E-07, obs_avail_flag:14},
    // MODLST_Day: 1, MODLST_Night: 1, MYDLST_Day: 0, MYDLST_Night: 1
    13: {intercept: 0.2080247987705,    Tx: 0.998557440221747, SW_netx: 2.29617740169069E-07,  obs_avail_flag:13},
    // MODLST_Day: 1, MODLST_Night: 0, MYDLST_Day: 1, MYDLST_Night: 1
    11: {intercept: -0.710224635510656, Tx: 0.969619217974844, SW_netx: 1.17703947635499E-08,  obs_avail_flag:11},
    // MODLST_Day: 0, MODLST_Night: 1, MYDLST_Day: 1, MYDLST_Night: 1
    7 : {intercept: -0.0074406421379301,Tx: 1.00258673602663,  SW_netx: 8.30382103055948E-08,  obs_avail_flag:7},
    // MODLST_Day: 1, MODLST_Night: 1, MYDLST_Day: 1, MYDLST_Night: 1
    15: {intercept: -0.155889791750814, Tx: 0.996384902208461, SW_netx: 2.61860711397444E-09,  obs_avail_flag:15}
};

// 2.3 Create the main map and add arctic dem as base map.
var mapPanel = ui.Map();
mapPanel.setOptions('HYBRID').setControlVisibility(true);
var layers = mapPanel.layers();
layers.add(demLayer, 'arctic dem');


/*
 * Panel setup
 */

// Create a panel to hold title, intro text, chart and legend components.
var inspectorPanel = ui.Panel({style: {width: '30%'}});

// // Create an intro panel with labels.
// var intro = ui.Panel([
//   ui.Label({
//     value: 'Land Surface Temperature - Time Series Inspector',
//     style: {fontSize: '20px', fontWeight: 'bold'}
//   }),
//   ui.Label('Click a location to see its time series of temperature.')
// ]);
// inspectorPanel.add(intro);

// // Create panels to hold lon/lat values.
// var lon = ui.Label();
// var lat = ui.Label();
// inspectorPanel.add(ui.Panel([lon, lat], ui.Panel.Layout.flow('horizontal')));

// // Add placeholders for the chart and legend.
// inspectorPanel.add(ui.Label('[Chart]'));
// inspectorPanel.add(ui.Label('[Legend]'));


/*
 * Chart setup
 */

// Generates a new time series chart of SST for the given coordinates.
// var generateChart = function (coords) {
//   // Update the lon/lat panel with values from the click event.
//   lon.setValue('lon: ' + coords.lon.toFixed(4));
//   lat.setValue('lat: ' + coords.lat.toFixed(4));

//   // Add a dot for the point clicked on.
//   var point = ee.Geometry.Point(coords.lon, coords.lat);
//   var dot = ui.Map.Layer(point, {color: '000000'}, 'clicked location');
//   // Add the dot as the third layer, so it shows up on top of all layers.
//   mapPanel.layers().set(3, dot);


//   var colFilter = ee.Filter.and(
//     ee.Filter.bounds(point),
//     ee.Filter.date(date_start, date_end)
//     // ee.Filter.calendarRange(6, 8, 'month')
//   );
  
//     var MOD11A1Daytime = ee.ImageCollection('MODIS/061/MOD11A1')
//     .select(['LST_Day_1km', 'QC_Day'])
//     .filter(colFilter)
//     .map(maskQualityDaytime)
//     .map(function(image) {
//         var lst = image.select('LST_Day_1km')
//             .multiply(0.02).subtract(273.15).rename('MODLST_Day'); // convert to Celsius degree
//         var qa = image.select('QC_Day').rename('MODQA_Day');
//         return image.addBands([lst, qa]).updateMask(greenlandmask);
//     });

//     var MYD11A1Daytime = ee.ImageCollection('MODIS/061/MYD11A1')
//     .select(['LST_Day_1km', 'QC_Day'])
//     .filter(colFilter)
//     .map(maskQualityDaytime)
//     .map(function(image) {
//         var lst = image.select('LST_Day_1km')
//             .multiply(0.02).subtract(273.15).rename('MYDLST_Day'); // convert to Celsius degree
//         var qa = image.select('QC_Day').rename('MYDQA_Day');
//         return image.addBands([lst, qa]).updateMask(greenlandmask);
//     });

//     var MOD11A1Nighttime = ee.ImageCollection('MODIS/061/MOD11A1')
//     .select(['LST_Night_1km', 'QC_Night'])
//     .filter(colFilter)
//     .map(maskQualityNighttime)
//     .map(function(image) {
//         var lst = image.select('LST_Night_1km')
//             .multiply(0.02).subtract(273.15).rename('MODLST_Night'); // convert to Celsius degree
//         var qa = image.select('QC_Night').rename('MODQA_Night');
//         return image.addBands([lst, qa]).updateMask(greenlandmask);
//     });

//     var MYD11A1Nighttime = ee.ImageCollection('MODIS/061/MYD11A1')
//     .select(['LST_Night_1km', 'QC_Night'])
//     .filter(colFilter)
//     .map(maskQualityNighttime)
//     .map(function(image) {
//         var lst = image.select('LST_Night_1km')
//             .multiply(0.02).subtract(273.15).rename('MYDLST_Night'); // convert to Celsius degree
//         var qa = image.select('QC_Night').rename('MYDQA_Night');
//         return image.addBands([lst, qa]).updateMask(greenlandmask);
//     });

//     // 2.3 Load ERA5 Land data (surface net solar radiation) and convert to daily average
//     var ERA5Land = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
//     .select('surface_net_solar_radiation', 'skin_temperature')
//     .filter(colFilter)
//     .map(function(image) {
//         return image.updateMask(greenlandmask);
//     });
  
//     // Difference in days between start and finish
//     var diff = date_end.difference(date_start, 'day');

//     // Make a list of all dates
//     var dayNum = 1; // steps of day number
//     var range = ee.List.sequence(0, diff.subtract(1), dayNum).map(function(day){return date_start.advance(day,'day')});

//     // Function for iteration over the range of dates
//     var day_mosaics = function(date, newlist) {
//     // Cast
//     date = ee.Date(date);
//     newlist = ee.List(newlist);

//     // Filter collection between date and the next day
//     var filtered = ERA5Land.filterDate(date, date.advance(dayNum,'day'));
//     // Make the mosaic
//     var image = ee.Image(
//         filtered.mean().copyProperties(filtered.first()))
//         .set({'system:index': date.format('yyyy_MM_dd')})
//         .set('system:time_start', filtered.first().get('system:time_start'));

//     // Add the mosaic to a list only if the collection has images
//     return ee.List(ee.Algorithms.If(filtered.size(), newlist.add(image), newlist));
//     };

//     var daily_ERA5Land = ee.ImageCollection(ee.List(range.iterate(day_mosaics, ee.List([]))));

//     // 2.4 Join all collections by date
//     var MODLST = MOD11A1Daytime.select(['MODLST_Day', 'MODQA_Day'])
//     .linkCollection(
//         MOD11A1Nighttime,
//         ['MODLST_Night', 'MODQA_Night']
//     ).linkCollection(
//         MYD11A1Daytime,
//         ['MYDLST_Day', 'MYDQA_Day']
//     ).linkCollection(
//         MYD11A1Nighttime,
//         ['MYDLST_Night', 'MYDQA_Night']
//     ).linkCollection(
//         daily_ERA5Land,
//         ['surface_net_solar_radiation', 'skin_temperature']
//     );
//     // 3.2 Calculate Availability Pattern
//     function calculateAvailability(terraDay, terraNight, aquaDay, aquaNight) {
//         return terraDay.mask().multiply(8)
//             .add(terraNight.mask().multiply(4))
//             .add(aquaDay.mask().multiply(2))
//             .add(aquaNight.mask().multiply(1));
//     }

//     // 4. Final Processing
//     // The function applyCorrection applies the calibration coefficients to the MODIS LST data
//     // and calculates the corrected LST
//     function applyCorrection(image) {
//         var MODLST_DAY_avail = image.select('MODLST_Day');
//         var MODLST_NIGHT_avail = image.select('MODLST_Night');
//         var MYDLST_DAY_avail = image.select('MYDLST_Day');
//         var MYDLST_NIGHT_avail = image.select('MYDLST_Night');

//         var availPattern = calculateAvailability(
//             MODLST_DAY_avail,
//             MODLST_NIGHT_avail,
//             MYDLST_DAY_avail,
//             MYDLST_NIGHT_avail
//         );

//         var availPatternUnique = availPattern.reduceRegion({
//             reducer: ee.Reducer.frequencyHistogram(),
//             geometry: greenland,
//             scale: 1000,
//             maxPixels: 1e13
//         });
//         var availPatternUniqueKeys = ee.Dictionary(
//             availPatternUnique.get(availPattern.bandNames().get(0))
//         ).keys().map(ee.Number.parse);

//         // discard the pattern with all bands masked
//         availPatternUniqueKeys = availPatternUniqueKeys.filter(
//             ee.Filter.neq('item', 0)
//         );

//         // calculate the average MODIS LST
//         var MODLSTimage = image.select(
//             ['MODLST_Day', 'MODLST_Night', 'MYDLST_Day', 'MYDLST_Night']
//         ).reduce(ee.Reducer.mean());
        
//         // if no MODIS LST is available, use ERA5 Land skin temperature
//         var ERA5LST = image.select('skin_temperature').subtract(273.15).updateMask(availPattern.eq(0));

//         var swNet = image.select('surface_net_solar_radiation');
        
//         // Create a function to process each coefficient pattern
//         var applyCoefficient = function(key, correctedLST) {
//             var numericKey = ee.Number(key).toInt();
//             var coeff = ee.Dictionary(coefficients).get(numericKey.format());
//             var coeffDict = ee.Dictionary(coeff);
//             var intercept = ee.Number(coeffDict.get('intercept'));
//             var tx = ee.Number(coeffDict.get('Tx'));
//             var swNetx = ee.Number(coeffDict.get('SW_netx'));

//             var patternMask = availPattern.eq(numericKey);
//             var calibratedLST = MODLSTimage.multiply(tx)
//                 .add(swNet.multiply(swNetx))
//                 .add(intercept)
//                 .updateMask(patternMask)
//                 .unmask(0);
//             // if no MODIS LST is available, use ERA5 Land skin temperature
//             calibratedLST = calibratedLST.where(patternMask.eq(0), ERA5LST);
//             return ee.Image(correctedLST).add(calibratedLST);
//         };

//         // Use iterate to process all coefficient patterns
//         var correctedLST = availPatternUniqueKeys
//             .iterate(applyCoefficient, ee.Image(0));

//         return image.addBands([
//             ee.Image(correctedLST).rename('Corrected_LST').updateMask(greenlandmask),
//             availPattern.rename('Available_Pattern').updateMask(greenlandmask)
//         ]);
//     }

//     // Apply the correction to the MODIS LST data
//     var finalLST = MODLST.map(function(image) {
//         return applyCorrection(image);
//     });
//   // Make a chart from the time series.
//   var geeChart = ui.Chart.image.series(finalLST.select('Corrected_LST'), point, ee.Reducer.mean(), 1000);

//   // Customize the chart.
//   geeChart.setOptions({
//     title: 'Temperature: time series',
//     vAxis: {title: 'Temperature (°C)'},
//     hAxis: {title: 'Date'},
//     series: {
//       0: {
//         color: 'blue',
//         lineWidth: 0,
//         pointsVisible: true,
//         pointSize: 2,
//       },
//     },
//     legend: {position: 'right'},
//   });
//   // Add the chart at a fixed position, so that new charts overwrite older ones.
//   inspectorPanel.widgets().set(2, geeChart);
// };




/*
 * Map setup
 */

// Register a callback on the default map to be invoked when the map is clicked.
// mapPanel.onClick(generateChart);

// Configure the map.
// mapPanel.style().set('cursor', 'crosshair');


// Initialize with a test point.
var initialPoint = ee.Geometry.Point(-50.3736, 71.1445); 
mapPanel.centerObject(initialPoint, 4);


/*
 * Initialize the app
 */

// Replace the root with a SplitPanel that contains the inspector and map.
ui.root.clear();
ui.root.add(ui.SplitPanel(inspectorPanel, mapPanel));
// ui.root.add(gifPanel);

// generateChart({
//   lon: initialPoint.coordinates().get(0).getInfo(),
//   lat: initialPoint.coordinates().get(1).getInfo()
// });


var dateIntro = ui.Panel([
  ui.Label({
    value: 'Map Viewer',
    style: {fontSize: '20px', fontWeight: 'bold'}
  }),
  ui.Label("Change date (YYYY-MM-DD) to load daily temperature map. ")
]);
inspectorPanel.widgets().set(1, dateIntro);

// You can even add panels to other panels
var dropdownPanel = ui.Panel({
  layout: ui.Panel.Layout.flow('horizontal'),
});
inspectorPanel.widgets().set(2, dropdownPanel);

var yearSelector = ui.Select({
  placeholder: 'please wait..',
  });
var monthSelector = ui.Select({
  placeholder: 'please wait..',
  });
var daySelector = ui.Select({
  placeholder: 'please wait..',
  });
// var weekSelector = ui.Select({
//   placeholder: 'please wait..',
//   });
var button = ui.Button('Load');
dropdownPanel.add(yearSelector);
dropdownPanel.add(monthSelector);
dropdownPanel.add(daySelector);
// dropdownPanel.add(weekSelector);
dropdownPanel.add(button);
var urlLabel = ui.Label('Download', {shown: false});
dropdownPanel.add(urlLabel);

// Let's add a dropdown with the year month day and week
var years = ee.List.sequence( date_end.get('year'), date_start.get('year'), -1),
    months = ee.List.sequence(1, 12),
    days = ee.List.sequence(1, 31);
    // weeks = ee.List.sequence(0.5, 4, 0.5);

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
// var weekStrings = weeks.map(function(week){
//   return ee.Number(week).format('%.1f');
// });

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

// weekStrings.evaluate(function(weekList) {
//   weekSelector.items().reset(weekList);
//   weekSelector.setPlaceholder('select time step (week)');
// });


// Define a function that triggers when any value is changed
var loadComposite = function() {
    var aoi = ee.Geometry.Rectangle(mapPanel.getBounds());
    var year = yearSelector.getValue(),
        month = monthSelector.getValue(),
        day = daySelector.getValue();
        // week = weekSelector.getValue();

    var startDate = ee.Date.fromYMD(
      ee.Number.parse(year), ee.Number.parse(month), ee.Number.parse(day));
    var endDate = startDate.advance(1, 'day');

    var colFilter = ee.Filter.and(
      ee.Filter.bounds(aoi),
      ee.Filter.date(startDate, endDate)
      // ee.Filter.calendarRange(6, 8, 'month')
    );

    var MOD11A1Daytime = ee.ImageCollection('MODIS/061/MOD11A1')
    .select(['LST_Day_1km', 'QC_Day'])
    .filter(colFilter)
    .map(maskQualityDaytime)
    .map(function(image) {
        var lst = image.select('LST_Day_1km')
            .multiply(0.02).subtract(273.15).rename('MODLST_Day'); // convert to Celsius degree
        var qa = image.select('QC_Day').rename('MODQA_Day');
        return image.addBands([lst, qa]).updateMask(greenlandmask);
    });

    var MYD11A1Daytime = ee.ImageCollection('MODIS/061/MYD11A1')
    .select(['LST_Day_1km', 'QC_Day'])
    .filter(colFilter)
    .map(maskQualityDaytime)
    .map(function(image) {
        var lst = image.select('LST_Day_1km')
            .multiply(0.02).subtract(273.15).rename('MYDLST_Day'); // convert to Celsius degree
        var qa = image.select('QC_Day').rename('MYDQA_Day');
        return image.addBands([lst, qa]).updateMask(greenlandmask);
    });

    var MOD11A1Nighttime = ee.ImageCollection('MODIS/061/MOD11A1')
    .select(['LST_Night_1km', 'QC_Night'])
    .filter(colFilter)
    .map(maskQualityNighttime)
    .map(function(image) {
        var lst = image.select('LST_Night_1km')
            .multiply(0.02).subtract(273.15).rename('MODLST_Night'); // convert to Celsius degree
        var qa = image.select('QC_Night').rename('MODQA_Night');
        return image.addBands([lst, qa]).updateMask(greenlandmask);
    });

    var MYD11A1Nighttime = ee.ImageCollection('MODIS/061/MYD11A1')
    .select(['LST_Night_1km', 'QC_Night'])
    .filter(colFilter)
    .map(maskQualityNighttime)
    .map(function(image) {
        var lst = image.select('LST_Night_1km')
            .multiply(0.02).subtract(273.15).rename('MYDLST_Night'); // convert to Celsius degree
        var qa = image.select('QC_Night').rename('MYDQA_Night');
        return image.addBands([lst, qa]).updateMask(greenlandmask);
    });

    // 2.3 Load ERA5 Land data (surface net solar radiation) and convert to daily average
    var ERA5Land = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
    .select('surface_net_solar_radiation', 'skin_temperature')
    .filter(colFilter)
    .map(function(image) {
        return image.updateMask(greenlandmask);
    });
  
    // Difference in days between start and finish
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
    var filtered = ERA5Land.filterDate(date, date.advance(dayNum,'day'));
    // Make the mosaic
    var image = ee.Image(
        filtered.mean().copyProperties(filtered.first()))
        .set({'system:index': date.format('yyyy_MM_dd')})
        .set('system:time_start', filtered.first().get('system:time_start'));

    // Add the mosaic to a list only if the collection has images
    return ee.List(ee.Algorithms.If(filtered.size(), newlist.add(image), newlist));
    };

    var daily_ERA5Land = ee.ImageCollection(ee.List(range.iterate(day_mosaics, ee.List([]))));

    // 2.4 Join all collections by date
    var MODLST = daily_ERA5Land.select(['surface_net_solar_radiation', 'skin_temperature'])
    .linkCollection(
        MOD11A1Daytime, 
        ['MODLST_Day', 'MODQA_Day']
    ).linkCollection(
        MOD11A1Nighttime,
        ['MODLST_Night', 'MODQA_Night']
    ).linkCollection(
        MYD11A1Daytime,
        ['MYDLST_Day', 'MYDQA_Day']
    ).linkCollection(
        MYD11A1Nighttime,
        ['MYDLST_Night', 'MYDQA_Night']
    );
    // 3.2 Calculate Availability Pattern
    function calculateAvailability(terraDay, terraNight, aquaDay, aquaNight) {
        return terraDay.mask().multiply(8)
            .add(terraNight.mask().multiply(4))
            .add(aquaDay.mask().multiply(2))
            .add(aquaNight.mask().multiply(1));
    }

    // 4. Final Processing
    // The function applyCorrection applies the calibration coefficients to the MODIS LST data
    // and calculates the corrected LST
    function applyCorrection(image) {
        var MODLST_DAY_avail = image.select('MODLST_Day');
        var MODLST_NIGHT_avail = image.select('MODLST_Night');
        var MYDLST_DAY_avail = image.select('MYDLST_Day');
        var MYDLST_NIGHT_avail = image.select('MYDLST_Night');

        var availPattern = calculateAvailability(
            MODLST_DAY_avail,
            MODLST_NIGHT_avail,
            MYDLST_DAY_avail,
            MYDLST_NIGHT_avail
        );

        var availPatternUnique = availPattern.reduceRegion({
            reducer: ee.Reducer.frequencyHistogram(),
            geometry: greenland,
            scale: 1000,
            maxPixels: 1e13
        });
        var availPatternUniqueKeys = ee.Dictionary(
            availPatternUnique.get(availPattern.bandNames().get(0))
        ).keys().map(ee.Number.parse);

        // discard the pattern with all bands masked
        availPatternUniqueKeys = availPatternUniqueKeys.filter(
            ee.Filter.neq('item', 0)
        );

        // calculate the average MODIS LST
        var MODLSTimage = image.select(
            ['MODLST_Day', 'MODLST_Night', 'MYDLST_Day', 'MYDLST_Night']
        ).reduce(ee.Reducer.mean());
        
        // if no MODIS LST is available, use ERA5 Land skin temperature
        var ERA5LST = image.select('skin_temperature').subtract(273.15).updateMask(availPattern.eq(0));

        var swNet = image.select('surface_net_solar_radiation');
        
        // Create a function to process each coefficient pattern
        var applyCoefficient = function(key, correctedLST) {
          var numericKey = ee.Number(key).toInt();
          var coeff = ee.Dictionary(coefficients).get(numericKey.format());
          var coeffDict = ee.Dictionary(coeff);
          var intercept = ee.Number(coeffDict.get('intercept'));
          var tx = ee.Number(coeffDict.get('Tx'));
          var swNetx = ee.Number(coeffDict.get('SW_netx'));

          var patternMask = availPattern.eq(numericKey);
          var calibratedLST = MODLSTimage.multiply(tx)
              .add(swNet.multiply(swNetx))
              .add(intercept)
              .updateMask(patternMask)
              .unmask(0);
              
          return ee.Image(correctedLST).add(calibratedLST);
        };

        // Use iterate to process all coefficient patterns
        var correctedLST = availPatternUniqueKeys
            .iterate(applyCoefficient, ee.Image(0));

        return image.addBands([
            // if no MODIS LST is available, use ERA5 Land skin temperature
            ee.Image(correctedLST).where(availPattern.eq(0), ERA5LST).rename('Corrected_LST').updateMask(greenlandmask),
            availPattern.rename('Available_Pattern').updateMask(greenlandmask)
        ]);
    }

    // Apply the correction to the MODIS LST data
    var finalLST = MODLST.map(function(image) {
        return applyCorrection(image);
    });

    var imMean = finalLST.select('Corrected_LST').mean().updateMask(greenlandmask);
    var imgDownload = imMean.select('Corrected_LST');
    var layerName = 'tmperature ' + year + '-' + month + '-' + day;
    var imgComposite = imgDownload.visualize(vis);//.updateMask(greenlandmask);
    var imgCompositeLayer = ui.Map.Layer(imgComposite).setName(layerName);
    // layers.add(imgCompositeLayer, layerName);
    mapPanel.layers().set(1, imgCompositeLayer);
    // Define a function to generate a download URL of the image for the
    // viewport region. 
//     function downloadImg(img) {
//       // var viewBounds = ee.Geometry.Rectangle(mapPanel.getBounds());
//       var downloadArgs = {
//         name: 'GEMLST',
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
//   ui.Label("https://github.com/fsn1995/Remote-Sensing-of-Albedo", {}, "https://github.com/fsn1995/Remote-Sensing-of-Albedo"),
//   ui.Label("Feng, S., Cook, J. M., Anesio, A. M., Benning, L. G. and Tranter, M. (2023) “Long time series (1984–2020) of albedo variations on the Greenland ice sheet from harmonized Landsat and Sentinel 2 imagery,” Journal of Glaciology. Cambridge University Press, 69(277), pp. 1225–1240. doi: 10.1017/jog.2023.11.", {}, "https://doi.org/10.1017/jog.2023.11"),
//   ui.Label("Feng, S., Cook, J. M., Onuma, Y., Naegeli, K., Tan, W., Anesio, A. M., Benning, L. G., & Tranter, M. (2023). Remote sensing of ice albedo using harmonized Landsat and Sentinel 2 datasets: validation. International Journal of Remote Sensing, 00(00), 1–29. https://doi.org/10.1080/01431161.2023.2291000", {}, "https://doi.org/10.1080/01431161.2023.2291000")
]);
inspectorPanel.widgets().set(7, logoIntro);