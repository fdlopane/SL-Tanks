"""
This module contains a set of bespoke geocomputation function
"""

import rasterio
from rasterio.enums import Resampling
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
def resample_raster(input_path, output_path, x_resolution, y_resolution):
    """This function resamples a raster file given a new resolution."""
    # Open the input raster file
    with rasterio.open(input_path) as src:
        # Define the resampling method (e.g., cubic for cubic convolution)
        # Resampling documentation: https://rasterio.readthedocs.io/en/stable/topics/resampling.html
        resampling_method = Resampling.bilinear

        # Set the desired resolution
        target_resolution = (x_resolution, y_resolution)  # Set your desired resolution here

        # Resample the raster
        data = src.read(
            out_shape=(
                src.count,
                int(src.height * src.res[0] / target_resolution[0]),
                int(src.width * src.res[1] / target_resolution[1]),
            ),
            resampling=resampling_method
        )

        # Update the metadata
        transform = rasterio.transform.from_origin(
            src.bounds.left, src.bounds.top, target_resolution[0], target_resolution[1]
        )

        kwargs = src.meta.copy()
        kwargs.update({
            'crs': src.crs,
            'transform': transform,
            'width': int(src.width * src.res[1] / target_resolution[1]),
            'height': int(src.height * src.res[0] / target_resolution[0])
        })

        # Write the resampled data to the output raster file
        with rasterio.open(output_path, 'w', **kwargs) as dst:
            dst.write(data)

########################################################################################################################

'''
from osgeo import gdal

def raster_to_shp(input_raster, raster_band, field_name, output_shp):
    # Open the raster dataset
    raster_ds = gdal.Open(input_raster)
    band = raster_ds.GetRasterBand(raster_band)

    # Get raster geotransformation information
    transform = raster_ds.GetGeoTransform()

    # Create an empty GeoDataFrame
    points_gdf = gpd.GeoDataFrame(columns=[field_name], geometry=gpd.GeoSeries([], name='geometry'))

    # Loop through each pixel in the raster
    for y in range(raster_ds.RasterYSize):
        for x in range(raster_ds.RasterXSize):
            value = band.ReadAsArray(x, y, 1, 1)[0, 0]

            if value is not None:
                # Convert raster coordinates to geographic coordinates
                x_geo = transform[0] + x * transform[1] + y * transform[2]
                y_geo = transform[3] + x * transform[4] + y * transform[5]

                # Append a new row to the GeoDataFrame
                points_gdf = points_gdf._append({field_name: int(value), 'geometry': gpd.points_from_xy([x_geo], [y_geo])[0]}, ignore_index=True)

    # Set the GeoDataFrame's coordinate reference system
    points_gdf.crs = raster_ds.GetProjection()

    # Save the GeoDataFrame to a shapefile
    points_gdf.to_file(output_shp)
'''

### Joe's method:
def raster_to_shp_THIS_WORKS(input_raster, output_shp):
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
    gdf_pop = gpd.GeoDataFrame({'geometry': geometry, 'raster_value': raster_values}, crs=raster_crs)
    print('Worldpop raster converted into points')

    gdf_pop.to_feather(output_shp)

def raster_to_shp(input_raster, output_shp, field_name:str):
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

    gdf_pop.to_feather(output_shp)

    return gdf_pop