"""
This module calculates the values for the rejuvenation prioritisation index for each tank.
"""

# Import phase
import datetime
import pytz

tz_London = pytz.timezone('Europe/London')
now = datetime.datetime.now(tz_London)
print("Program started at: ", now.strftime("%H:%M:%S"), "(London time)")
print()

from config import *
from globals import *
import numpy as np
import geopandas as gpd

print("All packages imported")
print()
########################################################################################################################

# Input files

## Joining small tanks > siltation information > rock structure > rainfall variability
## SUPPLY SIDE INDEX CREATION ##########################################################################################
if not os.path.isfile(outputs["tanks_dsd_level_csv"]):
    # Input the tanks polygons
    tanks_polygons = gpd.read_file(inputs["tanks_polygons"])

    # Create scaled version of silt_score
    tanks_polygons['silt_score'] = tanks_polygons.silt_p / tanks_polygons.silt_p.max()

    # Check it
    silt_table = tanks_polygons['silt_score'].value_counts()
    # (1: less than 1 foot, 2: 1-3 feet, 3: more than 3 feet)
    #print(silt_table)
    #print()

    # Create a soil erosion normalized score (continuous)
    tanks_polygons['soil_score'] = tanks_polygons.max_soil_d / tanks_polygons.max_soil_d.max()
    # Check it
    soil_table = tanks_polygons['soil_score'].value_counts()
    #print(soil_table)
    #print()

    # Create the supply side index
    tanks_polygons['tank_supply_score'] = (tanks_polygons.silt_score + tanks_polygons.soil_score)/2
    #print(tanks_polygons['tank_supply_score'])
    #print()

    # Normalise
    tanks_polygons['tank_supply_index'] = tanks_polygons.tank_supply_score / tanks_polygons.tank_supply_score.max()

    # Check it
    tank_supply_table=tanks_polygons['tank_supply_index'].value_counts()
    #print(tank_supply_table)
    #print()

    # Functionality score generation
    tanks_polygons['func_score'] = None
    tanks_polygons['func_score'] = np.where(tanks_polygons['functional']=="Abandoned", 0, np.nan )
    tanks_polygons.loc[tanks_polygons['functional']== "Damaged", 'func_score']= 1
    tanks_polygons.loc[tanks_polygons['functional']== "Functioning", 'func_score']= 2

    func_table = tanks_polygons['functional'].value_counts()
    #print(func_table)
    #print()

    # TODO: Add in a regression or scatter plot against the functionality score (as a validation)
    # justification as being about using a more objective measure

    ## DEMAND SIDE INDEX CREATION ######################################################################################

    # Import agricultural dependent population output
    adp = gpd.read_file(outputs["tanks_buffers_pop"])

    # Create a normalized ag dep pop for weighting at the dsd level
    adp['norm_adp'] = adp.pop_count / adp.pop_count.max()

    # Check it
    adp_table = adp['norm_adp'].value_counts()
    #print(adp_table)
    #print()

    # Import cov rainfall at tank level
    cov = gpd.read_file(inputs["cov_rainfall"])

    # Normalise the values
    cov['norm_cov'] = cov.gridcode_m / cov.gridcode_m.max()

    # Create a new df with only the columns that we need for the following merge
    cov_filtered = cov[["Map_id", "norm_cov"]]

    # Check it
    cov_table = cov['norm_cov'].value_counts()
    # print(cov_table)
    # print()

    # Join the two datasets together on the Map_id (TankID) variable
    demand_data = adp.merge(cov_filtered, on="Map_id", how='left')
    # print(demand_data[['norm_adp', 'norm_cov']])
    # print()

    # Compute the tank demand index (cov rainfall weighted by adp)
    demand_data['demand_index'] = demand_data.norm_adp * demand_data.norm_cov
    # print(demand_data[['norm_adp', 'norm_cov', 'demand_index']])
    # print()

    ## UTILITY OF REJUVENATION #########################################################################################
    rock_structure = gpd.read_file(inputs["rock_structure"])
    # print(rock_structure)

    # Generate pump yield variable
    rock_structure['pump_yield'] = None

    rock_structure.loc[rock_structure['AquName'] == "Shallow alluvial aquifer", 'pump_yield'] = 920
    rock_structure.loc[rock_structure['AquName'] == "Deep confined aquifer", 'pump_yield'] = 585
    rock_structure.loc[rock_structure['AquName'] == "Shallow karstic acquifer", 'pump_yield'] = 400
    rock_structure.loc[rock_structure['AquName'] == "Shallow sandy aquifer", 'pump_yield'] = 225
    rock_structure.loc[rock_structure['AquName'] == "Basement regolith aquifer", 'pump_yield'] = 150
    rock_structure.loc[rock_structure['AquName'] == "Regolith or fractured aquifer", 'pump_yield'] = 75
    rock_structure.loc[rock_structure['AquName'] == "Laterite (cabook) aquifer", 'pump_yield'] = 70

    # Check it
    rock_table = rock_structure['pump_yield'].value_counts()
    # print(rock_table)
    # print()

    # Generate ranks
    rock_structure['geo_rank'] = None

    rock_structure.loc[rock_structure['pump_yield'] == 920, 'geo_rank'] = 7
    rock_structure.loc[rock_structure['pump_yield'] == 585, 'geo_rank'] = 6
    rock_structure.loc[rock_structure['pump_yield'] == 400, 'geo_rank'] = 5
    rock_structure.loc[rock_structure['pump_yield'] == 225, 'geo_rank'] = 4
    rock_structure.loc[rock_structure['pump_yield'] == 150, 'geo_rank'] = 3
    rock_structure.loc[rock_structure['pump_yield'] == 75, 'geo_rank'] = 2
    rock_structure.loc[rock_structure['pump_yield'] == 70, 'geo_rank'] = 1

    # Normalise the values
    rock_structure['n_geo_rank'] = rock_structure.geo_rank / rock_structure.geo_rank.max()

    # Create a new rock_structure df with only the columns we need for the following merge:
    # rock_structure_filtered = rock_structure[['Map_id', 'AquName', 'pump_yield', 'geo_rank', 'n_geo_rank']]

    # Create a new tanks_polygons df with only the columns we need for the following merge:
    tanks_polygons_filtered = tanks_polygons[['Map_id', 'silt_score', 'soil_score', 'tank_supply_score', 'tank_supply_index', 'func_score']]

    # Create a new demand data df with only the columns we need for the following merge:
    demand_data_filtered = demand_data[['Map_id', 'pop_count', 'norm_adp', 'norm_cov', 'demand_index', 'ADM3_PCODE']]

    # Merge this into the demand and supply index
    #two_part_index = demand_data.merge(rock_structure_filtered, on="Map_id", how='left')
    two_part_index = rock_structure.merge(demand_data_filtered, on="Map_id", how='left')
    three_part_index = two_part_index.merge(tanks_polygons_filtered, on="Map_id", how='left')

    # Now can collapse/group by DSD and District
    dsd_level = three_part_index.dissolve(
                by='ADM3_PCODE',
                aggfunc={'silt_p': "mean",
                         'max_soil_d': "mean",
                         'tank_supply_index': "mean",
                         'demand_index': "mean",
                         'n_geo_rank': "mean",
                         'Map_id': "count"})

  # Create a csv with all that information for each tank id
    dsd_level.drop('geometry', axis=1).to_csv(outputs["tanks_dsd_level_csv"])

    DSD_zones = gpd.read_file(inputs["SL_DSD"])
    DSD_zones = DSD_zones[["ADM3_PCODE", "geometry"]]

    dsd_level = dsd_level.reset_index()
    print(dsd_level.columns)
    dsd_level_filtered = dsd_level[['silt_p', 'max_soil_d', 'tank_supply_index', 'demand_index', 'n_geo_rank', 'ADM3_PCODE', 'Map_id']]

    # Merge to change the output geometry
    dsd_level_ng = DSD_zones.merge(dsd_level_filtered, on='ADM3_PCODE', how='left')

    # Drop the DSD areas with no tanks
    dsd_level_ng.dropna(inplace=True)

    # Save to file
    dsd_level_ng.to_file(outputs["tanks_dsd_level"])

    # Create a csv with all that information for each tank id
    dsd_level_ng.drop('geometry', axis=1).to_csv(outputs["tanks_dsd_level_csv"])
