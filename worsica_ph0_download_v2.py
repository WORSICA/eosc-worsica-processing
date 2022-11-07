#!/usr/bin/python
# -*- coding: utf-8 -*-

# ========================================================================
# File:   worsica_ph0_download.py
# ========================================================================
__author__ = 'Ricardo Martins'
__doc__ = "Very lightweight script just to download Sentinel 1 and 2 satellite data. All rights belong to Alberto Azevedo with GTI_Sentinel.py"
__datetime__ = '& November 2020 &'
__email__ = 'aazevedo@lnec.pt'
# ========================================================================

import sys
import SSecrets

from sentinelsat.sentinel import SentinelAPI
import time
import sentinelsat
import logging


def checkImagesetAvailability(uuid, api):
    product_info = api.get_product_odata(uuid)
    if product_info['Online']:
        print('[worsica_ph0_download][checkImagesetAvailability] Product ' + str(uuid) + ' is online.')
        return True
    else:
        print(
            '[worsica_ph0_download][checkImagesetAvailability] Product ' +
            str(uuid) +
            ' is not online.')
        return False


def get_api(userkey):
    try:
        print('[worsica_ph0_download][downloadUUID] Get credentials of ' + str(userkey) + '...')
        Credentials = SSecrets.getCredentials()[userkey]
    except Exception as e:
        print('[worsica_ph0_download][downloadUUID] Credentials ' + str(userkey) + ' do not exist!')
        exit(1)

    try:
        api = SentinelAPI(Credentials["user"], Credentials["password"])
        print('[worsica_ph0_download][downloadUUID] Authentication successfull!')
        return api
    except Exception as e:
        print('[worsica_ph0_download][downloadUUID] Authentication failed!')
        print(e)
        exit(1)


def downloadUUID(uuid):
    num_attempts = 1
    max_attempts = 25
    cooldown = 2  # minutes
    api = None
    Credentials = None
    numCredentials = len(SSecrets.getCredentials())
    hasDownloaded = False
    logger = logging.getLogger('sentinelsat')
    logger.setLevel('INFO')

    h = logging.StreamHandler()
    h.setLevel('INFO')
    fmt = logging.Formatter('%(message)s')
    h.setFormatter(fmt)
    logger.addHandler(h)
    # start download
    try:
        userid = 1
        while num_attempts <= max_attempts and not hasDownloaded:
            # connect to the API
            userkey = 'user' + str(userid)
            api = get_api(userkey)
            try:
                print(
                    '[worsica_ph0_download][downloadUUID][' +
                    userkey +
                    '] Attempt ' +
                    str(num_attempts) +
                    '...')
                print('[worsica_ph0_download][downloadUUID][' + userkey + '] Check availability...')
                if checkImagesetAvailability(uuid, api):
                    print('[worsica_ph0_download][downloadUUID][' + userkey +
                          '] Available! Start the download ' + str(uuid))
                    api.download(uuid, checksum=True)
                    hasDownloaded = True
                    print(
                        '[worsica_ph0_download][downloadUUID][' +
                        userkey +
                        '] Downloaded ' +
                        str(uuid))
                    print('[worsica_ph0_download][downloadUUID] state: downloaded')
                    break
                else:
                    print(
                        '[worsica_ph0_download][downloadUUID][' +
                        userkey +
                        '] Not available, trigger download to retrieve from LTA service, you need to wait some time to be able download.')
                    api.trigger_offline_retrieval(uuid)
                    print('[worsica_ph0_download][downloadUUID] state: download-waiting-lta')
                    exit(1)
            except sentinelsat.InvalidChecksumError:
                print('[worsica_ph0_download][downloadUUID][' + userkey + '] Failed! Corrupted file!')
                print('[worsica_ph0_download][downloadUUID] state: error-download-corrupt')
                exit(1)

            except Exception as e:
                print('[worsica_ph0_download][downloadUUID][' + userkey + '] Failed! ' + str(e))
                if 'concurrent flows' in str(e) or 'exceed user quota' in str(e):  # if concurrent
                    if userid <= numCredentials:
                        print(
                            '[worsica_ph0_download][downloadUUID][' +
                            userkey +
                            '] Try another account!')
                        userid += 1
                        time.sleep(10)
                    else:
                        print(
                            '[worsica_ph0_download][downloadUUID][' +
                            userkey +
                            '] Tried all accounts, no one was available! Retrying download in ' +
                            str(cooldown) +
                            ' minutes...')
                        userid = 1
                        time.sleep(cooldown * 60)  # 2 minutes
                        num_attempts += 1
                elif 'Error creating stream' in str(e):
                    # Failed! HTTP status 500 Internal Server Error:
                    # UnsupportedOperationException : Error creating stream from file
                    print('[worsica_ph0_download][downloadUUID][' + userkey +
                          '] Number of attempts to download this file has exceeded, fail.')
                    print('[worsica_ph0_download][downloadUUID] state: error-downloading')
                    exit(1)
                else:  # other error
                    print(
                        '[worsica_ph0_download][downloadUUID][' +
                        userkey +
                        '] Retrying download in ' +
                        str(cooldown) +
                        ' minutes...')
                    time.sleep(cooldown * 60)  # 2 minutes
                    num_attempts += 1
        # ------------------------------------------
        if (hasDownloaded):
            exit(0)
        elif (num_attempts > max_attempts):
            print('[worsica_ph0_download][downloadUUID][' + userkey +
                  '] Number of attempts to download this file has exceeded, fail.')
            print('[worsica_ph0_download][downloadUUID] state: error-downloading')
            exit(1)
    except Exception as e:
        print('[worsica_ph0_download][downloadUUID][' + userkey + '] Failed! ' + str(e))
        print('[worsica_ph0_download][downloadUUID] state: error-downloading')
        exit(1)


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) != 2:
        print("Usage: ./worsica_ph0_download_v2.py [UUID] ")
        print("UUID - file identifier for download")
        print('[worsica_ph0_download][downloadUUID] state: error-downloading')
        exit(1)
    else:
        args = sys.argv
        downloadUUID(args[1])
