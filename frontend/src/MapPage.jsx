import React, { useState, useRef, useCallback } from 'react';
import Map, { Popup } from 'react-map-gl/maplibre';
import MiningPitVisualizer from './components/Visualization3D/MiningPitVisualizer';
import 'maplibre-gl/dist/maplibre-gl.css';
import './App.css';

function MapPage() {
  const [viewState, setViewState] = useState({
    longitude: 78.98,
    latitude: 20.58,
    zoom: 10,
    pitch: 0,
    bearing: 0
  });

  const [popupInfo, setPopupInfo] = useState(null);
  const [currentViewMode, setCurrentViewMode] = useState('top-down');
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationProgress, setAnimationProgress] = useState(0);
  const [is3DEnabled, setIs3DEnabled] = useState(true);
  const mapRef = useRef();

  // Toggle between 2D and 3D modes with a single button
  const toggle3DMode = useCallback(() => {
    const enable3D = !is3DEnabled;
    setIs3DEnabled(enable3D);
    setIsAnimating(true);
    
    if (enable3D) {
      // Switching to 3D - enable perspective view
      setViewState(prev => ({
        ...prev,
        pitch: 45,
        bearing: -30,
        zoom: 11.2,
        transitionDuration: 1500,
        transitionEasing: t => 1 - Math.pow(1 - t, 2)
      }));
      setCurrentViewMode('perspective');
    } else {
      // Switching to 2D - force top-down view
      setViewState(prev => ({
        ...prev,
        pitch: 0,
        bearing: 0,
        zoom: 10.5,
        transitionDuration: 1500,
        transitionEasing: t => 1 - Math.pow(1 - t, 2)
      }));
      setCurrentViewMode('top-down');
    }

    setTimeout(() => {
      setIsAnimating(false);
    }, 1500);
  }, [is3DEnabled]);

  // Enhanced flyTo with smooth easing and progress tracking
  const flyToMine = useCallback((mineCoords, properties) => {
    const targetPitch = is3DEnabled ? (currentViewMode === 'top-down' ? 45 : 60) : 0;
    setIsAnimating(true);
    setAnimationProgress(0);
    
    setViewState({
      longitude: mineCoords.lng,
      latitude: mineCoords.lat,
      zoom: properties.status === 'illegal' ? 14.5 : 13.5,
      pitch: targetPitch,
      bearing: is3DEnabled ? -30 : 0,
      transitionDuration: 3000,
      transitionEasing: t => {
        const progress = 1 - Math.pow(1 - t, 3);
        setAnimationProgress(progress);
        return progress;
      }
    });

    setTimeout(() => {
      setIsAnimating(false);
      setAnimationProgress(1);
    }, 3000);
  }, [currentViewMode, is3DEnabled]);

  // Enhanced view mode transitions with morphing effect (only in 3D mode)
  const setViewMode = useCallback((mode) => {
    if (!is3DEnabled) {
      // If in 2D mode, toggle to 3D first
      toggle3DMode();
      return;
    }
    
    setCurrentViewMode(mode);
    setIsAnimating(true);
    setAnimationProgress(0);
    
    const presets = {
      'top-down': { 
        pitch: 0, 
        bearing: 0, 
        zoom: 10.5,
        transitionDuration: 2000
      },
      'perspective': { 
        pitch: 60, 
        bearing: -30, 
        zoom: 11.2,
        transitionDuration: 1800
      },
      'cross-section': { 
        pitch: 75, 
        bearing: -45, 
        zoom: 12.5,
        transitionDuration: 2200
      }
    };

    setViewState(prev => ({
      ...prev,
      ...presets[mode],
      transitionEasing: t => {
        const progress = 1 - Math.pow(1 - t, 2);
        setAnimationProgress(progress);
        return progress;
      }
    }));

    setTimeout(() => {
      setIsAnimating(false);
      setAnimationProgress(1);
    }, 2000);
  }, [is3DEnabled, toggle3DMode]);

  // Orbital rotation animation (only in 3D mode)
  const startOrbitalRotation = useCallback(() => {
    if (!is3DEnabled) return;
    
    setIsAnimating(true);
    let startTime = Date.now();
    const duration = 15000;
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = (elapsed % duration) / duration;
      
      setViewState(prev => ({
        ...prev,
        bearing: progress * 360,
        transitionDuration: 0
      }));
      
      if (isAnimating && is3DEnabled) {
        requestAnimationFrame(animate);
      }
    };
    
    animate();
  }, [isAnimating, is3DEnabled]);

  const stopOrbitalRotation = () => {
    setIsAnimating(false);
  };

  // Handle map click
  const handleMapClick = (e) => {
    if (e.features && e.features.length > 0) {
      const feature = e.features[0];
      setPopupInfo({
        lngLat: e.lngLat,
        properties: feature.properties
      });
      
      flyToMine(e.lngLat, feature.properties);
    }
  };

  const mapStyle = {
    "version": 8,
    "sources": {
      "satellite": {
        "type": "raster",
        "tiles": [
          "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
        ],
        "tileSize": 256
      }
    },
    "layers": [{
      "id": "satellite",
      "type": "raster",
      "source": "satellite",
      "minzoom": 0,
      "maxzoom": 22
    }]
  };

  const showReportPreview = (mineData) => {
    alert(`📊 REPORT PREVIEW: ${mineData.name}\n\nStatus: ${mineData.status.toUpperCase()}\n\nNote: This is a preview with sample data.`);
  };

  return (
    <div className="app-container">
      <div className="header-bar">
        <h1>MINING ACTIVITY {is3DEnabled ? '3D' : '2D'} VISUALIZER</h1>
        <p>
          {currentViewMode.toUpperCase()} • 
          {is3DEnabled ? ' 3D 🏔️' : ' 2D 🗺️'} •
          {isAnimating ? ` 🎬 (${Math.round(animationProgress * 100)}%)` : ' ✅'} •
          Click mines
        </p>
      </div>
      
      <div className="map-container-full">
        <Map
          ref={mapRef}
          {...viewState}
          onMove={evt => setViewState(evt.viewState)}
          onClick={handleMapClick}
          interactiveLayerIds={['mining-pits-click', 'mining-pits-2d', 'mining-pits-3d']}
          mapStyle={mapStyle}
          style={{ width: '100%', height: '100%' }}
          maxPitch={is3DEnabled ? 85 : 0}
        >
          <MiningPitVisualizer />
          
          {popupInfo && (
            <Popup
              longitude={popupInfo.lngLat.lng}
              latitude={popupInfo.lngLat.lat}
              anchor="bottom"
              onClose={() => setPopupInfo(null)}
              closeButton={false}
              closeOnClick={true}
              maxWidth="400px"
            >
              <div className="custom-popup">
                <div className="popup-header">
                  <h3>{popupInfo.properties.name}</h3>
                  <span className={`status-badge ${popupInfo.properties.status}`}>
                    {popupInfo.properties.status.toUpperCase()}
                  </span>
                </div>

                <div className="popup-grid">
                  <div>
                    <strong>📍 Depth:</strong><br />
                    <span className="highlight-text">
                      {popupInfo.properties.depth} meters
                    </span>
                  </div>
                  <div>
                    <strong>📦 Volume:</strong><br />
                    {popupInfo.properties.volume}
                  </div>
                  <div>
                    <strong>📐 Area:</strong><br />
                    {popupInfo.properties.area}
                  </div>
                  <div>
                    <strong>🏢 Company:</strong><br />
                    {popupInfo.properties.company}
                  </div>
                </div>

                <div className="popup-details">
                  <div>
                    <strong>📄 License:</strong> {popupInfo.properties.license}
                  </div>
                  <div>
                    <strong>⛏️ Material:</strong> {popupInfo.properties.material}
                  </div>
                  <div>
                    <strong>📅 Started:</strong> {popupInfo.properties.start_date}
                  </div>
                  <div>
                    <strong>👥 Employees:</strong> {popupInfo.properties.employees}
                  </div>
                  <div>
                    <strong>🌿 Eco Rating:</strong> {popupInfo.properties.environmental_rating}
                  </div>
                </div>

                {popupInfo.properties.violation && (
                  <div className="violation-section">
                    <div className="violation-header">
                      <span>⚠️</span>
                      <strong>COMPLIANCE VIOLATION</strong>
                    </div>
                    <div className="violation-text">
                      {popupInfo.properties.violation}
                    </div>
                    <div className="violation-details">
                      <strong>Fine:</strong> {popupInfo.properties.fine_amount}<br />
                      <strong>Inspected:</strong> {popupInfo.properties.inspection_date}
                    </div>
                  </div>
                )}

                <div className="popup-actions">
                  <button 
                    className="popup-btn primary"
                    onClick={() => showReportPreview(popupInfo.properties)}
                  >
                    👁️ Preview Report
                  </button>
                  <button 
                    className="popup-btn secondary"
                    onClick={() => flyToMine(popupInfo.lngLat, popupInfo.properties)}
                  >
                    🎬 Re-fly to Mine
                  </button>
                </div>

                <div className="popup-footer">
                  View: {currentViewMode} • Mode: {is3DEnabled ? '3D' : '2D'}
                </div>
              </div>
            </Popup>
          )}
        </Map>

        {/* Single Toggle Button for 2D/3D */}
        <div className="compact-mode-toggle">
          <button 
            className={`compact-btn ${is3DEnabled ? 'active-3d' : 'active-2d'}`}
            onClick={toggle3DMode}
            disabled={isAnimating}
            title={is3DEnabled ? "Switch to 2D View" : "Switch to 3D View"}
          >
            {is3DEnabled ? '🏔️' : '🗺️'}
          </button>
        </div>

        {/* 3D View Toggles - Only show in 3D mode */}
        {is3DEnabled && (
          <div className="compact-3d-views">
            <button 
              className={`compact-btn ${currentViewMode === 'top-down' ? 'active' : ''}`}
              onClick={() => setViewMode('top-down')}
              disabled={isAnimating}
              title="Top Down View"
            >
              🛰️
            </button>
            <button 
              className={`compact-btn ${currentViewMode === 'perspective' ? 'active' : ''}`}
              onClick={() => setViewMode('perspective')}
              disabled={isAnimating}
              title="Perspective View"
            >
              🏔️
            </button>
            <button 
              className={`compact-btn ${currentViewMode === 'cross-section' ? 'active' : ''}`}
              onClick={() => setViewMode('cross-section')}
              disabled={isAnimating}
              title="Cross Section View"
            >
              📐
            </button>
          </div>
        )}

        <div className="controls-3d">
          <div className="camera-controls">
            <button 
              className="control-btn compact"
              onClick={() => setViewState(prev => ({
                ...prev,
                bearing: prev.bearing - 45,
                transitionDuration: 800,
                transitionEasing: t => t * (2 - t)
              }))}
              disabled={isAnimating}
              title="Rotate Left"
            >
              ↻
            </button>
            <button 
              className="control-btn compact"
              onClick={() => setViewState(prev => ({
                ...prev,
                bearing: prev.bearing + 45,
                transitionDuration: 800,
                transitionEasing: t => t * (2 - t)
              }))}
              disabled={isAnimating}
              title="Rotate Right"
            >
              ↺
            </button>
            
            {is3DEnabled && (
              <>
                <button 
                  className="control-btn compact"
                  onClick={() => setViewState(prev => ({
                    ...prev,
                    pitch: Math.min(prev.pitch + 15, 85),
                    transitionDuration: 600,
                    transitionEasing: t => t * (2 - t)
                  }))}
                  disabled={isAnimating}
                  title="Tilt Up"
                >
                  ⬆️
                </button>
                <button 
                  className="control-btn compact"
                  onClick={() => setViewState(prev => ({
                    ...prev,
                    pitch: Math.max(prev.pitch - 15, 0),
                    transitionDuration: 600,
                    transitionEasing: t => t * (2 - t)
                  }))}
                  disabled={isAnimating}
                  title="Tilt Down"
                >
                  ⬇️
                </button>
              </>
            )}
          </div>

          {is3DEnabled && (
            <div className="advanced-controls">
              <button 
                className={`control-btn compact ${isAnimating ? 'active' : ''}`}
                onClick={isAnimating ? stopOrbitalRotation : startOrbitalRotation}
                title="Auto Orbit"
              >
                {isAnimating ? '⏹️' : '🛸'}
              </button>
              <button 
                className="control-btn compact"
                onClick={() => setViewMode(is3DEnabled ? 'perspective' : 'top-down')}
                disabled={isAnimating}
                title="Reset View"
              >
                🔄
              </button>
            </div>
          )}

          {is3DEnabled && currentViewMode !== 'top-down' && (
            <div className="view-info compact">
              <span>P: {viewState.pitch}°</span>
              <span>B: {Math.round(viewState.bearing)}°</span>
              <span>Z: {viewState.zoom.toFixed(1)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MapPage;