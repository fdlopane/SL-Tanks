# Sri Lanka Tank rejuvenation priority index
# This script generates an agricultural dependent population shapefile and attributes
# agricltural dependent population to water tanks to determine the serviced population
# of each tank. The higher the population, the higher the priority of the tank.

########################################################################################################################
# Import phase
import datetime
import pytz
tz_London = pytz.timezone('Europe/London')
now = datetime.datetime.now(tz_London)
print("Program started at: ", now.strftime("%H:%M:%S"), "(London time)")

from config import *
from globals import *

print("All packages imported")
########################################################################################################################
# List of Sri Lanka district names:
dist_filename = ['01_Ampara',
                 '02_Anuradhapura',
                 '03_Badulla',
                 '04_Batticaloa',
                 '05_Colombo',
                 '06_Galle',
                 '07_Gampaha',
                 '08_Hambantota',
                 '09_Jaffna',
                 '10_Kalutara',
                 '11_Kandy',
                 '12_Kegalle',
                 '13_Kilinochchi',
                 '14_Kurunegala',
                 '15_Mannar',
                 '16_Matale',
                 '17_Matara',
                 '18_Monaragala',
                 '19_Mullaitivu',
                 '20_Nuwara Eliya',
                 '21_Polonnaruwa',
                 '22_Puttalam',
                 '23_Ratnapura',
                 '24_Trincomalee',
                 '25_Vavuniya']
########################################################################################################################
# Preprocessing of the 1km Unconstrained Worldpop data to be 100m resolution

"""
#TODO: need to transform the following code in pure python (without QGIS)
# Resample the 1km population file to a 100m grid.
# Note: it copies the values over for each 100m grid cell
processing.run("grass7:r.resample", {'input':inputs["WorldPop_1km_raster"],
                                     'output':'TEMPORARY_OUTPUT',
                                     'GRASS_REGION_PARAMETER':'79.647916363,81.877916354,5.918750178,9.835416829 [EPSG:4326]',
                                     'GRASS_REGION_CELLSIZE_PARAMETER':0.0008983,
                                     'GRASS_RASTER_FORMAT_OPT':'',
                                     'GRASS_RASTER_FORMAT_META':''})

#convert pixels to points
processing.run("native:pixelstopoints", {'INPUT_RASTER':'/private/var/folders/dj/b71b_bsj1fjgr9t6wy_dt0m40000gn/T/processing_tvulde/36a299cdbea44ae58f07577f5df3f201/output.tif',
                                         'RASTER_BAND':1,
                                         'FIELD_NAME':'pop_at_1km_in_100m',
                                         'OUTPUT':'/Users/sophieayling/Library/CloudStorage/OneDrive-UniversityCollegeLondon/GitHub/SriLanka/08_Data/map_intermediate/WorldPop/resampling/1km_to_100m_resampled.shp'})

# 2. We then divide the 1km population by 100 so that each 100m grid cell has a population
"""