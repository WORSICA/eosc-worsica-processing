#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ========================================================================
__author__ = 'Alberto Azevedo, Jules Buquen and Alphonse Nahon'
__doc__ = "Script to produce a subpixel output in .shp format. This script uses the DEA-TOOLS package."
__datetime__ = '& May 2022 &'
__email__ = 'aazevedo@lnec.pt'
# ========================================================================

import pandas as pd
import xarray as xr
from dea_tools.spatial import subpixel_contours
import argparse
import traceback


def run_multiline_string_vectorization(image, threshold, elev, output_name):
    print('run_multiline_string_vectorization')
    try:
        # Read in the elevation data from file
        raster_path = image
        elevation_array = xr.open_rasterio(raster_path).squeeze('band')

        # Modify CRS attribute into a format consistent with `dc.load`
        elevation_array.attrs['crs'] = 'EPSG:4326'

        z_values = [threshold]
        attribute_df = pd.DataFrame({'elev_cm': z_values,
                                    'elev': [elev],
                                     'DN': [0],
                                     'DN_1': [1]})
        # Extract contours with custom attribute fields:
        contours_gdf = subpixel_contours(da=elevation_array,
                                         z_values=z_values,
                                         attribute_df=attribute_df,
                                         output_path=output_name,
                                         verbose=True)

        # Print output
        contours_gdf.head()
        print('DONE!')
        # return None
    except BaseException:
        traceback.print_exc()


def getARGScmd():
    parser = argparse.ArgumentParser(
        description='worsica_subpixel: Script to produce a subpixel output in shapefile format.')
    parser.add_argument('-img', help='Image path', required=True)
    parser.add_argument(
        "-t",
        "--threshold",
        help="Threshold value for the definition of the contours in water indexes.",
        type=float,
        default=0.,
        required=False)
    parser.add_argument(
        "-l",
        "--level",
        help="Corrected level of the coastline (FES2014+Inv.Barometer+WaveSetup) .",
        type=float,
        default=0.,
        required=False)
    parser.add_argument(
        "-o",
        "--output",
        help="Name of the output shapefile with the coastline level for each image (.shp format)",
        required=True)
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = getARGScmd()
    print(args)
    run_multiline_string_vectorization(args.img, args.threshold, args.level, args.output)
