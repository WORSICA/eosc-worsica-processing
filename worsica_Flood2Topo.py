#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ========================================================================
# File:   worsica-resampling.py
# ========================================================================
__author__ = 'Alberto Azevedo & Alice Fassoni'
__doc__ = "Script to calculate the topography from sentinel-2 images"
__datetime__ = '& October 2021 &'
__email__ = 'aazevedo@lnec.pt'
# This script can retrieve the tidal data from FES2014 model
# or
# The user can upload a tidal series file. The tidal data must cover all the dates of the images selected by the user.
# The file can be read with the 'read_tidalseries' function, and must have the following format.
# Example of a TidalSeries.txt file:
# Location: 46.281289 N / -1.171555 W
# 2020-02-06 00:00:00    1.1254290883044473
# 2020-02-06 00:10:00    1.166774695078127
# 2020-02-06 00:20:00    1.1969266659418396
# 2020-02-06 00:30:00    1.2156988438899512
# 2020-02-06 00:40:00    1.223223757919919
# ...
# ...
# ...
# ========================================================================

import os
import re
import sys
import uptide
import argparse
import numpy as np
from glob import glob
from pathlib import Path
from osgeo import gdal, osr
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from datetime import datetime, timedelta
import worsica_common_script_functions
np.seterr(divide='ignore', invalid='ignore')

cwd = None


def worsicaTide(dateIni, dateEnd, point, dt=600., zref=0., outfile="TidalSeries.txt",
                pathData="/usr/local/bin/FES2014/data/ocean_tide_extrapolated", graphics=False, outfolder='TopoOutputs'):

    d1str = dateIni.strftime("%Y%m%d")
    d2str = dateEnd.strftime("%Y%m%d")

    tide_fes2014 = ['2N2', 'EPS2', 'J1', 'K1', 'K2', 'L2',
                    'LAMBDA2', 'M2', 'M3', 'M4', 'M6', 'M8',
                    'MF', 'MKS2', 'MM', 'MN4', 'MS4', 'MSF',
                    'MSQM', 'MTM', 'MU2', 'N2', 'N4', 'NU2',
                    'O1', 'P1', 'Q1', 'R2', 'S1', 'S2', 'S4',
                    'SA', 'SSA', 'T2']

    delta_run = dateEnd.date() - dateIni.date()
    days = delta_run.days

    tide = uptide.Tides(tide_fes2014)
    tide.set_initial_time(dateIni)

    base = dateIni
    t = np.arange(0, days * 24 * 3600, dt)
    tarr = np.array([base + timedelta(seconds=round(i)) for i in t])

    tnci = uptide.FES2014TidalInterpolator(tide, pathData)

    eta = []
    data = [f"Location: {point[0]} N / {point[1]} W"]
    for n, i in enumerate(t):
        tnci.set_time(int(i))
        eta.append(tnci.get_val(point) + zref)
        data.append(f"{tarr[n]}    {eta[-1][0]}")
    # eta = np.array(eta)

    if outfile == "TidalSeries.txt":
        Outputs = cwd / outfolder
        Outputs.mkdir(exist_ok=True)
        fileout = str(Outputs / f"TidalSeries_{d1str}-{d2str}.txt")
    else:
        fileout = outfile
    dataSTR = "\n".join(data)
    with open(fileout, "w") as fout:
        fout.write(dataSTR)
    print(f"{fileout} was created!!!")

    if graphics:
        figTide = plt.figure()
        plt.plot_date(tarr, eta, "-r")
        figTide.autofmt_xdate()
        plt.savefig(fileout[:-4] + ".png")

    return [tarr, eta]


def worsicaTopoMap(FreqIdx, Freq, water_level_desc):
    # # Create topographic map
    FF1 = FreqIdx.flatten()
    FF2 = interp1d(Freq, water_level_desc)(FF1)
    topo = np.reshape(FF2, FreqIdx.shape)
    return topo


def read_tidalseries(filein, str_fmt="%Y-%m-%d %H:%M:%S"):
    with open(filein, "r") as fid:
        text = fid.readlines()
    dt, da = [], []
    for i in text[1:]:
        dt.append(datetime.strptime(i[:20].strip(), str_fmt))
        da.append(float(i.split()[2]))
    return dt, da


def worsica_readBinary(img):
    gdalImg = gdal.Open(img)
    Bin = gdalImg.ReadAsArray()
    Metadata = gdalImg.GetMetadata()
    band = gdalImg.GetRasterBand(1)
    arr = band.ReadAsArray()
    [rows, cols] = arr.shape
    GCPs = gdalImg.GetGCPs()
    GCPsProj = gdalImg.GetGCPProjection()
    geotransform = gdalImg.GetGeoTransform()
    Description = gdalImg.GetDescription()
    proj = osr.SpatialReference(wkt=gdalImg.GetProjection())

    data = {"Bin": Bin,
            "Metadata": Metadata,
            "Dims": [cols, rows],
            "EPSG": np.int32(proj.GetAttrValue('AUTHORITY', 1)),
            "GCPs": GCPs,
            "GCPsProj": GCPsProj,
            "geotransform": geotransform,
            "Description": Description}
    return data


def normalizeWaterIndexArrayByRange(arr, minVal, maxVal):
    arr1 = np.where(arr > maxVal, maxVal, arr)
    arr2 = np.where(arr1 < minVal, minVal, arr1)
    return arr2


def GetCoords(filein):
    worsica_common_script_functions._run_gdalinfo(filein, "Info_Coords.txt")
    fid = open("Info_Coords.txt", "r")
    data = fid.readlines()
    for n, line in enumerate(data):
        if re.match("Corner Coordinates:", line):
            LineCoords = n
    Coords = [[np.float(data[LineCoords + 1].split("(")[1].split(",")[0]), np.float(data[LineCoords + 1].split("(")[1].split(",")[1].split(")")[0])],
              [np.float(data[LineCoords + 2].split("(")[1].split(",")[0]),
               np.float(data[LineCoords + 2].split("(")[1].split(",")[1].split(")")[0])],
              [np.float(data[LineCoords + 3].split("(")[1].split(",")[0]),
               np.float(data[LineCoords + 3].split("(")[1].split(",")[1].split(")")[0])],
              [np.float(data[LineCoords + 4].split("(")[1].split(",")[0]), np.float(data[LineCoords + 4].split("(")[1].split(",")[1].split(")")[0])]]
    fid.close()
    worsica_common_script_functions._run_rm("Info_Coords.txt")
    Coords = np.array(Coords)
    return Coords


def GetImgSize(filein):
    worsica_common_script_functions._run_gdalinfo(filein, "Info_ImgSize.txt")
    fid = open("Info_ImgSize.txt", "r")
    data = fid.readlines()
    for n, line in enumerate(data):
        if re.search("Size is ", line):
            LineSize = n
    y = np.int(data[LineSize].split(" is ")[1].split(",")[1])
    x = np.int(data[LineSize].split(" is ")[1].split(",")[0])
    ImgSize = [y, x]
    fid.close()
    worsica_common_script_functions._run_rm("Info_ImgSize.txt")
    return ImgSize


def GetLonLat(filein):
    ImgSize = GetImgSize(filein)
    Coords = GetCoords(filein)
    lon = np.zeros(ImgSize, dtype=np.float32)
    lat = np.zeros_like(lon)
    Lat_vals = np.linspace(Coords[:, 1].min(), Coords[:, 1].max(), ImgSize[0])
    for i in range(ImgSize[0]):
        lon[i] = np.linspace(Coords[:, 0].min(), Coords[:, 0].max(), ImgSize[1])
        lat[i] = np.ones((ImgSize[1])) * Lat_vals[i]
    lat = lat[:: -1, :]
    return lon, lat


def array2raster(img, data, EPSG_out=4326, fileout="ImgOut.tif"):
    output_raster = gdal.GetDriverByName('GTiff').Create(
        fileout, data["Dims"][0], data["Dims"][1], 1, gdal.GDT_Float32)
    output_raster.SetGeoTransform(data["geotransform"])
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG_out)
    output_raster.SetProjection(srs.ExportToWkt())
    output_raster.GetRasterBand(1).WriteArray(img)
    output_raster.GetRasterBand(1).SetNoDataValue(0)
    return None


def getARGScmd():
    parser = argparse.ArgumentParser(
        description='worsica_Flood2Topo: Script to calculate topography from sentinel-2 images')
    parser.add_argument('-path', help='Simulation path', required=True)
    parser.add_argument('-zref', help='Vertical reference level provided by user.', required=False)
    parser.add_argument(
        "-point",
        help="Coordinates of the point (Lat,Lon), to extract the time series. Example: -p '40.6323579, -8.786425'",
        required=False)
    parser.add_argument(
        "-tide",
        help="Name of the tidal series file, uploaded by the user. If not defined a tidal series will be obtained from FES2014.",
        required=False)
    parser.add_argument('-outfolder', help='Output folder', required=False)

    args = parser.parse_args()
    if not args.point and not args.tide:
        sys.exit("Please specify the coordinate of the point to calculate the tide (argument -p) or upload a tidal data file (argument -tide).")
    return args


def worsicaFloodFreq(imgarr):
    # sum img in each loop
    sum_imgarr = np.sum(imgarr, axis=0)
    # flood frequency for each water index
    floodfreq = sum_imgarr * 100. / imgarr.shape[0]
    return floodfreq


def selectPeriod(data, dateIni=datetime(2020, 1, 1), dateEnd=datetime(2021, 1, 1)):
    arr1 = np.where(data >= np.datetime64(dateIni))
    arr2 = np.where(data <= np.datetime64(dateEnd))
    idx = [arr1[0][0], arr2[0][-1]]
    return idx


if __name__ == '__main__':
    args = getARGScmd()
    # print(args)
    cwd = Path(args.path)
    wdir = Path(args.path).resolve()
    simulation = wdir.name
    if args.outfolder:
        outfolder = args.outfolder
    else:
        outfolder = 'TopoOutputs'

    Outputs = cwd / outfolder
    Outputs.mkdir(exist_ok=True)

    if args.zref:
        zref = float(args.zref)
    else:
        zref = 0.

    foldersList = glob(f"{wdir}/*")
    print(foldersList)

    my_dates = []
    for i in foldersList:
        if outfolder not in i:
            i_split = re.split(r'-|/', i)
            for idx, s in enumerate(
                    i_split):
                if 'merged_resampled_' in s:
                    get_date = i_split[idx].replace("merged_resampled_", '').split('_')
                    my_dates.append(get_date[0])
    my_dates.sort(key=lambda date: datetime.strptime(date, "%Y%m%d"))
    print(my_dates)

    sortedFolders = []
    for date in my_dates:
        for folder in foldersList:
            if (date in folder) and (folder not in sortedFolders):
                sortedFolders.append(folder)
    # readImgs
    waterIndxs = ["AWEI", "AWEISH", "NDWI", "MNDWI", "MNDWI2"]

    imgData = {}
    indexBin = {}
    nFiles = len(sortedFolders)
    d1 = datetime.strptime(my_dates[0], "%Y%m%d")
    d2 = datetime.strptime(my_dates[-1], "%Y%m%d")

    aweiArr, mndwi2Arr, ndwiArr, mndwiArr, aweishArr = [], [], [], [], []
    for n, folder in enumerate(sortedFolders):
        lastDir = glob(f"{folder}/**/", recursive=True)[-1]
        print(lastDir)
        for i in waterIndxs:
            # merged_resampled_yyyyy_xxxxx_aweish_cleanup/merged_resampled_yyyyy_xxxxx_aweish_cleanup_binary
            # merged_resampled_yyyyy_xxxxx/merged_resampled_yyyyy_xxxxx_aweish_binary
            filename = glob(f"{lastDir}/*_{i.lower()}_cleanup_binary.tif")
            for fn in filename:
                if fn:
                    if "_" + i.lower() + "_threshold_cleanup" in lastDir:
                        fn2 = fn.replace(
                            "_threshold_cleanup", "").replace(
                            "_" + i.lower() + "/", "/")
                    elif "_" + i.lower() + "_threshold" in lastDir:
                        fn2 = fn.replace("_threshold", "").replace("_" + i.lower() + "/", "/")
                    elif "_" + i.lower() + "_cleanup" in lastDir:
                        fn2 = fn.replace("_cleanup", "").replace("_" + i.lower() + "/", "/")
                    print("found " + fn + ", replace with " + fn2)
                    os.replace(fn, fn2)

    # sort again after replace
    sortedFolders = []
    for date in my_dates:
        for folder in foldersList:
            if (date in folder) and (folder not in sortedFolders):
                sortedFolders.append(folder)
    print(sortedFolders)

    for n, folder in enumerate(sortedFolders):
        lastDir = glob(f"{folder}/**/", recursive=True)[-1]
        print(lastDir)
        for i in waterIndxs:
            filename = glob(f"{lastDir}/*_{i.lower()}_binary.tif")
            if not filename:
                print(f"{lastDir}/*_{i.lower()}_binary.tif not found, skip")
                pass
            else:
                print(f"{lastDir}/*_{i.lower()}_binary.tif found, process")
                filein = str(filename[0])
                print(filein)
                if Path(filein).is_file():
                    data = worsica_readBinary(filein)
                    dataImg = data["Bin"]

                    # Check if this line is still needed!!!
                    img = np.where(dataImg == -1, 0, dataImg)

                    if i == "AWEI":
                        aweiArr.append(img)
                    if i == "AWEISH":
                        aweishArr.append(img)
                    if i == "NDWI":
                        ndwiArr.append(img)
                    if i == "MNDWI":
                        mndwiArr.append(img)
                    if i == "MNDWI2":
                        mndwi2Arr.append(img)

    Freqs = {"AWEI": np.array(aweiArr),
             "AWEISH": np.array(aweishArr),
             "NDWI": np.array(ndwiArr),
             "MNDWI": np.array(mndwiArr),
             "MNDWI2": np.array(mndwi2Arr)}

    # Create water level duration curve
    if args.tide:
        time_water_level, water_level = read_tidalseries(args.tide)
        print(d1)
        print(time_water_level[0])
        print(d2)  # maintain the date of last image
        print(time_water_level[-1])
        if time_water_level[0] > d1:  # time_water_level[0] > d1:
            sys.exit("Error - The initial time must be lower than the date of the first image.")
        if time_water_level[-1] < d2:  # time_water_level[-1] < d2:
            sys.exit("Error - The final time must be greater than the date of the last image.")
        timeSlice = selectPeriod(time_water_level, dateIni=d1, dateEnd=d2)
        time_water_level = time_water_level[timeSlice[0]:timeSlice[1] + 1]
        water_level = water_level[timeSlice[0]:timeSlice[1] + 1]
    else:
        pointAux = args.point.split(",")
        pointAux2 = [float(i) for i in pointAux]
        point = tuple(pointAux2)
        d2 = d2 + timedelta(days=1)  # add one more day for the tides
        tidalSeries = worsicaTide(d1, d2, point, outfolder=outfolder)
        water_level = []
        for i in tidalSeries[1]:
            water_level.append(i[0])
    water_level_desc = np.sort(water_level)[::-1]
    Freq = np.linspace(0, 100, num=water_level_desc.size)

    # Calculate the flood frequency for each index
    FloodFreqs = {}
    TopoMaps = {}
    for widx in waterIndxs:
        if Freqs[widx].size != 0:
            FloodFreqs[widx] = worsicaFloodFreq(Freqs[widx])
            array2raster(
                FloodFreqs[widx],
                data,
                EPSG_out=4326,
                fileout=str(
                    Outputs /
                    f"FloodFreqs_{widx}.tif"))

            # Create topographic map (matlab cod)
            TopoMaps[widx] = worsicaTopoMap(FloodFreqs[widx], Freq, water_level_desc)
            # Export geotiff - Write/convert TopoMaps arrays to GeoTiFFs files.
            array2raster(
                TopoMaps[widx],
                data,
                EPSG_out=4326,
                fileout=str(
                    Outputs /
                    f"Topography_{widx}.tif"))
