This folder is empty. 
This is supposed to have processed products and unit test products, both derived from a imageset you previously downloaded from ESA Copernicus Open Hub, but due to the folder size and due to being proprietary by their respective owners (and to avoid problems on the future), they were not added to the Git.
Please read the documentation in order to understand how to generate these products.

To make things easier, and without any further headaches on configuring:
1) Grab the imageset S2A_MSIL2A_20181229T113501_N0211_R080_T29SMC_20181229T124502 from ESA (as reference this is the zone covering Lisbon, Cascais and Caparica beach), download the zip, and put it in this folder.
2) You need to generate the original processed products. Open a command line from this folder and run python3 ../worsica_ut_generate_originals.py. Please check the documentation to make sure you do have the required dependencies to run it. In order to do the unitary tests, you only need to run this ONCE, unless you have made changes to the processing script or you want to test in another region, and remember this will ERASE all the processed products (even unitary tests ones) on this folder.
3) After running that, you can run the unitary tests, any as you wish. Open a command line from this folder and run python3 [pr pytest] ../worsica_unit_tests.py.

Tips:
- If you want to test this in another zone, you need to do the steps 2 and 3 again. Please make sure you do change the file name, the ROI_POLYGON.