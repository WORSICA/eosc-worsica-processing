source ./worsica_bash_common_uc.sh

function control_c {
    echo "[worsica_calculate_anomaly_uc_v2.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ $MERGED_IMAGESET_STATE == *'calculating-diff'* ]] ; then
    	MERGED_IMAGESET_STATE='error-calculating-diff'
    fi
    echo "[worsica_calculate_anomaly_uc_v2.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: ${MERGED_IMAGESET_STATE}"
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
AVERAGE_IMAGE_NAME=$7
WATER_INDEX=$8
LD_IMAGE_NAME=$9
USERCHOSEN_ID=${10}

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID})
PATH_TO_PRODUCTS_SIM=$(get_path_to_products_sim ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Calculating anomaly]
if [[ $MERGED_IMAGESET_STATE == *'submitted'* ]] || [[ $MERGED_IMAGESET_STATE == *'stored'* ]] || [[ $MERGED_IMAGESET_STATE == *'error-calculating-diff'* ]] ; then
	#create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_STATE}
	echo "[worsica_calculate_anomaly_uc_v2.sh] [Calculating anomaly] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: calculating-diff"
	echo "==========================Calculating anomaly=============================="
	#echo "[worsica_calculate_anomaly_uc_v2.sh] [Calculating anomaly] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS_SIM} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${MERGED_IMAGESET_NAME}
    pull_processing_sim ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${AVERAGE_IMAGE_NAME}
	#move from /userchosen directory to /simulation
    mv ${PATH_TO_PRODUCTS}/${MERGED_IMAGESET_NAME} ${PATH_TO_PRODUCTS_SIM}/${MERGED_IMAGESET_NAME}
    if (cd ${PATH_TO_PRODUCTS_SIM} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_${SERVICE}_calculating_anomaly.py ${MERGED_IMAGESET_NAME} ${AVERAGE_IMAGE_NAME} "${WATER_INDEX}" ${LD_IMAGE_NAME}) ; then
		push_processing_sim ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${LD_IMAGE_NAME}
        rm -rf ${PATH_TO_PRODUCTS_SIM}/${AVERAGE_IMAGE_NAME}
		rm -rf ${PATH_TO_PRODUCTS_SIM}/${MERGED_IMAGESET_NAME}
		echo "[worsica_calculate_anomaly_uc_v2.sh] [Calculating anomaly] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: calculated-diff"
		exit 0
	else
		#rm -rf ${PATH_TO_PRODUCTS}
		echo "[worsica_calculate_anomaly_uc_v2.sh] [Calculating anomaly] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: error-calculating-diff"
		exit 1
	fi
fi
