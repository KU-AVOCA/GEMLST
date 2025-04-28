/*
This is a GEE app for visualizing the Greenland Ecosystem Monitoring (GEM) NDVI data.
The app displays Sentinel-2 derived NDVI at 10m resolution with cloud masking using Cloud Score+.
Users can explore time series data at specific locations and view daily NDVI maps.

Shunan Feng (shf@ign.ku.dk)
*/


/*
 * Map layer configuration
 */

// Define Greenland extent for visualization and masking
var greenland = ee.Geometry.Polygon([
  [[-74.0, 83.0], [-74.0, 59.0], 
   [-11.0, 59.0], [-11.0, 83.0], [-74.0, 83.0]]
]);

// Create land mask for Greenland (areas that are not ice or ocean)
var greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                    .select('ocean_mask').eq(0).and(
                    ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                    .select('ice_mask').eq(0));

// Import color palette package
var palettes = require('users/gena/packages:palettes');


/*
 * Prepare NDVI data parameters
 */

// Set the date range for data analysis
var date_start = ee.Date.fromYMD(2019, 1, 1),
    date_end = ee.Date(Date.now());

// Set color palette and visualization parameters for NDVI
var pallete = palettes.colorbrewer.RdYlGn[11];
var vis = {min: -1, max: 1, palette: pallete};

// Function to rename Sentinel-2 bands for NDVI calculation
function renameS2(img) {
  return img.select(
    ['B4',  'B8',  'SCL', QA_BAND],
    ['Red', 'NIR', 'SCL', QA_BAND]
  );
}

/**
 * Function to mask clouds using Cloud Score+
 * Cloud Score+ provides cloud probability scores that can be thresholded
 * to create cloud masks for Sentinel-2 imagery
 */
var QA_BAND = 'cs'; // Cloud Score+ band (more robust than 'cs_cdf')
var CLEAR_THRESHOLD = 0.65; // Threshold for cloud masking (0.5-0.65 works well)

function maskS2sr(image) {
  // Remove saturated or defective pixels (SCL=1)
  var not_saturated = image.select('SCL').neq(1);
  return image.updateMask(image.select(QA_BAND).gte(CLEAR_THRESHOLD))
              .updateMask(not_saturated)
              .updateMask(greenlandmask)
              .divide(10000); // Scale reflectance values
}

/**
 * Calculate NDVI (Normalized Difference Vegetation Index)
 * NDVI = (NIR - Red) / (NIR + Red)
 */
function addNDVI(image) {
  var ndvi = image.normalizedDifference(['NIR', 'Red']).rename('NDVI');
  return image.addBands(ndvi);
}


// Create the main map with hybrid basemap
var mapPanel = ui.Map();
mapPanel.setOptions('HYBRID').setControlVisibility(true);
var layers = mapPanel.layers();


/*
 * Panel setup
 */

// Create a panel to hold title, intro text, chart and legend components
var inspectorPanel = ui.Panel({style: {width: '30%'}});

// Create an intro panel with title and description
var intro = ui.Panel([
  ui.Label({
    value: 'NDVI - Time Series Inspector',
    style: {fontSize: '20px', fontWeight: 'bold'}
  }),
  ui.Label('This web app displays Sentinel-2 derived NDVI at 10m resolution.')
]);
inspectorPanel.add(intro);

// Create panels to display longitude/latitude coordinates
var lon = ui.Label();
var lat = ui.Label();
inspectorPanel.add(ui.Panel([lon, lat], ui.Panel.Layout.flow('horizontal')));

// Add placeholders for the chart and legend
inspectorPanel.add(ui.Label('[Chart]'));
inspectorPanel.add(ui.Label('[Legend]'));


/*
 * Chart setup
 */

// Generate a time series chart of NDVI for clicked coordinates
var generateChart = function (coords) {
  // Update the lon/lat panel with values from the click event
  lon.setValue('lon: ' + coords.lon.toFixed(4));
  lat.setValue('lat: ' + coords.lat.toFixed(4));

  // Add a dot for the point clicked on
  var point = ee.Geometry.Point(coords.lon, coords.lat);
  var dot = ui.Map.Layer(point, {color: '000000'}, 'clicked location');
  // Add the dot as the third layer, so it shows up on top of all layers
  mapPanel.layers().set(3, dot);

  // Filter image collection to point location and date range
  var s2colFilter = ee.Filter.and(
    ee.Filter.bounds(point),
    ee.Filter.date(date_start, date_end)
  );
    
  // Process Sentinel-2 imagery for NDVI calculation
  function prepS2(img) {
    var orig = img;
    img = renameS2(img);
    img = maskS2sr(img);
    img = addNDVI(img);

    return ee.Image(img.copyProperties(orig, orig.propertyNames()).set('SATELLITE', 'SENTINEL_2'));
  }
  
  // Retrieve Cloud Score+ and Sentinel-2 collections
  var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
                .filter(s2colFilter);
  var s2Col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') 
                .filter(s2colFilter) 
                .linkCollection(csPlus, [QA_BAND])
                .map(prepS2)
                .select(['NDVI']);
    
  // Create time series chart for the selected point
  var geeChart = ui.Chart.image.series(s2Col.select('NDVI'), point, ee.Reducer.mean(), 250);

  // Customize the chart appearance
  geeChart.setOptions({
    title: 'NDVI: time series',
    vAxis: {title: 'NDVI'},
    hAxis: {title: 'Date'},
    series: {
      0: {
        color: 'blue',
        lineWidth: 1,
        pointsVisible: true,
        pointSize: 2,
      },
    },
    legend: {position: 'right'},
  });
  // Add the chart at a fixed position, so that new charts overwrite older ones
  inspectorPanel.widgets().set(2, geeChart);
};


/*
 * Legend setup
 */

// Create a color bar thumbnail image for the legend
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

// Create a panel with min, middle, and max values for the legend
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

/*
 * Map setup
 */

// Register a callback on the map to be invoked when the map is clicked
mapPanel.onClick(generateChart);

// Configure the map
mapPanel.style().set('cursor', 'crosshair');

// Initialize with a test point (Kangerdlussuaq) in Greenland
var initialPoint = ee.Geometry.Point(-50.7110, 67.0106); 
mapPanel.centerObject(initialPoint, 10);


/*
 * Initialize the app
 */

// Replace the root with a SplitPanel that contains the inspector and map
ui.root.clear();
ui.root.add(ui.SplitPanel(inspectorPanel, mapPanel));

// Generate initial chart for the test point
generateChart({
  lon: initialPoint.coordinates().get(0).getInfo(),
  lat: initialPoint.coordinates().get(1).getInfo()
});


/*
 * Date selector for NDVI maps
 */

var dateIntro = ui.Panel([
  ui.Label({
    value: 'Map Viewer',
    style: {fontSize: '20px', fontWeight: 'bold'}
  }),
  ui.Label("Change date (YYYY-MM-DD) to load daily NDVI map. ")
]);
inspectorPanel.widgets().set(4, dateIntro);

// Create dropdown panel for date selection
var dropdownPanel = ui.Panel({
  layout: ui.Panel.Layout.flow('horizontal'),
});
inspectorPanel.widgets().set(5, dropdownPanel);

// Create selectors for year, month, and day
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

// Generate lists for dropdown options
var years = ee.List.sequence(date_end.get('year'), date_start.get('year'), -1),
    months = ee.List.sequence(1, 12),
    days = ee.List.sequence(1, 31);

// Format numbers as strings for dropdown items
var yearStrings = years.map(function(year){
  return ee.Number(year).format('%04d');
});
var monthStrings = months.map(function(month){
  return ee.Number(month).format('%02d');
});
var dayStrings = days.map(function(day){
  return ee.Number(day).format('%02d');
});

// Populate dropdown menus with options
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

// Function to load and display NDVI composite for selected date
var loadComposite = function() {
    var aoi = ee.Geometry.Rectangle(mapPanel.getBounds());
    var year = yearSelector.getValue(),
        month = monthSelector.getValue(),
        day = daySelector.getValue();

    var startDate = ee.Date.fromYMD(
      ee.Number.parse(year), ee.Number.parse(month), ee.Number.parse(day));
    var endDate = startDate.advance(1, 'day');

    var s2colFilter = ee.Filter.and(
    ee.Filter.bounds(aoi),
    ee.Filter.date(startDate, endDate)
    );

    // Process Sentinel-2 imagery for selected date
    function prepS2(img) {
        var orig = img;
        img = renameS2(img);
        img = maskS2sr(img);
        img = addNDVI(img);

        return ee.Image(img.copyProperties(orig, orig.propertyNames()).set('SATELLITE', 'SENTINEL_2'));
    }
    
    // Retrieve and process imagery
    var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
                  .filter(s2colFilter);
    var s2Col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') 
                  .filter(s2colFilter) 
                  .linkCollection(csPlus, [QA_BAND])
                  .map(prepS2)
                  .select(['NDVI']);

    // Create and display NDVI composite
    var imMean = s2Col.select('NDVI').mean().updateMask(greenlandmask);
    var imgDownload = imMean.select('NDVI');
    var layerName = 'NDVI ' + year + '-' + month + '-' + day;
    var imgComposite = imgDownload.visualize(vis);
    var imgCompositeLayer = ui.Map.Layer(imgComposite).setName(layerName);
    mapPanel.layers().set(1, imgCompositeLayer);
};
button.onClick(loadComposite);


/*
 * Add GEM logo and project information
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
  style: {height: '100/2px', width: '516/2px', padding: '0'}
});
var logoPanel = ui.Panel(thumb, 'flow', {width: '300px'});
inspectorPanel.widgets().set(6, logoPanel);

// Add project information and links
var logoIntro = ui.Panel([
  ui.Label("Developed and maintained by Shunan Feng and Andreas Westergaard-Nielsen. The project is part of the Greenland Environmental Monitoring (GEM) program, funded by the Danish Ministry of Energy, Utilities and Climate. The project is hosted by the Department of Geosciences and Natural Resource Management, University of Copenhagen. It is also supported by Villum Foundation (project No. 42069)."),
  ui.Label("https://g-e-m.dk/", {}, "https://g-e-m.dk/"),
  ui.Label("https://github.com/KU-AVOCA/GEMLST", {}, "https://github.com/KU-AVOCA/GEMLST"),
]);
inspectorPanel.widgets().set(7, logoIntro);
