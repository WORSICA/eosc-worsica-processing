
CREDENTIALS=""
function get_nextcloud_credentials_from_file {
    CREDENTIALS_FILE="/usr/local/worsica_web_products/nc-credentials"
    if [[ -f ${CREDENTIALS_FILE} ]] ; then
        CREDENTIALS=$(cat ${CREDENTIALS_FILE})
        echo "[worsica_bash_common_uc.sh] [get_nextcloud_credentials_from_file] [SUCCESS] Found nextcloud credentials (${CREDENTIALS_FILE})"
    else
        echo "[worsica_bash_common_uc.sh] [get_nextcloud_credentials_from_file] [FAILURE] Error, no credentials found, abort. (${CREDENTIALS_FILE})"
        exit 1
    fi
}

#affect the ROI_SIMULATION_FOLDER and PATH_TO_PRODUCTS
WORSICA_FOLDER_PATH=$(pwd)
ROI_SIMULATION_FOLDER=""
ROI_SIMULATION_FOLDER_SIM=""
PATH_TO_PRODUCTS=""
PATH_TO_PRODUCTS_SIM=""
function set_path_to_products {
    #$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    ROI_SIMULATION_FOLDER="$1/user$2/roi$3/userchosen$4"
    PATH_TO_PRODUCTS="${WORSICA_FOLDER_PATH}/${ROI_SIMULATION_FOLDER}"
    #echo "[worsica_bash_common_uc.sh] [set_path_to_products] Register PATH_TO_PRODUCTS=${PATH_TO_PRODUCTS}"
}
function set_path_to_products_sim {
	#$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    ROI_SIMULATION_FOLDER_SIM="$1/user$2/roi$3/simulation$4"
    PATH_TO_PRODUCTS_SIM="${WORSICA_FOLDER_PATH}/${ROI_SIMULATION_FOLDER_SIM}"
    #echo "[worsica_bash_common_uc.sh] [set_path_to_products_sim] Register PATH_TO_PRODUCTS=${PATH_TO_PRODUCTS}"

}
#get path, when calling this function from an external script bash
function get_path_to_products {
    #$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    set_path_to_products $1 $2 $3 $4
    echo PATH_TO_PRODUCTS
}
function get_roi_simulation_folder {
    #$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    set_path_to_products $1 $2 $3 $4
    echo ROI_SIMULATION_FOLDER
}
function get_path_to_products_sim {
    #$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    set_path_to_products_sim $1 $2 $3 $4
    echo ${PATH_TO_PRODUCTS_SIM}
}
function get_roi_simulation_folder_sim {
    #$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    set_path_to_products_sim $1 $2 $3 $4
    echo ROI_SIMULATION_FOLDER_SIM
}

#affect the NEXTCLOUD_PATH_TO_PRODUCTS
NEXTCLOUD_WEBDAV_PATH="remote.php/dav/files/worsicaAdmin"
NEXTCLOUD_REMOTE_PATH="http://nextcloud/${NEXTCLOUD_WEBDAV_PATH}"
NEXTCLOUD_PATH_TO_REPOSITORY="${NEXTCLOUD_REMOTE_PATH}/repository_images"
NEXTCLOUD_PATH_TO_PRODUCTS=""
function set_nextcloud_path_to_products {
    #$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    set_path_to_products $1 $2 $3 $4
    NEXTCLOUD_PATH_TO_PRODUCTS="${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER}"
    #echo "[worsica_bash_common_uc.sh] [set_nextcloud_path_to_products] Register NEXTCLOUD_PATH_TO_PRODUCTS=${NEXTCLOUD_PATH_TO_PRODUCTS}"
}
function set_nextcloud_path_to_products_sim {
    #$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    set_path_to_products_sim $1 $2 $3 $4
    NEXTCLOUD_PATH_TO_PRODUCTS="${NEXTCLOUD_REMOTE_PATH}/${ROI_SIMULATION_FOLDER_SIM}"
    #echo "[worsica_bash_common_uc.sh] [set_nextcloud_path_to_products] Register NEXTCLOUD_PATH_TO_PRODUCTS=${NEXTCLOUD_PATH_TO_PRODUCTS}"
}
#get nextcloud path, when calling this function from an external script bash
function get_nextcloud_path_to_products {
    #$1 SERVICE
    #$2 USER_ID
    #$3 ROI_ID
    #$4 USERCHOSEN_ID
    set_nextcloud_path_to_products $1 $2 $3 $4
    echo PATH_TO_PRODUCTS
}


function create_folder {
    #$1 is ${SERVICE}
	#$2 is ${USER_ID}
	#$3 is ${ROI_ID} 
	#$4 is ${USERCHOSEN_ID}
    #$5 is ${SIMULATION_STATE}

    get_nextcloud_credentials_from_file
    set_nextcloud_path_to_products $1 $2 $3 $4

	echo "[worsica_bash_common_uc.sh] [create_folder] $1-user$2-roi$3-uc$4 state: $5"
	echo "============================START============================"
	echo "[worsica_bash_common_uc.sh] [create_folder] Check if folder exists"
	if cd "${PATH_TO_PRODUCTS}" ; then
		echo "[worsica_bash_common_uc.sh] [create_folder] Found folder, no need to create"
	else
		echo "[worsica_bash_common_uc.sh] [create_folder] [FAILURE] Folder does not exist"
		echo "[worsica_bash_common_uc.sh] [create_folder] Create folder ${PATH_TO_PRODUCTS}"
		if mkdir -p "${PATH_TO_PRODUCTS}" ; then
			echo "[worsica_bash_common_uc.sh] [create_folder] [SUCCESS] Created folder, change directory"
			cd "${PATH_TO_PRODUCTS}"
			echo $(pwd)
		else
			echo "[worsica_bash_common_uc.sh] [create_folder] [FAILURE] Unable to create folder"
			exit 1
		fi
	fi
	echo "[worsica_bash_common_uc.sh] [create_folder] Check if nextcloud folder exists"
	CURL_STATUS=$(curl -u ${CREDENTIALS} -X PROPFIND ${NEXTCLOUD_PATH_TO_PRODUCTS} -w '<http_code>%{http_code}</http_code>' | grep -oP '(?<=<http_code>).*?(?=</http_code>)')
	echo $CURL_STATUS
    if [[ $CURL_STATUS -eq 200 ]] || [[ $CURL_STATUS -eq 207 ]] ; then
		echo "[worsica_bash_common_uc.sh] [create_folder] [SUCCESS] Nextcloud ${NEXTCLOUD_PATH_TO_PRODUCTS} folder exists"
	else
		#create folders inside nextcloud
		#create the workspace folder, then the simulation folder
		echo "[worsica_bash_common_uc.sh] [create_folder] Nextcloud ${NEXTCLOUD_PATH_TO_PRODUCTS} folder does not exist"
		CURL_STATUS=$(curl -u ${CREDENTIALS} -X MKCOL "${NEXTCLOUD_REMOTE_PATH}/$1" -w '<http_code>%{http_code}</http_code>' | grep -oP '(?<=<http_code>).*?(?=</http_code>)')
		echo $CURL_STATUS
		if [[ $CURL_STATUS -eq 201 ]] || [[ $CURL_STATUS -eq 405 ]] ; then
			echo "[worsica_bash_common_uc.sh] [create_folder] Nextcloud ${NEXTCLOUD_PATH_TO_PRODUCTS}/$1 folder does not exist"
			CURL_STATUS=$(curl -u ${CREDENTIALS} -X MKCOL "${NEXTCLOUD_REMOTE_PATH}/$1/user$2" -w '<http_code>%{http_code}</http_code>' | grep -oP '(?<=<http_code>).*?(?=</http_code>)')
			echo $CURL_STATUS
			if [[ $CURL_STATUS -eq 201 ]] || [[ $CURL_STATUS -eq 405 ]] ; then
				echo "[worsica_bash_common_uc.sh] [create_folder] Nextcloud ${NEXTCLOUD_PATH_TO_PRODUCTS}/$1/user$2 folder does not exist"
				CURL_STATUS=$(curl -u ${CREDENTIALS} -X MKCOL "${NEXTCLOUD_REMOTE_PATH}/$1/user$2/roi$3" -w '<http_code>%{http_code}</http_code>' | grep -oP '(?<=<http_code>).*?(?=</http_code>)')
				echo $CURL_STATUS
				if [[ $CURL_STATUS -eq 201 ]] || [[ $CURL_STATUS -eq 405 ]] ; then
					echo "[worsica_bash_common_uc.sh] [create_folder] Nextcloud ${NEXTCLOUD_PATH_TO_PRODUCTS}/$1/user$2/roi$3 folder does not exist"
					CURL_STATUS=$(curl -u ${CREDENTIALS} -X MKCOL "${NEXTCLOUD_REMOTE_PATH}/$1/user$2/roi$3/userchosen$4" -w '<http_code>%{http_code}</http_code>' | grep -oP '(?<=<http_code>).*?(?=</http_code>)')
					echo $CURL_STATUS
					if [[ $CURL_STATUS -eq 201 ]] || [[ $CURL_STATUS -eq 405 ]] ; then
						echo "[worsica_bash_common_uc.sh] [create_folder] [SUCCESS] Created nextcloud folder ${NEXTCLOUD_PATH_TO_PRODUCTS}, change directory"
					else
						echo "[worsica_bash_common_uc.sh] [create_folder] [FAILURE] Unable to create nextcloud folder /userchosen$4 in ${NEXTCLOUD_REMOTE_PATH}/$1/user$2/roi$3"
						exit 1
					fi
				else
					echo "[worsica_bash_common_uc.sh] [create_folder] [FAILURE] Unable to create nextcloud folder /roi$3 in ${NEXTCLOUD_REMOTE_PATH}/$1/user$2"
					exit 1
				fi
			else
				echo "[worsica_bash_common_uc.sh] [create_folder] [FAILURE] Unable to create nextcloud folder /user$2 in ${NEXTCLOUD_REMOTE_PATH}/$1"
				exit 1
			fi
		else
			echo "[worsica_bash_common_uc.sh] [create_folder] [FAILURE] Unable to create nextcloud folder /$1 in ${NEXTCLOUD_REMOTE_PATH}"
			exit 1
		fi
	fi
}

function upload_file {
	#$1 source 
	#$2 destination (nextcloud)
	#upload_file ${IMAGESET_NAME}.zip '${NEXTCLOUD_PATH_TO_REPOSITORY}/${IMAGESET_NAME}.zip'
	#states: 201 (CREATED), 204
	#(STATUS=$(curl -u ${CREDENTIALS} -T w1a.log 'http://nextcloud/remote.php/dav/files/worsicaAdmin/w1a.log' -w '<http_code>%{http_code}</http_code>' | grep -oP '(?<=<http_code>).*?(?=</http_code>)'); echo $STATUS; if [ $STATUS -eq 201 ]; then echo 'OK'; else echo 'Fail'; fi)
	get_nextcloud_credentials_from_file
    echo "[worsica_bash_common_uc.sh] [upload_file] Uploading $1 to $2";
	CURL_STATUS=$(curl --max-time 60 -u ${CREDENTIALS} -T $1 $2 -w '<http_code>%{http_code}</http_code>' | grep -oP '(?<=<http_code>).*?(?=</http_code>)')
	echo $CURL_STATUS
	if [[ $CURL_STATUS -eq 201 ]] || [[ $CURL_STATUS -eq 204 ]]; then
		echo "[worsica_bash_common_uc.sh] [upload_file] [SUCCESS] Uploaded to nextcloud $1 to $2"
	else
		echo "[worsica_bash_common_uc.sh] [upload_file] [FAILURE] Fail upload to nextcloud $1 to $2"
		exit 1
	fi
}

function download_file {
	#$1 source (nextcloud)
	#$2 destination
	#download_file ${f} ${PATH_TO_PRODUCTS}/${f2}
	#states: 200 (OK), 404
	#(STATUS=$(curl -u ${CREDENTIALS} -kL 'http://nextcloud/remote.php/dav/files/worsicaAdmin/w2.log' -w '<http_code>%{http_code}</http_code>' -o w2.log | grep -oP '(?<=<http_code>).*?(?=</http_code>)'); echo $STATUS; if [ $STATUS -eq 200 ]; then echo 'OK'; else echo 'Fail'; fi)
	get_nextcloud_credentials_from_file
    echo "[worsica_bash_common_uc.sh] [download_file] Downloading $1 to $2";
	CURL_STATUS=$(curl --max-time 60 -u ${CREDENTIALS} -kL $1 -o $2 -w '<http_code>%{http_code}</http_code>' | grep -oP '(?<=<http_code>).*?(?=</http_code>)')
	if [[ $CURL_STATUS -eq 200 ]] ; then
		echo "[worsica_bash_common_uc.sh] [download_file] [SUCCESS] Downloaded $1 to $2";
	else
		echo "[worsica_bash_common_uc.sh] [download_file] [FAILURE] Failed downloading $1 to $2. File does not exist or a problem occured with the download.";
		rm -rf $2 #remove the file from host, it will output trash
		exit 1
	fi
}

#$1 is full nextcloud path ${NEXTCLOUD_PATH_TO_PRODUCTS}	
function list_files_nextcloud {
	get_nextcloud_credentials_from_file
	LF=$(curl -u ${CREDENTIALS} -X PROPFIND $1)
	echo $LF | grep -oP '(?<=<d:href>).*?(?=</d:href>)'
}

#load the processing state from nextcloud
function pull_processing {
	#$1 is ${SERVICE}
	#$2 is ${USER_ID}
	#$3 is ${ROI_ID} 
	#$4 is ${USERCHOSEN_ID}
	#$5 is ${IMAGESET_NAME}
    TAR_FILE_PREFIX=$1-user$2-roi$3-uc$4-$5
    set_nextcloud_path_to_products $1 $2 $3 $4
	
    echo "[worsica_bash_common_uc.sh] [pull_processing] Check for final products ${TAR_FILE_PREFIX}"
	LIST_FILES=$(list_files_nextcloud ${NEXTCLOUD_PATH_TO_PRODUCTS})
	f2="${TAR_FILE_PREFIX}-final-products.zip"
	if [[ ${LIST_FILES} == *${f2}* ]]; then
		echo "[worsica_bash_common_uc.sh] [pull_processing] $f2 found, downloading tar ..."
		download_file ${NEXTCLOUD_PATH_TO_PRODUCTS}/$f2 ${WORSICA_FOLDER_PATH}/$f2
		cd ${WORSICA_FOLDER_PATH}
		unzip -o ${WORSICA_FOLDER_PATH}/$f2
		rm -rf $f2
	else
		echo "[worsica_bash_common_uc.sh] [pull_processing] $f2 not found, skip ..."					
	fi
	#done
}

#load the processing state from nextcloud
function pull_processing_sim {
	#$1 is ${SERVICE}
	#$2 is ${USER_ID}
	#$3 is ${ROI_ID} 
	#$4 is ${USERCHOSEN_ID}
	#$5 is ${IMAGESET_NAME}
    TAR_FILE_PREFIX=$1-user$2-roi$3-s$4-$5
    set_nextcloud_path_to_products_sim $1 $2 $3 $4
	
    echo "[worsica_bash_common_uc.sh] [pull_processing_sim] Check for final products ${TAR_FILE_PREFIX}"
	LIST_FILES=$(list_files_nextcloud ${NEXTCLOUD_PATH_TO_PRODUCTS})
	f2="${TAR_FILE_PREFIX}-final-products.zip"
	if [[ ${LIST_FILES} == *${f2}* ]]; then
		echo "[worsica_bash_common_uc.sh] [pull_processing_sim] $f2 found, downloading tar ..."
		download_file ${NEXTCLOUD_PATH_TO_PRODUCTS}/$f2 ${WORSICA_FOLDER_PATH}/$f2
		cd ${WORSICA_FOLDER_PATH}
		unzip -o ${WORSICA_FOLDER_PATH}/$f2
		rm -rf $f2
	else
		echo "[worsica_bash_common_uc.sh] [pull_processing_sim] $f2 not found, skip ..."					
	fi
	#done
}

#load the processing state from nextcloud
function remove_multiple_processing {
	#$1 is ${IMAGESETS_NAME} string by comma joined
	#$2 is ${PATH_TO_PRODUCTS} 
    echo "[worsica_bash_common_uc.sh] [remove_multiple_processing] Remove multiple imagesets $1"
    #IFS=','
    for i in $(echo $1 | sed "s/,/ /g") ; do #`echo "$1"`; do 
        echo "[worsica_bash_common_uc.sh] [remove_multiple_processing] Remove $2/$i"
        rm -rf $2/$i
    done
}
function pull_multiple_processing {
	#$1 is ${SERVICE}
	#$2 is ${USER_ID}
	#$3 is ${ROI_ID} 
	#$4 is ${USERCHOSEN_ID}
	#$5 is ${IMAGESETS_NAME} string by comma joined
    echo "[worsica_bash_common_uc.sh] [pull_multiple_processing] Pull multiple imagesets"
    #IFS=','
    for i in $(echo $5 | sed "s/,/ /g") ; do # `echo "$5"`; do  
        echo "[worsica_bash_common_uc.sh] [pull_multiple_processing] Pull $i"
        pull_processing $1 $2 $3 $4 $i
    done
}
function push_processing {
	#$1 is ${SERVICE}
	#$2 is ${USER_ID}
	#$3 is ${ROI_ID} 
	#$4 is ${USERCHOSEN_ID}
	#$5 is ${IMAGESET_NAME}
	#upload workspace to nextcloud as tar gz
	#upload_folder ${PATH_TO_PRODUCTS} '${NEXTCLOUD_PATH_TO_PRODUCTS}'
    set_nextcloud_path_to_products $1 $2 $3 $4
    TAR_FILE_PREFIX=$1-user$2-roi$3-uc$4-$5
    
	cd ${WORSICA_FOLDER_PATH}
	TAR_FILE_FINAL_PRODUCTS=${TAR_FILE_PREFIX}-final-products.zip
	echo "[worsica_bash_common_uc.sh] [push_processing] Tar ${TAR_FILE_FINAL_PRODUCTS}"
	if (zip -r ${TAR_FILE_FINAL_PRODUCTS} ${ROI_SIMULATION_FOLDER}/$5); then
		echo "[worsica_bash_common_uc.sh] [push_processing] Upload tar ${TAR_FILE_FINAL_PRODUCTS} to nextcloud"
		upload_file ${WORSICA_FOLDER_PATH}/${TAR_FILE_FINAL_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}/${TAR_FILE_FINAL_PRODUCTS}
		rm -rf ${ROI_SIMULATION_FOLDER}/$5
		rm -rf ${TAR_FILE_FINAL_PRODUCTS}
	else
		echo "[worsica_bash_common_uc.sh] [push_processing] Files/folders not found to tar ${TAR_FILE_FINAL_PRODUCTS} to nextcloud, moving on"
	fi
}
function push_processing_sim {
	#$1 is ${SERVICE}
	#$2 is ${USER_ID}
	#$3 is ${ROI_ID} 
	#$4 is ${USERCHOSEN_ID}
	#$5 is ${IMAGESET_NAME}
	#upload workspace to nextcloud as tar gz
	#upload_folder ${PATH_TO_PRODUCTS} '${NEXTCLOUD_PATH_TO_PRODUCTS}'
    set_nextcloud_path_to_products_sim $1 $2 $3 $4
    TAR_FILE_PREFIX=$1-user$2-roi$3-s$4-$5
    
	cd ${WORSICA_FOLDER_PATH}
	TAR_FILE_FINAL_PRODUCTS=${TAR_FILE_PREFIX}-final-products.zip
	echo "[worsica_bash_common_uc.sh] [push_processing] Tar ${TAR_FILE_FINAL_PRODUCTS}"
	if (zip -r ${TAR_FILE_FINAL_PRODUCTS} ${ROI_SIMULATION_FOLDER_SIM}/$5); then
		echo "[worsica_bash_common_uc.sh] [push_processing] Upload tar ${TAR_FILE_FINAL_PRODUCTS} to nextcloud"
		upload_file ${WORSICA_FOLDER_PATH}/${TAR_FILE_FINAL_PRODUCTS} ${NEXTCLOUD_PATH_TO_PRODUCTS}/${TAR_FILE_FINAL_PRODUCTS}
		rm -rf ${ROI_SIMULATION_FOLDER_SIM}/$5
		rm -rf ${TAR_FILE_FINAL_PRODUCTS}
	else
		echo "[worsica_bash_common_uc.sh] [push_processing] Files/folders not found to tar ${TAR_FILE_FINAL_PRODUCTS} to nextcloud, moving on"
	fi
}

function pull_imageset {
    #$1 is ${SERVICE}
	#$2 is ${USER_ID}
	#$3 is ${ROI_ID} 
	#$4 is ${USERCHOSEN_ID}
	#$5 is ${IMAGESET_NAME}
    set_path_to_products $1 $2 $3 $4
	echo "[worsica_bash_common_uc.sh] [pull_imageset] Download the imageset from the ${NEXTCLOUD_PATH_TO_REPOSITORY}/$5.zip to the ${PATH_TO_PRODUCTS}/$5.zip"
	LIST_FILES=$(list_files_nextcloud ${NEXTCLOUD_PATH_TO_REPOSITORY})
	#download_file ${NEXTCLOUD_PATH_TO_REPOSITORY}/${f2} ${PATH_TO_PRODUCTS}/${f2}
	f2="$5.zip"
	#for f in $(list_files_nextcloud ${NEXTCLOUD_PATH_TO_REPOSITORY}); do 
	#	f2=${f#/${NEXTCLOUD_WEBDAV_PATH}/repository_images/}
	#	echo $f2
	if [[ ${LIST_FILES} == *${f2}* ]]; then
		echo "[worsica_bash_common_uc.sh] [pull_imageset] $f2 found, downloading zip..."
		download_file ${NEXTCLOUD_PATH_TO_REPOSITORY}/$f2 ${PATH_TO_PRODUCTS}/$f2
	else
		echo "[worsica_bash_common_uc.sh] [pull_imageset] $f2 not found, skip..."
	fi
	#done
}

#store the processing state to nextcloud
function push_imageset {
	#$1 is ${SERVICE}
	#$2 is ${USER_ID}
	#$3 is ${ROI_ID} 
	#$4 is ${USERCHOSEN_ID}
	#$5 is ${IMAGESET_NAME}
    set_path_to_products $1 $2 $3 $4
	echo "[worsica_bash_common_uc.sh] [push_imageset] Upload $5.zip"
	upload_file ${PATH_TO_PRODUCTS}/$5.zip ${NEXTCLOUD_PATH_TO_REPOSITORY}/$5.zip
	echo "[worsica_bash_common_uc.sh] [push_imageset] Remove zip and sha1 files on host side"
	#rm -rf ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip.sha1 ${PATH_TO_PRODUCTS}/${IMAGESET_NAME}.zip
	rm -rf ${PATH_TO_PRODUCTS}/$5.zip
}
