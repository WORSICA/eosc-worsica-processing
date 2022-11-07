#!/usr/bin/python
# -*- coding: utf-8 -*-

# ========================================================================
# File:   worsica_ph0_download.py
# ========================================================================
__author__ = 'Ricardo Martins'
__doc__ = "Very lightweight script just to check integrity download Sentinel 1 and 2 satellite data. All rights belong to Alberto Azevedo with GTI_Sentinel.py"
__datetime__ = '& November 2020 &'
__email__ = 'aazevedo@lnec.pt'
# ========================================================================

import sys
import worsica_common_script_functions


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) != 2:
        print("Usage: ./worsica_ph0_check_download_v2.py [ZIPNAME] ")
        print("ZIPNAME - file zip")
        print('[worsica_ph0_download][downloadUUID_checkFile] state: error-downloading')
        exit(1)
    else:
        args = sys.argv
        imgZip = args[1]
        unzipcmd = worsica_common_script_functions._run_unzip_test(imgZip + ".zip")
        if unzipcmd != 0:
            print('[worsica_ph0_download][downloadUUID_checkFile]: Error on unzip! Corrupt file!!')
            print('[worsica_ph0_download][downloadUUID_checkFile] state: error-download-corrupt')
            exit(1)
        else:
            print('[worsica_ph0_download][downloadUUID_checkFile]: File is OK!')
            print('[worsica_ph0_download][downloadUUID_checkFile] state: downloaded')
            exit(0)
