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
            
            # --- FIX STARTS HERE ---
            # If the user's uploaded shapefile is missing CRS info,
            # assume it's the same as the CRS from our ML-detected polygons.
            if authorized.crs is None:
                print("⚠️  Warning: Uploaded boundary is missing CRS info. Assuming same CRS as satellite data.")
                authorized.crs = detected.crs
            # --- FIX ENDS HERE ---
            
            # Ensure same coordinate system
            if authorized.crs != detected.crs:
                print(f"CRS Mismatch: Converting detected areas from {detected.crs} to {authorized.crs}")
                detected = detected.to_crs(authorized.crs)
            
            # Convert to projected CRS for accurate area calculations
            projected_crs = 'EPSG:3857'
            authorized_proj = authorized.to_crs(projected_crs)
            detected_proj = detected.to_crs(projected_crs)
            
            # Identify illegal and legal mining
            illegal_mining = gpd.overlay(detected_proj, authorized_proj, how='difference')
            legal_mining = gpd.overlay(detected_proj, authorized_proj, how='intersection')
            
            # Calculate areas
            illegal_area_km2 = illegal_mining.geometry.area.sum() / 1_000_000
            legal_area_km2 = legal_mining.geometry.area.sum() / 1_000_000
            total_detected_area_km2 = detected_proj.geometry.area.sum() / 1_000_000
            
            print(f"📊 BOUNDARY ANALYSIS COMPLETE:")
            print(f"   Illegal Mining Area: {illegal_area_km2:.4f} km²")
            
            # Calculate volumes for illegal mining areas
            print("📦 CALCULATING EXCAVATION VOLUMES...")
            volume_results = []
            total_illegal_volume = 0
            
            illegal_mining_orig = illegal_mining.to_crs(authorized.crs)
            
            for idx, pit in illegal_mining_orig.iterrows():
                pit_id = idx + 1
                volume_data = self.calculate_excavation_volume(dem_path, pit.geometry)
                if volume_data:
                    volume_data['pit_id'] = pit_id
                    # Calculate area in projected CRS for accuracy
                    pit_proj = gpd.GeoSeries([pit.geometry], crs=authorized.crs).to_crs(projected_crs)
                    volume_data['area_km2'] = pit_proj.area.sum() / 1_000_000
                    volume_results.append(volume_data)
                    total_illegal_volume += volume_data['volume_m3']
            
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
            return results
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e), 'status': 'FAILED'}
    
    def calculate_excavation_volume(self, dem_path, mining_polygon):
        try:
            with rasterio.open(dem_path) as dem:
                geom = [mapping(mining_polygon)]
                clipped_dem, transform = mask(dem, geom, crop=True, nodata=np.nan)
                current_elevation = clipped_dem[0]
                
                if np.all(np.isnan(current_elevation)):
                    print("      ⚠️ Warning: Clipped DEM is empty. Cannot calculate volume for this pit.")
                    return None

                cell_area = abs(transform[0] * transform[4])
                
                buffer_distance = 50
                buffered_polygon = mining_polygon.buffer(buffer_distance)
                buffered_geom = [mapping(buffered_polygon)]
                
                buffered_dem, _ = mask(dem, buffered_geom, crop=True, nodata=np.nan)
                
                original_surface = np.nanmean(buffered_dem[0])
                if np.isnan(original_surface):
                    print("      ⚠️ Warning: Could not determine original surface level. Using DEM average.")
                    original_surface = np.nanmean(dem.read(1))

                depth_map = original_surface - current_elevation
                depth_map[depth_map < 0] = 0
                depth_map[np.isnan(depth_map)] = 0
                
                volume = np.sum(depth_map) * cell_area
                
                excavation_depths = depth_map[depth_map > 0]
                avg_depth = np.mean(excavation_depths) if len(excavation_depths) > 0 else 0
                max_depth = np.max(excavation_depths) if len(excavation_depths) > 0 else 0
                
                return {
                    'volume_m3': float(volume),
                    'avg_depth_m': float(avg_depth),
                    'max_depth_m': float(max_depth),
                }
                
        except Exception as e:
            print(f"      ❌ Volume calculation error: {str(e)}")
            return None
