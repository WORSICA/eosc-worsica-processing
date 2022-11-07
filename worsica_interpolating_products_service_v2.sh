source ./worsica_bash_common.sh

function control_c {
    echo "[worsica_interpolating_products_service_v2.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ $SIMULATION_STATE == *'interpolating-products'* ]] ; then
    	SIMULATION_STATE='error-interpolating-products'
    fi
    echo "[worsica_interpolating_products_service_v2.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: ${SIMULATION_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SERVICE=$1
USER_ID=$2
ROI_ID=$3
SIMULATION_ID=$4
SIMULATION_STATE=$5
MERGED_IMAGESET_NAME=$6
MERGED_IMAGESET_DATE=$7
IMAGESETS_NAME=$8
IMAGESETS_DATE=$9

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Intepolating products]
if [[ $SIMULATION_STATE == *'generated-virtual'* ]] || [[ $SIMULATION_STATE == *'error-interpolating-products'* ]] ; then
	create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${SIMULATION_STATE}
	echo "[worsica_interpolating_products_service_v2.sh] [Intepolating products] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: interpolating-products"
	echo "==========================Intepolating products=============================="
	#echo "[worsica_interpolating_products_service_v2.sh] [Intepolating products] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_NAME}
	pull_multiple_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${IMAGESETS_NAME}
	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_${SERVICE}_interpolating_products.py ${MERGED_IMAGESET_NAME} ${MERGED_IMAGESET_DATE} "${IMAGESETS_NAME}" "${IMAGESETS_DATE}") ; then
		push_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_NAME}
		remove_multiple_processing ${IMAGESETS_NAME} ${PATH_TO_PRODUCTS} #as i am using one worker, this has no problems
		rm -rf ${PATH_TO_PRODUCTS}/${MERGED_IMAGESET_NAME}
        #rm -rf ${PATH_TO_PRODUCTS}
		echo "[worsica_interpolating_products_service_v2.sh] [Intepolating products] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: interpolated-products"
		exit 0
	else
		remove_multiple_processing ${IMAGESETS_NAME} ${PATH_TO_PRODUCTS} #as i am using one worker, this has no problems
		rm -rf ${PATH_TO_PRODUCTS}/${MERGED_IMAGESET_NAME}
		#rm -rf ${PATH_TO_PRODUCTS}
		echo "[worsica_interpolating_products_service_v2.sh] [Intepolating products] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: error-interpolating-products"
		exit 1
	fi
fi