source ./worsica_bash_common.sh

function control_c {
    echo "[worsica_generating_topography_v2.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ $GENERATE_TOPO_STATE == *'generating-topo'* ]] ; then
    	GENERATE_TOPO_STATE='error-generating-topo'
    fi
    echo "[worsica_generating_topography_v2.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID}-gt${GENERATE_TOPO_ID} state: ${GENERATE_TOPO_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SERVICE=$1
USER_ID=$2
ROI_ID=$3
SIMULATION_ID=$4
GENERATE_TOPO_ID=$5
GENERATE_TOPO_STATE=$6
MERGED_IMAGESETS_NAME=$7
GENERATE_TOPO_NAME=$8
ZREF=$9
GT_GENERATE_FROM=${10}
COORDS_OR_FILENAME=${11}

PATH_TO_PRODUCTS=$(get_path_to_products_topo ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${GENERATE_TOPO_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Generating topography]
if [[ $GENERATE_TOPO_STATE == *'submitted'* ]] || [[ $GENERATE_TOPO_STATE == *'error-generating-topo'* ]] ; then
	create_folder_topo ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${GENERATE_TOPO_ID} ${GENERATE_TOPO_STATE}
	echo "[worsica_generating_topography_v2.sh] [Generating topography] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID}-gt${GENERATE_TOPO_ID} state: generating-topo"
	echo "==========================Generating topography=============================="
	#echo "[worsica_generating_topography_v2.sh] [Generating topography] Download content from the nextcloud ${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
	#download_folder ${PATH_TO_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}
	pull_multiple_processing_binary_topo ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${MERGED_IMAGESETS_NAME}
    #GT_GENERATE_FROM: -point or -tide?
	if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_Flood2Topo.py -path "${WORSICA_FOLDER_PATH}/${SERVICE}/user${USER_ID}/roi${ROI_ID}/simulation${SIMULATION_ID}" -outfolder "gt${GENERATE_TOPO_ID}" -zref ${ZREF} -${GT_GENERATE_FROM} "${COORDS_OR_FILENAME}" ) ; then
		push_processing_topo ${SERVICE} ${USER_ID} ${ROI_ID} ${SIMULATION_ID} ${GENERATE_TOPO_ID} ${GENERATE_TOPO_NAME}
		remove_multiple_processing ${MERGED_IMAGESETS_NAME} "${WORSICA_FOLDER_PATH}/${SERVICE}/user${USER_ID}/roi${ROI_ID}/simulation${SIMULATION_ID}"
        rm -rf ${PATH_TO_PRODUCTS}/${GENERATE_TOPO_NAME}
		echo "[worsica_generating_topography_v2.sh] [Generating topography] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID}-gt${GENERATE_TOPO_ID} state: generated-topo"
		exit 0
	else
		remove_multiple_processing ${MERGED_IMAGESETS_NAME} "${WORSICA_FOLDER_PATH}/${SERVICE}/user${USER_ID}/roi${ROI_ID}/simulation${SIMULATION_ID}"
		rm -rf ${PATH_TO_PRODUCTS}/${GENERATE_TOPO_NAME}
		echo "[worsica_generating_topography_v2.sh] [Generating topography] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-s${SIMULATION_ID}-gt${GENERATE_TOPO_ID} state: error-generating-topo"
		exit 1
	fi
fi