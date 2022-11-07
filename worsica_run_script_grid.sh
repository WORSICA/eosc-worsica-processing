#Submit script to grid
#worsica_run_script_grid.sh [script_name_sh]
source ./worsica_run_script_grid_sensitive.sh

UDOCKER_VERSION=1.3.1
TAR_FILE=worsica-processing-dev.tar
TIMEOUT=5

#install udocker
echo "[worsica_run_script_grid.sh] 1) Download Udocker"
while true ; do
    if curl --max-time 600 -L https://github.com/indigo-dc/udocker/releases/download/${UDOCKER_VERSION}/udocker-${UDOCKER_VERSION}.tar.gz -o udocker-${UDOCKER_VERSION}.tar.gz && gzip -t udocker-${UDOCKER_VERSION}.tar.gz ; then
        echo "[worsica_run_script_grid.sh] downloaded!"
        break
    else
        echo "[worsica_run_script_grid.sh] retrying download!"
        sleep $TIMEOUT
    fi
done
echo "[worsica_run_script_grid.sh] 2) Install Udocker"
if tar zxvf udocker-${UDOCKER_VERSION}.tar.gz ; then 
    export PATH=`pwd`/udocker:$PATH
    udocker install
    echo "[worsica_run_script_grid.sh] Udocker installed!"
    break
else
    echo "[worsica_run_script_grid.sh] Fail installing udocker"
    exit 1
fi

#get the worsica-processing image and run
echo "[worsica_run_script_grid.sh] 3) Download the worsica-processing image"
#synch issues
retry=0
max_retries=10
while [ $retry -le $max_retries ] ; do
    echo "[worsica_run_script_grid.sh] downloading..."
    if [ $retry -eq $max_retries ] ; then
        echo "[worsica_run_script_grid.sh] Max retries exeeded, exit"
        exit 1
    fi
    if  curl --max-time 600 -u ${WDV_USER_PWD} -L ${NEXTCLOUD_URL}/remote.php/dav/files/worsicaAdmin/${TAR_FILE} -o ${TAR_FILE} && tar -tf ${TAR_FILE} ; then
        echo "[worsica_run_script_grid.sh] downloaded!"
        break
    else
        echo "[worsica_run_script_grid.sh] Failed on download, retrying!"
        retry=$((retry+1))
        sleep $TIMEOUT
    fi
done

echo "[worsica_run_script_grid.sh] 4) Load the worsica-processing image"
#synch issues
retry=0
max_retries=10
while [ $retry -le $max_retries ] ; do
    echo "[worsica_run_script_grid.sh] loading..."
    if [ $retry -eq $max_retries ] ; then
        echo "[worsica_run_script_grid.sh] Max retries exeeded, exit"
        exit 1
    fi
    if udocker load -i ${TAR_FILE} ; then
        echo "[worsica_run_script_grid.sh] Loaded"
        break
    else
        echo "[worsica_run_script_grid.sh] Failed on load, retrying"
        retry=$((retry+1))
        sleep $TIMEOUT
    fi
done

#run
echo "[worsica_run_script_grid.sh] 5) Run command"
if udocker run worsica/worsica-processing:development /bin/bash -c "$(cat mycommand.txt)" ; then 
    echo "[worsica_run_script_grid.sh] Success on run"
    exit 0
else
    echo "[worsica_run_script_grid.sh] Failed on run"
    exit 1
fi
