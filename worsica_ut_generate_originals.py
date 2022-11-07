#!/usr/bin/python3
# -*- coding: utf-8 -*-

# pylint: disable=C0301,C0303

"""
worsica script to generate original products
Author: rjmartins

Script to generate the first-time original products for unitary tests.
This can be run when an update to the processing was made.
Please DO NOT run this when you are running the unitary tests,
since it will wipe all existing files in the folder.

This deletes the existing files inside unit_tests_files folder,
runs the worsica_sentinel_script_ut_coastal.py,
and renames them by adding 'original_' prefix
for comparison during unitary tests

"""
import os
import shutil
import worsica_sentinel_script_ut_coastal


def _search_and_remove_files(files):
    '''
    checks if file exists and deletes
    '''
    for file in files:
        if os.path.exists(file):
            print('remove old ' + file)
            os.remove(file)


def _check_condition(text, condition):
    '''
    checks if a condition is valid (true), and throws exception if not
    '''
    if condition:
        print('[OK] ' + text)
    else:
        raise Exception("[FAILED] " + text)


def yes_or_no(question):
    '''
    prompt question Y/N
    '''
    reply = str(input(question)).lower().strip()
    if reply[0] == 'y' or reply[0] == 'Y':
        boo = True
    elif reply[0] == 'n' or reply[0] == 'N':
        boo = False
    else:
        yes_or_no(question)
    return boo


if __name__ == '__main__':
    # check current working directory before running this
    # we dont want this to be run in other directory than unit_tests_files
    WORKSPACE_PATH = os.getcwd()
    if '/unit_tests_files' in WORKSPACE_PATH:
        IMAGESET_NAME_NO_ZIP_EXTENSION = "S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502"  # is the imageset name
        ROI_NAME = '.'
        # is a string with a geojson POLYGON definition.
        ROI_POLYGON = "POLYGON ((-9.29732860720871 38.690406978809875,-9.351916925079804 38.690406978809875,-9.351916925079804 38.66708931583892,-9.29732860720871 38.66708931583892,-9.29732860720871 38.690406978809875))"
        BATHYMETRY_THRESHOLD = -2
        TOPOGRAPHY_THRESHOLD = 5
        WI_THRESHOLD = '0.3,0.1,-0.2'
        WATER_INDEX = 'mndwi,ndwi,ndwi2'
        print('========WARNING=======')
        print('This script will generate the original products to be compared during the unit tests. This deletes the existing files inside unit_tests_files folder, runs the worsica_sentinel_script_ut_coastal.py, and renames its products with original_ prefix. This operation is not reversible. If you do not want to do that, please abort.')
        print('======================')
        if yes_or_no('Are you sure do you want to proceed? (Y/N) '):
            # delete all files inside folder
            for filename in os.listdir(WORKSPACE_PATH):
                file_path = os.path.join(WORKSPACE_PATH, filename)
                try:
                    if '.zip' not in file_path and '.txt' not in file_path and os.path.isfile(
                            file_path):
                        print('remove ' + file_path)
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as err:
                    print('Failed to delete %s. Reason: %s' % (file_path, err))
            # run script
            worsica_sentinel_script_ut_coastal.run_script(['', IMAGESET_NAME_NO_ZIP_EXTENSION, ROI_NAME, ROI_POLYGON, str(
                BATHYMETRY_THRESHOLD), str(TOPOGRAPHY_THRESHOLD), WI_THRESHOLD, WATER_INDEX])
            # rename
            print('Rename')
            for filename in os.listdir(WORKSPACE_PATH):
                file_path = WORKSPACE_PATH + '/' + filename
                print(file_path)
                if os.path.isdir(
                        WORKSPACE_PATH + '/' + filename):  # inside subdirectory, just rename the files inside and the folder
                    for filename2 in os.listdir(file_path):
                        os.rename(file_path + '/' + filename2, file_path + '/original_' + filename2)
                else:
                    if '.zip' not in file_path and '.txt' not in file_path and os.path.isfile(
                            file_path):
                        print('rename ' + file_path)
                        os.rename(
                            WORKSPACE_PATH + '/' + filename,
                            WORKSPACE_PATH + '/original_' + filename)
        else:
            print('Aborted')
    else:
        print('Error: You must run this script inside unit_tests_files folder in order to run this script!')
