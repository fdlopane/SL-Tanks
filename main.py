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
print()

from config import *
from globals import *
import geocomputation as gcpt
import geopandas as gpd

print("All packages imported")
print()
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
    print()

# Convert the 100m WoldPop raster to a point shapefile:
if not os.path.isfile(pop_points_shp):
    pop_points_gdf = gcpt.raster_to_shp_point(Resampled_pop_raster, pop_points_shp, 'pop_count')
    print('WorldPop raster converted into points')
    print()

########################################################################################################################
# CREATION OF GHSL LAYER

# Create the GHSL layer ready to be joined by location (attributes) with 100m population points
# Merge together the components of the GHSL layer

# List of GHSL inputs
ghsl_to_merge = [inputs["GHSL_raw_1"], inputs["GHSL_raw_2"], inputs["GHSL_raw_3"], inputs["GHSL_raw_4"]]

if not os.path.isfile(ghsl_merged):
    print('Merging GHSL input layers...')
    print()
    gcpt.merge_raster_files(ghsl_to_merge, ghsl_merged)
    print('GHSL inputs merged into a single raster file.\n')
    print()

# Convert crs of merged sri lanka file:
if not os.path.isfile(ghsl_merged_wgs84):
    st_crs = 'EPSG:4326' # WGS84 projection
    gcpt.reproject_raster(ghsl_merged, st_crs, ghsl_merged_wgs84)
    print('GHSL raster converted to CRS EPSG:4326.\n')
    print()

# Now clip the shape to sri lanka boundaries:

# Read in vector boundaries
districts_shp = gpd.read_file(inputs["SL_Districts"])

if not os.path.isfile(ghsl_merged_clipped):
    gcpt.clip_raster_file(ghsl_merged_wgs84, districts_shp, ghsl_merged_clipped)
    print('GHSL raster clipped to state boundaries and exported as .tif.\n')
    print()

# Transform the raster GHSL layer into a polygon
if not os.path.isfile(ghsl_poly):
    target_classes = [11, 12, 13, 21] # Target classes value to be filtered out during shp creation
    gcpt.raster_to_shp_poly(ghsl_merged_clipped, ghsl_poly, target_classes, dissolve=True)
    print('GHSL polygon layer created.')
    print()

########################################################################################################################
# INDIVIDUAL DISTRICT FILES CREATION

# Create individual district boundaries shapefiles
# (these will be used later for populations assignment to ag lands and ind districts)
print('Checking if individual district border shapefiles have already been created.')
print()
flag = True
for y in dist_filename:
    if not os.path.isfile(ind_dist_boundaries_filepath + y[3:]):
        flag = False

if flag == False:
    print('Creating individual district border shapefiles...')
    print()
    # run individual districts polygons creation function:
    field_name = 'ADM2_EN'
    districts_gdf = gpd.read_file(inputs["SL_Districts"])
    gcpt.split_vector_layer(districts_gdf, field_name, ind_dist_boundaries_filepath)
else:
    print('Borders already created.')
    print()

########################################################################################################################
now = datetime.datetime.now(tz_London)
print("Program finished at: ", now.strftime("%H:%M:%S"), "(London time)")