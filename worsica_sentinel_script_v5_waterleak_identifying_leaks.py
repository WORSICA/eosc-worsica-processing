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

import worsica_leakdetection

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
        print('-- 1) Identifying leaks ' + args[3] + ' ' + args[1] + ' (' + args[2] + ') --')
        print('---------------------------------------------')
        waterIndexes = args[2].split(',')
        fromAnomaly = (args[3] == 'by_anomaly')  # by_anomaly or by_index
        filterByMask = (args[5] == 'filter_by_mask')
        # ./ldYYY/merged_resampled_xxxxxxxxx_wi[_anomaly]_2nd_deriv.tif
        for wi in waterIndexes:
            worsica_leakdetection.identifying_leaks(WORKSPACE_PATH +
                                                    '/' +
                                                    args[4] +
                                                    '/' +
                                                    args[1] +
                                                    '_' +
                                                    wi +
                                                    ('_anomaly' if fromAnomaly else '') +
                                                    '_2nd_deriv.tif', WORKSPACE_PATH +
                                                    '/' +
                                                    args[4], filterByMask, WORKSPACE_PATH +
                                                    '/' +
                                                    args[4] +
                                                    '/' +
                                                    args[4] +
                                                    '_mask.tif')

    except BaseException:
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) != 6:
        print(
            "Usage: ./worsica_sentinel_script_v5_waterleak_identifying_leaks.py [MERGED_IMAGESET_NAME] [WATER_INDEX] [FROM_ANOMALY] [LD_IMAGE_NAME] [FILTER_BY_MASK]")
        exit(1)
    else:
        run_script(sys.argv)
        exit(0)
