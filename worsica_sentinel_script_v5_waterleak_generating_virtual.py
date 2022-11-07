#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""
worsica script for edge detection using opencv
Author: rjmartins

Script to run all the image processing,
This does not include running the topo-bath image generation
since it is only once made and should be manually done.

Args:
>1) ZIPFILE is the imageset name located
in the same folder as this script
>2) ROI-NAME_is a region of interest name
>3 and 4) [now deprecated] BATHYMETRY-THRESHOLD and TOPOGRAPHY-THRESHOLD are threshold
values given for bath and topography during MNDWI filtering
>5) WI_THRESHOLD is a comma separate value string that defines the threshold filtering value for each water index
>6) WATER_INDEX is a comma separate value string that defines the chosen water indexes

Usage: ./worsica_sentinel_script_v5_waterleak_generating_virtual.py  [ZIPFILE] [ROI-NAME] [ROI-POLYGON] [BATHYMETRY-THRESHOLD] [TOPOGRAPHY-THRESHOLD] [WI_THRESHOLD] [WATER_INDEX]
e.g: ./worsica_sentinel_script_v5_waterleak_generating_virtual.py  S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502
MARGEM-SUL -2 5 0.3,0.1,-0.2 mndwi,ndwi,ndwi2
"""

import sys
import os

import worsica_leakdetection

import worsica_common_script_functions

import traceback


WORKSPACE_PATH = '.'
SCRIPT_PATH = '/usr/local/worsica_web_products'


def run_script(args):
    '''
    run all the image processing
    '''
    # resample
    try:
        print(WORKSPACE_PATH)
        print('---------------------------------------------')
        print('-- 1) Generate virtual empty image ' + args[2] + ' --')
        print('---------------------------------------------')
        worsica_common_script_functions.search_and_remove_files(
            [WORKSPACE_PATH + '/' + args[2] + '/' + args[1] + '.tif'])
        worsica_leakdetection.generate_virtual_empty_image(
            WORKSPACE_PATH + '/' + args[2] + '/' + args[1] + '.tif',
            WORKSPACE_PATH + '/' + args[4] + '/' + args[3] + '.tif')

        print('SUCCESS!')
    except BaseException:
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(
            "Usage: ./worsica_sentinel_script_v5_waterleak_generating_virtual.py [VIRTUAL_IMAGESET_NAME] [FOLDER_NAME_VIRTUAL] [SAMPLE_IMAGESET_NAME] [FOLDER_NAME_SAMPLE]")
        exit(1)
    else:
        if not os.path.exists(WORKSPACE_PATH + '/' + sys.argv[4] + '/' + sys.argv[3] + '.tif'):
            print(
                'ERROR: sample ' +
                sys.argv[3] +
                '.tif does not exist. Make sure you write the file name correctly, or check if exists.')
            exit(1)
        else:
            if not os.path.exists(WORKSPACE_PATH + '/' + sys.argv[2]):
                print('Creating directory ' + WORKSPACE_PATH + '/' + sys.argv[2])
                os.mkdir(WORKSPACE_PATH + '/' + sys.argv[2])
            run_script(sys.argv)
            exit(0)
