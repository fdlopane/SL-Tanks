# Sri Lanka Tank rejuvenation priority index
# This script generates an agricultural dependent population shapefile and attributes
# agricultural dependent population to water tanks to determine the serviced population
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
import geocomputation as gcpt

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
# Preprocessing of the 1km Unconstrained WorldPop data to be 100m resolution

# Resample the WorldPop raster from 1km resolution to 100m
# Define inputs for resampling function:
input_raster_path = inputs["WorldPop_1km_raster"]
output_raster_path = Resampled_pop_raster
x_resolution = 0.0008983 # 100m in degrees
y_resolution = 0.0008983 # 100m in degrees

if not os.path.isfile(output_raster_path):
    gcpt.resample_raster(input_raster_path, output_raster_path, x_resolution, y_resolution)
    print("Raster resampling completed.")

# Convert the 100m WoldPop raster to a point shapefile:
if not os.path.isfile(pop_points_shp):
    pop_points_gdf = gcpt.raster_to_shp(Resampled_pop_raster, pop_points_shp, 'pop_count')
    print('Worldpop raster converted into points')
