#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""
worsica script K-Means image generation using opencv
Author: rjmartins

Grabs the MNDWI product and generate its respective K-Means classification.
K-Means is used to classify each pixel value, it is determined by doing its difference with each class value,
the pixel class is determined by the one who has the lowest diff.
This step is required in order to run the polygonization.
4 classes (class 0 to 3) were used to provide a more approximate result.

Args:
FILE_NAME is a string for a file name
"""

import sys
import numpy as np
from osgeo import gdal  # dnf install gdal-python3
import cv2

import worsica_common_script_functions


def run_k_means(input_file, k_clusters=4):
    '''
    rum k means function from opencv
    '''
    img = cv2.imread(input_file, cv2.IMREAD_LOAD_GDAL)
    input_file_split = input_file.split('/')
    input_file_name_split = input_file_split[2].split('.')
    input_file_name_split[0] = input_file_name_split[0].replace('_mndwi', '')
    img_z = img.reshape((-1, 1))
    img_z = np.float32(img_z)
    # define criteria, number of clusters(K) and apply kmeans()
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1.0)
    cluster_num_k = k_clusters
    _, label, center = cv2.kmeans(img_z, cluster_num_k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    center = np.float32(center)

    center_ord = np.sort(center, axis=0)
    center_ord = center_ord[::-1]

    for c in range(0, len(center)):
        for co in range(0, len(center_ord)):
            if center[c] == center_ord[co]:
                center[c] = co

    res = center[label.flatten()]
    res_reshape = res.reshape((img.shape))

    img_kmeans = worsica_common_script_functions.generate_new_image(
        './' +
        input_file_split[1] +
        '/' +
        input_file_name_split[0] +
        '_kmeans.tif',
        1,
        gdal.GDT_Float32,
        worsica_common_script_functions.get_image_info(input_file))
    img_kmeans.GetRasterBand(1).WriteArray(res_reshape)
    res_reshape = None
    img_kmeans = None


def run_k_means_binarization(input_file):
    img = cv2.imread(input_file, cv2.IMREAD_LOAD_GDAL)
    input_file_split = input_file.split('/')
    input_file_name_split = input_file_split[2].split('.')
    input_file_name_split[0] = input_file_name_split[0].replace('_kmeans', '')
    img_z = img.reshape((-1, 1))
    for c in range(0, len(img_z)):
        img_z[c] = (-999 if (img_z[c] == 0 or img_z[c] == 1) else 999)

    res_reshape = img_z.reshape((img.shape))

    img_kmeans = worsica_common_script_functions.generate_new_image(
        './' +
        input_file_split[1] +
        '/' +
        input_file_name_split[0] +
        '_kmeans_binary.tif',
        1,
        gdal.GDT_Float32,
        worsica_common_script_functions.get_image_info(input_file))
    img_kmeans.GetRasterBand(1).WriteArray(res_reshape)
    res_reshape = None
    img_kmeans = None


# Usage: ./worsica_ph3_opencv_kmeans.py [FILE_NAME]
# e.g: ./worsica_ph3_opencv_kmeans.py S2B_MSIL1C_20180224T112109_N0206_R037_T29SMC_20180224T164834
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: ./worsica_ph3_opencv_kmeans.py [KIND] [FILE_PATH] ")
        print("KIND - available options are 'kmeans' (to generate kmeans image) or 'kmeans-binary' (to generate kmeans binary)")
    else:
        if sys.argv[1] == 'kmeans':
            run_k_means(sys.argv[2], 4)
        elif sys.argv[1] == 'kmeans-binary':
            run_k_means_binarization(sys.argv[2])
        else:
            print(
                sys.argv[1] +
                " kind not valid. Available options are 'kmeans' (to generate kmeans image) or 'kmeans-binary' (to generate kmeans binary)")
