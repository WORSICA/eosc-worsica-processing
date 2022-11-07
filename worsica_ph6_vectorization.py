#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""
worsica script for edge detection using opencv
Author: rjmartins

Run the gdal polygonize to generate a shapeline based on the pixel value (class number)

Args:
FOLDER-NAME is the imageset folder name where files exist
MASK_FILE_NAME_NO_EXTENSION is the imageset file name
CLASS_NUM is the number of class to generate the polygon.
"""

import sys
from osgeo import gdal, osr, ogr  # dnf install gdal-python3


def run_multiline_string_vectorization(mask_input, shp_output, detect_class):
    '''
    do the vectorization by using polygonize
    '''
    imgmask = gdal.Open(mask_input)

    driver = ogr.GetDriverByName('ESRI Shapefile')
    dest_srs = osr.SpatialReference()
    dest_srs.ImportFromEPSG(4326)  # 32629

    srcband = imgmask.GetRasterBand(1)
    dst_ds = driver.CreateDataSource(shp_output)
    dst_layer = dst_ds.CreateLayer("test", srs=dest_srs, geom_type=ogr.wkbMultiLineString)
    dst_layer.CreateField(ogr.FieldDefn('DN', ogr.OFTInteger), 0)
    dst_layer.CreateField(ogr.FieldDefn('DN_1', ogr.OFTInteger), 1)
    gdal.Polygonize(srcband, srcband, dst_layer, detect_class)  # use black from mask.
    print('DONE!')


# Usage: ./worsica-ph6-vectorization.py [FOLDER-NAME] [MASK_FILE_NAME_NO_EXTENSION] [CLASS_NUM]
# e.g: ./worsica-ph6-vectorization.py .
# S2B_MSIL1C_20180224T112109_N0206_R037_T29SMC_20180224T164834 2
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(
            "Usage: ./worsica-ph6-vectorization.py [FOLDER-NAME] [MASK_FILE_NAME_NO_EXTENSION] [CLASS_NUM]")
    else:
        run_multiline_string_vectorization('./' +
                                           sys.argv[1] +
                                           '/' +
                                           sys.argv[2] +
                                           '_binary_closing_edge_detection.tif', './' +
                                           sys.argv[1] +
                                           '/' +
                                           sys.argv[2] +
                                           '.shp', int(sys.argv[3]))
