#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback
import os
import sys
from datetime import datetime, timedelta
import time

from google.cloud import storage
from google.api_core import page_iterator
# pip install google-cloud-storage==1.37.1
from google.oauth2 import service_account

import shutil

BUCKET_ID = 'gcp-public-data-sentinel-2'


def getPathToImageset(sentinel_fname):
    try:
        # '/gcp-public-data-sentinel-2/L2/tiles/18/T/XT/S2A_MSIL2A_20181214T154641_N0211_R011_T18TXT_20181214T181045.SAFE'
        if 'S2' in sentinel_fname:
            sentinel_fname_split = sentinel_fname.split('_')
            tileId = sentinel_fname_split[5]
            level = 'L2/' if 'L2' in sentinel_fname else ''
            url = level + 'tiles/' + tileId[1:3] + '/' + tileId[3] + \
                '/' + tileId[4:6] + '/' + sentinel_fname + '.SAFE'
            return url
        else:
            raise Exception('Error: Unknown sentinel product format.')
    except Exception as e:
        print(e)


def list_prefixes(client, bucket_name, prefix, delimiter):
    # Adapted from https://stackoverflow.com/a/59008580
    print('This will take a while, please wait...')
    return page_iterator.HTTPIterator(
        client=client,
        api_request=client._connection.api_request,
        path=f"/b/{bucket_name}/o",
        items_key="prefixes",
        item_to_value=lambda iterator, item: item,
        extra_params={
            "projection": "noAcl",
            "prefix": prefix,
            "delimiter": delimiter,
        },
    )


def download(sentinel_fname):
    # ./google-cloud-sdk/bin/gsutil -m cp -r "gs://gcp-public-data-sentinel-2/tiles/31/C/DM/S2A_MSIL1C_20161018T062812_N0204_R048_T31CDM_20161018T063145.SAFE/" .
    user_id = 1
    num_attempts = 1
    max_attempts = 5
    cooldown = 2
    path = os.getcwd()
    downloadSuccesful = False
    while num_attempts <= max_attempts and not downloadSuccesful:
        try:
            userkey = 'user' + str(user_id)
            print('[gcp_download][downloadURL][' + userkey + '] Attempt ' + str(num_attempts) + '...')
            print('[gcp_download][downloadURL][' + userkey + '] Check availability...')

            credentials = service_account.Credentials.from_service_account_file(
                os.path.dirname(os.path.realpath(sys.argv[0])) + '/gcp-key.json')
            scoped_credentials = credentials.with_scopes(
                ['https://www.googleapis.com/auth/cloud-platform'])
            storage_client = storage.Client(credentials=scoped_credentials)

            print('[gcp_download][downloadURL][' + userkey +
                  '] List only SAFE folders from the bucket... please wait')
            sentinel_fname_split = sentinel_fname.split('_')
            tileId = sentinel_fname_split[5]
            date = datetime.strptime(sentinel_fname_split[2].split('T')[0], '%Y%m%d')
            start = date
            sstart = start.strftime('%Y-%m-%d')
            end = (date + timedelta(days=2))
            send = end.strftime('%Y-%m-%d')

            output = []
            level = 'L2/' if 'L2' in sentinel_fname_split[1] else ''
            prefix = level + 'tiles/' + tileId[1:3] + '/' + \
                tileId[3] + '/' + tileId[4:6] + '/'  # +'/*.SAFE_$folder$'

            # get only the main folders
            # one problem, some imagesets stored on google do not have _$folder$,
            # making the filtering hard
            lcf = []
            all_blobs = list_prefixes(storage_client, BUCKET_ID, prefix=prefix, delimiter='/')
            for x in all_blobs:
                bname = x.replace(prefix, '').replace('_$folder$', '')
                bname_split = bname.split('/')
                isSAFEFolder = '.SAFE' in bname_split[0]
                if isSAFEFolder and bname_split[0] not in lcf:
                    lcf.append(bname_split[0])
            for foldername in lcf:
                # filter now by date
                foldername_split = foldername.split('_')
                fdate = datetime.strptime(foldername_split[2].split('T')[0], '%Y%m%d')
                if fdate >= start and fdate < end:
                    output.append(foldername)
            print(output)
            if len(output) > 0:
                fn = output[0].replace('.SAFE', '')
                print('[gcp_download][downloadURL][' + userkey +
                      ']: Available! Start the download of ' + str(fn))
                prefix = getPathToImageset(fn) + '/'
                dl_dir = './' + fn + '.SAFE/'

                if os.path.exists(dl_dir):
                    shutil.rmtree(dl_dir)
                os.makedirs(dl_dir, exist_ok=True)

                blobs = storage_client.list_blobs(BUCKET_ID, prefix=prefix)  # Get list of files
                for blob in blobs:
                    bn = blob.name.replace(prefix, '')
                    if '_$folder$' not in bn:
                        filepath_split = bn.split('/')
                        foldername = '/'.join(filepath_split[:-1])
                        filename = filepath_split[-1]
                        print('[gcp_download][downloadURL] Downloading ' + bn)
                        os.makedirs(dl_dir + '/' + foldername, exist_ok=True)
                        blob.download_to_filename(
                            dl_dir + '/' + foldername + '/' + filename)  # Download

                print('[gcp_download][downloadURL] Zipping folder ' + fn)
                shutil.make_archive(
                    path + '/' + sentinel_fname,
                    'zip',
                    root_dir=path,
                    base_dir=fn + '.SAFE')
                print('[gcp_download][downloadURL] Remove folder ' + fn)
                shutil.rmtree(dl_dir)

                downloadSuccesful = True
            else:
                print('[gcp_download][downloadURL] Error, no file found for download!')
                print('[gcp_download][downloadURL] state: error-download')
                return 'error-download'

            if (downloadSuccesful):
                print('[gcp_download][downloadURL] state: downloaded')
                return 'downloaded'
            else:
                print('[gcp_download][downloadURL] Error, something went wrong on the download!')
                print('[gcp_download][downloadURL] state: error-download')
                return 'error-download'

        except Exception as e:
            print(traceback.format_exc())
            print('[gcp_download][downloadURL][' + userkey + '] Failed! ' + str(e))
            seriousAccountProblem = ('401' in str(e) or '403' in str(e) or '404' in str(e))
            if seriousAccountProblem:
                print(
                    '[gcp_download][downloadURL][' +
                    userkey +
                    '] Retrying download in ' +
                    str(cooldown) +
                    ' minutes...')
                time.sleep(cooldown * 60)  # 2 minutes
                num_attempts += 1
            else:
                print('[gcp_download][downloadURL] state: error-download')
                exit(1)


if __name__ == '__main__':
    try:
        args = sys.argv
        sentinel_fname = args[1]
        state = download(sentinel_fname)
        if state == 'downloaded':
            exit(0)
        elif state == 'error-download':
            exit(1)
        else:
            exit(1)

    except Exception as e:
        print(traceback.format_exc())
        print(str(e))
        exit(1)
