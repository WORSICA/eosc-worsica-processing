source ./worsica_bash_common_uc.sh

function control_c {
    echo "[worsica_downloading_service_uc_v2.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    if [[ ${USERCHOSEN_STATE} == *'downloading'* ]] ; then
    	USERCHOSEN_STATE='error-downloading'
    fi
    echo "[worsica_downloading_service_uc_v2.sh] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: ${USERCHOSEN_STATE}"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SERVICE=$1
USER_ID=$2
ROI_ID=$3
USERCHOSEN_ID=$4
USERCHOSEN_STATE=$5
UUID=$6
IMAGESET_NAME=$7
ESA_USER_ID=$8
IMAGESET_STATE=$9
PROVIDER=${10}

PATH_TO_PRODUCTS=$(get_path_to_products ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID})
WORSICA_FOLDER_PATH=$(pwd)

#[Download]
#cd /usr/local/worsica_web_products/workspace-1/userchosen33 && 
if [[ ${USERCHOSEN_STATE} == *'submitted'* ]] || [[ ${USERCHOSEN_STATE} == *'error-downloading'* ]] || [[ ${USERCHOSEN_STATE} == *'error-download-corrupt'* ]] || [[ ${IMAGESET_STATE} == *'download-timeout-retry'* ]] ; then
	create_folder ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${USERCHOSEN_STATE}
	echo "[worsica_downloading_service_uc_v2.sh] [Download] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: downloading"
	echo "============================DOWNLOADING============================"
	#try to get the downloaded imageset from repository whether its submitted or eror downloading
	#if download corrupt, do not grab it again!
	#if [[ ${USERCHOSEN_STATE} == *'submitted'* ]] || [[ ${USERCHOSEN_STATE} == *'error-downloading'* ]] ; then
	pull_imageset ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${IMAGESET_NAME}
	#fi
	#if [[ ${IMAGESET_STATE} == *'error-download-corrupt'* ]] || [[ ${IMAGESET_STATE} == *'download-timeout-retry' ]] ; then
	if [[ ${PROVIDER} == *'gcp'* ]]; then
		#download from google
		rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip.incomplete
		if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_ph0_download_gcp_sentinel.py ${IMAGESET_NAME}) ; then
			rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.SAFE
			echo "[worsica_downloading_service_uc_v2.sh] [Download] Checking if file is corrupt"	
			if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_ph0_check_download_v2.py ${IMAGESET_NAME}) ; then  			
				echo "[worsica_downloading_service_uc_v2.sh] [Download] Start uploading to nextcloud"	
				#upload imageset to another place
				push_imageset ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${IMAGESET_NAME}
				echo "[worsica_downloading_service_uc_v2.sh] [Download] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: downloaded"		
				exit 0
			else
				echo "[worsica_downloading_service_uc_v2.sh] [Download] File Corrupt! "
				echo "[worsica_downloading_service_uc_v2.sh] [Download] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: state: error-download-corrupt"		
				#delete it!
				rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip
				exit 1
			fi
		else
			echo "[worsica_downloading_service_uc_v2.sh] [Download] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: error-downloading-gcp (Download failed or folder does not exist)"
			exit 1
		fi
	else
		if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_ph0_download_v2.py ${UUID}) ; then
			echo "[worsica_downloading_service_uc_v2.sh] [Download] Checking if file is corrupt"	
			if (cd ${PATH_TO_PRODUCTS} && python3 -u ${WORSICA_FOLDER_PATH}/worsica_ph0_check_download_v2.py ${IMAGESET_NAME}) ; then  			
				echo "[worsica_downloading_service_uc_v2.sh] [Download] Start uploading to nextcloud"	
				#upload imageset to another place
				push_imageset ${SERVICE} ${USER_ID} ${ROI_ID} ${USERCHOSEN_ID} ${IMAGESET_NAME}
				echo "[worsica_downloading_service_uc_v2.sh] [Download] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: downloaded"		
				exit 0
			else
				echo "[worsica_downloading_service_uc_v2.sh] [Download] File Corrupt! "
				echo "[worsica_downloading_service_uc_v2.sh] [Download] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: state: error-download-corrupt"		
				#delete it!
				rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip
				exit 1
			fi
		else
			echo "[worsica_downloading_service_uc_v2.sh] [Download] ${SERVICE}-user${USER_ID}-roi${ROI_ID}-uc${USERCHOSEN_ID} state: error-downloading-esa (Download failed or folder does not exist)"
			exit 1
		fi
	fi
fi