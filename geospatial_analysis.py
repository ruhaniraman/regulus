import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
from shapely.geometry import mapping
import json

class GeospatialAnalyzer:
    def __init__(self):
        print("✅ Geospatial Analyzer Ready")
    
    def analyze_mining_areas(self, authorized_boundary_path, detected_mining_path, dem_path):
        """
        MAIN FUNCTION - Complete Member 3 Requirements
        """
        print("🚀 Starting Comprehensive Mining Analysis...")
        
        try:
            # Read input files
            authorized = gpd.read_file(authorized_boundary_path)
            detected = gpd.read_file(detected_mining_path)
            
            print(f"📁 Loaded: {len(authorized)} authorized areas, {len(detected)} detected mining sites")
            
            # Ensure same coordinate system
            if authorized.crs != detected.crs:
                detected = detected.to_crs(authorized.crs)
            
            # Convert to projected CRS for accurate area calculations
            projected_crs = 'EPSG:3857'  # Web Mercator for area calculations
            authorized_proj = authorized.to_crs(projected_crs)
            detected_proj = detected.to_crs(projected_crs)
            
            # Identify illegal mining (outside authorized boundaries)
            illegal_mining = gpd.overlay(detected_proj, authorized_proj, how='difference')
            legal_mining = gpd.overlay(detected_proj, authorized_proj, how='intersection')
            
            # Calculate areas
            illegal_area_km2 = illegal_mining.geometry.area.sum() / 1000000
            legal_area_km2 = legal_mining.geometry.area.sum() / 1000000
            total_detected_area_km2 = detected_proj.geometry.area.sum() / 1000000
            
            print(f"📊 BOUNDARY ANALYSIS COMPLETE:")
            print(f"   Total Detected Mining: {total_detected_area_km2:.4f} km²")
            print(f"   Legal Mining Area: {legal_area_km2:.4f} km²")
            print(f"   Illegal Mining Area: {illegal_area_km2:.4f} km²")
            print(f"   Illegal Operations Found: {len(illegal_mining)}")
            
            # Calculate volumes for illegal mining areas
            print("📦 CALCULATING EXCAVATION VOLUMES...")
            volume_results = []
            total_illegal_volume = 0
            
            # Convert back to original CRS for DEM operations
            illegal_mining_orig = illegal_mining.to_crs(authorized.crs)
            
            for idx, pit in illegal_mining_orig.iterrows():
                pit_id = idx + 1
                print(f"   Analyzing illegal pit {pit_id}...")
                
                volume_data = self.calculate_excavation_volume(dem_path, pit.geometry)
                if volume_data:
                    volume_data['pit_id'] = pit_id
                    volume_data['area_km2'] = pit.geometry.area / 1000000
                    volume_results.append(volume_data)
                    total_illegal_volume += volume_data['volume_m3']
                    
                    print(f"      📏 Volume: {volume_data['volume_m3']:,.0f} m³")
                    print(f"      📐 Depth: {volume_data['avg_depth_m']:.1f}m (max: {volume_data['max_depth_m']:.1f}m)")
            
            # Prepare comprehensive results
            results = {
                'summary': {
                    'total_detected_area_km2': float(total_detected_area_km2),
                    'legal_mining_area_km2': float(legal_area_km2),
                    'illegal_mining_area_km2': float(illegal_area_km2),
                    'illegal_mining_volume_m3': float(total_illegal_volume),
                    'illegal_operations_count': len(illegal_mining),
                    'analysis_timestamp': np.datetime64('now').astype(str),
                    'status': 'COMPLETED_SUCCESS'
                },
                'illegal_operations': volume_results,
                'geospatial_data': {
                    'illegal_polygons': json.loads(illegal_mining_orig.to_json()),
                    'legal_polygons': json.loads(legal_mining.to_crs(authorized.crs).to_json())
                }
            }
            
            print("✅ COMPREHENSIVE ANALYSIS COMPLETE!")
            print(f"🎯 ILLEGAL MINING ASSESSMENT REPORT:")
            print(f"   📍 Illegal Mining Area: {results['summary']['illegal_mining_area_km2']:.4f} km²")
            print(f"   📦 Total Excavated Volume: {results['summary']['illegal_mining_volume_m3']:,.0f} m³")
            print(f"   ⚠️  Illegal Operations: {results['summary']['illegal_operations_count']}")
            print(f"   ✅ Legal Mining Area: {results['summary']['legal_mining_area_km2']:.4f} km²")
            
            return results
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def calculate_excavation_volume(self, dem_path, mining_polygon):
        """
        Calculate mining volume using DEM data
        Uses surrounding terrain to estimate original surface level
        """
        try:
            with rasterio.open(dem_path) as dem:
                # Clip DEM to mining pit area
                geom = [mapping(mining_polygon)]
                clipped_dem, transform = mask(dem, geom, crop=True, filled=True)
                current_elevation = clipped_dem[0]
                
                # Get cell size for volume calculation
                cell_size_x = transform[0]
                cell_size_y = abs(transform[4])
                cell_area = cell_size_x * cell_size_y
                
                # Estimate original surface using buffer around mining area
                buffer_distance = 50  # meters
                buffered_polygon = mining_polygon.buffer(buffer_distance)
                buffered_geom = [mapping(buffered_polygon)]
                
                buffered_dem, _ = mask(dem, buffered_geom, crop=True, filled=True)
                buffered_elevation = buffered_dem[0]
                
                # Original surface = average of surrounding terrain
                original_surface = np.nanmean(buffered_elevation)
                
                # Calculate excavation depth
                depth_map = original_surface - current_elevation
                depth_map[depth_map < 0] = 0  # Remove negative values (fill areas)
                
                # Calculate volume using Simpson's method approximation
                volume = np.sum(depth_map) * cell_area
                
                # Calculate depth statistics
                excavation_depths = depth_map[depth_map > 0]
                if len(excavation_depths) > 0:
                    avg_depth = np.mean(excavation_depths)
                    max_depth = np.max(excavation_depths)
                else:
                    avg_depth = 0
                    max_depth = 0
                
                return {
                    'volume_m3': float(volume),
                    'avg_depth_m': float(avg_depth),
                    'max_depth_m': float(max_depth),
                    'original_surface_m': float(original_surface)
                }
                
        except Exception as e:
            print(f"      ❌ Volume calculation error: {str(e)}")
            return None

# Export for integration with backend
if __name__ == "__main__":
    analyzer = GeospatialAnalyzer()
    print("📍 Member 3 - Geospatial & Volume Analysis Module")
    print("📋 Ready for integration with backend system")