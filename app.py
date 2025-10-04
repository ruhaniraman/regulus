import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import the modules from your teammates
from mine_detector.predict import detect_mines
from geospatial_analysis import GeospatialAnalyzer
from mask_converter import mask_to_geojson

# --- 1. INITIALIZATION AND CONFIGURATION ---

app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing

# Configure paths for file handling
# These folders must exist in your project directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['TEMP_FOLDER'] = 'temp/'
app.config['ALLOWED_EXTENSIONS'] = {'shp', 'shx', 'dbf', 'prj', 'cpg', 'zip'} # Common shapefile extensions

# --- 2. THE MAIN ANALYSIS API ENDPOINT ---

@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    print("🚀 Received new analysis request...")
    
    # --- A. HANDLE FILE UPLOAD ---
    if 'boundaryFile' not in request.files:
        return jsonify({'error': 'No boundaryFile part in the request'}), 400
    
    boundary_file = request.files['boundaryFile']
    if boundary_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Securely save the uploaded file
    filename = secure_filename(boundary_file.filename)
    boundary_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    boundary_file.save(boundary_filepath)
    print(f"📁 Boundary file saved to: {boundary_filepath}")

    # --- B. DEFINE FILE PATHS (for hackathon demo) ---
    # In a real app, these would be selected by the user. For the demo, we'll use
    # pre-defined files that match the area of the user's uploaded boundary.
    SATELLITE_IMAGE_TIF = 'test_data/jharia_coalfield_export.tif' # Original GeoTIFF
    SATELLITE_IMAGE_PNG = 'test_data/jharia_converted.png'     # Converted PNG for prediction
    DEM_FILE = 'test_data/jharia_dem.tif'                        # Digital Elevation Model
    
    # Path for the intermediate GeoJSON file we will create
    detected_geojson_path = os.path.join(app.config['TEMP_FOLDER'], 'detected_mining.geojson')
    
    try:
        # --- C. RUN THE FULL ANALYSIS PIPELINE ---

        # STEP 1: Run Member 1's ML Model to get the pixel mask
        print("🧠 Step 1/3: Running ML model to detect mining areas...")
        predicted_mask_array = detect_mines(SATELLITE_IMAGE_PNG)
        
        # STEP 2: Convert the pixel mask to vector polygons (GeoJSON)
        print("🔄 Step 2/3: Converting pixel mask to GeoJSON polygons...")
        mask_to_geojson(predicted_mask_array, SATELLITE_IMAGE_TIF, detected_geojson_path)
        
        # STEP 3: Run Member 3's Geospatial Analysis
        print("🌍 Step 3/3: Running geospatial analysis for area and volume...")
        analyzer = GeospatialAnalyzer()
        results = analyzer.analyze_mining_areas(
            authorized_boundary_path=boundary_filepath,
            detected_mining_path=detected_geojson_path,
            dem_path=DEM_FILE
        )
        
        if results is None:
            raise Exception("Geospatial analysis returned no results.")
            
        print("✅ Analysis complete! Sending results to frontend.")
        return jsonify(results)

    except Exception as e:
        print(f"❌ An error occurred during analysis: {str(e)}")
        return jsonify({'error': 'An internal error occurred', 'details': str(e)}), 500

# --- 3. START THE SERVER ---

if __name__ == '__main__':
    # The host='0.0.0.0' makes the server accessible from other devices on your network
    app.run(host='0.0.0.0', port=5000, debug=True)