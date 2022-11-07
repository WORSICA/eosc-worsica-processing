'''
Author: rjmartins

This python is just to list the common shareable functions available in all python scripts.
You cannot run it!
'''

import os
import subprocess
from osgeo import gdal, osr
import shlex


def _run_gdalinfo(fin, fout):
    args = ['gdalinfo', fin, '>', fout]
    return subprocess.call(args)


def _run_rm(fin):
    args = ['rm', '-f', fin]
    return subprocess.call(args)


def _run_unzip(fin, d=None):
    if d:
        args = ['unzip', '-u', fin, '-d', d]
    else:
        args = ['unzip', '-u', fin]
    return subprocess.call(args)


def _run_unzip_test(fin):
    args = ['unzip', '-t', fin]
    return subprocess.call(args)


def _run_gdalmerge(_additional_params, outputImage, inputImagesForMerge):
    cmd = 'gdal_merge.py -n 0 ' + _additional_params + ' -o ' + outputImage + ' ' + inputImagesForMerge
    COMMAND = shlex.split(cmd)
    print(str(COMMAND))
    return subprocess.Popen(COMMAND, shell=False)


def get_image_info(input_file):
    '''
    use gdal and osr to get the image information
    and store it temporarily for a new image
    '''
    img = gdal.Open(input_file)
    rows, cols = int(img.RasterYSize), int(img.RasterXSize)
    geot = img.GetGeoTransform()
    projection = osr.SpatialReference()
    projection.ImportFromWkt(img.GetProjectionRef())
    img = None
    return rows, cols, geot, projection


def generate_new_image(output_file, bands, etype, image_info):
    '''
    generate new image object file to store the array inside
    '''
    ysize, xsize, geot, projection = image_info  # cols, rows, geot, proj
    img_out = gdal.GetDriverByName('GTiff').Create(
        output_file, xsize=xsize, ysize=ysize, bands=bands, eType=etype)
    img_out.SetGeoTransform(geot)
    img_out.SetProjection(projection.ExportToWkt())
    return img_out


def run_external_app(_exec, xmlfile, args):
    '''
    bind function to run an external app by cmd line
    '''
    print(_exec + ' ' + xmlfile + ' ' + args)
    run = subprocess.run([_exec, xmlfile, args], check=False)
    check_condition(_exec + ' finished successfully?', run.returncode == 0)


def search_and_remove_files(files):
    '''
    checks if file exists and deletes
    '''
    for file in files:
        if os.path.exists(file):
            print('remove old ' + file)
            os.remove(file)


def check_condition(text, condition):
    '''
    checks if a condition is valid (true), and throws exception if not
    '''
    if condition:
        print('[OK] ' + text)
    else:
        raise Exception("[FAILED] " + text)


def generate_bbox_from_wkt(wkt_str):
    # bbox = -9.28 38.68 -9.17 38.57
    bbox = [None, None, None, None]
    wkt = wkt_str.replace('POLYGON', '').replace(' ((', '').replace(')) ', '').replace(
        '((', '').replace('))', '')  # even is there's a space between polygon and parethesis
    wkt_split = wkt.split(',')
    print(wkt_split)
    for w in wkt_split:
        latlon = w.split(' ')
        if bbox[0] is None and bbox[2] is None:
            bbox[0] = bbox[2] = float(latlon[0])
            bbox[1] = bbox[3] = float(latlon[1])
        else:
            bbox[0] = min(bbox[0], float(latlon[0]))
            bbox[1] = max(bbox[1], float(latlon[1]))
            bbox[2] = max(bbox[2], float(latlon[0]))
            bbox[3] = min(bbox[3], float(latlon[1]))
    print(bbox)
    return bbox
