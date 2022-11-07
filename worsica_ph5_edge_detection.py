#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""
worsica script for edge detection using opencv
Author: rjmartins

Grabs the K-Means binarized image (black-white image) and try to improve its quality for easier detection.
First close the dots inside of the white lines and apply a kernel to generate edges.

Args:
FILE_NAME is a string for a file name
"""

import sys
import numpy as np
from osgeo import gdal  # dnf install gdal-python3
import cv2
import traceback

import worsica_common_script_functions

KERNEL_SIZE = (3, 3)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, KERNEL_SIZE)


def run_cleanup_edge_detection(input_file, custom_output_file=None):
    '''
    run cleanup of kmeans, by using closing morphology and edge detection
    '''
    try:
        img = cv2.imread(input_file, cv2.IMREAD_LOAD_GDAL)
        closing = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
        img = None
        edges = cv2.Canny(np.uint8(closing), 0.01, 0.99)  # -999, 999)
        closing = None
        if custom_output_file is None:
            input_file_split = input_file.split('/')
            input_file_name_split = input_file_split[-1].split('.')
            output_file = './' + input_file_split[1] + '/' + \
                input_file_name_split[0] + '_closing_edge_detection.tif'
        else:
            output_file = custom_output_file
        img_edges = worsica_common_script_functions.generate_new_image(
            output_file, 1, gdal.GDT_Byte, worsica_common_script_functions.get_image_info(input_file))
        img_edges.GetRasterBand(1).WriteArray(edges)
        edges = None
        img_edges = None
        print('DONE!')
    except BaseException:
        traceback.print_exc()


def run_cleanup_edge_detection_inland(input_file, custom_output_file=None):
    '''
    run cleanup of kmeans, by using closing morphology and edge detection
    '''
    try:
        img = cv2.imread(input_file, cv2.IMREAD_LOAD_GDAL)
        closing = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)  # -999 ... 999
        img = None
        edges = closing
        closing = None
        if custom_output_file is None:
            input_file_split = input_file.split('/')
            input_file_name_split = input_file_split[-1].split('.')
            output_file = './' + input_file_split[1] + '/' + \
                input_file_name_split[0] + '_closing_edge_detection.tif'
        else:
            output_file = custom_output_file
        img_edges = worsica_common_script_functions.generate_new_image(
            output_file, 1, gdal.GDT_Byte, worsica_common_script_functions.get_image_info(input_file))
        img_edges.GetRasterBand(1).WriteArray(edges)  # 0 ... 255
        edges = None
        img_edges = None
        print('DONE!')
    except BaseException:
        traceback.print_exc()


# Usage: ./worsica-ph5-edge-detection.py [FILE_NAME]
# e.g: ./worsica-ph5-edge-detection.py S2B_MSIL1C_20180224T112109_N0206_R037_T29SMC_20180224T164834
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./worsica-ph5-edge-detection.py [FILE_NAME] ")
    else:
        run_cleanup_edge_detection('./outputs/' + sys.argv[1] + '_kmeans_binary.tif')
