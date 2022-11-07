source ./worsica_bash_common.sh

function control_c {
    echo "[worsica_generating_virtual_imgs_service.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ $SIMULATION_STATE == *'generating-virtual'* ]] ; then
    	SIMULATION_STATE='error-generating-virtual'
    fi
    echo "[worsica_generating_virtual_imgs_service.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: ${SIMULATION_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SERVICE=$1
USER_ID=$2
ROI_ID=$3
SIMULATION_ID=$4
SIMULATION_STATE=$5
VIRTUAL_IMAGESET_NAME=$6
SIMULATION_NAME=$7
SAMPLE_IMAGESET_NAME=$8
SIMULATION_NAME2=$9

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Generating virtual]
if [[ $SIMULATION_STATE == *'merged'* ]] || [[ $SIMULATION_STATE == *'error-generating-virtual'* ]] ; then
	create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${SIMULATION_STATE}
	echo "[worsica_generating_virtual_imgs_service.sh] [Generating virtual] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: generating-virtual"
	echo "==========================Generating virtual images=============================="
	#echo "[worsica_generating_virtual_imgs_service.sh] [Generating virtual] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	#pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${VIRTUAL_IMAGESET_NAME}
	#pull_imageset
	if (cd ${PATH_TO_PRODUCTS}/${SAMPLE_IMAGESET_NAME}) ; then
		echo "Image ${SAMPLE_IMAGESET_NAME} already downloaded. "
	else
		echo "Image ${SAMPLE_IMAGESET_NAME} needs to be downloaded. "
    	pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${SAMPLE_IMAGESET_NAME}
	fi
	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_${SERVICE}_generating_virtual.py ${VIRTUAL_IMAGESET_NAME} ${SIMULATION_NAME} ${SAMPLE_IMAGESET_NAME} ${SIMULATION_NAME2}) ; then
		push_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${VIRTUAL_IMAGESET_NAME}
		#rm -rf ${PATH_TO_PRODUCTS}
		echo "[worsica_generating_virtual_imgs_service.sh] [Generating virtual] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: generated-virtual"
		exit 0
	else
		#rm -rf ${PATH_TO_PRODUCTS}
		echo "[worsica_generating_virtual_imgs_service.sh] [Generating virtual] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID} state: error-generating-virtual"
		exit 1
	fi
fi