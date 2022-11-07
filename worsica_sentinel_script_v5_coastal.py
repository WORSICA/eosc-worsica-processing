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

Usage: ./worsica_sentinel_script_v5_coastal.py  [ZIPFILE] [ROI-NAME] [ROI-POLYGON] [BATHYMETRY-THRESHOLD] [TOPOGRAPHY-THRESHOLD] [WI_THRESHOLD] [WATER_INDEX]
e.g: ./worsica_sentinel_script_v5_coastal.py  S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502
MARGEM-SUL -2 5 0.3,0.1,-0.2 mndwi,ndwi,ndwi2
"""

import sys
import os

import worsica_waterIndexes
import worsica_automaticThreshold
import worsica_ph5_edge_detection
import worsica_ph6_vectorization_v3

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
        wis = args[6].split(',')  # water indexes
        thrs = args[5].split(',')
        for wi, thr in zip(wis, thrs):
            # wi proc
            print('Processing ' + wi + ' now!')
            print('---------------------------------------------')
            print('-- 2) Start processing ' + wi + ' WATER INDEX')
            print('---------------------------------------------')
            worsica_common_script_functions.search_and_remove_files(
                [WORKSPACE_PATH + '/' + args[2] + '/' + args[1] + '_' + wi + '.tif'])
            worsica_waterIndexes.worsicaWaterIndexes(
                WORKSPACE_PATH +
                '/' +
                args[2] +
                '/' +
                args[1] +
                '.tif',
                wi.upper(),
                os.getcwd() +
                '/' +
                args[2])
            print('---------------------------------------------')
            print('-- 3) Apply threshold ' + str(thr) + ' on ' + wi + ' for ' + args[2] + ' --')
            print('---------------------------------------------')
            if (thr == 'AUTO'):
                print('Calculating threshold...')
                thr = worsica_automaticThreshold.worsicaAutomaticThreshold(
                    WORKSPACE_PATH + '/' + args[2] + '/' + args[1] + '_' + wi + '.tif')
                # create file
                with open(WORKSPACE_PATH + '/' + args[2] + '/' + args[1] + '_' + wi + '_auto_threshold_val.txt', 'w') as f:
                    f.write(str(thr))
                print('Finished, threshold is ' + str(thr))
            worsica_common_script_functions.search_and_remove_files(
                [WORKSPACE_PATH + '/' + args[2] + '/' + args[1] + '_' + wi + '_binary.tif'])
            worsica_waterIndexes.worsicaApplyWaterIndexesThreshold(
                WORKSPACE_PATH +
                '/' +
                args[2] +
                '/' +
                args[1] +
                '_' +
                wi +
                '.tif',
                float(thr),
                os.getcwd() +
                '/' +
                args[2])
            print('---------------------------------------------')
            print('-- 4) Start ' + wi + ' edge detection for ' + args[2] + ' --')
            print('---------------------------------------------')
            worsica_common_script_functions.search_and_remove_files(
                [
                    WORKSPACE_PATH +
                    '/' +
                    args[2] +
                    '/' +
                    args[1] +
                    '_' +
                    wi +
                    '_binary_closing.tif',
                    WORKSPACE_PATH +
                    '/' +
                    args[2] +
                    '/' +
                    args[1] +
                    '_' +
                    wi +
                    '_binary_closing_edge_detection.tif'])
            worsica_ph5_edge_detection.run_cleanup_edge_detection(
                WORKSPACE_PATH + '/' + args[2] + '/' + args[1] + '_' + wi + '_binary.tif')
            # vectorization
            print('---------------------------------------------')
            print('-- 5) Start vectorization for ' + args[2] + ' --')
            print('---------------------------------------------')
            worsica_common_script_functions.search_and_remove_files(
                [
                    WORKSPACE_PATH +
                    '/' +
                    args[2] +
                    '/' +
                    args[1] +
                    '_' +
                    wi +
                    '.shp',
                    WORKSPACE_PATH +
                    '/' +
                    args[2] +
                    '/' +
                    args[1] +
                    '_' +
                    wi +
                    '.dbf',
                    WORKSPACE_PATH +
                    '/' +
                    args[2] +
                    '/' +
                    args[1] +
                    '_' +
                    wi +
                    '.shx'])
            worsica_ph6_vectorization_v3.run_multiline_string_vectorization(
                WORKSPACE_PATH +
                '/' +
                args[2] +
                '/' +
                args[1] +
                '_' +
                wi +
                '.tif',
                float(thr),
                0,
                WORKSPACE_PATH +
                '/' +
                args[2] +
                '/' +
                args[1] +
                '_' +
                wi +
                '.shp')
            print('Processing ' + wi + ' done!')
        print('SUCCESS!')
    except BaseException:
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 7:
        print(
            "Usage: ./worsica_sentinel_script_v5_coastal.py [IMAGESET_NAME_NO_ZIP_EXTENSION] [ROI-NAME] [BATHYMETRY-THRESHOLD] [TOPOGRAPHY-THRESHOLD] [WI_THRESHOLD] [WATER_INDEX]")
        exit(1)
    else:
        if os.path.exists(WORKSPACE_PATH + '/' + sys.argv[2] + '/' + sys.argv[1] + '.tif'):
            run_script(sys.argv)
            exit(0)
        else:
            print(
                'ERROR: ' +
                sys.argv[1] +
                '.tif does not exist. Make sure you write the file name correctly, or check if exists.')
            exit(1)
