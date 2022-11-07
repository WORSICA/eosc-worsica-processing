source ./worsica_bash_common.sh

function control_c {
    echo "[worsica_merging_service.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ ${SIMULATION_STATE} == *'merging'* ]] ; then
    	SIMULATION_STATE='error-merging'
    fi
    echo "[worsica_merging_service.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: ${SIMULATION_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SERVICE=$1
USER_ID=$2
ROI_ID=$3
SIMULATION_ID=$4
SIMULATION_STATE=$5
IMAGESETS_NAME=$6
MERGED_IMAGESET_NAME=$7

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Merge]
if [[ ${SIMULATION_STATE} == *'resampled'* ]] || [[ ${SIMULATION_STATE} == *'error-merging'* ]] ; then
	create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${SIMULATION_STATE}
	echo "[worsica_processing_service.sh] [Merging] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: merging"
	echo "==========================MERGING=============================="
	#echo "[worsica_processing_service.sh] [Merging] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	#IFS=',' ;for i in `echo "${IMAGESET_NAME}"`; do pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} $i; done
	pull_multiple_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${IMAGESETS_NAME}
	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_merging.py "${IMAGESETS_NAME}" ${MERGED_IMAGESET_NAME} ${SERVICE} ) ; then
		#remove imageset to free up the workspace folder
		push_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_NAME}
		#IFS=',' ;for i in `echo "${IMAGESETS_NAME}"`; do rm -rf ${PATH_TO_PRODUCTS}/$i*; done
		remove_multiple_processing ${IMAGESETS_NAME} ${PATH_TO_PRODUCTS}
		rm -rf ${PATH_TO_PRODUCTS}/${MERGED_IMAGESET_NAME}
		echo "[worsica_processing_service.sh] [Merging] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: merged"
		exit 0
	else
		#remove imageset to free up the workspace folder
		#rm -rf ${PATH_TO_PRODUCTS}
		remove_multiple_processing ${IMAGESETS_NAME} ${PATH_TO_PRODUCTS}
		rm -rf ${PATH_TO_PRODUCTS}/${MERGED_IMAGESET_NAME}
		echo "[worsica_processing_service.sh] [Merging] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: error-merging"
		exit 1
	fi
fi