"""
This module contains a set of bespoke geocomputation function
"""

import rasterio
from rasterio.enums import Resampling
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.features import shapes
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, shape
import os
def resample_raster(input_path, output_path, x_resolution, y_resolution):
    """This function resamples a raster file given a new resolution."""
    # Open the input raster file
    with rasterio.open(input_path) as src:
        # Define the resampling method (e.g., cubic for cubic convolution)
        # Resampling documentation: https://rasterio.readthedocs.io/en/stable/topics/resampling.html
        resampling_method = Resampling.nearest

        # Set the desired resolution
        target_resolution = (x_resolution, y_resolution)  # Set your desired resolution here

        # Resample the raster
        data = src.read(out_shape = (src.count,
                                     int(src.height * src.res[0] / target_resolution[0]),
                                     int(src.width * src.res[1] / target_resolution[1]),),
                        resampling = resampling_method)

        # Update the metadata
        transform = rasterio.transform.from_origin(
            src.bounds.left, src.bounds.top, target_resolution[0], target_resolution[1])

        kwargs = src.meta.copy()
        kwargs.update({'crs': src.crs,
                       'transform': transform,
                       'width': int(src.width * src.res[1] / target_resolution[1]),
                       'height': int(src.height * src.res[0] / target_resolution[0])})

        # Write the resampled data to the output raster file
        with rasterio.open(output_path, 'w', **kwargs) as dst:
            dst.write(data)

def raster_to_shp_point(input_raster, output_shp, field_name:str):
    """This function converts a raster file into a point shapefile.
    Negative or null values in the raster input will be deleted in the shp output."""
    with rasterio.open(input_raster) as src:
        raster_data = src.read(1)  # Read the raster data and mask out any NoData values
        transform = src.transform  # Get the transformation matrix to convert pixel coordinates to geographic coordinates
        raster_crs = src.crs

    # Get the number of rows and columns in the raster:
    num_rows, num_cols = raster_data.shape

    # Create a regular grid of points based on the raster's extent and resolution:
    x_coords, y_coords = np.meshgrid(np.arange(0, num_cols), np.arange(0, num_rows))
    points = np.c_[x_coords.ravel(), y_coords.ravel()]

    # Transform the grid of points from pixel coordinates to geographic coordinates
    lon, lat = rasterio.transform.xy(transform, points[:, 1], points[:, 0])

    # Get the raster values at each point location
    raster_values = raster_data.ravel()

    # Create a GeoDataFrame with the points and set the CRS to match the raster
    geometry = [Point(lon[i], lat[i]) for i in range(len(lon))]
    gdf_pop = gpd.GeoDataFrame({'geometry': geometry, field_name: raster_values}, crs=raster_crs)

    # Turn the negative values (e.g. -999 values) into zeros:
    # gdf_pop[field_name] = np.where(gdf_pop['field_name'] < 0, 0, int(gdf_pop['field_name']))

    # Remove the negative values:
    gdf_pop = gdf_pop[gdf_pop[field_name] > 0]

    # Convert values to integers and divide by 100 (because of change of resolution):
    gdf_pop[field_name] = gdf_pop[field_name]/100

    gdf_pop.to_feather(output_shp)

    return gdf_pop

def merge_raster_files(list_of_raster_files, output_file):
    """This function merges a list of input raster files into a single output"""
    src_files_to_merge = []  # initialise empty list
    for file in list_of_raster_files:
        src = rasterio.open(file)
        src_files_to_merge.append(src)

    merged, out_trans = merge(src_files_to_merge)

    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": merged.shape[1],
                     "width": merged.shape[2],
                     "transform": out_trans})

    with rasterio.open(output_file, # output filepath
                       "w",         # = overwrite existing files
                       **out_meta   # set the file metadata
                       ) as dest:
        dest.write(merged)

def reproject_raster(input_file, dst_crs:str, output_file):
    """This function reproject a raster file given an input, an output and a coordinate system"""
    with rasterio.open(input_file) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({'crs': dst_crs,
                       'transform': transform,
                       'width': width,
                       'height': height})

        with rasterio.open(output_file, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(source=rasterio.band(src, i),
                          destination=rasterio.band(dst, i),
                          src_transform=src.transform,
                          src_crs=src.crs,
                          dst_transform=transform,
                          dst_crs=dst_crs,
                          resampling=Resampling.nearest)

def clip_raster_file(input_file, clip_shp, output_file):
    # Read in GHSL raster to be clipped
    with rasterio.open(input_file) as src:
        raster_meta = src.meta
        raster_crs = src.crs
        # Clip the raster using 'mask' function
        clipped_raster, out_transform = mask(dataset=src,
                                             shapes=clip_shp.geometry,
                                             crop=True,  # crops the raster to the mask geometry
                                             nodata=0,  # sets the value for pixels outside the vector boundaries
                                             all_touched=True)  # decides whether to consider all pixels that touch the vector features

    # Update the metadata of clipped file
    clipped_meta = raster_meta.copy()
    clipped_meta.update({'height': clipped_raster.shape[1],
                         'width': clipped_raster.shape[2],
                         'transform': out_transform,
                         'crs': raster_crs})

    # Export clipped raster to .tif
    with rasterio.open(output_file, 'w', **clipped_meta) as dst:
        dst.write(clipped_raster)

def raster_to_shp_poly(input_file, output_file, target_classes=None, dissolve=True):
    # Read in raster:
    with rasterio.open(input_file) as src:
        raster_data = src.read(1).astype(np.float32)  # use 'astype' to ensure values are in a format that can be used by shapely
        transform = src.transform  # Get the transformation matrix to convert pixel coordinates to geographic coordinates
        raster_crs = src.crs

    # Filter out the target class values during shape generation
    vector_features = (shape(geom).buffer(0) for geom, val in shapes(raster_data, transform=transform) if val in target_classes)

    # Create a GeoDataFrame directly from the shapes iterator
    gdf = gpd.GeoDataFrame({'geometry': vector_features}, crs=raster_crs)

    #  Fix the geometries in GeoDataFrame (resolves self-intersections, overlapping polygons, etc.)
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: shape(geom).buffer(0))

    print('Raster vectorised.\n')

    if dissolve==True:
        # Dissolve geometries into a single feature
        gdf['dissolve_id'] = 1  # Create a new column with a constant value (ensures all dissolved into a single feature)
        dissolved_gdf = gdf.dissolve(by='dissolve_id', as_index=False)
        dissolved_gdf.drop(columns='dissolve_id', inplace=True)  # Remove the 'dissolve_id' column (optional)
        print('Vector file dissolved into single feature.\n')

        dissolved_gdf.to_feather(output_file)
    else: gdf.to_feather(output_file)

def split_vector_layer(input_gdf, field_name:str, output_directory):
    """This function splits a vector layer (input GeoDtaFrame) into different polygons layers"""
    # Group the GeoDataFrame by the specified field
    grouped = input_gdf.groupby(field_name)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for group_name, group_data in grouped:
        # Create a GeoDataFrame for each group
        output_gdf = gpd.GeoDataFrame(group_data)

        # Define the output file path for the group
        output_file_path = f"{output_directory}/{group_name}.shp"

        # Save the group's GeoDataFrame to a shapefile
        output_gdf.to_file(output_file_path)
