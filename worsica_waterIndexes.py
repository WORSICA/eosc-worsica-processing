#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ========================================================================
# File:   worsica-resampling.py
# ========================================================================
__author__ = 'Alberto Azevedo'
__doc__ = "Script to calculate the water indexes"
__datetime__ = '& September 2020 &'
__email__ = 'aazevedo@lnec.pt'
# ========================================================================

import os
import re
import argparse
import traceback
import numpy as np
from osgeo import gdal
from osgeo import osr
import worsica_common_script_functions
np.seterr(divide='ignore', invalid='ignore')


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
    lat = lat[::-1, :]
    return lon, lat


def scale_img(img, type):
    """
    If type = 8 => dtype=np.uint8 => n_colors = 256 and range from 0 to 255
    If type = 16 => dtype=np.uint16 => n_colors = 65536 and range from 0 to 65535
    If type = 32 => dtype=np.float32 => n_colors = 1 and range from 0 to 1.
    """
    n_colors = {"8": 255., "16": 65536., "32": 1.}
    if type == 8:
        out_type = np.uint8
    elif type == 16:
        out_type = np.uint16
    elif type == 32:
        out_type = np.float32
    else:
        print("ERROR! Check <type> argument!!!")
    img_new = np.array(img * n_colors[str(type)] / np.nanmax(img), dtype=out_type)
    return img_new


def array2raster(img, data, EPSG_out=4326, fileout="ImgOut.tif"):

    output_raster = gdal.GetDriverByName('GTiff').Create(
        fileout, data["Dims"][0], data["Dims"][1], 1, gdal.GDT_Float32)  # Open the file
    output_raster.SetGeoTransform(data["geotransform"])  # Specify its coordinates

    srs = osr.SpatialReference()                 # Establish its coordinate encoding
    srs.ImportFromEPSG(EPSG_out)                 # This one specifies WGS84 lat long.
    # Anyone know how to specify the
    # IAU2000:49900 Mars encoding?
    output_raster.SetProjection(srs.ExportToWkt())   # Exports the coordinate system
    # to the file

    output_raster.GetRasterBand(1).WriteArray(img)   # Writes my array to the raster
    return None


def worsica_readImg(img):

    gdalImg = gdal.Open(img, gdal.GA_ReadOnly)
    print('Number of bands: ' + str(gdalImg.RasterCount))

    maxH, maxW = gdalImg.RasterYSize, gdalImg.RasterXSize
    Swir_B11 = np.zeros((maxH, maxW))  # None
    Swir_B12 = np.zeros((maxH, maxW))  # None
    Blue_B2 = np.array(gdalImg.GetRasterBand(1).ReadAsArray()) * 0.001
    Green_B3 = np.array(gdalImg.GetRasterBand(2).ReadAsArray()) * 0.001
    Red_B4 = np.array(gdalImg.GetRasterBand(3).ReadAsArray()) * 0.001
    Nir_B8 = np.array(gdalImg.GetRasterBand(4).ReadAsArray()) * 0.001
    if gdalImg.RasterCount > 4:
        Swir_B11 = np.array(gdalImg.GetRasterBand(5).ReadAsArray()) * 0.001
        Swir_B12 = np.array(gdalImg.GetRasterBand(6).ReadAsArray()) * 0.001

    Metadata = gdalImg.GetMetadata()
    band = gdalImg.GetRasterBand(1)
    arr = band.ReadAsArray()
    [rows, cols] = arr.shape
    GCPs = gdalImg.GetGCPs()
    GCPsProj = gdalImg.GetGCPProjection()
    geotransform = gdalImg.GetGeoTransform()
    Description = gdalImg.GetDescription()
    proj = osr.SpatialReference(wkt=gdalImg.GetProjection())

    data = {"Blue": Blue_B2,
            "Green": Green_B3,
            "Red": Red_B4,
            "Nir": Nir_B8,
            "Swir1": Swir_B11,
            "Swir2": Swir_B12,
            "Metadata": Metadata,
            "Dims": [cols, rows],
            "EPSG": np.int(proj.GetAttrValue('AUTHORITY', 1)),
            "GCPs": GCPs,
            "GCPsProj": GCPsProj,
            "geotransform": geotransform,
            "Description": Description}
    gdalImg = None
    return data


def worsicaApplyWaterIndexesThreshold(img, threshold, actual_path, custom_fout=None):
    try:
        imgSTR = img.split("/")[-1]
        if custom_fout:
            fout = custom_fout
        else:
            # _WATERINDEX.tif -> _WATERINDEX_binary.tif
            fout = actual_path + '/' + imgSTR[:-4] + "_binary.tif"
        gdalImg = gdal.Open(img, gdal.GA_ReadOnly)
        arr = gdalImg.GetRasterBand(1).ReadAsArray()
        arr2 = np.where(arr >= threshold, 1, 0)  # -1)
        [rows, cols] = arr.shape
        data = {
            "Dims": [cols, rows],
            "EPSG": np.int(osr.SpatialReference(wkt=gdalImg.GetProjection()).GetAttrValue('AUTHORITY', 1)),
            "geotransform": gdalImg.GetGeoTransform()}
        array2raster(arr2, data, EPSG_out=data["EPSG"], fileout=fout)
        arr = None
        arr2 = None
        gdalImg = None
        return None
    except BaseException:
        traceback.print_exc()

# normalize the array to avoid abnormal WI values >1 or <-1


def normalizeWaterIndexArrayByRange(arr, minVal, maxVal):
    arr1 = np.where(arr > maxVal, maxVal, arr)
    arr2 = np.where(arr1 < minVal, minVal, arr1)
    return arr2


def worsicaWaterIndexes(img, index, actual_path):
    try:
        print(img)
        data = worsica_readImg(img)
        OutIndex = 0
        if index == "NDWI":
            # Normalized  Difference  water  Index (NDWI) 1 - For waterbodies
            # NDWI=(GREEN−NIR/GREEN+NIR)
            NDWI = (data["Green"] - data["Nir"]) / (data["Green"] + data["Nir"])
            OutIndex = normalizeWaterIndexArrayByRange(NDWI, -1, 1)

        elif index == "NDWI1":
            # Normalized  Difference  water  Index (NDWI) 2 - For water content of leaves
            # NDWI=(GREEN−NIR/GREEN+NIR)
            NDWI_B11 = (data["Nir"] - data["Swir1"]) / (data["Nir"] + data["Swir1"])
            OutIndex = normalizeWaterIndexArrayByRange(NDWI_B11, -1, 1)

        elif index == "NDWI2":
            # Normalized  Difference  water  Index (NDWI) 3 - For water content of leaves
            # NDWI=(GREEN−NIR/GREEN+NIR)
            NDWI_B12 = (data["Nir"] - data["Swir2"]) / (data["Nir"] + data["Swir2"])
            OutIndex = normalizeWaterIndexArrayByRange(NDWI_B12, -1, 1)

        elif index == "MNDWI":
            # Modification  Of  Normalized  Difference Water Index (MNDWI)
            # MNDWI=(GREEN−SWIR2/GREEN+SWIR2)
            MNDWI = (data["Green"] - data["Swir1"]) / (data["Green"] + data["Swir1"])
            OutIndex = normalizeWaterIndexArrayByRange(MNDWI, -1, 1)

        elif index == "MNDWI2":
            # Modification  Of  Normalized  Difference Water Index (MNDWI)
            # MNDWI=(GREEN−SWIR2/GREEN+SWIR2)
            MNDWI = (data["Green"] - data["Swir2"]) / (data["Green"] + data["Swir2"])
            OutIndex = normalizeWaterIndexArrayByRange(MNDWI, -1, 1)
            # OutIndex=data["Green"]

        elif index == "NDFI":
            # Normalized  Difference  Flooding  Index (NDFI)
            # NDMI=RED−SWIR2/RED+SWIR2
            NDFI = (data["Red"] - data["Swir2"]) / (data["Red"] + data["Swir2"])
            OutIndex = normalizeWaterIndexArrayByRange(NDFI, -1, 1)

        elif index == "NDMI":
            # Normalized  Difference  Moisture  Index (NDMI)
            # NDMI=RED−NIR/RED+NIR
            NDMI = (data["Red"] - data["Nir"]) / (data["Red"] + data["Nir"])
            OutIndex = normalizeWaterIndexArrayByRange(NDMI, -1, 1)

        elif index == "AWEI":
            # Automated  Water  Extraction Index(AWEI)
            # AWEI= 4*(GREEN-SWIR2)-(0.25*NIR+2.75*SWIR1)
            # This index is suited for situations where shadows are not a major problem
            AWEI = 4 * (data["Green"] - data["Swir2"]) - (0.25 * data["Nir"] + 2.75 * data["Swir1"])
            OutIndex = AWEI

        elif index == "AWEISH":
            # Automated  Water  Extraction Index(AWEI)
            # AWEISH = BLUE + D1 * GREEN – D2 * (NIR + SWIR1) – D3 * SWIR2
            # This equation is intended to effectively eliminate shadow pixels and
            # improve water extraction accuracy in areas with shadow and/or other dark
            # surfaces.
            D1 = 2.5
            D2 = 1.5
            D3 = 0.25

            AWEISH = data["Blue"] + (D1 * data["Green"]) - \
                (D2 * (data["Nir"] + data["Swir1"])) - (D3 * data["Swir2"])
            OutIndex = AWEISH

        elif index == "WRI":
            # Water Ratio Index(WRI)
            # WRI=GREEN+RED/NIR+SWIR2
            WRI = (data["Green"] + data["Red"]) / (data["Nir"] + data["Swir2"])
            OutIndex = WRI

        imgSTR = img.split("/")[-1]
        if "_resampled.tif" in imgSTR:
            n_imgSTR = imgSTR[:-14]
        else:
            n_imgSTR = imgSTR[:-4]
        # remove "_resampled.tif", instead of ".tif"
        fout = "".join((actual_path + "/", n_imgSTR, f"_{index.lower()}", ".tif"))
        array2raster(np.array(OutIndex), data, EPSG_out=data["EPSG"], fileout=fout)
        print('DONE!')
        return None
    except BaseException:
        traceback.print_exc()


def getARGScmd():
    parser = argparse.ArgumentParser(
        description='worsica_resampling: Script to resample images from satellites sentinel 1/2 to 10m resolution')
    parser.add_argument('-img', '--image', help='Name of the input image.', required=True)
    parser.add_argument(
        '-index',
        '--index',
        help='Name of the water index to be calculated.',
        default="MNDWI",
        required=False)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = getARGScmd()
    img = args.image
    index = args.index
    ACTUAL_PATH = os.getcwd()
    worsicaWaterIndexes(img, index, ACTUAL_PATH)
