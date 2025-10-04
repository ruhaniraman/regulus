import cv2
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd

def mask_to_geojson(mask_array, original_image_path, output_geojson_path):
    """
    Converts a binary mask (NumPy array) to a GeoJSON file of polygons.

    Args:
        mask_array (np.ndarray): The black and white mask from your predict.py.
        original_image_path (str): Path to the original GeoTIFF satellite image
                                   to get georeferencing info.
        output_geojson_path (str): Path to save the final .geojson file.
    """
    print(f"🔄 Converting mask to polygons...")
    
    # Read the georeferencing information from the original satellite image
    with rasterio.open(original_image_path) as src:
        transform = src.transform
        crs = src.crs

    # Find contours (pixel outlines) in the mask
    contours, _ = cv2.findContours(mask_array, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Use rasterio.features.shapes to convert pixel contours to geographic shapes
    # The 'transform' argument is what maps pixels to real-world coordinates
    shapes_generator = shapes(mask_array, mask=(mask_array > 0), transform=transform)

    # Create a list of geometries
    geometries = [shape(geom) for geom, val in shapes_generator if val == 255]

    if not geometries:
        print("⚠️ No polygons found in the mask.")
        return False

    # Create a GeoDataFrame and save it as a GeoJSON file
    gdf = gpd.GeoDataFrame(geometry=geometries)
    gdf.crs = crs # Assign the correct coordinate system
    
    gdf.to_file(output_geojson_path, driver='GeoJSON')
    print(f"✅ Polygons saved successfully to '{output_geojson_path}'")
    return True

# --- Example of how the backend would use this ---
if __name__ == '__main__':
    # This is a placeholder for your actual mask output
    # In the real app, this would come from your detect_mines() function
    dummy_mask = cv2.imread('test_output_mask.png', cv2.IMREAD_GRAYSCALE)
    
    # Path to the original GeoTIFF from which the mask was generated
    original_geotiff = 'jharia_coalfield_export.tif' # Make sure this file exists
    
    # Define where the output for Member 3 will be saved
    output_for_member_3 = 'detected_mining.geojson'
    
    # Run the conversion
    mask_to_geojson(dummy_mask, original_geotiff, output_for_member_3)