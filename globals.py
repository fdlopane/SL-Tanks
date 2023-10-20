"""
globals.py

Globals used by model
"""
import os

# Directories paths
inputFolder = "./input-data"
modelRunsDir = "./generated-files"
outputFolder = "./output-data"

ind_dist_boundaries_filepath = "./generated-files/individual-districts-boundaries" # Folder containing districts boundaries
ind_dists_filepath = "./generated-files/individual-districts" # Folder containing single districts files
ag_lands_only_path = "./generated-files/ag_lands_only"

# Files
Resampled_pop_raster = os.path.join(modelRunsDir,"100m_resampled_pop.tif") # Worldpop rasted resampled to 100m resolution
pop_points_shp = os.path.join(modelRunsDir, "100m_pop_point.shp") # Point shp with population at 100m
ghsl_merged = os.path.join(modelRunsDir,"GHSL_sri_lanka.tif") # Merged GHSL raster
ghsl_merged_wgs84 = os.path.join(modelRunsDir,"GHSL_sl_wgs84.tif") # Merged GHSL raster in WGS84
ghsl_merged_clipped = os.path.join(modelRunsDir,"GHSL_sl_wgs84_clipped.tif") # GHSL raster in WGS84 clipped to Sri Lanka
ghsl_poly = os.path.join(modelRunsDir,"GHSL_sl.shp") # GHSL layer polygon
ag_lands = os.path.join(modelRunsDir, "ag_lands_only.shp") # Agricultural lands polygons (only agricultural lands - got rid of all other land uses)
ag_lands_dissolved = os.path.join(modelRunsDir, "ag_lands_dissolved.shp") # Dissolved agricultural lands polygons
pop_points_ghsl_shp = os.path.join(modelRunsDir, "WP_points_ghsl.shp") # Population point shapefile joined to GHSL layer
rur_points_shp = os.path.join(modelRunsDir, "100m_rural_pts_2020_only.shp")# Rural population point shapefile