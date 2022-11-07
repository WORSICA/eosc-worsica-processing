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
>3) ROI-POLYGON is a string with a WKT POLYGON definition.

Usage: ./worsica_sentinel_script_v5_resampling.py  [ZIPFILE] [ROI-NAME] [ROI-POLYGON] [BATHYMETRY-THRESHOLD] [TOPOGRAPHY-THRESHOLD] [WI_THRESHOLD] [WATER_INDEX]
e.g: ./worsica_sentinel_script_v5_resampling.py  S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502
MARGEM-SUL "POLYGON ((-9.29732860720871 38.690406978809875,-9.351916925079804 38.690406978809875,
-9.351916925079804 38.66708931583892,-9.29732860720871 38.66708931583892,
-9.29732860720871 38.690406978809875))"
"""

import sys
import os

import worsica_ph1_resample_crop_rgb

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
        print('-- 1) Resampling+Crop for ' + args[2] + ' (' + args[3] + ') --')
        print(args[5])  # BANDS
        print('---------------------------------------------')
        worsica_common_script_functions.search_and_remove_files(
            [WORKSPACE_PATH + '/' + args[2] + '/' + args[1] + '_RGB.tif'])
        bbox = worsica_common_script_functions.generate_bbox_from_wkt(str(args[3]))
        procDict = [{'imgZip': args[1] + '.zip',
                     'path': os.getcwd() + '/' + args[2],
                     'projWinArgs': {'projWinSRS': 'EPSG:4326',
                    'projWin': bbox},
                     'bands': args[5]}]
        if (args[4] == 'waterleak'):
            worsica_ph1_resample_crop_rgb.run_resample_waterleak(procDict)
        else:
            worsica_ph1_resample_crop_rgb.run_resample(procDict)

        print('SUCCESS!')
    except BaseException:
        traceback.print_exc()
        print('FAIL')
        exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print(
            "Usage: ./worsica_sentinel_script_v5_resampling.py [IMAGESET_NAME_NO_ZIP_EXTENSION] [ROI-NAME] [ROI-POLYGON] [SERVICE] [BANDS]")
        exit(1)
    else:
        if os.path.exists(sys.argv[1] + '.zip'):
            run_script(sys.argv)
            exit(0)
        else:
            print(
                'ERROR: ' +
                sys.argv[1] +
                '.zip does not exist. Make sure you write the file name correctly, or check if exists.')
            exit(1)
