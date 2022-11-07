source ./worsica_bash_common.sh

function control_c {
    echo "[worsica_processing_service.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ $SIMULATION_STATE == *'processing'* ]] ; then
    	SIMULATION_STATE='error-processing'
    fi
    echo "[worsica_processing_service.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: ${SIMULATION_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM


SERVICE=$1
USER_ID=$2
ROI_ID=$3
SIMULATION_ID=$4
SIMULATION_STATE=$5
SIMULATION_NAME=$6
MERGED_IMAGESET_NAME=$7
BATH_VALUE=$8
TOPO_VALUE=$9
#use curly braces for more than 10 arguments
WI_THRESHOLD=${10}
WATER_INDEX=${11}

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Process]
if [[ $SIMULATION_STATE == *'merged'* ]] || [[ $SIMULATION_STATE == *'interpolated-products'* ]] || [[ $SIMULATION_STATE == *'error-processing'* ]] ; then
	create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${SIMULATION_STATE}
	echo "[worsica_processing_service.sh] [Process] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: processing"
	echo "==========================PROCESSING=============================="
	#echo "[worsica_processing_service.sh] [Process] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_NAME}
	#pull_imageset
	#if download_file ${NEXTCLOUD_PATH_TO_REPOSITORY}/${IMAGESET_NAME}.zip ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip ; then
	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_${SERVICE}.py ${MERGED_IMAGESET_NAME} ${SIMULATION_NAME} ${BATH_VALUE} ${TOPO_VALUE} ${WI_THRESHOLD} ${WATER_INDEX}) ; then
		push_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_NAME}
		rm -rf ${PATH_TO_PRODUCTS}/${MERGED_IMAGESET_NAME}
		echo "[worsica_processing_service.sh] [Process] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: processed"
		exit 0
	else
		rm -rf ${PATH_TO_PRODUCTS}/${MERGED_IMAGESET_NAME}
		echo "[worsica_processing_service.sh] [Process] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: error-processing"
		exit 1
	fi
fi



