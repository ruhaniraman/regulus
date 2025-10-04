// This is the primary component. It manages the application's state,
// handles file uploads, communicates with the backend server, and passes
// the analysis results down to the map and visualizer components.
import React, { useState, useCallback, useRef } from 'react';
import Map, { Popup } from 'react-map-gl/maplibre';
import MiningPitVisualizer from './components/Visualization3D/MiningPitVisualizer.jsx';
import 'maplibre-gl/dist/maplibre-gl.css';
import './App.css';

function App() {
  const [viewState, setViewState] = useState({
    longitude: 86.44, // Center on Jharia
    latitude: 23.75,
    zoom: 10,
    pitch: 45, // Start with a 3D view
    bearing: -30,
  });
  
  const [popupInfo, setPopupInfo] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleAnalysis = useCallback(async () => {
    const file = fileInputRef.current.files[0];
    if (!file) {
      alert("Please select a boundary file first.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append('boundaryFile', file);

    try {
      const response = await fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.details || 'Backend analysis failed');
      }

      const results = await response.json();
      setAnalysisResult(results);
      
      const allFeatures = [
          ...(results.geospatial_data.illegal_polygons.features || []),
          ...(results.geospatial_data.legal_polygons.features || [])
      ];
      
      if (allFeatures.length > 0) {
        const firstCoord = allFeatures[0].geometry.coordinates[0][0];
        setViewState(prev => ({
            ...prev,
            longitude: firstCoord[0],
            latitude: firstCoord[1],
            zoom: 12,
            transitionDuration: 2000,
        }));
      }

    } catch (err) {
      setError(err.message);
      console.error("Analysis failed:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  const handleMapClick = (e) => {
    if (e.features && e.features.length > 0) {
      const feature = e.features[0];
      setPopupInfo({
        lngLat: e.lngLat,
        properties: feature.properties
      });
    }
  };

  const mapStyle = {
    "version": 8,
    "sources": {
      "satellite": {
        "type": "raster",
        "tiles": ["https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"],
        "tileSize": 256
      }
    },
    "layers": [{ "id": "satellite", "type": "raster", "source": "satellite" }]
  };

  return (
    <div className="app-container">
      <header className="header-bar">
        <h1>MineSight 3D Visualizer</h1>
        <div className="upload-section">
          <input type="file" ref={fileInputRef} accept=".shp,.zip" />
          <button onClick={handleAnalysis} disabled={isLoading}>
            {isLoading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
      </header>
      
      <main className="map-container-full">
        {isLoading && <div className="status-overlay">Analyzing... Please Wait.</div>}
        {error && <div className="status-overlay" style={{color: '#FF6B6B'}}>Error: {error}</div>}
        
        <Map
          {...viewState}
          onMove={evt => setViewState(evt.viewState)}
          onClick={handleMapClick}
          interactiveLayerIds={['illegal-pits-2d', 'legal-pits-2d']}
          mapStyle={mapStyle}
          style={{ width: '100%', height: '100%' }}
          maxPitch={85}
        >
          {analysisResult && <MiningPitVisualizer data={analysisResult} />}

          {popupInfo && (
            <Popup
              longitude={popupInfo.lngLat.lng}
              latitude={popupInfo.lngLat.lat}
              anchor="bottom"
              onClose={() => setPopupInfo(null)}
              closeButton={true}
            >
              <div className="custom-popup">
                <div className="popup-header">
                  <h3>{popupInfo.properties.name}</h3>
                   <span className={`status-badge ${popupInfo.properties.status}`}>
                    {popupInfo.properties.status.toUpperCase()}
                  </span>
                </div>
                <div className="popup-grid">
                    <div><strong>Depth:</strong> {Number(popupInfo.properties.depth).toFixed(1)} m</div>
                    <div><strong>Volume:</strong> {Number(popupInfo.properties.volume).toLocaleString()} m³</div>
                </div>
              </div>
            </Popup>
          )}
        </Map>
      </main>
    </div>
  );
}

export default App;

