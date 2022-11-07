echo '0- reinstall gdal (wheel issues)'
.tox/worsica-processing-unittest/bin/pip3 install --force-reinstall GDAL==3.0.4 --no-cache

echo '1- generate ssecrets'
/usr/local/worsica_web_products/worsica_jenkins_generate_ssecrets.sh

echo '2- copy gcp file'
echo "${WORSICA_PROCESSING_GCP_KEY_FILE}"
cp "${WORSICA_PROCESSING_GCP_KEY_FILE}" /usr/local/worsica_web_products/gcp-key.json

echo '3- download an imageset sample'
cd /usr/local/worsica_web_products/unit_tests_files/
curl -L "https://www.dropbox.com/s/pnbdhot4xwagm3p/S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502.zip?dl=1" -o S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502.zip 

echo '4- force generation of original processing inputs before running unit tests'
cd /usr/local/worsica_web_products/unit_tests_files/ 
(echo 'Y' | /usr/local/worsica_web-py363_venv/bin/python3 /usr/local/worsica_web_products/worsica_ut_generate_originals.py)