"""
globals.py

Globals used by model
"""
import os

########################################################################################################################
# Directories paths
inputFolder = "./input-data"
modelRunsDir = "./generated-files"
outputFolder = "./output-data"

########################################################################################################################
# File names (no complete path as they might be present in more folders with the same name)
# e.g. check that this file is in AAA folder, otherwise load it from BBB folder
CCC_example = 'CCC_file.csv'


########################################################################################################################
# -- Non-Output generated files --

Resampled_pop_raster = os.path.join(modelRunsDir,"100m_resampled_pop.tif")



########################################################################################################################
# -- OUTPUT FILES --

# Output category 1
BBB_example = os.path.join(outputFolder,"BBB_output.csv")


########################################################################################################################
