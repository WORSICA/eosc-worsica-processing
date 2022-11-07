source ./worsica_bash_common_uc.sh

function control_c {
    echo "[worsica_resampling_service_uc_v2.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ ${USERCHOSEN_STATE} == *'resampling'* ]] ; then
    	USERCHOSEN_STATE='error-resampling'
    fi
    echo "[worsica_resampling_service_uc_v2.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: ${USERCHOSEN_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SERVICE=$1
USER_ID=$2
ROI_ID=$3
USERCHOSEN_ID=$4
USERCHOSEN_STATE=$5
USERCHOSEN_NAME=$6
IMAGESET_NAME=$7
GEOJSON_POLYGON=$8

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Resampling]
if [[ ${USERCHOSEN_STATE} == *'downloaded'* ]] || [[ ${USERCHOSEN_STATE} == *'error-resampling'* ]] || [[ ${USERCHOSEN_STATE} == *'converted'* ]] ; then
	create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${USERCHOSEN_STATE}
	echo "[worsica_resampling_service_uc_v2.sh] [Resampling] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: resampling"
	echo "==========================RESAMPLING=============================="
	#echo "[worsica_resampling_service_uc_v2.sh] [Resampling] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	pull_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${IMAGESET_NAME}
	pull_imageset ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${IMAGESET_NAME}
	#if download_file ${NEXTCLOUD_PATH_TO_REPOSITORY}/${IMAGESET_NAME}.zip ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip ; then
	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_sentinel_script_v5_resampling.py ${IMAGESET_NAME} ${USERCHOSEN_NAME} "${GEOJSON_POLYGON}" ${SERVICE} ); then
		rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip
		push_processing ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${IMAGESET_NAME}
		#remove folder (either .safe or not)
		rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}*
		echo "[worsica_resampling_service_uc_v2.sh] [Resampling] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: resampled"
		exit 0
	else
		#remove imageset to free up the workspace folder
		rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip
		#remove folder (either .safe or not)
		rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}*
		echo "[worsica_resampling_service_uc_v2.sh] [Resampling] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: error-resampling"
		exit 1
	fi
fi