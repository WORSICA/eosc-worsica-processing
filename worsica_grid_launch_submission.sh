#./worsica_grid_launch_submission.sh teste3 "[./worsica_downloading_service_v2.sh coastal 999 999 999 submitted b8ca9170-e895-4b2e-b866-ab71fc2c5dbc S2A_MSIL2A_20200929T113321_N0214_R080_T29TME_20200929T143142]" $HOME/worsica_web_products/log/teste3.test.log
source ./worsica_grid_launch_submission_sensitive.sh

function control_c {
    echo "[worsica_grid_launch_submission.sh] HALT! Caught ctrl+c; Clean up and Exit \n"
    echo "[worsica_grid_launch_submission.sh] ${SUBMISSION_NAME} state: killed"
    exit 1
}
trap control_c SIGINT
trap control_c SIGTERM

SUBMISSION_NAME=$1
SCRIPT_FILE=$2
SANITIZE_SCRIPT_FILE=${SCRIPT_FILE:1:-1}
LOG_FILEPATH=$3

JOBID_FILEPATH=$HOME/worsica_web_products/grid/jobids/$1.job.id
XRSL_FILEPATH=$HOME/worsica_web_products/grid/filesubs/$1.xrsl
COMMAND_FILEPATH=$HOME/worsica_web_products/grid/filesubs/$1.mycommand

TIME_SLEEP=10

echo "Create mycommand.txt"
echo -e $SANITIZE_SCRIPT_FILE > $COMMAND_FILEPATH

echo "Create XRSL"
echo -e "&
	( stdout = \"stdout\" )
	( stderr = \"stdout\" )
	( inputfiles = 
		( \"worsica_run_script_grid.sh\" \"file:worsica_run_script_grid.sh\" ) 
		( \"worsica_run_script_grid_sensitive.sh\" \"file:worsica_run_script_grid_sensitive.sh\" ) 
		( \"mycommand.txt\" \"file:$COMMAND_FILEPATH\" ))
	( gmlog = \"gmlog\" )
	( jobname = \"$SUBMISSION_NAME\" )
	( executable = \"worsica_run_script_grid.sh\" )" > $XRSL_FILEPATH

echo "[worsica_grid_launch_submission.sh] 1) Initialize proxy"
if (voms-proxy-init --voms $VO_ENDPOINT --cert $CERT_FILE -k $KEY_FILE) ; then
    echo "[worsica_grid_launch_submission.sh] Initialized proxy!"
else
    echo "[worsica_grid_launch_submission.sh] Fail initializing proxy!"
    exit 1
fi

retry=0
max_retries=10
while [ $retry -le $max_retries ] ; do
    echo "[worsica_grid_launch_submission.sh] 2) Start submitting $1"
    #rm $JOBID_FILEPATH
    SUB_STATE=$(arcsub -C $ARC_ENDPOINT -o $JOBID_FILEPATH $XRSL_FILEPATH)
    echo "${SUB_STATE}"
    if [ $retry -eq $max_retries ] ; then
        echo "[worsica_grid_launch_submission.sh] Max retries exeeded, exit"
        exit 1
    fi
    if  [[ ${SUB_STATE} == *"Job submitted"* ]] ; then
        echo "[worsica_grid_launch_submission.sh] Submitted $1!"
        break    
    elif [[ ${SUB_STATE} == *"ERROR: Can't get the first byte of input BIO to get its format"* ]] ; then
        echo "[worsica_grid_launch_submission.sh] Failed on submitting (possible race condition on creating proxy)"
        retry=$((retry+1))
        sleep ${TIME_SLEEP}
    else
        echo "[worsica_grid_launch_submission.sh] Fail submitting $1!"
        exit 1
    fi
done

echo '[worsica_grid_launch_submission.sh] 3) Check status' 
while true ; do
    JOB_STATE=$(arcstat -i $JOBID_FILEPATH | grep "Finished\|Finishing\|Job not found in job list\|no proxy")
    echo '------------'
    echo $JOB_STATE
    echo '------------'
    #if this script is still running, and job goes away because it's killed, stop looping
    if [[ ${JOB_STATE} == *"Job not found in job list"* ]] ; then
        echo "[worsica_grid_launch_submission.sh] Job not found in job list! Exit!"
        exit 1
    fi
    if [[ ${JOB_STATE} == *"no proxy"* ]] ; then
        echo "[worsica_grid_launch_submission.sh] No proxy!"
        exit 1
    fi
    #or else proceed
    echo "[worsica_grid_launch_submission.sh] Fetch output to $LOG_FILEPATH..."
    arccat -o -i $JOBID_FILEPATH > $LOG_FILEPATH
    if cat $LOG_FILEPATH | grep "Success on run" ; then
        echo "[worsica_grid_launch_submission.sh] Finished!"
        break
    elif cat $LOG_FILEPATH | grep "Failed on run\|Failed on loading" ; then
        echo "[worsica_grid_launch_submission.sh] Failed!"
        exit 1
    else
        echo "[worsica_grid_launch_submission.sh] ...check again ${TIME_SLEEP}s..."
        sleep ${TIME_SLEEP}
    fi
done

echo "[worsica_grid_launch_submission.sh] 4) Kill job"
if arckill -i $JOBID_FILEPATH; then
    echo "[worsica_grid_launch_submission.sh] Done!"
    exit 0
else
    echo "[worsica_grid_launch_submission.sh] Fail killing $1!"
    exit 1
fi

#echo "[worsica_grid_launch_submission.sh] 4) Clean job"
#if arcclean -i $JOBID_FILEPATH; then
#    echo "[worsica_grid_launch_submission.sh] Done!"
#    exit 0
#else
#    echo "[worsica_grid_launch_submission.sh] Fail cleaning $1!"
#    exit 1
#fi
