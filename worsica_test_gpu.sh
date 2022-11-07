function control_c {
    echo "[worsica_test_gpu.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

WORSICA_FOLDER_PATH=$(pwd)
PATH_TO_PRODUCTS="${WORSICA_FOLDER_PATH}/teste_gpu"

echo "[worsica_test_gpu.sh] [Test] Run GPU test"		
if (cd ${PATH_TO_PRODUCTS} && python3 -u RunAAzevedoCVscript.py) ; then 
	echo "[worsica_test_gpu.sh] [Test] Finished!"		
	exit 0
else
	echo "[worsica_test_gpu.sh] [Test] Failed!"
	exit 1
fi
		

