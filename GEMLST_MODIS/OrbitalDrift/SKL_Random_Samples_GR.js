/* 
Script by Shunan Feng 
https://github.com/fsn1995/orbit-drift-MODIS-ice-albedo/blob/main/gee/randomSampleBuffer.js
with a few little alterations by Simon Kleiner to meet the GEMLST aims. 
Run the script directly in the GEE console. 
*/

/*
initialize random sampler
*/
var cellSize = 10000, //size of the sample grid
    seed = 17793, // just the year of this script :)
    projcrs = "EPSG:3413"; //in WGS 84 / EPSG Greenland Polar Stereographic

               
var greenlandmask = ee.Image('OSU/GIMP/2000_ICE_OCEAN_MASK')
                   .select('ocean_mask').eq(0); // #'ice_mask', 'ocean_mask'    

/*
Functions for random sampling with buffer by Noel Gorelick,
modifed to mask out by ELA.
ref:https://medium.com/google-earth/random-samples-with-buffering-6c8737384f8c
*/

// Generate random points in the given region, buffered by the scale of the given projection.
// When strict is
//   true: points will be at least 'scale' apart, with an average spacing of 2*scale.
//   false: points will be, on average, 'scale' apart, but with no minimum distance guarantee.
var pointsWithBuffer = function(proj, region, seed, strict) {
  // Construct a grid of random numbers with the appropriate sized pixels 
  // and randomly offset it, so subsequent runs don't sample from the exact same cells.
  var looseGrid = ee.Image.random(seed).multiply(1000000).int();

  // To ensure no points can be closer than the given distance we mask off 8 out of 9 grid cells.
  // leaving only those cells have an odd x and y coordinates.  
  // Cell coordinates are centered on the 1/2 pixel. The double not is to avoid float comparison issues.
  var mask = ee.Image.pixelCoordinates(proj)
      .expression('!((b("x") + 0.5) % 2 != 0 || (b("y") + 0.5) % 2 != 0)');
  var strictGrid = looseGrid.updateMask(mask);

  // Pick a grid based on the 'strict' option.
  var cells = ee.Image(ee.Algorithms.If(strict, strictGrid, looseGrid)).clip(region).reproject(proj);
  // Uncomment to visuaize cells.
  // Map.addLayer(cells.randomVisualizer());
  
  // Generate another random image and select the maximum random value 
  // in each grid cell as the sample point.
  var random = ee.Image.random(seed).multiply(1000000).int();
  var maximum = cells.addBands(random).reduceConnectedComponents(ee.Reducer.max());
  
  // Find all the points that are local maximums and convert to a FeatureCollection.
  var points = random.eq(maximum).selfMask()
  var samples = points.reduceToVectors({
    reducer: ee.Reducer.countEvery(),
    geometry: region,
    crs: proj.scale(1/16, 1/16),
    geometryType: 'centroid',
    maxPixels: 1e13,
  })

  return samples
}

// Translates a projection by a random amount between 0 and 1 in projection units.
var randomOffset = function(projection, seed) {
  var values = ee.FeatureCollection([ee.Feature(null, null)])
    .randomColumn('x', seed)
    .randomColumn('y', seed)
    .first()
  return projection.translate(values.get("x"), values.get("y"))
}

// Display the pixel grid assocaited with a projection, as box outlines.
var displayGrid = function(proj, mask) {
  // Scale by 2 because we have 2 zero crossings when using round.
  var cells = ee.Image.pixelCoordinates(proj.scale(2,2))
  return cells.subtract(cells.round()).zeroCrossing().reduce('sum').selfMask().updateMask(mask)
}

/*
random sampling points with strict buffer
*/

var region = greenlandmask.selfMask().reduceToVectors({
  geometryType: 'polygon',
  reducer: ee.Reducer.countEvery(),
  scale: cellSize,
  maxPixels: 1e13
});

var grid = randomOffset(ee.Projection(projcrs).atScale(cellSize), seed);

Map.addLayer(pointsWithBuffer(grid, region, seed, true), {color: '#b22222'}, 'Strict')
Map.addLayer(displayGrid(grid, greenlandmask).clip(region), {palette: ['#92222244']}, 'Strict Grid');
print(pointsWithBuffer(grid, region, seed, true).size(), " strict points, spaced ", grid.nominalScale(), " meters apart.")

// Export an ee.FeatureCollection as an Earth Engine asset in case the sampling points size is too big.
Export.table.toAsset({
    collection: pointsWithBuffer(grid, region, seed, true),
    description:'randomGR5km',
    assetId: 'projects/ee-ivanburgov666/assets/orbitdrift/randomGrIS5km_260423',
  });

// Export the feature collection as a shapefile to Google Drive.
Export.table.toDrive({
    collection: pointsWithBuffer(grid, region, seed, true),
    description:'randomGR5km_260423',
    fileFormat: 'SHP'
  });


/*
Visualize the exported feature collection the the grid
*/

// var poi = ee.FeatureCollection("projects/ee-deeppurple/assets/topography/randomELA2000");  
// Map.addLayer(poi, {color: '#b22222'}, 'Strict Points')     
// print(poi.size(), " strict points, spaced ", grid.nominalScale(), " meters apart.")