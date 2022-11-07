[![GitHub license](https://img.shields.io/github/license/WorSiCa/worsica-processing.svg?maxAge=2592000&style=flat-square)](https://github.com/WorSiCa/worsica-processing/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/release/WorSiCa/worsica-processing.svg?maxAge=3600&style=flat-square)](https://github.com/WorSiCa/worsica-processing/releases/latest)
[![Build Status](https://jenkins.eosc-synergy.eu/buildStatus/icon?job=WORSICA%2Fworsica-processing%2Fdevelopment)](https://jenkins.eosc-synergy.eu/job/WORSICA/job/worsica-processing/job/development/)
# worsica-processing
Repository that includes all processing files.

## Notes regarding google cloud
The worsica_ph0_download_gcp_sentinel.py requires a key to access and download the files from Sentinel2 cloud repository.
The file is called gcp-key.json, but you have a template file to see how it looks.
You need to have a google cloud account, go to console, and then create a project and a service account with scope for google cloud. (https://cloud.google.com/iam/docs/creating-managing-service-account-keys), and generate a .json key that will be download to your computer. 
Rename it as gcp-key.json and move it to the main directory.
If the script throws errors due to permissions, please check the authorizations/scope on the console.
