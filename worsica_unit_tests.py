#!/usr/bin/python3
# -*- coding: utf-8 -*-


"""worsica processing script - unitary tests
Author: rjmartins

Script to run all the tests required to run jenkins on this
This is pretty similiar to the existing processing script,
but it will be limited just for checking validity of the
outputs generated in each step of a processing iteration.

REMEMBER:
If anything on the processing script is changed,
the outputs MUST be updated too. Check documentation.

"""

import os
import filecmp
import shutil
import numpy as np
from osgeo import gdal

import worsica_ph1_resample_crop_rgb
import worsica_waterIndexes
import worsica_automaticThreshold
import worsica_ph5_edge_detection
import worsica_ph6_vectorization

import worsica_common_script_functions

WORKSPACE_PATH = os.getcwd()
IMAGESET_NAME_NO_ZIP_EXTENSION = "S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502"  # is the imageset name
# is a string with a geojson POLYGON definition.
ROI_POLYGON = "POLYGON ((-9.29732860720871 38.690406978809875,-9.351916925079804 38.690406978809875,-9.351916925079804 38.66708931583892,-9.29732860720871 38.66708931583892,-9.29732860720871 38.690406978809875))"
BATHYMETRY_THRESHOLD = -2
TOPOGRAPHY_THRESHOLD = 5
WI_THRESHOLD = '0.3,0.1,-0.2'
WATER_INDEX = 'mndwi,ndwi,ndwi2'
SCRIPT_PATH = '/usr/local/worsica_web_products'
TEST_FOLDER_NAME = 'unit_tests_files'
TEST_FOLDER_PATH = SCRIPT_PATH + '/' + TEST_FOLDER_NAME


LIST_OF_ACCESSIBLE_FILE_PATHS = {
    'resampled': [
        # unable to compare due to the timestamps
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_resampled.tif', 'ph1'],
    ],
    '.': [
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_RGB.tif', 'ph1'],
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_#WATERINDEX#.tif', 'ph2'],
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_#WATERINDEX#_auto_threshold_val.txt', 'ph3'],
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_#WATERINDEX#_binary.tif', 'ph3'],
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_#WATERINDEX#_binary_closing_edge_detection.tif', 'ph4'],
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_#WATERINDEX#.shp', 'ph5'],
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_#WATERINDEX#.shx', 'ph5'],
        [IMAGESET_NAME_NO_ZIP_EXTENSION + '_#WATERINDEX#.prj', 'ph5'],
    ]
}


def list_file_paths_by_phase(phase):
    '''
    list the files (paths) available by a phase to be taken in account
    '''
    files_by_phase = {}
    for folder, list_files in LIST_OF_ACCESSIBLE_FILE_PATHS.items():
        for file in list_files:
            if file[1] == phase:
                if folder not in files_by_phase:
                    files_by_phase[folder] = []
                files_by_phase[folder].append(file[0])
    return files_by_phase


def _compare_images(originalfile, testfile):
    '''
    a simpler way to compare the tif images, by checking its pixels
    '''
    ds_original = gdal.Open(originalfile)
    ds_test = gdal.Open(testfile)
    r_original = np.array(ds_original.ReadAsArray())
    r_test = np.array(ds_test.ReadAsArray())
    return np.array_equal(r_original, r_test)


def _00_check_requirements():
    '''
    check requirements needed to run the processing script and its tests
    '''
    print('test 00: check requirements needed to run the processing script and its tests')

    worsica_common_script_functions.check_condition(
        TEST_FOLDER_PATH + ' exists?', os.path.exists(TEST_FOLDER_PATH))
    worsica_common_script_functions.check_condition(
        IMAGESET_NAME_NO_ZIP_EXTENSION +
        ' exist to run these tests?',
        os.path.exists(
            TEST_FOLDER_PATH +
            '/' +
            IMAGESET_NAME_NO_ZIP_EXTENSION +
            '.zip'))

    for folder, list_files in LIST_OF_ACCESSIBLE_FILE_PATHS.items():
        for file in list_files:
            if '#WATERINDEX#' in file[0]:
                for wi, thr in zip(WATER_INDEX.split(','), WI_THRESHOLD.split(',')):
                    f0 = file[0].replace('#WATERINDEX#', wi)
                    if wi + '_auto_threshold_val.txt' in f0:
                        if thr == 'AUTO':
                            worsica_common_script_functions.check_condition(
                                './' + folder + '/original_' + f0 + ' exists?',
                                os.path.exists(TEST_FOLDER_PATH + '/' + folder + '/original_' + f0)
                            )
                    else:
                        worsica_common_script_functions.check_condition(
                            './' + folder + '/original_' + f0 + ' exists?',
                            os.path.exists(TEST_FOLDER_PATH + '/' + folder + '/original_' + f0)
                        )
            else:
                worsica_common_script_functions.check_condition(
                    './' + folder + '/original_' + file[0] + ' exists?',
                    os.path.exists(TEST_FOLDER_PATH + '/' + folder + '/original_' + file[0])
                )

    _01_check_ph1_resample_output()


def _01_check_ph1_resample_output():
    '''
    check outputs generated in the resample
    '''
    print('test 01: check outputs generated in the resample')

    print('---------------------------------------------')
    print('-- 1) Resampling+Crop+RGB for . (' + ROI_POLYGON + ') --')
    print('---------------------------------------------')

    list_file_paths = list_file_paths_by_phase('ph1')
    for folder, filepaths in list_file_paths.items():
        for path in filepaths:
            print(path)
            if '/' in path and os.path.isdir(TEST_FOLDER_PATH + '/' +
                                             folder + '/' + path):  # check if its a folder
                print('check existing and remove subfolder ' +
                      TEST_FOLDER_PATH + '/' + folder + '/' + path)
                # if(os.path.exists(TEST_FOLDER_PATH+'/'+folder+'/'+path)):
                shutil.rmtree(TEST_FOLDER_PATH + '/' + folder + '/' + path)
            else:
                print(
                    'check existing and remove file ' +
                    TEST_FOLDER_PATH +
                    '/' +
                    folder +
                    '/' +
                    path)
                worsica_common_script_functions.search_and_remove_files(
                    [TEST_FOLDER_PATH + '/' + folder + '/' + path])

    worsica_common_script_functions.search_and_remove_files(
        [WORKSPACE_PATH + '/./' + IMAGESET_NAME_NO_ZIP_EXTENSION + '_RGB.tif'])
    bbox = worsica_common_script_functions.generate_bbox_from_wkt(str(ROI_POLYGON))
    procDict = [{'imgZip': IMAGESET_NAME_NO_ZIP_EXTENSION + '.zip',
                 'path': os.getcwd() + '/.',
                 'projWinArgs': {'projWinSRS': 'EPSG:4326',
                                 'projWin': bbox},
                 'bands': 'auto'}]
    worsica_ph1_resample_crop_rgb.run_resample_rgb(procDict)

    # dim file is not easily comparable, since it generates a timestamp on the metadata to mark the time when the processing started
    # instead compare files for each .data folder in resample
    for folder, filepaths in list_file_paths.items():
        for path in filepaths:
            if '/' in path and os.path.isdir(TEST_FOLDER_PATH + '/' +
                                             folder + '/' + path):  # check if its a folder
                compared = filecmp.dircmp(
                    TEST_FOLDER_PATH + '/' + folder + '/original_' + path,
                    TEST_FOLDER_PATH + '/' + folder + '/' + path
                )
                compared.report_full_closure()
                worsica_common_script_functions.check_condition(
                    'compare ' + '/' + folder + '/original_' + path + ' - ' + '/' + folder + '/' + path,
                    not (
                        compared.left_only or compared.right_only or compared.diff_files or compared.funny_files)
                )
                filecmp.clear_cache()

    for wi, thr in zip(WATER_INDEX.split(','), WI_THRESHOLD.split(',')):
        print('Processing ' + wi + ' now!')
        _02_check_ph2_waterindex_output(wi, thr)

    print('Finished all the tests!')


def _02_check_ph2_waterindex_output(wi, thr):
    '''
    check outputs generated for a Water Index
    '''
    print('test 02: check outputs generated in the ' + wi)

    print('---------------------------------------------')
    print('-- 2) Start processing ' + wi + ' WATER INDEX--')
    print('---------------------------------------------')

    list_file_paths = list_file_paths_by_phase('ph2')
    for folder, files in list_file_paths.items():
        for file in files:
            file = file.replace('#WATERINDEX#', wi)
            print('check existing and remove file ' + TEST_FOLDER_PATH + '/' + folder + '/' + file)
            worsica_common_script_functions.search_and_remove_files(
                [TEST_FOLDER_PATH + '/' + folder + '/' + file])
    worsica_common_script_functions.search_and_remove_files(
        [WORKSPACE_PATH + '/./' + IMAGESET_NAME_NO_ZIP_EXTENSION + '_' + wi + '.tif'])
    worsica_waterIndexes.worsicaWaterIndexes(
        WORKSPACE_PATH +
        '/./resampled/' +
        IMAGESET_NAME_NO_ZIP_EXTENSION +
        '_resampled.tif',
        wi.upper(),
        os.getcwd() +
        '/.')

    for folder, files in list_file_paths.items():
        for file in files:
            file = file.replace('#WATERINDEX#', wi)
            worsica_common_script_functions.check_condition(
                'compare ' + '/' + folder + '/original_' + file + ' - ' + '/' + folder + '/' + file,
                _compare_images(
                    TEST_FOLDER_PATH + '/' + folder + '/original_' + file,
                    TEST_FOLDER_PATH + '/' + folder + '/' + file)
            )
    _03_check_ph3_waterindex_threshold_output(wi, thr)


def _03_check_ph3_waterindex_threshold_output(wi, thr):
    '''
    check threshold application
    '''
    print('test 03: check threshold application')
    print('---------------------------------------------')
    print('-- 3) Apply threshold ' + str(thr) + ' on ' + wi +
          ' for . (' + IMAGESET_NAME_NO_ZIP_EXTENSION + ')--')
    print('---------------------------------------------')
    list_file_paths = list_file_paths_by_phase('ph3')
    for folder, files in list_file_paths.items():
        for file in files:
            file = file.replace('#WATERINDEX#', wi)
            print('check existing and remove file ' + TEST_FOLDER_PATH + '/' + folder + '/' + file)
            worsica_common_script_functions.search_and_remove_files(
                [TEST_FOLDER_PATH + '/' + folder + '/' + file])
    if (thr == 'AUTO'):
        print('Calculating threshold...')
        thr = worsica_automaticThreshold.worsicaAutomaticThreshold(
            WORKSPACE_PATH + '/./' + IMAGESET_NAME_NO_ZIP_EXTENSION + '_' + wi + '.tif')
        # create file
        with open(WORKSPACE_PATH + '/./' + IMAGESET_NAME_NO_ZIP_EXTENSION + '_' + wi + '_auto_threshold_val.txt', 'w') as f:
            f.write(str(thr))
        print('Finished, threshold is ' + str(thr))
    worsica_common_script_functions.search_and_remove_files(
        [WORKSPACE_PATH + '/./' + IMAGESET_NAME_NO_ZIP_EXTENSION + '_' + wi + '_binary.tif'])
    worsica_waterIndexes.worsicaApplyWaterIndexesThreshold(
        WORKSPACE_PATH +
        '/./' +
        IMAGESET_NAME_NO_ZIP_EXTENSION +
        '_' +
        wi +
        '.tif',
        float(thr),
        os.getcwd() +
        '/.')
    for folder, files in list_file_paths.items():
        for file in files:
            file = file.replace('#WATERINDEX#', wi)
            if wi + '_auto_threshold_val.txt' in file:
                if thr == 'AUTO':
                    worsica_common_script_functions.check_condition(
                        'compare ' + TEST_FOLDER_PATH + '/' + folder + '/original_' +
                        file + ' - ' + TEST_FOLDER_PATH + '/' + folder + '/' + file,
                        filecmp.cmp(
                            TEST_FOLDER_PATH + '/' + folder + '/original_' + file,
                            TEST_FOLDER_PATH + '/' + folder + '/' + file, shallow=False)
                    )
                    filecmp.clear_cache()
            elif '.tif' in file:
                worsica_common_script_functions.check_condition(
                    'compare ' + '/' + folder + '/original_' + file + ' - ' + '/' + folder + '/' + file,
                    _compare_images(
                        TEST_FOLDER_PATH + '/' + folder + '/original_' + file,
                        TEST_FOLDER_PATH + '/' + folder + '/' + file)
                )

    _04_check_ph4_waterindex_binary_output(wi)


def _04_check_ph4_waterindex_binary_output(wi):
    '''
    check edge detection
    '''
    print('test 04: check edge detection')
    print('---------------------------------------------')
    print('-- 4) Start ' + wi + ' edge detection for . (' + ROI_POLYGON + ')--')
    print('---------------------------------------------')
    list_file_paths = list_file_paths_by_phase('ph4')
    for folder, files in list_file_paths.items():
        for file in files:
            file = file.replace('#WATERINDEX#', wi)
            print('check existing and remove file ' + TEST_FOLDER_PATH + '/' + folder + '/' + file)
            worsica_common_script_functions.search_and_remove_files(
                [TEST_FOLDER_PATH + '/' + folder + '/' + file])
    # replace WORKSPACE_PATH by a dot
    worsica_common_script_functions.search_and_remove_files(
        [
            '././' +
            IMAGESET_NAME_NO_ZIP_EXTENSION +
            '_' +
            wi +
            '_binary_closing.tif',
            '././' +
            IMAGESET_NAME_NO_ZIP_EXTENSION +
            '_' +
            wi +
            '_binary_closing_edge_detection.tif'])
    worsica_ph5_edge_detection.run_cleanup_edge_detection(
        '././' + IMAGESET_NAME_NO_ZIP_EXTENSION + '_' + wi + '_binary.tif')
    for folder, files in list_file_paths.items():
        for file in files:
            file = file.replace('#WATERINDEX#', wi)
            if '.tif' in file:
                worsica_common_script_functions.check_condition(
                    'compare ' + '/' + folder + '/original_' + file + ' - ' + '/' + folder + '/' + file,
                    _compare_images(
                        TEST_FOLDER_PATH + '/' + folder + '/original_' + file,
                        TEST_FOLDER_PATH + '/' + folder + '/' + file)
                )

    _05_check_ph5_vectorization_output(wi)


def _05_check_ph5_vectorization_output(wi):
    '''
    check outputs generated in the vectorization
    '''
    print('test 05: check outputs generated in the vectorization')
    print('---------------------------------------------')
    print('-- 5) Start ' + wi + ' vectorization for ' +
          TEST_FOLDER_NAME + ' (' + ROI_POLYGON + ')--')
    print('---------------------------------------------')
    list_file_paths = list_file_paths_by_phase('ph5')
    for folder, files in list_file_paths.items():
        for file in files:
            file = file.replace('#WATERINDEX#', wi)
            print('check existing and remove file ' + TEST_FOLDER_PATH + '/' + folder + '/' + file)
            worsica_common_script_functions.search_and_remove_files(
                [TEST_FOLDER_PATH + '/' + folder + '/' + file])
    # instead of absolute path, give the relative path.
    # workaround: Since we are running this INSIDE of unit_tests_paths, we must point it to here
    worsica_ph6_vectorization.run_multiline_string_vectorization(
        '././' +
        IMAGESET_NAME_NO_ZIP_EXTENSION +
        '_' +
        wi +
        '_binary_closing_edge_detection.tif',
        '././' +
        IMAGESET_NAME_NO_ZIP_EXTENSION +
        '_' +
        wi +
        '.shp',
        1)  # white line

    for folder, files in list_file_paths.items():
        for file in files:
            file = file.replace('#WATERINDEX#', wi)
            if '.dbf' not in file:  # binaries are harder to compare
                worsica_common_script_functions.check_condition(
                    'compare ' + TEST_FOLDER_PATH + '/' + folder + '/original_' +
                    file + ' - ' + TEST_FOLDER_PATH + '/' + folder + '/' + file,
                    filecmp.cmp(
                        TEST_FOLDER_PATH + '/' + folder + '/original_' + file,
                        TEST_FOLDER_PATH + '/' + folder + '/' + file, shallow=False)
                )
                filecmp.clear_cache()


def test_start():
    '''
    this function is to allow pytest run the test (since has the test_ prefix, assumes it as a test)
    '''
    _00_check_requirements()


# Usage: ./worsica_unit_tests.py
# e.g: ./worsica_unit_tests.py
if __name__ == '__main__':
    WORKSPACE_PATH = os.getcwd()
    if '/unit_tests_files' in WORKSPACE_PATH:
        test_start()
    else:
        print('Error: You must run this script inside unit_tests_files folder in order to run this script!')
