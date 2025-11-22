# Regulus: 3D Mining Activity Monitor

**Regulus** is a comprehensive solution designed to monitor and analyze mining activities using satellite imagery and 3D visualization. Developed as an **SIH Project**, it leverages Deep Learning to detect mining pits and performs geospatial analysis to distinguish between legal and illegal operations, estimating excavation volumes and visualizing them in a 3D web interface.

## 🚀 Key Features

  * **AI-Powered Detection**: Uses a custom TensorFlow/Keras model (`mining_detector.h5`) to automatically identify mining activities in high-resolution satellite imagery.
  * **Geospatial Analysis**:
      * Differentiates between **Authorized** (legal) and **Unauthorized** (illegal) mining by cross-referencing detected areas with government-issued boundary shapefiles.
      * Calculates the precise **area (km²)** of encroachment.
      * Estimates **excavation volume (m³)** and depth using Digital Elevation Models (DEM).
  * **3D Visualization**: Interactive web frontend that renders mining pits in 3D, color-coded by legality (Green for Legal, Red for Illegal).
  * **Automated Pipeline**: Seamlessly processes shapefile uploads, runs ML inference, and generates GeoJSON reports.

## 🛠️ Tech Stack

### Backend

  * **Framework**: Flask (Python)
  * **Machine Learning**: TensorFlow, OpenCV
  * **Geospatial Processing**: GeoPandas, Rasterio, Shapely
  * **Data Handling**: NumPy

### Frontend

  * **Framework**: React + Vite
  * **Mapping**: React Map GL, MapLibre GL
  * **Styling**: CSS Modules

## 📂 Project Structure

```text
regulus/
├── app.py                 # Main Flask application and API endpoints
├── geospatial_analysis.py # Logic for area/volume calculation & legal checks
├── mask_converter.py      # Utility to convert ML pixel masks to GeoJSON polygons
├── mine_detector/
│   ├── predict.py         # ML inference logic
│   └── mining_detector.h5 # Pre-trained Deep Learning model
├── frontend/              # React frontend application
├── uploads/               # Temporary storage for uploaded boundary files
└── test_data/             # Sample satellite imagery and DEMs for demo purposes
```

## ⚙️ Installation & Setup

### Prerequisites

  * Python 3.10+
  * Node.js & npm
  * GDAL (Required for GeoPandas/Rasterio on some systems)

### 1\. Backend Setup

1.  Navigate to the project root:
    ```bash
    cd regulus
    ```
2.  Install the required Python dependencies (ensure you have a `requirements.txt` or install manually):
    ```bash
    pip install flask flask-cors tensorflow opencv-python-headless geopandas rasterio shapely
    ```
3.  Start the Flask server:
    ```bash
    python app.py
    ```
    *The server will start at `http://0.0.0.0:5000`*

### 2\. Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    *The application will be accessible at the URL provided by Vite (usually `http://localhost:5173`)*

## 🔌 API Usage

### `POST /analyze`

The core endpoint used by the frontend to trigger analysis.

  * **Request**: `multipart/form-data`
      * `boundaryFile`: The authorized boundary shapefile (e.g., `.shp`, `.zip`).
  * **Process**:
    1.  Uploads and saves the boundary file.
    2.  Runs ML detection on pre-loaded satellite imagery (`test_data/`).
    3.  Converts ML output to GeoJSON.
    4.  Performs geospatial analysis against the uploaded boundary and DEM.
  * **Response** (JSON):
    ```json
    {
      "summary": {
        "illegal_mining_area_km2": 1.25,
        "illegal_mining_volume_m3": 50000.0,
        "status": "COMPLETED_SUCCESS"
      },
      "geospatial_data": {
        "legal_polygons": { ... },
        "illegal_polygons": { ... }
      }
    }
    ```
