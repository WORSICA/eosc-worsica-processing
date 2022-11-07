#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""
worsica script for edge detection using opencv
Author: rjmartins

Script to run all the image processing,
This does not include running the topo-bath image generation
since it is only once made and should be manually done.

Args:
>1) ZIPFILE is the imagesets name to merge separated by comma
>2) MERGEDNAME is a name for output merged file

Usage: ./worsica_sentinel_script_v5_merging.py  [ZIPFILE] [MERGEDNAME]
e.g: ./worsica_sentinel_script_v5_merging.py  S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502,S2A_MSIL2A_20181229T113501_N0211_R080_T29SMD_20181229T124502 merged_resampled_imagesets_2018_12_29
"""

import sys
import os

import worsica_ph1_resample_crop_rgb

import worsica_common_script_functions

import traceback

WORKSPACE_PATH = '.'
SCRIPT_PATH = '/usr/local/worsica_web_products'


def get_resampled_file(path):
    print('[get_resampled_file] Get _resampled.tif in ' + path)
    try:
        fname = None
        listd = os.listdir(path)
        if (len(listd) > 0):
            for f in listd:
                if os.path.isfile(path + '/' + f) and f.endswith("_resampled.tif"):
                    print('[get_resampled_file] found ' + f)
                    fname = f
                    print('[get_resampled_file] OK')
        return fname
    except Exception as e:
        raise Exception('Error on getting _resampled.tif! Not found!!')


def run_script(args):
    '''
    run all the image processing
    '''
    # resample
    try:
        print(WORKSPACE_PATH)
        if not os.path.exists(WORKSPACE_PATH + '/' + args[2] + '/'):
            os.makedirs(WORKSPACE_PATH + '/' + args[2] + '/', exist_ok=True)
        print('---------------------------------------------')
        print('-- 1) Merging resamples ' + args[1] + ' to ' + args[2] + '--')
        print('---------------------------------------------')
        inputImagesForMerge = ""
        for img in args[1].split(','):
            p = WORKSPACE_PATH + '/' + img + '/resampled'
            fileresampled = get_resampled_file(p)
            inputImagesForMerge += p + '/' + fileresampled + ' '

        outputImage = WORKSPACE_PATH + '/' + args[2] + '/' + args[2] + '.tif'
        _additional_params = "-of GTiff -co NUM_THREADS=16 -co COMPRESS=LZW -co PREDICTOR=2 -co TILED=YES"

        cmd = worsica_common_script_functions._run_gdalmerge(
            _additional_params, outputImage, inputImagesForMerge)
        cmd_wait = cmd.wait()
        if cmd_wait == 0:
            print('SUCCESS! Stored as ' + outputImage)
        else:
            print('FAIL')
            exit(1)

        if (args[3] in ['coastal', 'inland']):
            bands = [3, 2, 1]
            #if 'uploaded-user' in inputImagesForMerge:
            #    print('Has user uploaded images, invert band order')
            #    bands = [1, 2, 3]
            print(bands)
            print('---------------------------------------------')
            print('-- RGB for ' + args[2] + ' --')
            print('---------------------------------------------')
            worsica_common_script_functions.search_and_remove_files(
                [WORKSPACE_PATH + '/' + args[2] + '/' + args[2] + '_RGB.tif'])
            worsica_ph1_resample_crop_rgb.run_rgb(outputImage, os.getcwd() + '/' + args[2], bands)

    except BaseException:
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) != 4:
        print(
            "Usage: ./worsica_sentinel_script_v5_merging.py [IMAGESETS_NAME_NO_ZIP_EXTENSION] [MERGEDNAME] [SERVICE]")
        exit(1)
    else:
        run_script(sys.argv)
        exit(0)
