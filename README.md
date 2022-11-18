[![GitHub license](https://img.shields.io/github/license/WorSiCa/worsica-processing.svg?maxAge=2592000&style=flat-square)](https://github.com/WorSiCa/worsica-processing/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/release/WorSiCa/worsica-processing.svg?maxAge=3600&style=flat-square)](https://github.com/WorSiCa/worsica-processing/releases/latest)
[![Build Status](https://jenkins.eosc-synergy.eu/buildStatus/icon?job=WORSICA%2Fworsica-processing%2Fdevelopment)](https://jenkins.eosc-synergy.eu/job/WORSICA/job/worsica-processing/job/development/)
# worsica-processing

Repository that includes all processing files.

## Features

- Bash scripts that run respective python files
- Unitary tests

## Requirements

- worsica-essentials docker image

## Build

**NOTE: In order to build this image, you need to build the worsica-essentials docker image first, available at WORSICA/worsica-cicd repository.**

The Dockerfile.backend file provided at docker_backend/aio_v4, do:

```shell
cd docker_backend/aio_v4
docker build -t worsica/worsica-processing:development -f Dockerfile.backend .
```

## Configurations

Before running, first you need to config the following files:

```
worsica_grid_launch_submission_sensitive.sh: Sensitive configurations on submission launch to grid
worsica_run_script_grid_sensitive.sh: Sensitive configurations on running script on grid
SSecrets.py: Credentials for Sentinel image download
nc-credentials: Nextcloud credentials
gcp-key.json: Credential key for Google Cloud download (see Notes regarding Google Cloud)
```

We provided their _template files to copy them and set the respective file name above. For some cases, you need to create an user account in order to make it work.

## Notes regarding Google Cloud

The worsica_ph0_download_gcp_sentinel.py requires a key to access and download the files from Sentinel2 cloud repository.
The file is called gcp-key.json, but you have a template file to see how it looks.
You need to have a google cloud account, go to console, and then create a project and a service account with scope for [google cloud](https://cloud.google.com/iam/docs/creating-managing-service-account-keys), and generate a .json key that will be downloaded to your computer.
Rename it as gcp-key.json and move it to the main directory.
If the script throws errors due to permissions, please check the authorizations/scope on the console.

## Run

**NOTE: Assure that you already have the requirements in order to run the worsica-intermediate.**

worsica-processing container does not execute as a service, it is only run as image for processing on GRID.
On the GRID, it uses [udocker](https://github.com/indigo-dc/udocker/) instead of docker to avoid superuser permissions:

```shell
udocker run worsica/worsica-processing:development /bin/bash -c "ls -l"
```

In docker, the command is the same, just replace "udocker" by "docker".

An easier way to execute worsica-processing is by entering inside worsica-intermediate container, and do cd ../worsica_web_products.
