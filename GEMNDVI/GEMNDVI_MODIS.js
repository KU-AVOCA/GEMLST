

/**
 * @fileoverview GEMNDVI_MODIS.js - Calculates NDVI for Greenland using MODIS Terra and Aqua data
 * 
 * This script processes MODIS surface reflectance data to generate normalized difference
 * vegetation index (NDVI) composites for Greenland. It performs the following steps:
 * 1. Defines a Greenland land mask excluding ocean and ice areas
 * 2. Sets up a simple bounding box for Greenland
 * 3. Applies quality control to filter out low-quality pixels
 * 4. Calculates NDVI from both Terra (MOD09GQ) and Aqua (MYD09GQ) sensors
 * 5. Combines and averages NDVI values from both sensors
 * 6. Exports the resulting NDVI dataset to Google Drive in Greenland Polar Stereographic projection
 * 
 * Shunan Feng (shf@ign.ku.dk)
 */
// Greenland landmask - selects areas that are both not ocean and not ice
var greenland_landmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                    .select('ocean_mask').eq(0).and(
                      ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                      .select('ice_mask').eq(0));

var greenland = /* color: #ffc82d */ee.Geometry.Polygon(
    [[[-36.29516924635421, 83.70737243835941],
      [-51.85180987135421, 82.75597137647488],
      [-61.43188799635421, 81.99879137488564],
      [-74.08813799635422, 78.10103528196419],
      [-70.13305987135422, 75.65372336709613],
      [-61.08032549635421, 75.71891096312955],
      [-52.20337237135421, 60.9795530382023],
      [-43.41430987135421, 58.59235996703347],
      [-38.49243487135421, 64.70478286561182],
      [-19.771731746354217, 69.72271161037442],
      [-15.728762996354217, 76.0828635948066],
      [-15.904544246354217, 79.45091003031243],
      [-10.015872371354217, 81.62328742628017],
      [-26.627200496354217, 83.43179828852398],
      [-31.636966121354217, 83.7553561747887]]]); // whole greenland   

// Set the time period for analysis
var startDate = ee.Date.fromYMD(2024, 7, 1),
    endDate = ee.Date.fromYMD(2024, 8, 1);

// Quality Control Helper Functions
// Extract specific bits from QA band for quality assessment
// ref: https://gis.stackexchange.com/a/360887
function bitwiseExtract(input, fromBit, toBit) {
    var maskSize = ee.Number(1).add(toBit).subtract(fromBit);
    var mask = ee.Number(1).leftShift(maskSize).subtract(1);
    return input.rightShift(fromBit).bitwiseAnd(mask);
}

// Apply quality control masks to MODIS images
// Only keeps pixels with ideal quality across all bands
function maskQuality(image) {
    var qa = image.select('QC_250m');

    // Bits 0-1: land QA bits
    // 0: Corrected product produced at ideal quality - all bands
    // 1: Corrected product produced at less than ideal quality - some or all bands
    // 2: Corrected product not produced due to cloud effects - all bands
    // 3: Corrected product not produced for other reasons - some or all bands, may be fill value (11)
    var bits01Mask = bitwiseExtract(qa, 0, 1).eq(0);
    
    // Bits 4-7: band 1 data quality bits
    var bits47Mask = bitwiseExtract(qa, 4, 7).eq(0);
    
    // Bits 8-11: band 2 data quality bits
    var bits811Mask = bitwiseExtract(qa, 8, 11).eq(0);

    var mask = bits01Mask.and(bits47Mask).and(bits811Mask);

    return image.updateMask(mask);
}

// Load MODIS Terra data, apply quality control, and calculate NDVI
var MOD09GQ = ee.ImageCollection("MODIS/061/MOD09GQ")
    .filterDate(startDate, endDate)
    .filterBounds(greenland)
    .map(maskQuality)
    .map(function(image) {
        var ndvi = image.normalizedDifference(['sur_refl_b02', 'sur_refl_b01'])
                        .rename('MODNDVI');
        return image.addBands(ndvi);
    });

// Load MODIS Aqua data, apply quality control, and calculate NDVI
var MYD09GQ = ee.ImageCollection("MODIS/061/MYD09GQ")
    .filterDate(startDate, endDate)
    .filterBounds(greenland)
    .map(maskQuality)
    .map(function(image) {
        var ndvi = image.normalizedDifference(['sur_refl_b02', 'sur_refl_b01'])
                        .rename('MYDNDVI');
        return image.addBands(ndvi);
    });

// Join Terra and Aqua NDVI collections by date
// This creates a combined collection with both sensors' data
var MCDcol = MOD09GQ.select(['MODNDVI'])
                    .linkCollection(MYD09GQ.select(['MYDNDVI']), ['MYDNDVI']);

// Calculate the average NDVI from Terra and Aqua for each date
var MCDNDVI = MCDcol.map(function(image) {
    // var ndvi_avg = image.expression(
    //     '(MODNDVI + MYDNDVI) / 2', {
    //     'MODNDVI': image.select('MODNDVI'),
    //     'MYDNDVI': image.select('MYDNDVI')
    // }).updateMask(greenland_landmask);
    var ndvi_avg = image.select(['MODNDVI', 'MYDNDVI'])
                        .reduce(ee.Reducer.mean())
                        .updateMask(greenland_landmask);
    
    var NDVI = ndvi_avg
                       .set('system:time_start', image.get('system:time_start'))
                       .set('system:index', image.get('system:index'))
                       .rename('NDVI');
    
    return image.addBands(NDVI);
});


// Export the final NDVI dataset to Google Drive
var batch = require('users/fitoprincipe/geetools:batch');

// Batch export NDVI images with appropriate projection for Greenland
batch.Download.ImageCollection.toDrive(MCDNDVI.select('NDVI'), 'GEMNDVI', 
                {scale: 250,
                 crs: 'EPSG:3413', // Greenland Polar Stereographic projection
                 region: greenland, 
                 type: 'float',
                 name: 'GEMNDVI_MODIS_{system_date}',
                 maxPixels: 1e13,
                });


/**
 * Visualization code (commented out but available)
 */
// Visualize the average NDVI for the region of interest
var ndvi_avg = MCDNDVI.select('NDVI').mean();

var palettes = require('users/gena/packages:palettes');
// Using a green palette for NDVI visualization
var visParam = {min: -1, max: 1, palette: palettes.colorbrewer.RdYlGn[11]};

Map.addLayer(ndvi_avg, visParam, 'NDVI Average');

// Create a color bar for the map
var colorBar = ui.Thumbnail({
    image: ee.Image.pixelLonLat().select(0),
    params: {
        bbox: [0, 0, 1, 0.1],
        dimensions: '300x20',
        format: 'png',
        min: 0,
        max: 1,
        palette: visParam.palette
    },
    style: {position: 'bottom-right', margin: '0px 0px 30px 0px'}
});

// Create panel for colorbar legend
var legendPanel = ui.Panel({
    style: {
        position: 'bottom-right',
        padding: '8px 15px'
    }
});

// Function to generate the legend
function makeLegend() {
    legendPanel.clear();

    var legendTitle = ui.Label({
        value: 'NDVI',
        style: {
            fontWeight: 'bold',
            fontSize: '14px',
            margin: '0 0 4px 0',
            padding: '0'
        }
    });
    legendPanel.add(legendTitle);

    // Create and add the color bar
    legendPanel.add(colorBar);

    // Create min and max labels
    var minMaxPanel = ui.Panel({
        widgets: [
            ui.Label(visParam.min, {margin: '4px 8px'}),
            ui.Label(visParam.max, {margin: '4px 8px', textAlign: 'right', stretch: 'horizontal'})
        ],
        layout: ui.Panel.Layout.flow('horizontal')
    });
    legendPanel.add(minMaxPanel);

    Map.add(legendPanel);
}

makeLegend();