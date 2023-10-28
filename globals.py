"""
globals.py

Globals used by model
"""
import os

# Directories paths
inputFolder = "./input-data"
modelRunsDir = "./generated-files"
outputFolder = "./output-data"

ind_dist_boundaries_filepath = modelRunsDir + "/individual-districts-boundaries" # Folder containing districts boundaries
ind_dists_filepath = modelRunsDir + "/individual-districts" # Folder containing single districts files
ag_lands_only_path = modelRunsDir + "/ag_lands_only"
buffers_path = modelRunsDir + "/buffers"

# Files
Resampled_pop_raster = os.path.join(modelRunsDir,"100m_resampled_pop.tif") # Worldpop rasted resampled to 100m resolution
pop_points_shp = os.path.join(modelRunsDir, "100m_pop_point.shp") # Point shp with population at 100m
ghsl_merged = os.path.join(modelRunsDir,"GHSL_sri_lanka.tif") # Merged GHSL raster
ghsl_merged_wgs84 = os.path.join(modelRunsDir,"GHSL_sl_wgs84.tif") # Merged GHSL raster in WGS84
ghsl_merged_clipped = os.path.join(modelRunsDir,"GHSL_sl_wgs84_clipped.tif") # GHSL raster in WGS84 clipped to Sri Lanka
ghsl_poly = os.path.join(modelRunsDir,"GHSL_sl.shp") # GHSL layer polygon
ghsl_poly_dissolved = os.path.join(modelRunsDir,"GHSL_sl_dissolved.shp") # GHSL raster in WGS84 clipped to Sri Lanka
ag_lands = os.path.join(modelRunsDir, "ag_lands_only.shp") # Agricultural lands polygons (only agricultural lands - got rid of all other land uses)
ag_lands_dissolved = os.path.join(modelRunsDir, "ag_lands_dissolved.shp") # Dissolved agricultural lands polygons
rur_points_shp = os.path.join(modelRunsDir, "WP_points_ghsl.shp") # Rural population point shapefile (GHSL layer join)
pop_count_comparison_csv = os.path.join(modelRunsDir, "pop_df_hies.csv") # csv file contaning district level comparisons among pop counts
agland_buffers_radii_csv = os.path.join(modelRunsDir, "agland_buffer_radii.csv") # csv file with the final buffer radius value for each district
ag_lands_and_buffers = os.path.join(modelRunsDir, "ag_lands_and_buffers.shp") # Merged layer of all agricultural lands' buffers
tanks_buffers = os.path.join(modelRunsDir, "tanks_buffers.shp") # Buffers around water tanks