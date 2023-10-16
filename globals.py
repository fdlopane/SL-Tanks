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
# -- INPUT FILES --

# Retail data
AAA_example = os.path.join(modelRunsDir,"AAA_input.csv")



########################################################################################################################
# -- OUTPUT FILES --

# Output category 1
BBB_example = os.path.join(outputFolder,"BBB_output.csv")


########################################################################################################################
