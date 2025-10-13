// This component is responsible for rendering the 3D mining pits.
// It now takes real data from the backend as a 'prop' and creates
// two separate visual layers: one for legal pits (green) and one
// for illegal pits (red), based on the analysis results.
import React from 'react';
import { Source, Layer } from 'react-map-gl/maplibre';

const MiningPitVisualizer = ({ data }) => {
  // Don't render anything if there's no data yet
  if (!data || !data.geospatial_data) {
    return null;
  }

  const { legal_polygons, illegal_polygons } = data.geospatial_data;
  
  // A function to add depth data to each polygon for 3D extrusion
  const addDataToFeatures = (featureCollection, isIllegal) => {
      if (!featureCollection || !featureCollection.features) return null;

      return {
          ...featureCollection,
          features: featureCollection.features.map((feature, index) => {
              const operation = isIllegal ? (data.illegal_operations || [])[index] : null;
              return {
                ...feature,
                properties: {
                    ...feature.properties,
                    status: isIllegal ? 'illegal' : 'legal',
                    depth: operation ? operation.avg_depth_m : 50, // Use real depth or default
                    volume: operation ? operation.volume_m3 : 'N/A',
                    name: isIllegal ? `Illegal Pit #${index + 1}` : `Legal Area #${index + 1}`
                }
              };
          })
      };
  };
  
  const illegalPitsWithData = addDataToFeatures(illegal_polygons, true);
  const legalPitsWithData = addDataToFeatures(legal_polygons, false);

  const layerPaint3D = (color) => ({
    'fill-extrusion-color': color,
    'fill-extrusion-height': ['*', ['get', 'depth'], 10], // Exaggerate depth for visibility
    'fill-extrusion-base': 0,
    'fill-extrusion-opacity': 0.85
  });
  
  const layerPaint2D = (color) => ({
      'fill-color': color,
      'fill-opacity': 0.6,
      'fill-outline-color': '#ffffff'
  });

  return (
    <>
      {/* Source and Layers for ILLEGAL mining pits */}
      {illegalPitsWithData && (
        <Source id="illegal-pits" type="geojson" data={illegalPitsWithData}>
            <Layer id="illegal-pits-3d" type="fill-extrusion" paint={layerPaint3D('#B71C1C')} />
            <Layer id="illegal-pits-2d" type="fill" paint={layerPaint2D('#FF6B6B')} />
        </Source>
      )}
      
      {/* Source and Layers for LEGAL mining pits */}
      {legalPitsWithData && (
        <Source id="legal-pits" type="geojson" data={legalPitsWithData}>
            <Layer id="legal-pits-3d" type="fill-extrusion" paint={layerPaint3D('#1B5E20')} />
            <Layer id="legal-pits-2d" type="fill" paint={layerPaint2D('#50C878')} />
        </Source>
      )}
    </>
  );
};

export default MiningPitVisualizer;

