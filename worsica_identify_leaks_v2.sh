source ./worsica_bash_common.sh

function control_c {
    echo "[worsica_identify_leaks_v2.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ $MERGED_IMAGESET_STATE == *'determinating-leak'* ]] ; then
    	MERGED_IMAGESET_STATE='error-determinating-leak'
    fi
    echo "[worsica_identify_leaks_v2.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: ${MERGED_IMAGESET_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SERVICE=$1
USER_ID=$2
ROI_ID=$3
SIMULATION_ID=$4
MERGED_IMAGESET_STATE=$5
MERGED_IMAGESET_NAME=$6
WATER_INDEX=$7
FLAG_ANOMALY=$8
LD_IMAGE_NAME=$9
FILTER_BY_MASK=${10}

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Identifying leaks]
#'stored-calculated-leak','error-determinating-leak'
if [[ $MERGED_IMAGESET_STATE == *'stored-determinated-leak'* ]] || [[ $MERGED_IMAGESET_STATE == *'stored-calculated-leak'* ]] || [[ $MERGED_IMAGESET_STATE == *'generated-mask-leak'* ]] || [[ $MERGED_IMAGESET_STATE == *'error-determinating-leak'* ]] ; then
	#create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_STATE}
	echo "[worsica_identify_leaks_v2.sh] [Identifying leaks] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: determinating-leak"
	echo "==========================Identifying leaks=============================="
	#echo "[worsica_identify_leaks_v2.sh] [Identifying leaks] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${LD_IMAGE_NAME}
	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_${SERVICE}_identifying_leaks.py ${MERGED_IMAGESET_NAME} "${WATER_INDEX}" ${FLAG_ANOMALY} ${LD_IMAGE_NAME} ${FILTER_BY_MASK}) ; then
		push_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${LD_IMAGE_NAME}
		echo "[worsica_identify_leaks_v2.sh] [Identifying leaks] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: determinated-leak"
		exit 0
	else
		#rm -rf ${PATH_TO_PRODUCTS}
		echo "[worsica_identify_leaks_v2.sh] [Identifying leaks] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: error-determinating-leak"
		exit 1
	fi
fi
