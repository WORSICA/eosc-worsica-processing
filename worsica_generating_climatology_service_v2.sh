source ./worsica_bash_common.sh

function control_c {
    echo "[worsica_generating_climatology_service_v2.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ $SIMULATION_STATE == *'generating-average'* ]] ; then
    	SIMULATION_STATE='error-generating-average'
    fi
    echo "[worsica_generating_climatology_service_v2.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: ${SIMULATION_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SERVICE=$1
USER_ID=$2
ROI_ID=$3
SIMULATION_ID=$4
SIMULATION_STATE=$5
MERGED_IMAGESETS_NAME=$6
AVERAGE_IMAGE_NAME=$7
WATER_INDEX=$8

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Generating average]
if [[ $SIMULATION_STATE == *'processed'* ]] || [[ $SIMULATION_STATE == *'error-generating-average'* ]] ; then
	create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${SIMULATION_STATE}
	echo "[worsica_generating_climatology_service_v2.sh] [Generating average] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: generating-average"
	echo "==========================Generating average=============================="
	#echo "[worsica_generating_climatology_service_v2.sh] [Generating average] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	pull_multiple_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESETS_NAME}
	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_${SERVICE}_generating_average.py ${AVERAGE_IMAGE_NAME} "${MERGED_IMAGESETS_NAME}" "${WATER_INDEX}") ; then
		push_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${AVERAGE_IMAGE_NAME}
		remove_multiple_processing ${MERGED_IMAGESETS_NAME} ${PATH_TO_PRODUCTS}
        rm -rf ${PATH_TO_PRODUCTS}/${AVERAGE_IMAGE_NAME}
		echo "[worsica_generating_climatology_service_v2.sh] [Generating average] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: generated-average"
		exit 0
	else
		remove_multiple_processing ${MERGED_IMAGESETS_NAME} ${PATH_TO_PRODUCTS}
		rm -rf ${PATH_TO_PRODUCTS}/${AVERAGE_IMAGE_NAME}
		echo "[worsica_generating_climatology_service_v2.sh] [Generating average] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: error-generating-average"
		exit 1
	fi
fi