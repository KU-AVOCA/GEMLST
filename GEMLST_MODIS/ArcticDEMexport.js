/**
 * @function exportArcticDem
 * @description Exports ArcticDEM data for a given region of interest to Google Drive
 * @param {ee.Geometry} roi - The region of interest to export
 * @param {string} description - A descriptive name for the export task and filename
 * 
 * Shunan Feng (shf@ign.ku.dk)
 */

/**
 * Initialize the map and set the region of interest (ROI).
 */
var roi = /* color: #ffc82d */ee.Geometry.Polygon(
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
Map.centerObject(roi, 8);


// Load the ArcticDEM data.
var greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                      .select('ocean_mask').eq(0); //'ice_mask', 'ocean_mask'
var arcticDem = ee.Image('UMN/PGC/ArcticDEM/V3/2m_mosaic').updateMask(greenlandmask);
var palettes = require('users/gena/packages:palettes');
var elevationVis = {
  min: -100.0,
  max: 3500.0,
  palette: palettes.cmocean.Ice[7] //['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']//palettes.cmocean.Ice[7]
};   
Map.addLayer(arcticDem, elevationVis, 'ArcticDEM');

// Define a function to export the ArcticDEM data for a given ROI.
var exportArcticDem = function(roi, description) {
  Export.image.toDrive({
    image: arcticDem,
    description: description,
    folder: 'gee', // Change this to your desired folder
    fileNamePrefix: 'ArcticDEM_' + description,
    region: roi,
    scale: 500, // Resolution of ArcticDEM
    crs: 'EPSG:3413', // Polar Stereographic projection
    maxPixels: 1e13
  });
};

// Define a function to export the mask data for a given ROI.
var exportMask = function(roi, description) {
  Export.image.toDrive({
    image: greenlandmask,
    description: description,
    folder: 'gee', 
    fileNamePrefix: 'GreenlandMask_' + description,
    region: roi,
    scale: 500,  
    crs: 'EPSG:3413', 
    maxPixels: 1e13
  });
};

// Export ArcticDEM for each ROI.
exportArcticDem(roi, 'Greenland');

// Export the mask data for each ROI.
exportMask(roi, 'Greenland');