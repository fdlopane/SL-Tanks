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
from shapely.geometry import Point, shape

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

dist_filename = ['01_Ampara'] # light test
'''
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
    gcpt.raster_to_shp_poly(ghsl_merged_clipped, ghsl_poly, target_classes, dissolve=False)
    print('GHSL polygon layer created.')
    print()

if not os.path.isfile(ghsl_poly_dissolved):
    target_classes = [11, 12, 13, 21] # Target classes value to be filtered out during shp creation
    gcpt.raster_to_shp_poly(ghsl_merged_clipped, ghsl_poly_dissolved, target_classes, dissolve=True)
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
# AGRICULTURAL LAND FILES CREATION

print('Checking if agricultural lands shapefile has already been created.')
print()
if not os.path.isfile(ag_lands):
    print('Creating agricultural lands shapefile...')
    print()
    # bring in the ag lands file and replace the agland types specified with agland categories
    print('Recategorising agricultural lands.')
    print()

    # Shall we consider home gardens as agricultural lands? Yes=True, No=False
    Home_Gardens = False
    if Home_Gardens == True:
        agland_types = ['Chena', 'Coconut', 'Other (Mango, etc)', 'Paddy', 'Other plantations', 'Rubber', 'Tea', 'Uncultivated lands', 'Home Garden']
    else:
        agland_types = ['Chena', 'Coconut', 'Other (Mango, etc)', 'Paddy', 'Other plantations', 'Rubber', 'Tea', 'Uncultivated lands']

    land_use_gdf = gpd.read_file(inputs["land_use"]) # read geodataframe using geopandas

    # Initialise ag_lands to zero
    land_use_gdf['ag_lands'] = 0

    # Replace aglands with 1 for all those classified as such
    for i in agland_types:
        land_use_gdf.loc[land_use_gdf['LU'] == i,'ag_lands'] = 1

    # Export new gdf to shape
    land_use_gdf.to_file(ag_lands)

# Dissolve resulting shapefile into one agricultural land layer
if not os.path.isfile(ag_lands_dissolved):
    land_use_gdf = gpd.read_file(ag_lands)
    land_use_gdf = land_use_gdf[land_use_gdf['ag_lands'] == 1] # remove non-agricultural land types
    land_use_gdf['dissolve_id'] = 1  # Create a new column with a constant value (ensures all dissolved into a single feature)
    dissolved_land_use_gdf = land_use_gdf.dissolve(by='dissolve_id', as_index=False)
    dissolved_land_use_gdf.drop(columns='dissolve_id', inplace=True)  # Remove the 'dissolve_id' column (optional)

    dissolved_land_use_gdf.to_file(ag_lands_dissolved)
else:
    print('Agricultural land shapefile already created.')
    print()

# Now clip agricultural lands to each individual district
print('Checking if individual district ag lands have already been created.')
print()
flag = True
ag_lands_dist = []
for y in dist_filename:
    if not os.path.isfile(os.path.join(ag_lands_only_path, y[3:] + '_ag_lands_only.shp')):
        #print(os.path.join(ag_lands_only_path, y[3:] + '_ag_lands_only.shp'), "NOT FOUND")
        flag = False
    ag_lands_dist.append(os.path.join(ag_lands_only_path, y[3:] + '_ag_lands_only.shp'))

if flag == False:
    print('Clipping agricultural lands to individual districts...')
    print()

    # List of district filenames (e.g., ["ADM2_EN_001", "ADM2_EN_002", ...])
    # dist_filenames = ["ADM2_EN_" + y[3:] for y in dist_filename]
    dist_filenames = [y[3:] for y in dist_filename]

    # Create the output directories if they don't exist
    for directory in [ind_dists_filepath, ag_lands_only_path]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # Loop through the district filenames
    for y in dist_filenames:
        # Clip the ag_lands_dissolved layer with the district boundary
        district_boundary = gpd.read_file(os.path.join(ind_dist_boundaries_filepath, y + '.shp'))
        ag_lands_dissolved_gdf = gpd.read_file(ag_lands_dissolved)
        clipped_result = gpd.clip(ag_lands_dissolved_gdf, district_boundary)

        # Save the clipped result as a shapefile
        clipped_result.to_file(os.path.join(ind_dists_filepath, y + '_ag_lands.shp'))

        # Extract features with 'ag_lands' equal to 1
        ag_lands_only = clipped_result[clipped_result['ag_lands'] == 1]

        # Save the selection as a separate shapefile
        ag_lands_only.to_file(os.path.join(ag_lands_only_path, y + '_ag_lands_only.shp'))

print('Agricultural lands to individual district clipping completed.')
print()

# Join by attributes, summary of population points to: (a) district boundaries and (b) agricultural lands
# Join the urban/rural information from GHSL data to the population points

# Filter out urban population:
print('Joining land types to population points...')
print()
if not os.path.isfile(rur_points_shp):
    # Read the input shapefiles
    pop_points = gpd.read_file(pop_points_shp)
    ghsl_merged_dissolved = gpd.read_file(ghsl_poly_dissolved)

    # Perform the spatial join
    joined_gdf = gpd.sjoin(pop_points, ghsl_merged_dissolved, how="inner", predicate="intersects")

    # Save the result to the output shapefile
    joined_gdf.to_file(rur_points_shp)
'''
# RURAL POPULATION FILES
flag = True
for y in dist_filename:
    if not os.path.isfile(modelRunsDir + 'individual-districts/' + y[3:] + '_rur_dist_pop.shp'):
        print('Individual district rural population joins have NOT already been conducted for', y[3:])
        print("Joining the", y[3:], "district...")
        # Load the district boundaries and rural points shapefiles
        district_gdf = gpd.read_file(ind_dist_boundaries_filepath + '/' + y[3:] + '.shp')

        # TODO: eliminate the test file from the generated-files folder when debugged
        # rural_points_gdf = gpd.read_file(rur_points_shp)
        rural_points_gdf = gpd.read_file(modelRunsDir + "/TEST-pop-points.shp")

        # Perform the spatial join
        result_gdf = gpd.sjoin(district_gdf, rural_points_gdf, predicate='intersects', how='left')
        result_gdf['pop_count'] = result_gdf['pop_count_'].fillna(0) # TODO: remove the underscore when debugged
        print("debug 1")
        print(result_gdf)
        print()

        # Group by district and calculate the sum of 'pop_count_'
        dissolved_gdf = result_gdf.dissolve(by='index_right', aggfunc={'pop_count_': 'sum'})
        # Reset the index to restore 'index_right' as a regular column
        dissolved_gdf = dissolved_gdf.reset_index()
        print("debug 2")
        print(dissolved_gdf)
        print()

        # Save the result to a new shapefile
        dissolved_gdf.to_file(ind_dists_filepath + '/' + y[3:] + '_rur_dist_pop.shp')


########################################################################################################################
now = datetime.datetime.now(tz_London)
print("Program finished at: ", now.strftime("%H:%M:%S"), "(London time)")