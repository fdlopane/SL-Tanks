"""
globals.py

Globals used by model
"""
import os

# Directories paths
inputFolder = "./input-data"
modelRunsDir = "./generated-files"
outputFolder = "./output-data"

# Files
Resampled_pop_raster = os.path.join(modelRunsDir,"100m_resampled_pop.tif") # Worldpop rasted resampled to 100m resolution
pop_points_shp = os.path.join(modelRunsDir, "100m_pop_point.shp") # Point shp with population at 100m
