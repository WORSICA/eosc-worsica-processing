SUBMISSION_NAME=$1
TIME_SLEEP=10

#e.g: $1 = worsica-processing-service-coastal-user1-roi144-simulation170-1719-converting
echo "[worsica_grid_kill_submission.sh] 1) Get $1"
if ls ../worsica_web_products/grid/jobids/ | grep "$1"; then
    #20220517-172643-worsica-processing-service-coastal-user1-roi144-simulation170-1719-converting.job.id    
    JOBID_FILE=$(ls ../worsica_web_products/grid/jobids/ | grep "$1")
    #$HOME/worsica_web_products/grid/jobids/20220517-172643-worsica-processing-service-coastal-user1-roi144-simulation170-1719-converting.job.id    
    JOBID_FILEPATH=$HOME/worsica_web_products/grid/jobids/$JOBID_FILE
    #$HOME/worsica_web_products/log/20220517-172643-worsica-processing-service-coastal-user1-roi144-simulation170-1719-converting.out
    LOG_FILEPATH=${JOBID_FILEPATH/.job.id/.out}
    LOG_FILEPATH=${LOG_FILEPATH/grid\/jobids/log}
    echo "$LOG_FILEPATH"
    echo "[worsica_grid_kill_submission.sh] Found $JOBID_FILEPATH!"
else
    echo "[worsica_grid_kill_submission.sh] Fail getting $1!"
    exit 1
fi

#echo '[worsica_grid_kill_submission.sh] 2) Trying to clean job'
#if arcclean -i $JOBID_FILEPATH; then
#    echo "[worsica_grid_kill_submission.sh] Done!!"
#    exit 0
#else
#    echo "[worsica_grid_kill_submission.sh] Fail killing $1!"
#    #exit 1
#fi
echo '[worsica_grid_kill_submission.sh] 2) Killing' #queuing, running, finishing, 
while true; do
    JOB_STATE=$(arcstat -i $JOBID_FILEPATH | grep "Hold\|Accepted\|Preparing\|Queuing\|Running\|Finishing\|Finished\|Job information not found in the information system\|Job not found in job list")
    echo '[worsica_grid_kill_submission.sh] Check status'
    echo '------------'
    echo $JOB_STATE
    echo '------------'
    #stop looping if job does not exist
    if [[ ${JOB_STATE} == *"Job not found in job list"* ]] ; then
        echo "[worsica_grid_launch_submission.sh] Job not found in job list! Exit!"
        exit 1
    fi
    #
    if [[ ${JOB_STATE} == *"Finished"* ]] ; then
        #optionally clean
        if arcclean -i $JOBID_FILEPATH; then
            echo "[worsica_grid_kill_submission.sh] Cleaned!"
            break
        fi  
    fi
    #or proceed
    echo "[worsica_grid_kill_submission.sh] Fetch output to $LOG_FILEPATH..."
    if arccat -o -i $JOBID_FILEPATH > $LOG_FILEPATH ; then
        echo "[worsica_grid_kill_submission.sh] Fetched!"
    else
        echo "[worsica_grid_kill_submission.sh] Fail fetching, ignore!" #In some cases, the job has only been submitted, but not run.
    fi
    #
    echo '[worsica_grid_kill_submission.sh] Trying to kill job'
    if arckill -i $JOBID_FILEPATH; then
        echo "[worsica_grid_kill_submission.sh] Killed!"
        break
    else
        echo "[worsica_grid_kill_submission.sh] ...not yet dead..."
        echo "[worsica_grid_kill_submission.sh] ...check again ${TIME_SLEEP}s..."
        sleep ${TIME_SLEEP}
    fi
    
done
echo "[worsica_grid_kill_submission.sh] Done!"
exit 0


