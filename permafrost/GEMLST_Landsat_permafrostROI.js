/**
 * @file GEMLST_Landsat_permafrostROI.js
 * @description This script defines and visualizes permafrost study regions in Greenland, focusing on
 * locations of the Greenland Ecosystem Monitoring (GEM) program. It loads ArcticDEM elevation data,
 * defines multiple regions of interest (ROIs) including Disko, Kobbefjord, Zackenberg, Kangerlussuaq,
 * Ilulissat, Nuuk, Qaanaaq, and Aasiaat, and displays AWS (Automated Weather Station) points.
 * The script provides functionality to export ArcticDEM data for each ROI to Google Drive, 
 * which can be used for further permafrost studies or terrain analysis.
 * 
 * Shunan Feng (shf@ign.ku.dk)
 */

/**
 * Initialize the map and set the region of interest (ROI).
 */
// a list of points for GEM AWS stations with temperature data
var awsPoints = ee.FeatureCollection([
    // Kobbefjord
    ee.Feature(ee.Geometry.Point([-51.37199020385742, 64.12248229980469]), {
        id: 'Kobbefjord_M500'
    }),
    
    // Disko
    ee.Feature(ee.Geometry.Point([-53.479400634765625, 69.27300262451172]), {
        id: 'Disko_T1'
    }),
    ee.Feature(ee.Geometry.Point([-53.43281936645508, 69.28909301757812]), {
        id: 'Disko_T2'
    }),
    ee.Feature(ee.Geometry.Point([-53.45709991455078, 69.2767105102539]), {
        id: 'Disko_T3'
    }),
    ee.Feature(ee.Geometry.Point([-53.49897003173828, 69.25126647949219]), {
        id: 'Disko_T4'
    }),
    ee.Feature(ee.Geometry.Point([-53.514129638671875, 69.25348663330078]), {
        id: 'Disko_AWS2'
    }),
    
    // Zackenberg
    ee.Feature(ee.Geometry.Point([-20.563194274902344, 74.46549224853516]), {
        id: 'Zackenberg_M2'
    }),
    ee.Feature(ee.Geometry.Point([-20.459354400634766, 74.50310516357422]), {
        id: 'Zackenberg_M3'
    }),
    ee.Feature(ee.Geometry.Point([-20.552143096923828, 74.47307586669922]), {
        id: 'Zackenberg_M4_30min'
    })
]);

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
Map.addLayer(roi_disko, {}, 'Disko ROI');
Map.addLayer(roi_kobbefjord, {}, 'Kobbefjord ROI');
Map.addLayer(roi_zackenberg, {}, 'Zackenberg ROI');
Map.addLayer(roi_kangerlussuaq, {}, 'Kangerlussuaq ROI');
Map.addLayer(roi_ilulissat, {}, 'Ilulissat ROI');
Map.addLayer(roi_nuuk, {}, 'Nuuk ROI');
Map.addLayer(awsPoints, {}, 'AWS Points');

// Define a function to export the ArcticDEM data for a given ROI.
var exportArcticDem = function(roi, description) {
  Export.image.toDrive({
    image: arcticDem,
    description: description,
    folder: 'gee', // Change this to your desired folder
    fileNamePrefix: 'ArcticDEM_' + description,
    region: roi,
    scale: 30, // Resolution of ArcticDEM
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
    scale: 30,  
    crs: 'EPSG:3413', 
    maxPixels: 1e13
  });
};

// Export ArcticDEM for each ROI.
exportArcticDem(roi_disko, 'Disko');
exportArcticDem(roi_kobbefjord, 'Kobbefjord');
exportArcticDem(roi_zackenberg, 'Zackenberg');
exportArcticDem(roi_kangerlussuaq, 'Kangerlussuaq');
exportArcticDem(roi_ilulissat, 'Ilulissat');
exportArcticDem(roi_nuuk, 'Nuuk');
exportArcticDem(roi_qaanaaq, 'Qaanaaq');
exportArcticDem(roi_aasiaat, 'Aasiaat');

// Export mask for each ROI.
exportMask(roi_disko, 'Disko');
exportMask(roi_kobbefjord, 'Kobbefjord');
exportMask(roi_zackenberg, 'Zackenberg');
exportMask(roi_kangerlussuaq, 'Kangerlussuaq');
exportMask(roi_ilulissat, 'Ilulissat');
exportMask(roi_nuuk, 'Nuuk');
exportMask(roi_qaanaaq, 'Qaanaaq');
exportMask(roi_aasiaat, 'Aasiaat');
