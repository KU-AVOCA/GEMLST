/*
This is a Google Earth Engine (GEE) app for visualizing the Greenland Ecosystem Monitoring (GEM) 
Normalized Difference Vegetation Index (NDVI) data derived from MODIS imagery.

Author: Shunan Feng (shf@ign.ku.dk)
*/


/*
 * Map layer configuration
 * Sets up the base geographic boundaries and masks for Greenland
 */

var greenland = ee.Geometry.Polygon([
    [[-74.0, 83.0], [-74.0, 59.0], 
     [-11.0, 59.0], [-11.0, 83.0], [-74.0, 83.0]]
]);
var greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                                        .select('ocean_mask').eq(0).and(
                                        ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                                        .select('ice_mask').eq(0));
// var arcticDEM = ee.Image('UMN/PGC/ArcticDEM/V3/2m_mosaic').updateMask(greenlandmask);
var palettes = require('users/gena/packages:palettes');


/*
 * Prepare GEM-NDVI data parameters
 */

// 1. Set the date range and visualization parameters
var date_start = ee.Date.fromYMD(2000, 1, 1),
        date_end = ee.Date(Date.now());
var pallete = palettes.colorbrewer.RdYlGn[11];
var vis = {min: -1, max: 1, palette: pallete};

// 2. Functions to load and preprocess MODIS Terra and Aqua data
// 2.1 Quality Control Function for extracting specific bits from QA bands
// ref: https://gis.stackexchange.com/a/360887
function bitwiseExtract(input, fromBit, toBit) {
    var maskSize = ee.Number(1).add(toBit).subtract(fromBit);
    var mask = ee.Number(1).leftShift(maskSize).subtract(1);
    return input.rightShift(fromBit).bitwiseAnd(mask);
}

// 2.2 Function to mask low-quality pixels based on QA information in MODIS imagery
function maskQuality(image) {
        var qa = image.select('QC_250m');

        // Bits 0-1: land QA bits
        // 0: Corrected product produced at ideal quality - all bands
        // 1: Corrected product produced at less than ideal quality - some or all bands
        // 2: Corrected product not produced due to cloud effects - all bands
        // 3: Corrected product not produced for other reasons - some or all bands, may be fill value (11) [Note that a value of (11) overrides a value of (01)]
        var bits01Mask = bitwiseExtract(qa, 0, 1).eq(0);
        // var bits01Mask = bitwiseExtract(qa, 0, 1).lte(1); // if other quality is allowed
        // Bits 4-7: band 1 data quality bits
        var bits47Mask = bitwiseExtract(qa, 4, 7).eq(0);
        // Bits 8-11: band 2 data quality bits
        var bits811Mask = bitwiseExtract(qa, 8, 11).eq(0);

        var mask = bits01Mask.and(bits47Mask).and(bits811Mask);

        return image.updateMask(mask);
}


// 2.3 Create the main map and configure display options
var mapPanel = ui.Map();
mapPanel.setOptions('HYBRID').setControlVisibility(true);
var layers = mapPanel.layers();
// layers.add(demLayer, 'arctic dem');


/*
 * Panel setup
 * UI components for the application interface
 */

// Create a panel to hold title, intro text, chart and legend components.
var inspectorPanel = ui.Panel({style: {width: '30%'}});

// Create an intro panel with title and description
var intro = ui.Panel([
    ui.Label({
        value: 'NDVI - Time Series Inspector',
        style: {fontSize: '20px', fontWeight: 'bold'}
    }),
    ui.Label('This web app displays the daily MODIS derived NDVI at 250 m resolution.')
]);
inspectorPanel.add(intro);

// The commented sections below were for coordinate display and time series charting
// functionality which has been disabled in the current version

/*
 * Legend setup
 * Creates a visual legend for the NDVI map
 */

// Creates a color bar thumbnail image for use in legend from the given color palette
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

// Create the color bar for the NDVI legend
var colorBar = ui.Thumbnail({
    image: ee.Image.pixelLonLat().select(0),
    params: makeColorBarParams(vis.palette),
    style: {stretch: 'horizontal', margin: '0px 8px', maxHeight: '24px'},
});

// Create a panel with three numbers for the legend scale
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

var legendTitle = ui.Label({
    value: 'Map Legend: NDVI',
    style: {fontWeight: 'bold'}
});

var legendPanel = ui.Panel([legendTitle, colorBar, legendLabels]);
inspectorPanel.widgets().set(3, legendPanel);

// Initialize with a test point for map centering
var initialPoint = ee.Geometry.Point(-50.3736, 71.1445); 
mapPanel.centerObject(initialPoint, 4);

// Configure the main application UI layout
ui.root.clear();
ui.root.add(ui.SplitPanel(inspectorPanel, mapPanel));

/*
 * Date selector interface
 * Allows users to select specific dates to view NDVI data
 */

var dateIntro = ui.Panel([
    ui.Label({
        value: 'Map Viewer',
        style: {fontSize: '20px', fontWeight: 'bold'}
    }),
    ui.Label("Change date (YYYY-MM-DD) to load daily NDVI map. ")
]);
inspectorPanel.widgets().set(4, dateIntro);

// Create a panel for date selection dropdown menus
var dropdownPanel = ui.Panel({
    layout: ui.Panel.Layout.flow('horizontal'),
});
inspectorPanel.widgets().set(5, dropdownPanel);

// Create selectors for year, month, day and a load button
var yearSelector = ui.Select({
    placeholder: 'please wait..',
    });
var monthSelector = ui.Select({
    placeholder: 'please wait..',
    });
var daySelector = ui.Select({
    placeholder: 'please wait..',
    });
var button = ui.Button('Load');
dropdownPanel.add(yearSelector);
dropdownPanel.add(monthSelector);
dropdownPanel.add(daySelector);
dropdownPanel.add(button);
var urlLabel = ui.Label('Download', {shown: false});
dropdownPanel.add(urlLabel);

// Generate lists of years, months, and days for dropdown options
var years = ee.List.sequence(date_end.get('year'), date_start.get('year'), -1),
        months = ee.List.sequence(1, 12),
        days = ee.List.sequence(1, 31);

// Convert numeric values to formatted strings for dropdown display
var yearStrings = years.map(function(year){
    return ee.Number(year).format('%04d');
});
var monthStrings = months.map(function(month){
    return ee.Number(month).format('%02d');
});
var dayStrings = days.map(function(day){
    return ee.Number(day).format('%02d');
});

// Populate the dropdown menus with the generated options
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

/*
 * NDVI data processing and display function
 * Triggered when the Load button is clicked
 */
var loadComposite = function() {
        var aoi = ee.Geometry.Rectangle(mapPanel.getBounds());
        var year = yearSelector.getValue(),
                month = monthSelector.getValue(),
                day = daySelector.getValue();

        var startDate = ee.Date.fromYMD(
            ee.Number.parse(year), ee.Number.parse(month), ee.Number.parse(day));
        var endDate = startDate.advance(1, 'day');

        var colFilter = ee.Filter.and(
            ee.Filter.bounds(aoi),
            ee.Filter.date(startDate, endDate)
        );

        // Process MODIS Terra (MOD) data
        var MOD09GQ = ee.ImageCollection("MODIS/061/MOD09GQ")
        .filter(colFilter)
        .map(maskQuality)
        .map(function(image) {
                var ndvi = image.normalizedDifference(['sur_refl_b02', 'sur_refl_b01'])
                                                .rename('MODNDVI');
                return image.addBands(ndvi);
        });
        
        // Process MODIS Aqua (MYD) data
        var MYD09GQ = ee.ImageCollection("MODIS/061/MYD09GQ")
        .filter(colFilter)
        .map(maskQuality)
        .map(function(image) {
                var ndvi = image.normalizedDifference(['sur_refl_b02', 'sur_refl_b01'])
                                                .rename('MYDNDVI');
                return image.addBands(ndvi);
        });

        // Join Terra and Aqua collections by date
        var MCDcol = MOD09GQ.select(['MODNDVI'])
                                        .linkCollection(MYD09GQ.select(['MYDNDVI']), ['MYDNDVI']);
                                        
        // Calculate average NDVI between Terra and Aqua for each pixel
        var MCDNDVI = MCDcol.map(function(image) {
                // var ndvi_avg = image.expression(
                //         '(MODNDVI + MYDNDVI) / 2', {
                //         'MODNDVI': image.select('MODNDVI'),
                //         'MYDNDVI': image.select('MYDNDVI')
                // }).updateMask(greenlandmask);
                var ndvi_avg = image.select(['MODNDVI', 'MYDNDVI'])
                                        .reduce(ee.Reducer.mean())
                                        .updateMask(greenlandmask);
                var NDVI = ndvi_avg
                                    .set('system:time_start', image.get('system:time_start'))
                                    .set('system:index', image.get('system:index'))
                                    .rename('NDVI');
                return image.addBands(NDVI);
        });
        
        // Create and add the NDVI visualization layer to the map
        var imMean = MCDNDVI.select('NDVI').mean().updateMask(greenlandmask);
        var imgDownload = imMean.select('NDVI');
        var layerName = 'NDVI ' + year + '-' + month + '-' + day;
        var imgComposite = imgDownload.visualize(vis);
        var imgCompositeLayer = ui.Map.Layer(imgComposite).setName(layerName);
        mapPanel.layers().set(1, imgCompositeLayer);
};
button.onClick(loadComposite);

/*
 * Add GEM logo and project information
 * ref: https://gis.stackexchange.com/questions/331842/adding-a-logo-to-a-panel-on-an-app-in-google-earth-engine
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

// Add project information and acknowledgments
var logoIntro = ui.Panel([
    ui.Label("Developed and maintained by Shunan Feng and Andreas Westergaard-Nielsen. The project is part of the Greenland Environmental Monitoring (GEM) program, funded by the Danish Ministry of Energy, Utilities and Climate. The project is hosted by the Department of Geosciences and Natural Resource Management, University of Copenhagen.  It is also supported by Villum Foundation (project No. 42069)."),
    ui.Label("https://g-e-m.dk/", {}, "https://g-e-m.dk/"),
    ui.Label("https://github.com/KU-AVOCA/GEMLST", {}, "https://github.com/KU-AVOCA/GEMLST"),
]);
inspectorPanel.widgets().set(7, logoIntro);
