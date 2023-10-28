# The keys of the inputs and outputs dictionaries, as well as the file names should follow the camelCase notation.

inputs = {}

inputs["WorldPop_1km_raster"] = "./input-data/lka_ppp_2020_1km_Aggregated_UNadj.tif" #1km Unconstrained Worldpop data
inputs["GHSL_raw_1"] = "./input-data/GHSL/2020/GHS_SMOD_E2030_GLOBE_R2023A_54009_1000_V1_0_R8_C26.tif" # GHSL layer
inputs["GHSL_raw_2"] = "./input-data/GHSL/2020/GHS_SMOD_E2030_GLOBE_R2023A_54009_1000_V1_0_R8_C27.tif" # GHSL layer
inputs["GHSL_raw_3"] = "./input-data/GHSL/2020/GHS_SMOD_E2030_GLOBE_R2023A_54009_1000_V1_0_R9_C26.tif" # GHSL layer
inputs["GHSL_raw_4"] = "./input-data/GHSL/2020/GHS_SMOD_E2030_GLOBE_R2023A_54009_1000_V1_0_R9_C27.tif" # GHSL layer
inputs["SL_Districts"] = "./input-data/lka_admbnda_adm2_slsd_20200305.shp" # Shapefile with Sri Lanka districts
inputs["land_use"] = "./input-data/SL_LU.shp"
inputs["hies_pop_csv"] = './input-data/HIES_agri_labor.csv' # HIES data set on agricultural labour counts per districts
inputs["tanks_polygons"] = './input-data/undp_tanks_poly_silt.shp' # 11k tanks

outputs = {}

outputs["ag_dep_pop_shp"] = "./output-data/ag_dependent_population.shp"
