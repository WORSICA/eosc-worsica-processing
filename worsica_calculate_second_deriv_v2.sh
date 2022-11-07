source ./worsica_bash_common.sh

function control_c {
    echo "[worsica_calculate_second_deriv_v2.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ $MERGED_IMAGESET_STATE == *'calculating-diff'* ]] ; then
    	MERGED_IMAGESET_STATE='error-calculating-diff'
    fi
    echo "[worsica_calculate_second_deriv_v2.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: ${MERGED_IMAGESET_STATE}"
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

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Calculating 2nd deriv]
if [[ $MERGED_IMAGESET_STATE == *'submitted'* ]] || [[ $MERGED_IMAGESET_STATE == *'calculated-diff'* ]] || [[ $MERGED_IMAGESET_STATE == *'error-calculating-leak'* ]] ; then
	#create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_STATE}
	echo "[worsica_calculate_second_deriv_v2.sh] [Calculating 2nd deriv] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: calculating-leak"
	echo "==========================Calculating 2nd deriv=============================="
	#echo "[worsica_calculate_second_deriv_v2.sh] [Calculating 2nd deriv] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	if [[ $FLAG_ANOMALY == *'by_index'* ]] ; then
		pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESET_NAME}
	else
		pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${LD_IMAGE_NAME}
	fi	

	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_${SERVICE}_calculating_second_deriv.py ${MERGED_IMAGESET_NAME} "${WATER_INDEX}" ${FLAG_ANOMALY} ${LD_IMAGE_NAME}) ; then
		push_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${LD_IMAGE_NAME}
		if [[ $FLAG_ANOMALY == *'by_index'* ]] ; then
			rm -rf ${PATH_TO_PRODUCTS}/${MERGED_IMAGESET_NAME}
		fi
		echo "[worsica_calculate_second_deriv_v2.sh] [Calculating 2nd deriv] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: calculated-leak"
		exit 0
	else
		#rm -rf ${PATH_TO_PRODUCTS}
		echo "[worsica_calculate_second_deriv_v2.sh] [Calculating 2nd deriv] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: error-calculating-leak"
		exit 1
	fi
fi
