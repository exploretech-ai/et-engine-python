for state in SUBMITTED PENDING RUNNABLE STARTING RUNNING
do 
    for job in $(aws batch list-jobs --job-queue $JOB_QUEUE --job-status $state --output text --query "jobSummaryList[*].[jobId]")
    do 
        echo "Stopping job $job in state $state"
        aws batch terminate-job --reason "Terminating job." --job-id $job
    done
done
