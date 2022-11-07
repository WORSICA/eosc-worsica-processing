#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ========================================================================
# File:   worsica_ph1_resample_crop_rgb.py
# This script is based on worsica-resampling.py created by Alberto Azevedo
#
# Main diferences between this one and the original are:
# 1- This script already applies Resampling and RGB, in one step.
# 2- This script already crops the imageset according to WKT the user provides
#    (and this script automatically converts WKT to boundingbox)
# 3- This script uses a different file structure from the original
#     (but later this needs to be refined)
# -----------------------------------------------------------------------
# Log:
# October 20, 2020: Applied some fixes from the worsica_resampling.py to here
# September 22, 2020: Initial version
# ========================================================================
__author__ = 'Ricardo Martins (original author: Alberto Azevedo)'
__doc__ = "Script to resample Sentinel 2 images to 10 m resolution"
__datetime__ = '& September 2020 &'
__email__ = 'rjmartins (original author: aazevedo@lnec.pt)'
# ========================================================================

import os
import gdal
import ogr
from pathlib import Path
from glob import glob
import numpy as np
import argparse
from multiprocessing import cpu_count
import shutil
import traceback
import zipfile


import worsica_common_script_functions

projWinArgs = None


def get_top_level_safe_dir(imgZip):
    print('[get_top_level_safe_dir] Get .SAFE dir in ' + imgZip)
    try:
        folderNameSAFE = None
        with zipfile.ZipFile(imgZip) as f:
            finfolist = f.infolist()
            if (len(finfolist) > 0):
                for info in finfolist:
                    info_fn_split = info.filename.split('/')
                    if (len(info_fn_split) > 0):
                        if info_fn_split[0].endswith(".SAFE"):
                            print('[get_top_level_safe_dir] found ' + info_fn_split[0])
                            folderNameSAFE = info_fn_split[0]
                            print('[get_top_level_safe_dir] OK')
                            break
        return folderNameSAFE
    except Exception as e:
        raise Exception('Error on getting SAFE name! Not found!!')


def get_top_level_tif_file(imgZip):
    print('[get_top_level_tif_file] Get .TIF file in ' + imgZip)
    try:
        fileNameTIF = None
        with zipfile.ZipFile(imgZip) as f:
            finfolist = f.infolist()
            if (len(finfolist) > 0):
                for info in finfolist:
                    if '__MACOSX' not in info.filename:  # do not search tif under __MACOSX
                        info_fn_split = info.filename.split('/')
                        if (len(info_fn_split) > 0):
                            if info_fn_split[-1].endswith(".tif"):
                                print('[get_top_level_tif_file] found ' + info_fn_split[-1])
                                fileNameTIF = info_fn_split[-1]
                                print('[get_top_level_tif_file] OK')
                                break
        return fileNameTIF
    except Exception as e:
        raise Exception('Error on getting TIF filename! Not found!!')


def refitProjWin(ds1, projWin):
    print('refitProjWin')
    gt = ds1.GetGeoTransform()
    maxH, maxW = ds1.RasterYSize, ds1.RasterXSize
    ulx = gt[0]
    uly = gt[3]
    lrx = gt[0] + maxW * gt[1]
    lry = gt[3] + maxH * gt[5]
    print('raster')
    print([ulx, uly, lrx, lry])
    # check intersection
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(ulx, uly)
    ring.AddPoint(ulx, lry)
    ring.AddPoint(lrx, uly)
    ring.AddPoint(lrx, lry)
    ring.AddPoint(ulx, uly)
    rasterGeometry = ogr.Geometry(ogr.wkbPolygon)
    rasterGeometry.AddGeometry(ring)
    print('polygon')
    print(projWin)
    ulx2 = projWin[0]
    uly2 = projWin[1]
    lrx2 = projWin[2]
    lry2 = projWin[3]
    ring2 = ogr.Geometry(ogr.wkbLinearRing)
    ring2.AddPoint(ulx2, uly2)
    ring2.AddPoint(ulx2, lry2)
    ring2.AddPoint(lrx2, uly2)
    ring2.AddPoint(lrx2, lry2)
    ring2.AddPoint(ulx2, uly2)
    rasterGeometry2 = ogr.Geometry(ogr.wkbPolygon)
    rasterGeometry2.AddGeometry(ring2)
    if rasterGeometry2.Intersects(rasterGeometry):
        print('Intersect!')
        ulx2 = max(ulx, projWin[0])
        uly2 = min(uly, projWin[1])
        lrx2 = min(lrx, projWin[2])
        lry2 = max(lry, projWin[3])
        return ulx2, uly2, lrx2, lry2
    else:
        print('Does not insersect!')
        return None, None, None, None
# -----------------
# RUN RESAMPLING AND RGB
# -----------------


def worsicaResamplingRGB(procDicts):
    worsicaResampling(procDicts, 'rgb')


def worsicaRGB(imgZip, procDict, fileLista, actual_path):
    print('worsicaRGB')
    try:
        BandsRGB = {}
        if 'uploaded-user' in imgZip:  # if its an uploaded file
            # if has set bands: 'redband=1;greenband=2;blueband=3;nirband=4'
            if 'bands' in procDict and procDict['bands'] != "auto":
                bands = procDict['bands'].replace('band', '')  # 'red=1;green=2;blue=3;nir=4'
                bands = bands.replace(
                    'red',
                    'R').replace(
                    'green',
                    'G').replace(
                    'blue',
                    'B').replace(
                    'nir',
                    'NIR')  # 'R=1;G=2;B=3;NIR=4'
                bandsList = bands.split(';')  # ['R=1', 'G=2', 'B=3', 'NIR=4']
                tifFile = get_top_level_tif_file(imgZip)
                ds3 = gdal.Open(actual_path + "/resampled/" + tifFile[:-4] + "_resampled.tif")
                for bL in bandsList:
                    b = bL.split('=')
                    ds3b = ds3.GetRasterBand(int(b[1]))
                    BandsRGB[b[0]] = ds3b.GetDataset()
                    print('Loaded ' + b[0] + ' as band ' + str(b[1]))
                fout2 = actual_path + "/resampled/" + tifFile[:-4] + "_RGB.tif"
                print(fout2)
                projWinArgs = procDict['projWinArgs']
                ulx2, uly2, lrx2, lry2 = refitProjWin(ds3, projWinArgs['projWin'])
                outputBounds = (min(ulx2, lrx2), min(uly2, lry2), max(ulx2, lrx2), max(uly2, lry2))
                print(outputBounds)
                vrt_options = gdal.BuildVRTOptions(
                    outputBounds=outputBounds, separate=True, hideNodata=True)
                gdal.BuildVRT(actual_path + '/auxRGB/auxRGB.vrt',
                              [BandsRGB['R'], BandsRGB['G'], BandsRGB['B']], options=vrt_options)
                ds2 = gdal.Open(actual_path + '/auxRGB/auxRGB.vrt')
                NUM_THREADS = str(cpu_count())
                print('NUM_THREADS=' + NUM_THREADS)
                ds2 = gdal.Translate(
                    fout2,
                    ds2,
                    creationOptions=[
                        "NUM_THREADS=" +
                        NUM_THREADS,
                        "COMPRESS=LZW",
                        "PREDICTOR=2",
                        "TILED=YES"])
                ds2 = None
            else:
                raise Exception('Error: No bands list set for an uploaded file!')
        else:
            if 'L2A' in imgZip:
                l10JP2 = [
                    i for i in fileLista if (
                        i.endswith("B02_10m.jp2") or i.endswith("B03_10m.jp2") or i.endswith("B04_10m.jp2"))]
            elif 'L1C' in imgZip:
                l10JP2 = [
                    i for i in fileLista if (
                        i.endswith("B02.jp2") or i.endswith("B03.jp2") or i.endswith("B04.jp2"))]
            l1020 = l10JP2
            pathAux = Path(actual_path) / 'auxResample'
            pathAux.mkdir(exist_ok=True)
            for img in l1020:
                fout = "".join((str(pathAux), "/", img.split("SAFE")
                               [0][:-1], img.split("/")[-1][-12:-4], ".tif"))
                fout2 = actual_path + "/" + "_".join((img.split("SAFE")[0][:-1], "RGB.tif"))
                if "B02" in fout:  # "B02_10m"
                    BandsRGB["B"] = fout
                elif "B03" in fout:  # "B03_10m"
                    BandsRGB["G"] = fout
                elif "B04" in fout:  # "B04_10m"
                    BandsRGB["R"] = fout

            vrt_options = gdal.BuildVRTOptions(separate=True, hideNodata=True)
            gdal.BuildVRT(actual_path + '/auxRGB/auxRGB.vrt',
                          [BandsRGB['R'], BandsRGB['G'], BandsRGB['B']], options=vrt_options)
            ds2 = gdal.Open(actual_path + '/auxRGB/auxRGB.vrt')
            ds2 = gdal.Translate(fout2, ds2, outputType=gdal.GDT_Float32)
            ds2 = None

        print(f"{fout2} :: Done!!!")
        # return None
    except Exception as e:
        print(traceback.format_exc())
        exit(1)

# -----------------
# RUN ONLY RESAMPLING
# -----------------


def worsicaResampling(procDicts, mode='normal'):
    for procDict in procDicts:
        try:
            imgZip = procDict['imgZip']
            projWinArgs = procDict['projWinArgs']

            if ('path' in procDict):
                ACTUAL_PATH = procDict['path']
            else:
                ACTUAL_PATH = os.getcwd()

            print(ACTUAL_PATH)
            BandsRGB = {}
            print(procDict['bands'])
            if 'uploaded-user' in imgZip:  # if its an uploaded file
                # if has set bands: 'redband=1;greenband=2;blueband=3;nirband=4'
                if 'bands' in procDict and procDict['bands'] != "auto":
                    foutFiles = []
                    unzipcmd = worsica_common_script_functions._run_unzip(imgZip, ACTUAL_PATH)
                    if unzipcmd != 0:
                        print('Error on unzip! Corrupt file!!')
                        raise Exception('Error on unzip! Corrupt file!!')
                    bands = procDict['bands'].replace('band', '')  # 'red=1;green=2;blue=3;nir=4'
                    bands = bands.replace(
                        'red',
                        'R').replace(
                        'green',
                        'G').replace(
                        'blue',
                        'B').replace(
                        'nir',
                        'NIR')  # 'R=1;G=2;B=3;NIR=4'
                    bandsList = bands.split(';')  # ['R=1', 'G=2', 'B=3', 'NIR=4']
                    tifFile = get_top_level_tif_file(imgZip)
                    fileLista = [ACTUAL_PATH + '/' + tifFile]
                    foutFiles.append(ACTUAL_PATH + '/' + tifFile)
                    ds3 = gdal.Open(ACTUAL_PATH + '/' + tifFile)
                    # This step is REQUIRED in order to provide the correct output on the visualization.
                    # The wrap is used to convert the imageset from any EPSG to EPSG:4326
                    print('gdal.warp')
                    fout_wrap = ACTUAL_PATH + "/auxResample/" + "_".join((tifFile[:-4], "wrap.tif"))
                    print(fout_wrap)
                    foutFiles.append(fout_wrap)
                    ds1 = gdal.Warp(
                        fout_wrap,
                        ds3,
                        srcNodata=-32767,
                        dstNodata=0,
                        dstSRS=projWinArgs['projWinSRS'],
                        format='GTiff',
                        multithread=True,
                        outputType=gdal.GDT_Float32)
                    ds3 = None
                    # refit projwin according to the raster extent
                    ulx2, uly2, lrx2, lry2 = refitProjWin(ds1, projWinArgs['projWin'])
                    projWin = [ulx2, uly2, lrx2, lry2]
                    print(projWin)
                    NUM_THREADS = str(cpu_count())
                    print('NUM_THREADS=' + NUM_THREADS)
                    ds3 = gdal.Open(fout_wrap, gdal.GA_Update)
                    ds1 = None
                    BandsRGBTranslate = {}
                    for bL in bandsList:
                        b = bL.split('=')
                        ds3b = ds3.GetRasterBand(int(b[1]))
                        BandsRGB[b[0]] = ds3b.GetDataset()
                        BandsRGBTranslate[b[0]] = int(b[1])
                        print('Loaded ' + b[0] + ' as band ' + str(b[1]))
                    BandsLTranslate = [
                            BandsRGBTranslate['B'],
                            BandsRGBTranslate['G'],
                            BandsRGBTranslate['R'],
                            BandsRGBTranslate['NIR']]
                    # no SWIR1 and SWIR2
                    fout2 = ACTUAL_PATH + "/resampled/" + "_".join((tifFile[:-4], "resampled.tif"))
                    print(fout2)
                    Metadata = ds3.GetMetadata()
                    Description = ds3.GetDescription()
                    print('gdal.buildVRT')
                    outputBounds = (min(ulx2, lrx2), min(uly2, lry2),
                                    max(ulx2, lrx2), max(uly2, lry2))
                    print(outputBounds)
                    vrt_options = gdal.BuildVRTOptions(
                        outputBounds=outputBounds, separate=False, hideNodata=True)
                    gdal.BuildVRT(ACTUAL_PATH + '/auxResample/aux.vrt',
                                  [BandsRGB['B'],
                                   BandsRGB['G'],
                                      BandsRGB['R'],
                                      BandsRGB['NIR']],
                                  options=vrt_options)
                    ds2 = gdal.Open(ACTUAL_PATH + '/auxResample/aux.vrt')
                    print(BandsLTranslate)
                    ds2 = gdal.Translate(
                        fout2,
                        ds2,
                        bandList=BandsLTranslate,
                        creationOptions=[
                            "NUM_THREADS=" +
                            NUM_THREADS,
                            "COMPRESS=LZW",
                            "PREDICTOR=2",
                            "TILED=YES"])
                    ds2 = None
                    print('Update statistics...')
                    ds3 = gdal.Open(fout2, gdal.GA_Update)
                    for bL in bandsList:
                        b = bL.split('=')
                        band = ds3.GetRasterBand(int(b[1]))
                        band.ComputeStatistics(0)
                        band.FlushCache()
                        band = None
                        print('Updated stats for band ' + str(b[1]))
                    ds3.FlushCache()
                    ds3 = None
                else:
                    raise Exception('Error: No bands list set for an uploaded file!')
            else:
                unzipcmd = worsica_common_script_functions._run_unzip(imgZip)
                print(unzipcmd)
                if unzipcmd != 0:
                    print('Error on unzip! Corrupt file!!')
                    raise Exception('Error on unzip! Corrupt file!!')
                fileLista = []
                getSAFEFolderName = get_top_level_safe_dir(imgZip)  # f"{imgZip[:-4]}.SAFE"
                for root, dirs, files in os.walk(getSAFEFolderName, topdown=True):
                    for name in files:
                        fileLista.append(os.path.join(root, name))
                    for name in dirs:
                        fileLista.append(os.path.join(root, name))
                if 'L2A' in imgZip:
                    l10JP2 = [i for i in fileLista if (i.endswith("B02_10m.jp2") or i.endswith(
                        "B03_10m.jp2") or i.endswith("B04_10m.jp2") or i.endswith("B08_10m.jp2"))]
                    l20JP2 = [i for i in fileLista if i.endswith(
                        "B11_20m.jp2") or i.endswith("B12_20m.jp2")]
                elif 'L1C' in imgZip:
                    l10JP2 = [i for i in fileLista if (i.endswith("B02.jp2") or i.endswith(
                        "B03.jp2") or i.endswith("B04.jp2") or i.endswith("B08.jp2"))]
                    l20JP2 = [
                        i for i in fileLista if (
                            i.endswith("B11.jp2") or i.endswith("B12.jp2"))]
                l1020 = l10JP2 + l20JP2
                foutFiles = []
                for img in l1020:
                    fout = "".join((ACTUAL_PATH + "/auxResample/", img.split("SAFE")
                                   [0][:-1], img.split("/")[-1][-12:-4], ".tif"))
                    fout2 = ACTUAL_PATH + "/resampled/" + \
                        "_".join((img.split("SAFE")[0][:-1], "resampled.tif"))
                    foutFiles.append(fout)
                    fout_wrap = "".join((ACTUAL_PATH + "/auxResample/", img.split("SAFE")
                                        [0][:-1], img.split("/")[-1][-12:-4], "_wrap.tif"))
                    foutFiles.append(fout_wrap)

                    ds = gdal.Open(img, gdal.GA_Update)
                    band = ds.GetRasterBand(1)
                    arr = band.ReadAsArray()
                    [cols, rows] = arr.shape
                    Metadata = ds.GetMetadata()
                    GCPs = ds.GetGCPs()
                    GCPsProj = ds.GetGCPProjection()
                    geotransform = ds.GetGeoTransform()
                    Description = ds.GetDescription()
                    #
                    arr2 = np.where(arr < 0, 0, arr)
                    band.WriteArray(arr2)
                    band.SetNoDataValue(0)
                    ds.FlushCache()

                    # This step is REQUIRED in order to provide the correct output on the visualization.
                    # The wrap is used to convert the imageset from any EPSG to EPSG:4326
                    print('gdal.warp')
                    ds1 = gdal.Warp(
                        fout_wrap,
                        ds,
                        dstSRS=projWinArgs['projWinSRS'],
                        format='GTiff',
                        multithread=True,
                        outputType=gdal.GDT_Float32)
                    # The translate is required to crop the imageset according to the ROI
                    print('gdal.translate')
                    gdal.Translate(
                        fout,
                        ds1,
                        format="GTiff",
                        resampleAlg='cubic',
                        outputType=gdal.GDT_Float32,
                        projWinSRS=projWinArgs['projWinSRS'],
                        projWin=projWinArgs['projWin'])
                    ds = None
                    ds1 = None

                    if "B02" in fout:  # "B02_10m"
                        BandsRGB["B"] = fout
                        print(str(fout))
                    elif "B03" in fout:  # "B03_10m"
                        BandsRGB["G"] = fout
                        print(str(fout))
                    elif "B04" in fout:  # "B04_10m"
                        BandsRGB["R"] = fout
                        print(str(fout))
                    elif "B08" in fout:  # "B08_10m"
                        BandsRGB["NIR"] = fout
                        print(str(fout))
                    elif "B11" in fout:  # "B11_20m"
                        BandsRGB["SWIR1"] = fout
                        print(str(fout))
                    elif "B12" in fout:  # "B12_20m"
                        BandsRGB["SWIR2"] = fout
                        print(str(fout))
                print(BandsRGB)

                vrt_options = gdal.BuildVRTOptions(separate=True, hideNodata=True)
                gdal.BuildVRT(ACTUAL_PATH + '/auxResample/aux.vrt',
                              [BandsRGB['B'],
                               BandsRGB['G'],
                                  BandsRGB['R'],
                                  BandsRGB['NIR'],
                                  BandsRGB['SWIR1'],
                                  BandsRGB['SWIR2']],
                              options=vrt_options)
                ds2 = gdal.Open(ACTUAL_PATH + '/auxResample/aux.vrt')
                ds2 = gdal.Translate(fout2, ds2)
                ds2 = None

            dsOut = gdal.Open(fout2)
            dsOut.SetMetadata(Metadata)
            dsOut.SetDescription(Description)
            dsOut.GetRasterBand(1).SetDescription('Blue')
            dsOut.GetRasterBand(2).SetDescription('Green')
            dsOut.GetRasterBand(3).SetDescription('Red')
            dsOut.GetRasterBand(4).SetDescription('NIR')
            if 'uploaded-user' in imgZip:  # if its an uploaded file
                print('Skip: No description for swir1 and swir2')
            else:
                dsOut.GetRasterBand(5).SetDescription('SWIR1')
                dsOut.GetRasterBand(6).SetDescription('SWIR2')
            dsOut = None

            if mode == 'rgb':
                worsicaRGB(imgZip, procDict, fileLista, ACTUAL_PATH)

            foutFiles.append(ACTUAL_PATH + "/auxResample/aux.vrt")
            for trash in foutFiles:
                os.remove(trash)
            if 'uploaded-user' in imgZip:
                pass
            else:
                fDelete = getSAFEFolderName
                shutil.rmtree(f"{fDelete}")
            print(f"{fout2} :: Done!!!")
            return None
        except Exception as e:
            print(traceback.format_exc())
            exit(1)

# -----------------
# RUN ONLY RESAMPLING WATER LEAK
# DIFFERENCE: Apply cloud removal to the resample
# WARNING: DO NOT USE IT FOR L1C
# -----------------


def worsicaResamplingWaterLeakRGB(procDicts):
    for procDict in procDicts:
        try:
            imgZip = procDict['imgZip']
            projWinArgs = procDict['projWinArgs']

            if ('path' in procDict):
                ACTUAL_PATH = procDict['path']
            else:
                ACTUAL_PATH = os.getcwd()

            unzipcmd = worsica_common_script_functions._run_unzip(imgZip)
            if unzipcmd != 0:
                print('Error on unzip! Corrupt file!!')
                raise Exception('Error on unzip! Corrupt file!!')

            fileLista = []
            getSAFEFolderName = get_top_level_safe_dir(imgZip)  # f"{imgZip[:-4]}.SAFE"
            for root, dirs, files in os.walk(getSAFEFolderName, topdown=True):
                for name in files:
                    fileLista.append(os.path.join(root, name))
                for name in dirs:
                    fileLista.append(os.path.join(root, name))
            if 'L2A' in imgZip:
                l10JP2 = [i for i in fileLista if (i.endswith("B02_10m.jp2") or i.endswith(
                    "B03_10m.jp2") or i.endswith("B04_10m.jp2") or i.endswith("B08_10m.jp2"))]
                l20JP2 = [
                    i for i in fileLista if (
                        i.endswith("B11_20m.jp2") or i.endswith("B12_20m.jp2") or i.endswith("SCL_20m.jp2"))]
            elif 'L1C' in imgZip:
                l10JP2 = [i for i in fileLista if (i.endswith("B02.jp2") or i.endswith(
                    "B03.jp2") or i.endswith("B04.jp2") or i.endswith("B08.jp2"))]
                l20JP2 = [i for i in fileLista if (i.endswith("B11.jp2") or i.endswith("B12.jp2"))]
            l1020 = l10JP2 + l20JP2

            BandsRGB = {}
            foutFiles = []
            print('--Start resampling the images (wrap and translate)')
            for img in l1020:
                fout = "".join((ACTUAL_PATH + "/auxResample/", img.split("SAFE")
                               [0][:-1], img.split("/")[-1][-12:-4], ".tif"))
                fout2 = ACTUAL_PATH + "/resampled/" + \
                    "_".join((img.split("SAFE")[0][:-1], "resampled.tif"))
                foutFiles.append(fout)
                fout_wrap = "".join((ACTUAL_PATH + "/auxResample/", img.split("SAFE")
                                    [0][:-1], img.split("/")[-1][-12:-4], "_wrap.tif"))
                foutFiles.append(fout_wrap)

                ds = gdal.Open(img, gdal.GA_Update)
                band = ds.GetRasterBand(1)
                arr = band.ReadAsArray()
                [cols, rows] = arr.shape
                Metadata = ds.GetMetadata()
                GCPs = ds.GetGCPs()
                GCPsProj = ds.GetGCPProjection()
                geotransform = ds.GetGeoTransform()
                Description = ds.GetDescription()
                #
                arr2 = np.where(arr < 0, 0, arr)
                band.WriteArray(arr2)
                band.SetNoDataValue(0)
                ds.FlushCache()

                # This step is REQUIRED in order to provide the correct output on the visualization.
                # The wrap is used to convert the imageset from any EPSG to EPSG:4326 (projWinSRS)
                print('gdal.wrap ')
                ds1 = gdal.Warp(
                    fout_wrap,
                    ds,
                    dstSRS=projWinArgs['projWinSRS'],
                    format='GTiff',
                    multithread=True,
                    outputType=gdal.GDT_Float32)
                # The translate is required to crop the imageset according to the ROI
                print('gdal.translate ')
                gdal.Translate(
                    fout,
                    ds1,
                    format="GTiff",
                    resampleAlg='cubic',
                    outputType=gdal.GDT_Float32,
                    projWinSRS=projWinArgs['projWinSRS'],
                    projWin=projWinArgs['projWin'])
                ds = None
                ds1 = None

                if "B02" in fout:  # "B02_10m"
                    BandsRGB["B"] = fout
                elif "B03" in fout:  # "B03_10m"
                    BandsRGB["G"] = fout
                elif "B04" in fout:  # "B04_10m"
                    BandsRGB["R"] = fout
                elif "B08" in fout:  # "B08_10m"
                    BandsRGB["NIR"] = fout
                elif "B11" in fout:  # "B11_20m"
                    BandsRGB["SWIR1"] = fout
                elif "B12" in fout:  # "B12_20m"
                    BandsRGB["SWIR2"] = fout
                elif "SCL" in fout:  # "SCL_20m"
                    BandsRGB["SCL"] = fout

            print('--Convert vrt to tif')
            # hideNodata=False, srcNodata="0 0 0 0 0 0")
            vrt_options = gdal.BuildVRTOptions(separate=True, hideNodata=True)
            if 'L2A' in imgZip:
                gdal.BuildVRT(ACTUAL_PATH + '/auxResample/aux.vrt',
                              [BandsRGB['B'],
                               BandsRGB['G'],
                                  BandsRGB['R'],
                                  BandsRGB['NIR'],
                                  BandsRGB['SWIR1'],
                                  BandsRGB['SWIR2'],
                                  BandsRGB["SCL"]],
                              options=vrt_options)
            else:
                gdal.BuildVRT(ACTUAL_PATH + '/auxResample/aux.vrt',
                              [BandsRGB['B'],
                               BandsRGB['G'],
                                  BandsRGB['R'],
                                  BandsRGB['NIR'],
                                  BandsRGB['SWIR1'],
                                  BandsRGB['SWIR2']],
                              options=vrt_options)
            ds2 = gdal.Open(ACTUAL_PATH + '/auxResample/aux.vrt')
            ds2 = gdal.Translate(fout2, ds2)
            ds2 = None

            print('--Insert metadata')
            dsOut = gdal.Open(fout2)
            dsOut.SetMetadata(Metadata)
            dsOut.SetDescription(Description)
            dsOut.GetRasterBand(1).SetDescription('Blue')
            dsOut.GetRasterBand(2).SetDescription('Green')
            dsOut.GetRasterBand(3).SetDescription('Red')
            dsOut.GetRasterBand(4).SetDescription('NIR')
            dsOut.GetRasterBand(5).SetDescription('SWIR1')
            dsOut.GetRasterBand(6).SetDescription('SWIR2')
            if 'L2A' in imgZip:
                dsOut.GetRasterBand(7).SetDescription('SCL')
            dsOut = None

            # start cloud filtering
            if 'L2A' in imgZip:
                print('--Start cloud filtering')
                dsOut = gdal.Open(fout2, gdal.GA_Update)
                arrCloudMask = np.array(dsOut.GetRasterBand(7).ReadAsArray()).astype(int)
                for i in range(1, 7):
                    b = dsOut.GetRasterBand(i)
                    # 0: NODATA, 8: CLOUD_MEDIUM_PROB, 9: CLOUD_HIGH_PROB, 10: THIN_CIRRUS
                    filterClasses = [0, 8, 9, 10]
                    for f in filterClasses:
                        b.WriteArray(np.where((arrCloudMask == f), 0, b.ReadAsArray()))
                        b.SetNoDataValue(0)
                dsOut.FlushCache()
                dsOut = None

            worsicaRGB(imgZip, procDict, fileLista, ACTUAL_PATH)

            print('--Remove files')
            foutFiles.append(ACTUAL_PATH + "/auxResample/aux.vrt")
            for trash in foutFiles:
                os.remove(trash)
            fDelete = getSAFEFolderName  # imgZip.replace(".zip", ".SAFE")
            shutil.rmtree(f"{fDelete}")
            print(f"{fout2} :: Done!!!")
            return None
        except Exception as e:
            print(traceback.format_exc())
            exit(1)


def worsicaResamplingWaterLeak(procDicts):
    for procDict in procDicts:
        try:
            imgZip = procDict['imgZip']
            projWinArgs = procDict['projWinArgs']

            if ('path' in procDict):
                ACTUAL_PATH = procDict['path']
            else:
                ACTUAL_PATH = os.getcwd()

            unzipcmd = worsica_common_script_functions._run_unzip(imgZip)
            if unzipcmd != 0:
                print('Error on unzip! Corrupt file!!')
                raise Exception('Error on unzip! Corrupt file!!')

            fileLista = []
            getSAFEFolderName = get_top_level_safe_dir(imgZip)
            for root, dirs, files in os.walk(getSAFEFolderName, topdown=True):
                for name in files:
                    fileLista.append(os.path.join(root, name))
                for name in dirs:
                    fileLista.append(os.path.join(root, name))
            if 'L2A' in imgZip:
                l10JP2 = [i for i in fileLista if (i.endswith("B02_10m.jp2") or i.endswith(
                    "B03_10m.jp2") or i.endswith("B04_10m.jp2") or i.endswith("B08_10m.jp2"))]
                l20JP2 = [
                    i for i in fileLista if (
                        i.endswith("B11_20m.jp2") or i.endswith("B12_20m.jp2") or i.endswith("SCL_20m.jp2"))]
            elif 'L1C' in imgZip:
                l10JP2 = [i for i in fileLista if (i.endswith("B02.jp2") or i.endswith(
                    "B03.jp2") or i.endswith("B04.jp2") or i.endswith("B08.jp2"))]
                l20JP2 = [i for i in fileLista if (i.endswith("B11.jp2") or i.endswith("B12.jp2"))]
            l1020 = l10JP2 + l20JP2

            BandsRGB = {}
            foutFiles = []
            print('--Start resampling the images (wrap and translate)')
            for img in l1020:
                fout = "".join((ACTUAL_PATH + "/auxResample/", img.split("SAFE")
                               [0][:-1], img.split("/")[-1][-12:-4], ".tif"))
                fout2 = ACTUAL_PATH + "/resampled/" + \
                    "_".join((img.split("SAFE")[0][:-1], "resampled.tif"))
                foutFiles.append(fout)
                fout_wrap = "".join((ACTUAL_PATH + "/auxResample/", img.split("SAFE")
                                    [0][:-1], img.split("/")[-1][-12:-4], "_wrap.tif"))
                foutFiles.append(fout_wrap)

                ds = gdal.Open(img, gdal.GA_Update)
                band = ds.GetRasterBand(1)
                arr = band.ReadAsArray()
                [cols, rows] = arr.shape
                Metadata = ds.GetMetadata()
                GCPs = ds.GetGCPs()
                GCPsProj = ds.GetGCPProjection()
                geotransform = ds.GetGeoTransform()
                Description = ds.GetDescription()
                #
                arr2 = np.where(arr < 0, 0, arr)
                band.WriteArray(arr2)
                band.SetNoDataValue(0)
                ds.FlushCache()

                # This step is REQUIRED in order to provide the correct output on the visualization.
                # The wrap is used to convert the imageset from any EPSG to EPSG:4326 (projWinSRS)
                print(str(img))
                print('gdal.wrap ')
                ds1 = gdal.Warp(
                    fout_wrap,
                    ds,
                    dstSRS=projWinArgs['projWinSRS'],
                    format='GTiff',
                    multithread=True,
                    outputType=gdal.GDT_Float32)
                # The translate is required to crop the imageset according to the ROI
                print('gdal.translate ')
                gdal.Translate(
                    fout,
                    ds1,
                    format="GTiff",
                    resampleAlg='cubic',
                    outputType=gdal.GDT_Float32,
                    projWinSRS=projWinArgs['projWinSRS'],
                    projWin=projWinArgs['projWin'])
                ds = None
                ds1 = None

                if "B02" in fout:  # "B02_10m"
                    BandsRGB["B"] = fout
                elif "B03" in fout:  # "B03_10m"
                    BandsRGB["G"] = fout
                elif "B04" in fout:  # "B04_10m"
                    BandsRGB["R"] = fout
                elif "B08" in fout:  # "B08_10m"
                    BandsRGB["NIR"] = fout
                elif "B11" in fout:  # "B11_20m"
                    BandsRGB["SWIR1"] = fout
                elif "B12" in fout:  # "B12_20m"
                    BandsRGB["SWIR2"] = fout
                elif "SCL" in fout:  # "SCL_20m"
                    BandsRGB["SCL"] = fout

            print('--Convert vrt to tif')
            # hideNodata=False, srcNodata="0 0 0 0 0 0")
            vrt_options = gdal.BuildVRTOptions(separate=True, hideNodata=True)
            if 'L2A' in imgZip:
                gdal.BuildVRT(ACTUAL_PATH + '/auxResample/aux.vrt',
                              [BandsRGB['B'],
                               BandsRGB['G'],
                                  BandsRGB['R'],
                                  BandsRGB['NIR'],
                                  BandsRGB['SWIR1'],
                                  BandsRGB['SWIR2'],
                                  BandsRGB["SCL"]],
                              options=vrt_options)
            else:
                gdal.BuildVRT(ACTUAL_PATH + '/auxResample/aux.vrt',
                              [BandsRGB['B'],
                               BandsRGB['G'],
                                  BandsRGB['R'],
                                  BandsRGB['NIR'],
                                  BandsRGB['SWIR1'],
                                  BandsRGB['SWIR2']],
                              options=vrt_options)
            ds2 = gdal.Open(ACTUAL_PATH + '/auxResample/aux.vrt')
            ds2 = gdal.Translate(fout2, ds2)
            ds2 = None

            print('--Insert metadata')
            dsOut = gdal.Open(fout2)
            dsOut.SetMetadata(Metadata)
            dsOut.SetDescription(Description)
            dsOut.GetRasterBand(1).SetDescription('Blue')
            dsOut.GetRasterBand(2).SetDescription('Green')
            dsOut.GetRasterBand(3).SetDescription('Red')
            dsOut.GetRasterBand(4).SetDescription('NIR')
            dsOut.GetRasterBand(5).SetDescription('SWIR1')
            dsOut.GetRasterBand(6).SetDescription('SWIR2')
            if 'L2A' in imgZip:
                dsOut.GetRasterBand(7).SetDescription('SCL')
            dsOut = None

            # start cloud filtering
            if 'L2A' in imgZip:
                print('--Start cloud filtering')
                dsOut = gdal.Open(fout2, gdal.GA_Update)
                arrCloudMask = np.array(dsOut.GetRasterBand(7).ReadAsArray()).astype(int)
                for i in range(1, 7):
                    b = dsOut.GetRasterBand(i)
                    # 0: NODATA, 8: CLOUD_MEDIUM_PROB, 9: CLOUD_HIGH_PROB, 10: THIN_CIRRUS
                    filterClasses = [0, 8, 9, 10]
                    for f in filterClasses:
                        b.WriteArray(np.where((arrCloudMask == f), -999, b.ReadAsArray()))
                    b.SetNoDataValue(-999)
                    b.FlushCache()
                    b = None
                dsOut.FlushCache()
                dsOut = None

            print('--Remove files')
            foutFiles.append(ACTUAL_PATH + "/auxResample/aux.vrt")
            for trash in foutFiles:
                os.remove(trash)
            fDelete = getSAFEFolderName
            shutil.rmtree(f"{fDelete}")
            print(f"{fout2} :: Done!!!")
            return None
        except Exception as e:
            print(traceback.format_exc())
            exit(1)


# ---------------
# RUN ONLY RGB FROM RESAMPLING TIF
# ---------------
def run_rgb(tifFile, ACTUAL_PATH, bandList=[3, 2, 1]):
    try:
        ds = gdal.Open(tifFile)
        filename = tifFile.split('/')[-1][:-4]

        fout2 = ACTUAL_PATH + "/" + filename + "_RGB.tif"
        NUM_THREADS = str(cpu_count())
        print('NUM_THREADS=' + NUM_THREADS)
        gdal.Translate(
            fout2,
            ds,
            format="GTiff",
            bandList=bandList,
            outputType=gdal.GDT_Float32,
            creationOptions=[
                "NUM_THREADS=" +
                NUM_THREADS,
                "COMPRESS=LZW",
                "PREDICTOR=2",
                "TILED=YES"])
        ds = None

    except Exception as e:
        print(traceback.format_exc())
        exit(1)


def getARGScmd():
    parser = argparse.ArgumentParser(
        description='worsica_resampling: Script to resample images from satellites sentinel 1/2 to 10m resolution')
    parser.add_argument(
        '-l',
        '--list',
        help='File with the name of the images to be resampled.',
        required=False)
    parser.add_argument(
        '-b',
        '--wktpolygon',
        help='WKT polygon for bounding box for subset.',
        metavar='N',
        type=str,
        nargs='+',
        required=False)
    args = parser.parse_args()
    return args


def run_resample_rgb(procDicts):
    try:
        print('run_resample_rgb')

        for procDict in procDicts:
            if ('path' in procDict):
                ACTUAL_PATH = procDict['path']
            else:
                ACTUAL_PATH = os.getcwd()

            print('ACTUAL_PATH')
            print(ACTUAL_PATH)

            if not os.path.exists(ACTUAL_PATH + '/resampled'):
                os.makedirs(ACTUAL_PATH + '/resampled', exist_ok=True)
            if not os.path.exists(ACTUAL_PATH + '/auxResample'):
                os.makedirs(ACTUAL_PATH + '/auxResample', exist_ok=True)
            if not os.path.exists(ACTUAL_PATH + '/auxRGB'):
                os.makedirs(ACTUAL_PATH + '/auxRGB', exist_ok=True)

        worsicaResamplingRGB(procDicts)
        return None
    except Exception as e:
        print(traceback.format_exc())
        exit(1)


def run_resample(procDicts):
    try:
        print('run_resample')

        for procDict in procDicts:
            if ('path' in procDict):
                ACTUAL_PATH = procDict['path']
            else:
                ACTUAL_PATH = os.getcwd()

            print('ACTUAL_PATH')
            print(ACTUAL_PATH)

            if not os.path.exists(ACTUAL_PATH + '/resampled'):
                os.makedirs(ACTUAL_PATH + '/resampled', exist_ok=True)
            if not os.path.exists(ACTUAL_PATH + '/auxResample'):
                os.makedirs(ACTUAL_PATH + '/auxResample', exist_ok=True)
            if not os.path.exists(ACTUAL_PATH + '/auxRGB'):
                os.makedirs(ACTUAL_PATH + '/auxRGB', exist_ok=True)

        worsicaResampling(procDicts)
        return None
    except Exception as e:
        print(traceback.format_exc())
        exit(1)


def run_resample_waterleak_rgb(procDicts):
    try:
        print('run_resample_waterleak_rgb')

        for procDict in procDicts:
            if ('path' in procDict):
                ACTUAL_PATH = procDict['path']
            else:
                ACTUAL_PATH = os.getcwd()

            print('ACTUAL_PATH')
            print(ACTUAL_PATH)

            if not os.path.exists(ACTUAL_PATH + '/resampled'):
                os.makedirs(ACTUAL_PATH + '/resampled', exist_ok=True)
            if not os.path.exists(ACTUAL_PATH + '/auxResample'):
                os.makedirs(ACTUAL_PATH + '/auxResample', exist_ok=True)
            if not os.path.exists(ACTUAL_PATH + '/auxRGB'):
                os.makedirs(ACTUAL_PATH + '/auxRGB', exist_ok=True)

        worsicaResamplingWaterLeakRGB(procDicts)
        return None
    except Exception as e:
        print(traceback.format_exc())
        exit(1)


def run_resample_waterleak(procDicts):
    try:
        print('run_resample_waterleak')

        for procDict in procDicts:
            if ('path' in procDict):
                ACTUAL_PATH = procDict['path']
            else:
                ACTUAL_PATH = os.getcwd()

            print('ACTUAL_PATH')
            print(ACTUAL_PATH)

            if not os.path.exists(ACTUAL_PATH + '/resampled'):
                os.makedirs(ACTUAL_PATH + '/resampled', exist_ok=True)
            if not os.path.exists(ACTUAL_PATH + '/auxResample'):
                os.makedirs(ACTUAL_PATH + '/auxResample', exist_ok=True)
            if not os.path.exists(ACTUAL_PATH + '/auxRGB'):
                os.makedirs(ACTUAL_PATH + '/auxRGB', exist_ok=True)

        worsicaResamplingWaterLeak(procDicts)
        return None
    except Exception as e:
        print(traceback.format_exc())
        exit(1)


if __name__ == '__main__':
    try:
        args = getARGScmd()
        projWinArgs = None
        if args.list:
            with open(args.list, "r") as fin:
                imgs = fin.readlines()
                imgs = [i.strip() for i in imgs]
        else:
            imgs = glob("*MSIL2A*.zip")
        if args.wktpolygon:
            # bbox = -9.28 38.68 -9.17 38.57
            bbox = worsica_common_script_functions.generate_bbox_from_wkt(str(args.wktpolygon[0]))
            projWinArgs = {'projWinSRS': 'EPSG:4326', 'projWin': bbox}

        procDicts = [{'imgZip': img, 'path': os.getcwd(), 'projWinArgs': projWinArgs}
                     for img in imgs]
        run_resample_rgb(procDicts)
    except Exception as e:
        print(traceback.format_exc())
        exit(1)
