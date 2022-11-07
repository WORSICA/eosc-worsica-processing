#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ========================================================================
# File:   worsica_automaticThreshold.py
# ========================================================================
__author__ = 'Alberto Azevedo'
__doc__ = "Script to automatically calculate the water index threshold"
__datetime__ = '& November 2020 &'
__email__ = 'aazevedo@lnec.pt'
# ========================================================================

from osgeo import gdal, osr
import numpy as np
import argparse
import heapq
import matplotlib.pyplot as plt
from skimage import io
from scipy.signal import argrelextrema, find_peaks
import traceback
np.seterr(divide='ignore', invalid='ignore')


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def normalizeWaterIndexArrayByRange(arr, minVal, maxVal):
    arr1 = np.where(arr > maxVal, maxVal, arr)
    arr2 = np.where(arr < minVal, minVal, arr1)
    return arr2


def replaceMinMaxValuesNan(arr, minVal, maxVal):
    arr1 = np.where(arr >= maxVal, np.nan, arr)
    arr2 = np.where(arr1 <= minVal, np.nan, arr1)
    return arr2


def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w


def worsica_readWaterIndex(img):
    gdalImg = gdal.Open(img, gdal.GA_ReadOnly)
    WaterIndex = np.array(gdalImg.GetRasterBand(1).ReadAsArray())
    Metadata = gdalImg.GetMetadata()
    band = gdalImg.GetRasterBand(1)
    arr = band.ReadAsArray()
    [cols, rows] = arr.shape  # [rows, cols] = arr.shape
    GCPs = gdalImg.GetGCPs()
    GCPsProj = gdalImg.GetGCPProjection()
    geotransform = gdalImg.GetGeoTransform()
    Description = gdalImg.GetDescription()
    proj = osr.SpatialReference(wkt=gdalImg.GetProjection())

    data = {"WaterIndex": WaterIndex,
            "Metadata": Metadata,
            "Dims": [cols, rows],
            "EPSG": np.int(proj.GetAttrValue('AUTHORITY', 1)),
            "GCPs": GCPs,
            "GCPsProj": GCPsProj,
            "geotransform": geotransform,
            "Description": Description}
    return data


def worsicaAutomaticThreshold(img, graphics=False):
    try:
        # Modified histogram bimodal method (MHBM)
        image = io.imread(img)
        image2 = replaceMinMaxValuesNan(image, image.min(), image.max())
        image2 = image2[~np.isnan(image2)]
        # print(image2.min(), image2.max())
        if graphics:
            plt.figure()
            plt.subplot(311)
        hist = plt.hist(image2.ravel(), bins=256)
        histFiltered = moving_average(hist[0], 10)
        xHist = np.linspace(image2.min(), image2.max(), len(histFiltered))
        if graphics:
            plt.subplot(312)
            plt.plot(xHist, histFiltered)
            plt.ylim([0, histFiltered.max()])

        # for local maxima
        maxs = argrelextrema(histFiltered, np.greater)
        peaks, _ = find_peaks(histFiltered, height=100)
        TwoMaxsPos = heapq.nlargest(2,
                                    range(len(histFiltered[peaks])),
                                    key=histFiltered[peaks].__getitem__)
        TwoMaxs = heapq.nlargest(2, histFiltered[peaks])

        if graphics:
            for j in peaks[TwoMaxsPos]:
                plt.axvline(xHist[j], color="g")

        maxLow = peaks[TwoMaxsPos[1]]
        maxHigh = peaks[TwoMaxsPos[0]]
        maxs = [maxLow, maxHigh]
        maxsS = sorted(maxs)

        minHistFilt = np.min(histFiltered[maxsS[0]: maxsS[1]])
        idx = np.where(histFiltered[maxsS[0]: maxsS[1]] == minHistFilt)
        thresh_min = xHist[maxsS[0]: maxsS[1]][idx[0][0]]

        if graphics:
            plt.subplot(313)
            plt.plot(xHist, histFiltered)
            plt.ylim([0, histFiltered.max()])
            plt.axvline(thresh_min, color="r")
            arr1 = np.where(image > thresh_min, 1, image)
            arr2 = np.where(image < thresh_min, 0, arr1)
            # Creates two subplots and unpacks the output array immediately
            f, (ax1, ax2) = plt.subplots(1, 2, sharex=True, sharey=True)
            ax1.imshow(image, cmap="gray")
            ax2.imshow(arr2, cmap="gray")
            plt.show()

        return thresh_min
    except BaseException:
        traceback.print_exc()


def getARGScmd():
    parser = argparse.ArgumentParser(
        description='worsica_automaticThreshold: Script to automatically calculate the water index threshold.')
    parser.add_argument('-img', '--image', help='Name of the input image.', required=True)

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = getARGScmd()
    img = args.image
    worsicaAutomaticThreshold(img, graphics=False)
