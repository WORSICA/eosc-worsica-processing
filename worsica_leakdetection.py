import gdal
import osr
import ogr
import numpy as np
import traceback
import subprocess
from datetime import datetime

import gc
import copy
import os
import json


def generate_fake_climatology(img, actual_path):
    # generate a random climatology from the original index image for the test of anomaly
    try:
        print('.....generate a fake climatology.....')
        imgSTR = img.split("/")[-1]
        rst = gdal.Open(img)
        gt = rst.GetGeoTransform()
        proj = osr.SpatialReference(wkt=rst.GetProjection())
        srid = np.int(proj.GetAttrValue('AUTHORITY', 1))
        band = rst.GetRasterBand(1)
        arr = band.ReadAsArray()

        print(arr)
        randarr = np.random.uniform(low=0, high=0.2, size=arr.shape)
        print(randarr)
        c = _normalize_array_with_nans(arr)
        c = np.where(c > 0, c + randarr, c)
        c = np.where(c < 0, c - randarr, c)
        # c = c - randarr
        c = np.where(c > 1, 1, c)
        c = np.where(c < -1, -1, c)
        print(c)
        maxH, maxW = c.shape
        createTIFOutputImage(imgSTR[:-4] + '_fakeclimatology', actual_path, maxW, maxH, gt, srid, c)
    except Exception as e:
        print('Error generate_fake_climatology')
        print(str(e))
        traceback.print_exc()
        exit(1)


def _normalize_array_with_nans(array):
    return np.where(array == -999, np.nan, array)


def generate_virtual_empty_image(newimg, sampleimg):
    # newimg path of new virtual image
    # samplieimg path of the example image
    try:
        print('--Remove virtual folder ')
        newimgfolder = newimg
        newimgfile = newimg.split('/')[-1]
        newimgfolder = newimgfolder.replace(newimgfile, '')[:-1]
        sampleimgfolder = sampleimg
        sampleimgfile = sampleimg.split('/')[-1]
        sampleimgfolder = sampleimgfolder.replace(sampleimgfile, '')[:-1]
        print(sampleimgfile)
        print(sampleimgfolder)
        COMMAND4 = ["rm", "-rf", newimgfolder]
        print(str(COMMAND4))
        cmd4 = subprocess.Popen(COMMAND4, shell=False)
        cmd4_wait = cmd4.wait()
        if cmd4_wait == 0:
            print('OK')
            print('--Do a folder copy with cp -R ')
            COMMAND = ["cp", "-R", sampleimgfolder, newimgfolder]
            print(str(COMMAND))
            cmd = subprocess.Popen(COMMAND, shell=False)
            cmd_wait = cmd.wait()
            if cmd_wait == 0:
                print('--Remove old files on new folder copy')
                COMMAND3 = ["rm", newimgfolder + '/' + sampleimgfile[:-4] + '_*']
                print(str(COMMAND3))
                cmd3 = subprocess.Popen(COMMAND3, shell=False)
                cmd3_wait = cmd3.wait()
                if cmd3_wait == 0:
                    print('-Found and deleted them')
                else:
                    print('-Not found, skip')
                print('--Rename file to ' + newimg)
                COMMAND2 = ["mv", newimgfolder + '/' + sampleimgfile, newimg]
                print(str(COMMAND2))
                cmd2 = subprocess.Popen(COMMAND2, shell=False)
                cmd2_wait = cmd2.wait()
                if cmd2_wait == 0:
                    # empty new image
                    print('--Empty the new image as -999 ')
                    rstB = gdal.Open(newimg, gdal.GA_Update)
                    for i in range(1, rstB.RasterCount + 1):
                        print('Band ' + str(i))
                        band = rstB.GetRasterBand(i)
                        arr = band.ReadAsArray()
                        arr[:] = -999
                        band.WriteArray(arr)
                        band.FlushCache()
                        band.ComputeStatistics(0)
                        band.FlushCache()
                        band = None
                    rstB.FlushCache()
                    rstB = None
                    print('SUCCESS! Stored as ' + newimg)
                else:
                    print('FAIL')
                    traceback.print_exc()
                    exit(1)
            else:
                print('FAIL')
                traceback.print_exc()
                exit(1)
        else:
            print('FAIL')
            traceback.print_exc()
            exit(1)

    except Exception as e:
        print('Error generate_virtual_empty_image')
        print(str(e))
        traceback.print_exc()
        exit(1)


def interpolate_products_test():
    path = '/usr/local/worsica_web_products/tests_waterleak/test_interpolation'
    merged_date = '2020-07-15'
    merged_name = path + '/virtual_merged_resampled_20200715/virtual_merged_resampled_20200715.tif'
    imagesetNames = [
        path +
        '/' +
        iN +
        '/' +
        iN +
        '.tif' for iN in [
            'merged_resampled_20200713',
            'merged_resampled_20200718']]
    imagesetDates = ['2020-07-13', '2020-07-18']
    interpolate_products(merged_name, merged_date, imagesetNames, imagesetDates)


def interpolate_products(merged_image, merged_date, inames, idates):
    try:
        imageset_names = copy.deepcopy(inames)
        imageset_dates = copy.deepcopy(idates)
        TIMELINE_IMAGESET_DAYS = 10
        print('Find indexes ...')
        tdate = datetime.strptime(merged_date, "%Y-%m-%d")
        bdate = tdate
        x = 0
        for d in range(0, len(imageset_dates)):
            bdate = datetime.strptime(imageset_dates[d], "%Y-%m-%d")
            if bdate < tdate and x < len(imageset_dates):
                x = x + 1
            else:
                break
        print('x: ' + str(x))
        imageset_dates.insert(x, merged_date)  # add it
        imageset_names.insert(x, merged_image)
        bidx = 0
        for b in range(0, len(imageset_dates)):
            bdate = datetime.strptime(imageset_dates[x - b], "%Y-%m-%d")
            if ((tdate - bdate).days <= TIMELINE_IMAGESET_DAYS and x - b >= 0):
                bidx = b
            else:
                break
        print('bidx: ' + str(bidx) + ' prev: ' + imageset_dates[x - bidx])
        fdate = tdate
        fidx = 0
        for f in range(0, len(imageset_dates) - x):
            fdate = datetime.strptime(imageset_dates[x + f], "%Y-%m-%d")
            if ((fdate - tdate).days <= TIMELINE_IMAGESET_DAYS and x + f < len(imageset_dates)):
                fidx = f
            else:
                break
        print('fidx: ' + str(fidx) + ' next: ' + imageset_dates[x + fidx])
        print(imageset_dates)
        print(imageset_names)

        driver = gdal.GetDriverByName('GTiff')
        merged_raster_orig = gdal.Open(merged_image, gdal.GA_Update)
        merged_raster_orig_arr = merged_raster_orig.GetRasterBand(1).ReadAsArray()
        maxH, maxW = merged_raster_orig_arr.shape
        merged_raster = driver.CreateCopy(
            merged_image[:-4] + '_interpolated.tif', merged_raster_orig, strict=0)
        raster_count = merged_raster.RasterCount
        for i in range(1, raster_count + 1):
            print('Band ' + str(i))
            imagesetsArray = []
            band = merged_raster.GetRasterBand(i)
            prevImage, nextImage = None, None
            arr = _normalize_array_with_nans(band.ReadAsArray())
            imagesetsArray_isnan = np.isnan(arr)
            for name in imageset_names:
                try:
                    r = gdal.Open(name)
                    print(str(name) + ': get band ' + str(i))
                    imagesetsArray.append(
                        _normalize_array_with_nans(
                            np.array(
                                r.GetRasterBand(i).ReadAsArray(
                                    buf_xsize=maxW,
                                    buf_ysize=maxH,
                                    buf_type=gdal.GDT_Float32))))
                except Exception as e:
                    print(str(e))
                    print(str(name) + ': no band ' + str(i) + ', set an empty array')
                    emptyArr = np.empty((maxH, maxW,))
                    emptyArr.fill(np.nan)
                    imagesetsArray.append(emptyArr)
                    pass
            # print(imagesetsArray)
            imagesetsArrayInterp = copy.deepcopy(arr)
            print('LINEAR INTERPOLATION')
            for i in range(1, fidx + 1):  # seguinte
                if (x + i < len(imageset_dates)):
                    print('i=' + str(i) + ' - next: ' + imageset_dates[x + i])
                    for j in range(1, bidx + 1):  # anterior
                        if (x - j >= 0):
                            print('j=' + str(j) + ' - prev: ' + imageset_dates[x - j])
                            if (imagesetsArray_isnan.any() and (isinstance(imagesetsArray[x + i], np.ndarray) and isinstance(
                                    imagesetsArray[x - j], np.ndarray))):  # if prev and next, do interpolation
                                print(imageset_dates[x] + ' has NaN')
                                print('--> start interpolate')
                                # array of positions where the nans are located
                                idxs = np.where(imagesetsArray_isnan)
                                prevImage, nextImage = imagesetsArray[x - j], imagesetsArray[x + i]
                                prevDate, nextDate = datetime.strptime(
                                    imageset_dates[x - j], "%Y-%m-%d"), datetime.strptime(imageset_dates[x + i], "%Y-%m-%d")
                                m = ((nextImage - prevImage) / (nextDate -
                                     prevDate).days) if (nextDate - prevDate).days > 0 else 0
                                b = prevImage
                                ixs = (tdate - prevDate).days
                                imagesetsArrayInterp[idxs] = m[idxs] * ixs + b[idxs]
                                imagesetsArray_isnan = np.isnan(imagesetsArrayInterp)
            print('FILLING MISSING NAN')
            for j in range(1, bidx + 1):  # anterior
                if (x - j >= 0):
                    print('j=' + str(j) + ' - prev: ' + imageset_dates[x - j])
                    if (imagesetsArray_isnan.any() and (isinstance(
                            imagesetsArray[x - j], np.ndarray))):  # if prev and next, do interpolation
                        # fill the missing nans after doing this interpolation (if NaN+value or
                        # value+NaN happens)
                        print(imageset_dates[x] + ' has NaN')
                        print('--> start filling')
                        prevImage = imagesetsArray[x - j]
                        prevImage_idxs = np.where(
                            np.logical_and(
                                imagesetsArray_isnan,
                                np.isfinite(prevImage)))
                        imagesetsArrayInterp[prevImage_idxs] = prevImage[prevImage_idxs]
                        imagesetsArray_isnan = np.isnan(imagesetsArrayInterp)

            for i in range(1, fidx + 1):  # seguinte
                if (x + i < len(imageset_dates)):
                    print('i=' + str(i) + ' - next: ' + imageset_dates[x + i])
                    if (imagesetsArray_isnan.any() and (isinstance(
                            imagesetsArray[x + i], np.ndarray))):  # if prev and next, do interpolation
                        print(imageset_dates[x] + ' has NaN')
                        print('--> start filling')
                        nextImage = imagesetsArray[x + i]
                        nextImage_idxs = np.where(
                            np.logical_and(
                                imagesetsArray_isnan,
                                np.isfinite(nextImage)))
                        imagesetsArrayInterp[nextImage_idxs] = nextImage[nextImage_idxs]
                        imagesetsArray_isnan = np.isnan(imagesetsArrayInterp)

            idxs = np.where(np.isnan(imagesetsArrayInterp))
            imagesetsArrayInterp[idxs] = -999
            band.WriteArray(imagesetsArrayInterp)
            band.FlushCache()
            band.ComputeStatistics(0)
            band.FlushCache()
            band = None
            del imagesetsArray, imagesetsArrayInterp
            gc.collect()

        merged_raster.FlushCache()
        merged_raster = None
        merged_raster_orig = None

        del imageset_dates, imageset_names
        gc.collect()
    except Exception as e:
        traceback.print_exc()
        exit(1)


def generate_average_test():
    path = '/usr/local/worsica_web_products/tests_waterleak/test_interpolation3'
    args1 = 'climatology_0109'
    args2 = 'virtual_merged_resampled_20210109'
    args3 = 'ndwi,mndwi'
    imagesetNames = [path + '/' + iN + '/' + iN + '.tif' for iN in args2.split(',')]
    waterIndexes = args3.split(',')
    generate_average(
        path + '/' + args1 + '/' + args1 + '.tif',
        imagesetNames,
        waterIndexes)


def generate_average(avg_image_name, inames, water_indexes):
    try:
        for wi in water_indexes:
            print('Water index ' + str(wi))
            wi_inames = [iname[:-4] + '_' + wi + '.tif' for iname in inames]
            imagesetsArray = []
            print('---------- average ----------------')
            # test it first
            # construct an array, and insert inside them the imagesets
            # then, create an array mask to flag the NaNs to not be used for average
            maxW, maxH = None, None
            gt, srid = None, None
            for name in wi_inames:
                print(name)
                r = gdal.Open(name)
                b = r.GetRasterBand(1)
                a = b.ReadAsArray()
                maxH, maxW = a.shape
                gt = r.GetGeoTransform()
                srid = np.int(
                    osr.SpatialReference(
                        wkt=r.GetProjection()).GetAttrValue(
                        'AUTHORITY', 1))
                imagesetsArray.append(_normalize_array_with_nans(np.array(a)))

            c = np.zeros((maxH, maxW))  # array
            y = np.zeros((maxH, maxW))  # array weights

            for imageset in imagesetsArray:
                if (imageset is not None):
                    # which image indexes do have finite values
                    slimgset_idx = np.where(np.isfinite(_normalize_array_with_nans(imageset)))
                    # copy the array according to the indexes into a new array
                    c[slimgset_idx] += _normalize_array_with_nans(imageset[slimgset_idx])
                    # increment count
                    y[slimgset_idx] += 1
            c = c / y
            c[np.isnan(c)] = -999
            avg_image_name_split = avg_image_name.split('/')
            avg_image_name_file = avg_image_name_split[-1][:-4] + '_' + wi
            actual_path = '/'.join(avg_image_name_split[:-1])  # get the path
            if not os.path.exists(actual_path):
                print('create directory ' + actual_path)
                os.mkdir(actual_path)
            createTIFOutputImage(avg_image_name_file, actual_path, maxW, maxH, gt, srid, c)
            avg_raster = gdal.Open(actual_path + '/' + avg_image_name_file + '.tif', gdal.GA_Update)
            avg_band = avg_raster.GetRasterBand(1)
            avg_band.SetNoDataValue(-999)
            avg_band.FlushCache()
            avg_band = None
            avg_raster = None
    except Exception as e:
        traceback.print_exc()
        exit(1)


# for generation of tif outputs
def createTIFOutputImage(FILE_NAME, PATH_TO_PRODUCTS, maxW, maxH, gt, srid, c):
    print('createTIFOutputImage: ', PATH_TO_PRODUCTS + '/' + FILE_NAME + '.tif')
    try:
        driver = gdal.GetDriverByName('GTiff')
        outRaster = driver.Create(PATH_TO_PRODUCTS + '/' + FILE_NAME +
                                  '.tif', maxW, maxH, 1, gdal.GDT_Float32)
        outRaster.SetGeoTransform((gt[0], gt[1], gt[2], gt[3], gt[4], gt[5]))
        outband = outRaster.GetRasterBand(1)
        outband.WriteArray(c)
        outRasterSRS = osr.SpatialReference()
        outRasterSRS.ImportFromEPSG(srid)
        outRaster.SetProjection(outRasterSRS.ExportToWkt())
        outband.FlushCache()
        outband = None
        outRaster = None
    except Exception as e:
        print('Error createTIFOutputImage:')
        print(e)
        traceback.print_exc()
        exit(1)

# anomaly


def calculate_water_leak_anomaly(img, climatology_img, actual_path):
    print('OK! Start calculation')
    try:
        imgSTR = img.split("/")[-1]
        rstA = gdal.Open(img)  # the chosen image for leak processing
        print('open ' + str(img))
        bandA = rstA.GetRasterBand(1)
        arrA = bandA.ReadAsArray()
        gtA = rstA.GetGeoTransform()
        maxAH, maxAW = arrA.shape
        print(maxAH, maxAW)
        rstB = gdal.Open(climatology_img)  # the existing climatology image chosen by the system
        print('open ' + str(climatology_img))
        bandB = rstB.GetRasterBand(1)
        arrB = bandB.ReadAsArray()
        gtB = rstB.GetGeoTransform()
        maxBH, maxBW = arrB.shape
        print(maxBH, maxBW)
        rstC = None

        proj = osr.SpatialReference(wkt=rstA.GetProjection())
        srid = np.int(proj.GetAttrValue('AUTHORITY', 1))

        if (maxAW == maxBW and maxAH == maxBH):
            # if error due to different dimensions, trigger the error
            # Given an interval, values outside the interval are clipped to the interval edges.
            rstA_data = _normalize_array_with_nans(arrA)
            rstB_data = _normalize_array_with_nans(arrB)
            print('OK! They do have same size, start calculating!')

        else:
            # assuming the average has the biggest image size (it processed the merged file)
            print('Dimensions are different, but the chosen image is smaller than the average. Crop the average image (climatology) to the size of the chosen image.')
            # 1) crop the avgimage by the size of the selected raster
            xgeo, ygeo = gtA[0], gtA[3]  # rstA.origin[0], rstA.origin[1]
            wB, hB = maxBW, maxBH
            # determine the x and y pixel by the geo coordinates
            # this is used to determine where is the xy offset on the average image to start crop
            # this is done by reversing the geotransform formula calculation, not sure if it works
            yline = round(((gtB[1] * (ygeo - gtB[3])) - (gtB[4] * (xgeo - gtB[0]))
                           ) / ((gtB[1] * gtB[5]) - (gtB[2] * gtB[4])))
            if yline >= hB:
                yline = hB - 1
            elif yline < 0:
                yline = 0
            xpixel = round(((xgeo - gtB[0]) - (yline * gtB[2])) / gtB[1])
            if xpixel >= wB:
                xpixel = wB - 1
            elif xpixel < 0:
                xpixel = 0
            print('xgeo=' + str(xgeo))
            print('ygeo=' + str(ygeo))
            print('xpixel=' + str(xpixel))
            print('yline=' + str(yline))
            print('==rstA')
            rstA_data = _normalize_array_with_nans(arrA)
            print(rstA_data)
            print('==rstB')
            rstB_data = _normalize_array_with_nans(
                bandB.ReadAsArray(
                    xoff=xpixel,
                    yoff=yline,
                    win_xsize=maxAW,
                    win_ysize=maxAH))
            print(rstB_data)

        rstC = rstA_data - rstB_data
        rstC = np.where(rstC > 2, -999, rstC)
        rstC = np.where(rstC < -2, -999, rstC)
        maxCH, maxCW = rstC.shape  # what the f?

        if rstC is not None:  # only way to avoid problems
            # convert again to -999
            # to avoid the Failed to compute statistics, no valid pixels found in sampling.
            rstC[np.isnan(rstC)] = -999
            print('rstC')
            print(rstC)
            createTIFOutputImage(imgSTR[:-4] + '_anomaly', actual_path,
                                 maxCW, maxCH, gtA, srid, rstC)
        else:
            print('Error: Image is empty')
            exit(1)

    except Exception as e:
        print(e)
        traceback.print_exc()
        exit(1)


# 2nd derivative
def calculate_water_leak_second_deriv(img, actual_path):
    # calculate leakage

    try:
        imgSTR = img.split("/")[-1]
        rst = gdal.Open(img)
        band = rst.GetRasterBand(1)
        arr = band.ReadAsArray()
        print('----------------')
        maxH, maxW = arr.shape
        print(maxH, maxW)
        print('----------------')
        proj = osr.SpatialReference(wkt=rst.GetProjection())

        gt = rst.GetGeoTransform()
        srid = np.int(proj.GetAttrValue('AUTHORITY', 1))
        print(gt, srid)

        a = _normalize_array_with_nans(arr)
        na = np.zeros((maxH, maxW))
        print('calculating leak')
        # test it later (the buffer is to not process the margins of the image,
        # that caused some weird leak detections on the top of the image)
        Hbuff, Wbuff = 0, 0
        maxHbuff, maxWbuff = maxH - Hbuff, maxW - Wbuff
        for i in range(Hbuff, maxHbuff):
            pi, ni = i - 1, i + 1  # prev, next
            pi = 0 if pi < 0 else pi
            ni = maxHbuff - 1 if ni > maxHbuff - 1 else ni
            for j in range(Wbuff, maxWbuff):
                pj, nj = j - 1, j + 1  # prev, next
                pj = 0 if pj < 0 else pj
                nj = maxWbuff - 1 if nj > maxWbuff - 1 else nj
                na[i, j] = ((a[pi, j] - 2 * a[i, j] + a[ni, j]) / (10 * 10)) + \
                    ((a[i, pj] - 2 * a[i, j] + a[i, nj]) / (10 * 10))
        createTIFOutputImage(imgSTR[:-4] + "_2nd_deriv", actual_path, maxW, maxH, gt, srid, na)

        print('Success calculate_water_leak_second_deriv')
    except Exception as e:
        print('Error calculate_water_leak_second_deriv')
        print(str(e))
        traceback.print_exc()
        exit(1)


def identifying_leaks(img, actual_path, filterByMask, maskimg):
    # identify leaks
    NUMBER_OF_LEAK_POINTS = 10000

    def _convert_coords_leak_point(mlp, srid):
        # start by converting first these 2D indices into 3857 coords
        xgeo = gt[0] + mlp[1] * gt[1] + mlp[0] * gt[2]
        ygeo = gt[3] + mlp[1] * gt[4] + mlp[0] * gt[5]
        npoint = ogr.CreateGeometryFromWkt('POINT(' + str(ygeo) + ' ' + str(xgeo) + ')')
        geoSrs = ogr.osr.SpatialReference()
        geoSrs.ImportFromEPSG(int(srid))
        npoint.AssignSpatialReference(geoSrs)
        geoSrs2 = ogr.osr.SpatialReference()
        geoSrs2.ImportFromEPSG(3857)
        npoint.Transform(osr.CoordinateTransformation(geoSrs, geoSrs2))
        npy, npx = npoint.GetY() + (gt[5] / 2), npoint.GetX() + (gt[1] / 2)
        return {"y": npy, "x": npx, "value": float(Input[mlp[0]][mlp[1]])}
    try:
        rst = gdal.Open(img)
        band = rst.GetRasterBand(1)
        arr = band.ReadAsArray()
        gt = rst.GetGeoTransform()
        maxH, maxW = arr.shape
        proj = osr.SpatialReference(wkt=rst.GetProjection())
        srid = np.int(proj.GetAttrValue('AUTHORITY', 1))
        ulx = gt[0]
        uly = gt[3]
        lrx = gt[0] + maxW * gt[1]
        lry = gt[3] + maxH * gt[5]
        print([ulx, uly, lrx, lry])
        if (filterByMask):
            print('---filter by mask: get the mask')
            maskrst = gdal.Open(maskimg, gdal.GA_ReadOnly)
            maskrstT = gdal.Translate('', maskrst, format='MEM',
                                      projWinSRS='EPSG:4326', projWin=[ulx, uly, lrx, lry], noData=0,
                                      width=maxW, height=maxH)
            maskbandT = maskrstT.GetRasterBand(1)
            maskarrT = maskbandT.ReadAsArray()  # 0-255
            arr = np.where(maskarrT == 255, arr, -999)  # only the white
        Input = _normalize_array_with_nans(arr)
        cols = Input.shape[1]
        Aux = Input.ravel()
        MinList_aux = Aux.argsort()[:NUMBER_OF_LEAK_POINTS]
        MinList_Pos = []
        for i in MinList_aux:
            # conver the 1D indice by 2D indices
            dm = np.divmod(i, cols)
            MinList_Pos.append(dm)
        # the leftest and toppest point possible of the aos
        # remove first the existing leak points if it was run before.
        outputLeaks = [_convert_coords_leak_point(mlp, srid) for mlp in MinList_Pos]
        with open(img[:-4] + '_leaks.json', 'w') as f:
            json.dump(outputLeaks, f)
        print('Success identifying_leaks')
    except Exception as e:
        print('Error identifying_leaks')
        print(str(e))
        traceback.print_exc()
        exit(1)
