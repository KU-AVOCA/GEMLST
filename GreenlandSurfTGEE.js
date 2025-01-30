/*
This script aims to create a daily gapless surface temperature dataset for Greenland using MODIS Terra, MODIS Aqua, and ERA5 Land data.
It calibrates the temperature data using a set of coefficients and the surface net solar radiation data from ERA5 Land, 
and fills gaps in the MODIS LST data using ERA5 Land skin temperature data.

Steps:
1. Define the region of interest, mask, and time period.
2. Load MODIS Terra and Aqua LST data.
3. Apply quality control to the LST data.
4. Calibrate the LST data using ERA5 Land data.
5. Fill gaps in the LST data using ERA5 Land skin temperature data.
6. Generate the final gapless surface temperature dataset.
7. Export the final dataset to Google Drive.

Shunan Feng (shf@ign.ku.dk)
*/

// 1. Define the region of interest, mask, and time period
var greenland = ee.Geometry.Polygon([
  [[-74.0, 83.0], [-74.0, 59.0], 
   [-11.0, 59.0], [-11.0, 83.0], [-74.0, 83.0]]
]);
var greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK').select('ocean_mask').eq(0);
// Map.addLayer(greenlandmask, {min: 0, max: 1, palette: ['blue', 'white']}, 'Greenland Mask');

var startDate = ee.Date.fromYMD(2024, 1, 1),
    endDate = ee.Date.fromYMD(2024, 1, 31);

// 2. Load MODIS Terra and Aqua LST data
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

// 2.2 Load MODIS Terra, MODIS Aqua, and ERA5 Land data. Apply quality control and mask
var MOD11A1Daytime = ee.ImageCollection('MODIS/061/MOD11A1')
    .select(['LST_Day_1km', 'QC_Day'])
    .filterDate(startDate, endDate)
    .filterBounds(greenland)
    .map(maskQualityDaytime)
    .map(function(image) {
        var lst = image.select('LST_Day_1km')
            .multiply(0.02).subtract(273.15).rename('MODLST_Day'); // convert to Celsius degree
        var qa = image.select('QC_Day').rename('MODQA_Day');
        return image.addBands([lst, qa]).updateMask(greenlandmask);
    });

var MYD11A1Daytime = ee.ImageCollection('MODIS/061/MYD11A1')
    .select(['LST_Day_1km', 'QC_Day'])
    .filterDate(startDate, endDate)
    .filterBounds(greenland)
    .map(maskQualityDaytime)
    .map(function(image) {
        var lst = image.select('LST_Day_1km')
            .multiply(0.02).subtract(273.15).rename('MYDLST_Day'); // convert to Celsius degree
        var qa = image.select('QC_Day').rename('MYDQA_Day');
        return image.addBands([lst, qa]).updateMask(greenlandmask);
    });

var MOD11A1Nighttime = ee.ImageCollection('MODIS/061/MOD11A1')
    .select(['LST_Night_1km', 'QC_Night'])
    .filterDate(startDate, endDate)
    .filterBounds(greenland)
    .map(maskQualityNighttime)
    .map(function(image) {
        var lst = image.select('LST_Night_1km')
            .multiply(0.02).subtract(273.15).rename('MODLST_Night'); // convert to Celsius degree
        var qa = image.select('QC_Night').rename('MODQA_Night');
        return image.addBands([lst, qa]).updateMask(greenlandmask);
    });

var MYD11A1Nighttime = ee.ImageCollection('MODIS/061/MYD11A1')
    .select(['LST_Night_1km', 'QC_Night'])
    .filterDate(startDate, endDate)
    .filterBounds(greenland)
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
    .filterDate(startDate, endDate)
    .filterBounds(greenland)
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
var MODLST = MOD11A1Daytime.select(['MODLST_Day', 'MODQA_Day'])
.linkCollection(
    MOD11A1Nighttime,
    ['MODLST_Night', 'MODQA_Night']
).linkCollection(
    MYD11A1Daytime,
    ['MYDLST_Day', 'MYDQA_Day']
).linkCollection(
    MYD11A1Nighttime,
    ['MYDLST_Night', 'MYDQA_Night']
).linkCollection(
    daily_ERA5Land,
    ['surface_net_solar_radiation', 'skin_temperature']
);

// 3. Calculate Availability Pattern and Match Coefficients

// 3.1 coefficients for calbrating and calculating the final LST
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
        // if no MODIS LST is available, use ERA5 Land skin temperature
        calibratedLST = calibratedLST.where(patternMask.eq(0), ERA5LST);
        return ee.Image(correctedLST).add(calibratedLST);
    };

    // Use iterate to process all coefficient patterns
    var correctedLST = availPatternUniqueKeys
        .iterate(applyCoefficient, ee.Image(0));

    return image.addBands([
        ee.Image(correctedLST).rename('Corrected_LST').updateMask(greenlandmask),
        availPattern.rename('Available_Pattern').updateMask(greenlandmask)
    ]);
}

// Apply the correction to the MODIS LST data
var finalLST = MODLST.map(function(image) {
    return applyCorrection(image);
});

// visualize the corrected LST (first image) for quick inspection
var palettes = require('users/gena/packages:palettes');

Map.addLayer(finalLST.select('Corrected_LST').first(), {
    min: -30,
    max: 30,
    palette: palettes.cmocean.Thermal[7]
}, 'Corrected LST');

// 5. Export the final dataset
var batch = require('users/fitoprincipe/geetools:batch');

// batch export
batch.Download.ImageCollection.toDrive(finalLST.select(['Corrected_LST', 'Available_Pattern']), 'GEMLST', 
                {scale: 1000,
                 crs: 'EPSG:3413', // Greenland Polar Stereographic projection
                 region: greenland, 
                 type: 'double',
                 name: 'GEMLST_{system_date}',
                 maxPixels: 1e13,
                });

// archived script
// function applyCorrection(image) {
//     var MODLST_DAY_avail = image.select('MODLST_Day');
//     var MODLST_NIGHT_avail = image.select('MODLST_Night');
//     var MYDLST_DAY_avail = image.select('MYDLST_Day');
//     var MYDLST_NIGHT_avail = image.select('MYDLST_Night');

//     var availPattern = calculateAvailability(
//         MODLST_DAY_avail,
//         MODLST_NIGHT_avail,
//         MYDLST_DAY_avail,
//         MYDLST_NIGHT_avail
//     );

//     // calculate the average MODIS LST
//     var MODLST = image.select(
//         ['MODLST_Day', 'MODLST_Night', 'MYDLST_Day', 'MYDLST_Night']
//     ).reduce(ee.Reducer.mean());

//     var swNet = image.select('surface_net_solar_radiation');

//     // Create a function to process each coefficient pattern
//     var applyCoefficient = function(key, correctedLST) {
//         var coeff = ee.Dictionary(coefficients[ee.Number.parse(key)]);
//         var intercept = ee.Number(coeff.get('intercept'));
//         var tx = ee.Number(coeff.get('Tx'));
//         var swNetx = ee.Number(coeff.get('SW_netx'));

//         var patternMask = availPattern.eq(ee.Number.parse(key));
//         var calibratedLST = MODLST.multiply(tx)
//             .add(swNet.multiply(swNetx))
//             .add(intercept)
//             .updateMask(patternMask);

//         return ee.Image(correctedLST).add(calibratedLST);
//     };

//     // Use iterate to process all coefficient patterns
//     var correctedLST = ee.Dictionary(coefficients).keys()
//         .iterate(applyCoefficient, ee.Image(0));

//     return image.addBands(ee.Image(correctedLST).rename('Corrected_LST'));
// }                