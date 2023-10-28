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
import pandas as pd
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

#dist_filename = ['01_Ampara'] # debug test

########################################################################################################################
# Create the output directories if they don't exist
for directory in [ind_dist_boundaries_filepath, ind_dists_filepath, ag_lands_only_path, buffers_path]:
    if not os.path.exists(directory):
        os.makedirs(directory)

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

        # Add district name
        ag_lands_only["dist_name"] = y

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

# RURAL POPULATION FILES
for y in dist_filename:
    if not os.path.isfile(ind_dists_filepath + '/' + y[3:] + '_rur_dist_pop.shp'):
        print('Individual district rural population joins have NOT already been conducted for', y[3:])
        print("Joining the", y[3:], "district...")

        # Load the district boundaries and rural points shapefiles
        district_gdf = gpd.read_file(ind_dist_boundaries_filepath + '/' + y[3:] + '.shp')
        rural_points_gdf = gpd.read_file(rur_points_shp)

        # Perform the spatial join
        result_gdf = gpd.sjoin(district_gdf, rural_points_gdf, predicate='intersects', how='left')
        result_gdf['pop_count'] = result_gdf['pop_count'].fillna(0)

        # Sum the pop_count in the spatial join and number in a new field of the district_gdf
        district_rural_pop = result_gdf.pop_count.sum()
        district_gdf['rur_pop'] = district_rural_pop
        district_gdf = district_gdf[['ADM2_EN', 'geometry', 'rur_pop']]  # Filter only the useful fields
        district_gdf.to_file(ind_dists_filepath + '/' + y[3:] + '_rur_dist_pop.shp')

# TOTAL POPULATION (INCLUDING URBAN) FILES
for y in dist_filename:
    if not os.path.isfile(ind_dists_filepath + '/' + y[3:] + '_tot_dist_pop.shp'):
        print('Joining district populations (total including urban) to individual district admin boundaries for', y[3:])
        print()

        # Load the district boundaries and pop points shapefiles
        district_gdf = gpd.read_file(ind_dist_boundaries_filepath + '/' + y[3:] + '.shp')
        pop_points_gdf = gpd.read_file(pop_points_shp)

        # Perform the spatial join
        result_gdf = gpd.sjoin(district_gdf, pop_points_gdf, predicate='intersects', how='left')
        result_gdf['pop_count'] = result_gdf['pop_count'].fillna(0)

        # Sum the pop_count in the spatial join and number in a new field of the district_gdf
        district_pop = result_gdf.pop_count.sum()
        district_gdf['pop_count'] = district_pop
        district_gdf = district_gdf[['ADM2_EN', 'geometry', 'pop_count']]  # Filter only the useful fields
        district_gdf.to_file(ind_dists_filepath + '/' + y[3:] + '_tot_dist_pop.shp')

# POPULATION WITHIN AGRICULTURAL LAND FILES
print('Checking if ag land population joins have already been conducted.')
print()
for x, y in zip(ag_lands_dist, dist_filename):
    if not os.path.isfile(ind_dists_filepath + '/' + y[3:] + '_aglands_rur_pop.shp'):
        print('Joining ag populations to individual aglands boundaries (rural only) for', y[3:])
        print()

        # Load the district boundaries and pop points shapefiles
        district_gdf = gpd.read_file(x)
        rural_points_gdf = gpd.read_file(rur_points_shp)

        # Perform the spatial join
        result_gdf = gpd.sjoin(district_gdf, rural_points_gdf, predicate='intersects', how='left')
        result_gdf['pop_count'] = result_gdf['pop_count'].fillna(0)

        # Sum the pop_count in the spatial join and number in a new field of the district_gdf
        district_rural_pop = result_gdf.pop_count.sum()
        district_gdf['agland_pop'] = district_rural_pop
        district_gdf = district_gdf[['GFCODE', 'NAME_1', 'LU', 'Name', 'ag_lands', 'geometry', 'agland_pop']]  # Filter only the useful fields
        district_gdf.to_file(ind_dists_filepath + '/' + y[3:] + '_aglands_rur_pop.shp')

########################################################################################################################
# COMPARISON BETWEEN DISTRICT LEVEL STATISTICS AND GENERATED LOCAL POPULATION COUNTS

threshold = 0.05 # Acceptable % difference among pop counts

if not os.path.isfile(pop_count_comparison_csv):
    # Join dataframes together at the district level so each observation is a district
    # variables in this dataframe are:
    # (1) district population
    # (2) agland population
    # (3) % agland population
    # (4) hies estimate for ag population (%)
    # (5) % difference between aglands population & hies

    print('Starting comparison among local and global pop counts.')
    print()

    # create dataframe for population values
    pop_df = pd.DataFrame(columns=['dist_names', 'dist_pop', 'ag_lands_pop'])

    dist_names = [] # district names
    dist_pop = [] # district total population
    ag_lands_pop = [] # district population within agricultural lands
    dist_rur_pop = [] # district rural population

    for y in dist_filename:
        dist_pop_rur_dbf = ind_dists_filepath + '/' + y[3:] + '_rur_dist_pop.dbf' # districts polygons dbf file path
        t_dist_pop_rur_dbf = gpd.read_file(dist_pop_rur_dbf) # import the dbf file with geopandas
        pdf_dist_rur_pop = pd.DataFrame(t_dist_pop_rur_dbf) # turn the geopandas object into a pandas dataframe
        dist_names.append(pdf_dist_rur_pop['ADM2_EN'].values[0]) # append the district names to the dist_names list
        dist_rur_pop.append(pdf_dist_rur_pop['rur_pop'].values[0])  # append the district population to the dist_pop list

        ag_lands_pop_dbf = ind_dists_filepath + '/' + y[3:] + '_aglands_rur_pop.dbf' # agricultural lands polygons dbf file path
        t_ag_lands_pop_dbf = gpd.read_file(ag_lands_pop_dbf) # import the dbf file with geopandas
        pdf_ag_lands_pop = pd.DataFrame(t_ag_lands_pop_dbf) # turn the geopandas object into a pandas dataframe
        ag_lands_pop.append(pdf_ag_lands_pop['agland_pop'].values[0]) # append the population count within agricultural lands to the ag_lands_pop list

        dist_pop_dbf = ind_dists_filepath + '/' + y[3:] + '_tot_dist_pop.dbf'  # districts polygons dbf file path
        t_dist_pop_dbf = gpd.read_file(dist_pop_dbf)  # import the dbf file with geopandas
        pdf_dist_pop = pd.DataFrame(t_dist_pop_dbf)  # turn the geopandas object into a pandas dataframe
        dist_pop.append(pdf_dist_pop['pop_count'].values[0])  # append the district population to the dist_pop list

    # Add hies data
    hies_df = pd.read_csv(inputs["hies_pop_csv"]) # read the aggregate (district level) agricultural dependent population from csv

    # Make column with matching name
    hies_df['dist_names'] = hies_df['ADM2_EN']
    # Replace Numwara Eliya which has a wrong spelling with a "-" instead of a space
    hies_df.loc[hies_df['dist_names'] == 'Nuwara-eliya', 'dist_names'] = 'Nuwara Eliya'

    # Filter only the relevant columns
    hies_df = hies_df[['dist_names', 'pop_ag_ind_or_ag_income_1plus', 'pop_ag_reliant_income']]

    # Populate the pop_df with the lists from the previous loop (population counts)
    pop_df['dist_names'] = dist_names
    pop_df['dist_pop'] = dist_pop
    #pop_df['dist_pop'] = pop_df['dist_pop'].astype(np.int64)
    pop_df['dist_rur_pop'] = dist_rur_pop
    pop_df['ag_lands_pop'] = ag_lands_pop

    # join the hies data merging on district name
    pop_df = pd.merge(pop_df, hies_df, on='dist_names', how='left')

    pop_df['hies_ag_dep_pop_%'] = pop_df['pop_ag_ind_or_ag_income_1plus'] / 100  # % of agricultural dependent population - HIES data (column N) - new one to use

    # Create stats on comparison between hies ag land pop
    pop_df['aglands_pop_%'] = pop_df['ag_lands_pop'] / pop_df['dist_pop']  # Turning the population count in agricultural lands into a %

    pop_df['diff_hies_aglands_%'] = pop_df['aglands_pop_%'] - pop_df['hies_ag_dep_pop_%']  # calculating difference between aggregate input data and disaggregate modelled data (column N) for agricultural lands polygons buffers

    pop_df['use_aglands?'] = ''

    pop_df.loc[(pop_df['diff_hies_aglands_%'] > threshold), 'use_aglands?'] = 'too big'
    pop_df.loc[(pop_df['diff_hies_aglands_%'] < - threshold), 'use_aglands?'] = 'too small'

    # Identify agricultural lands population counts whose difference aggregate/disaggregate is < 10%
    pop_df.loc[(pop_df['diff_hies_aglands_%'] < threshold) & (pop_df['diff_hies_aglands_%'] > -threshold), 'use_aglands?'] = 'OK'

    # export dataframe to excel file
    # pop_df.to_excel(map_intermediate + 'pop_df_hies_no_hg.xlsx', index=True)

    # export dataframe to csv
    pop_df.to_csv(pop_count_comparison_csv)

########################################################################################################################
# BUFFER GENERATION

# Execute the buffer creation algorithm only if the final radius dimensions csv file does not exist.
# (i.e. if you want to regenerate all the buffers, just delete the 'agland_buffers_radii_csv' csv file)
print("Checking if agricultural lands' buffer already exist")
print()
if not os.path.isfile(agland_buffers_radii_csv):
    print("Creating agricultural lands buffers...")
    print()
    # According to the information contained in the csv file created in the previous section (comparison between global
    # and local pop counts), different buffers will be created:
    pop_df = pd.read_csv(pop_count_comparison_csv)

    r_increment = 100 # progressive increment of buffer radius (in metres)

    All_dist_pop_check = False # Check on population of all districts

    # Let's create a dictionary that contains the district name as key and the final buffer radius as values
    buffer_r_dict = {}
    # Initialise the dictionary with zero values:
    for y in dist_filename:
        buffer_r_dict[y] = 0

    while All_dist_pop_check==False:
        for y in dist_filename:
            buffer_radius = 100  # initial value in metres
            district_pop_check = False
            while district_pop_check == False:
                if pop_df.loc[pop_df['dist_names'] == y[3:], 'use_aglands?'].item() == 'too small':
                    print('Creating ' + str(buffer_radius) + 'm buffer on ag lands for district:' + y[3:])
                    print()
                    buffer_r_dict[y] = buffer_radius

                    # Create GeoSeries
                    aglands = gpd.read_file(ag_lands_only_path + '/' + y[3:] + '_ag_lands_only.shp')
                    district_series = aglands['geometry']

                    # Buffer creation
                    d_buffer = district_series.buffer(buffer_radius*(0.00001 / 1.11))
                    d_buffer.name = 'geometry'
                    buffered_gdf = gpd.GeoDataFrame(d_buffer, crs="EPSG:4326", geometry='geometry')
                    buffered_gdf['dist_name'] = y[3:]
                    buffered_gdf = buffered_gdf.dissolve()

                    # Clip the buffer to the district boundaries
                    district_boundary = gpd.read_file(os.path.join(ind_dist_boundaries_filepath, y[3:] + '.shp'))
                    clipped_buffer = gpd.clip(buffered_gdf, district_boundary)

                    # Join the clipped buffer to the rural points shapefile
                    rural_points_gdf = gpd.read_file(rur_points_shp)
                    joined_gdf = gpd.sjoin(clipped_buffer, rural_points_gdf, predicate='intersects', how='left')

                    # check value from HIES ag pop
                    hies_pop_ag_dep = pop_df.loc[pop_df['dist_names'] == y[3:], 'hies_ag_dep_pop_%'].item()  # ag dep pop for district y
                    # print("hies_pop_ag_dep =", hies_pop_ag_dep)
                    hies_dist_pop = pop_df.loc[pop_df['dist_names'] == y[3:], 'dist_pop'].item()  # tot pop of district y
                    # print("hies_dist_pop =", hies_dist_pop)
                    dist_rur_pop = pop_df.loc[pop_df['dist_names'] == y[3:], 'dist_rur_pop'].item()  # rur pop of district y
                    # print("dist_rur_pop =", dist_rur_pop)

                    # print(joined_gdf.columns.tolist())
                    # print(joined_gdf)
                    buffer_pop_count = joined_gdf.pop_count.sum()
                    # print("buffer_pop_count =", buffer_pop_count)


                    if (buffer_pop_count / hies_dist_pop) - hies_pop_ag_dep > -threshold: # '> -threshold' means buffer ok
                        # Save to file the last generated buffer
                        buffered_gdf.to_file(buffers_path + '/' + y[3:] + '_ag_lands_' + str(buffer_radius) + 'm_buffer.shp')
                        district_pop_check = True

                    elif abs(buffer_pop_count - dist_rur_pop) < threshold:
                        # this is the condition in which the whole rural population is already contained in the buffer
                        # with a 5% (or different value of threshold) error acceptance
                        district_pop_check = True

                    else:  # 'difference < -threshold' means buffer too small
                        buffer_radius = buffer_radius + r_increment

                elif pop_df.loc[pop_df['dist_names'] == y[3:], 'use_aglands?'].item() == 'too big':
                    print('Creating -' + str(buffer_radius) + 'm buffers on ag lands for district: ' + y[3:])
                    print()
                    buffer_r_dict[y] = (-1) * buffer_radius  # negative value = inward buffer

                    # Create GeoSeries
                    aglands = gpd.read_file(ag_lands_only_path + '/' + y[3:] + '_ag_lands_only.shp')
                    district_series = aglands['geometry']

                    # Buffer creation
                    d_buffer = district_series.buffer((-1) * buffer_radius * (0.00001 / 1.11))
                    d_buffer.name = 'geometry'
                    buffered_gdf = gpd.GeoDataFrame(d_buffer, crs="EPSG:4326", geometry='geometry')
                    buffered_gdf['dist_name'] = y[3:]
                    buffered_gdf = buffered_gdf.dissolve()

                    # Clip the buffer to the district boundaries
                    district_boundary = gpd.read_file(os.path.join(ind_dist_boundaries_filepath, y[3:] + '.shp'))
                    clipped_buffer = gpd.clip(buffered_gdf, district_boundary)

                    # Join the clipped buffer to the rural points shapefile
                    rural_points_gdf = gpd.read_file(rur_points_shp)
                    joined_gdf = gpd.sjoin(clipped_buffer, rural_points_gdf, predicate='intersects', how='left')

                    # check value from HIES ag pop
                    hies_pop_ag_dep = pop_df.loc[pop_df['dist_names'] == y[3:], 'hies_ag_dep_pop_%'].item()  # ag dep pop for district y
                    hies_dist_pop = pop_df.loc[pop_df['dist_names'] == y[3:], 'dist_pop'].item()  # tot pop of district y
                    dist_rur_pop = pop_df.loc[pop_df['dist_names'] == y[3:], 'dist_rur_pop'].item()  # rur pop of district y

                    buffer_pop_count = joined_gdf.pop_count.sum()

                    if (buffer_pop_count / hies_dist_pop) - hies_pop_ag_dep < threshold:  # '< threshold' means buffer ok
                        # Save to file the last generated buffer
                        buffered_gdf.to_file(buffers_path + '/' + y[3:] + '_ag_lands_-' + str(buffer_radius) + 'm_buffer.shp')
                        district_pop_check = True

                    elif abs(buffer_pop_count - dist_rur_pop) < threshold:
                        # this is the condition in which the whole rural population is already contained in the buffer
                        district_pop_check = True

                    else:  # 'difference > threshold' means buffer too big
                        buffer_radius = buffer_radius + r_increment

                elif pop_df.loc[pop_df['dist_names'] == y[3:], 'use_aglands?'].item() == 'OK':
                    district_pop_check = True

                else:
                    raise Exception('ERROR: something went wrong! Check the values of the use_aglands? column of pop counts csv file.')

        All_dist_pop_check = True

    # Create Pandas data frame from dictionary (df index=district, df column=buffer radius)
    buffer_r_df = pd.DataFrame.from_dict(buffer_r_dict, orient='index', columns=['buffer_radius'])
    buffer_r_df['district_name'] = buffer_r_df.index  # turn index into column named 'district_name'
    buffer_r_df.reset_index(drop=True, inplace=True)
    # Export data frame to csv
    buffer_r_df.to_csv(agland_buffers_radii_csv)

# Now let's create an agricultural dependent population layer by overlapping the rural population and the buffers
# Read final buffer radii dimensions from csv file
buffer_r_df = pd.read_csv(agland_buffers_radii_csv, usecols=['district_name', 'buffer_radius'])

# Merge the buffers into a single layer to be overlapped to the rural pop layer
if not os.path.isfile(ag_lands_and_buffers):
    # Create a list of input files. Select different files according to the buffer radius
    input_layers_list = []
    for y in dist_filename:
        if buffer_r_df.loc[buffer_r_df['district_name'] == y, 'buffer_radius'].item() == 0:
            input_layers_list.append(ag_lands_only_path + '/' + y[3:] + '_ag_lands_only.shp')
        elif buffer_r_df.loc[buffer_r_df['district_name'] == y, 'buffer_radius'].item() > 0:
            b_r = buffer_r_df.loc[buffer_r_df['district_name'] == y, 'buffer_radius'].item() # numeric value of buffer
            input_layers_list.append(buffers_path + '/' + y[3:] + '_ag_lands_' + str(b_r) + 'm_buffer.shp')
        elif buffer_r_df.loc[buffer_r_df['district_name'] == y, 'buffer_radius'].item() < 0:
            b_r = buffer_r_df.loc[buffer_r_df['district_name'] == y, 'buffer_radius'].item() # numeric value of buffer
            input_layers_list.append(buffers_path + '/' + y[3:] + '_ag_lands_' + str(b_r) + 'm_buffer.shp')
        else: raise Exception('ERROR: something went wrong! Check agland_buffers_radii_csv values data type.')

    print('Merging buffer layers...')
    print()
    # Load all input shapefiles into a list of GeoDataFrames
    input_gdfs = [gpd.read_file(layer) for layer in input_layers_list]

    # Concatenate (merge) the GeoDataFrames into a single GeoDataFrame
    merged_gdf = gpd.GeoDataFrame(pd.concat(input_gdfs, ignore_index=True), crs=input_gdfs[0].crs)

    # Create a spatial index
    merged_gdf.sindex

    # Save the merged GeoDataFrame to the output shapefile
    merged_gdf.to_file(ag_lands_and_buffers)
    print('Merged buffers layer and spatial index created.')
    print()

# Clip the rural population to ag land + buffer layer
print("Checking if agricultural dependent population output file already exists.")
if not os.path.isfile(outputs["ag_dep_pop_shp"]):
    print("Clipping rural population to agricultural lands' buffers...")
    print()
    rural_points_gdf = gpd.read_file(rur_points_shp)
    ag_lands_and_buffers_gdf = gpd.read_file(ag_lands_and_buffers)
    clipped_result = gpd.clip(rural_points_gdf, ag_lands_and_buffers_gdf)
    clipped_result.sindex
    clipped_result.to_file(outputs["ag_dep_pop_shp"])

########################################################################################################################
# ATTRIBUTION OF AGRICULTURAL DEPENDENT POPULATION TO TANKS

# Create a buffer around tanks
tank_buffer = 1000 # tank buffer in metres

print('Checking if tanks buffers have already been created...')
print()
if not os.path.isfile(tanks_buffers):
    print('Creating tanks buffers...')
    print()
    # Create GeoSeries
    tanks_polygons = gpd.read_file(inputs["tanks_polygons"])
    tanks_series = tanks_polygons['geometry']

    # Buffer creation
    t_buffer = tanks_series.buffer(tank_buffer * (0.00001 / 1.11)) # conversion to deg
    t_buffer.name = 'geometry'
    buffered_gdf = gpd.GeoDataFrame(t_buffer, crs="EPSG:4326", geometry='geometry')
    buffered_gdf = buffered_gdf.join(tanks_polygons.drop('geometry', axis=1))

    # Create a spatial index
    buffered_gdf.sindex

    # Save to file
    buffered_gdf.to_file(tanks_buffers)
'''
# Count served population by each tank (not using Voronoi split)
print('Checking if tanks buffers population count has already been performed...')
print()
if not os.path.isfile(outputs["tanks_buffers_pop"]):
    print('Counting agricultural dependent population within tanks buffers...')
    print()
    tanks_buffers_gdf = gpd.read_file(tanks_buffers)
    rural_points_gdf = gpd.read_file(rur_points_shp)
    # Perform the spatial join
    result_gdf = gpd.sjoin(tanks_buffers_gdf, rural_points_gdf, predicate='intersects', how='left')

    # Handle missing values in 'index_right'
    result_gdf['index_right'].fillna(-1, inplace=True)

    # Summarise the attributes based on the specified fields
    summary_df = result_gdf.groupby('index_right')["pop_count"].agg("sum").reset_index()

    # Merge the summary back into the input GeoDataFrame
    result_gdf = tanks_buffers_gdf.merge(summary_df, left_on=tanks_buffers_gdf.index, right_on='index_right', how='left')

    # Create a spatial index
    result_gdf.sindex

    # Save to file
    result_gdf.to_file(outputs["tanks_buffers_pop"])
'''
########################################################################################################################
now = datetime.datetime.now(tz_London)
print("Program finished at: ", now.strftime("%H:%M:%S"), "(London time)")