import json
import boto3

STATUS_MAP = {
    "CREATE_COMPLETE": "ready",
    "CREATE_IN_PROGRESS": "provisioning",
    "CREATE_FAILED": "error",
    "DELETE_COMPLETE": "destroyed",
    "DELETE_FAILED": "error",
    "DELETE_IN_PROGRESS": "destroying",
    "REVIEW_IN_PROGRESS": "provisioning",
    "ROLLBACK_COMPLETE": "ready",
    "ROLLBACK_FAILED": "error",
    "ROLLBACK_IN_PROGRESS": "provisioning",
    "UPDATE_COMPLETE": "ready",
    "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS": "provisioning",
    "UPDATE_FAILED": "error",
    "UPDATE_IN_PROGRESS": "provisioning",
    "UPDATE_ROLLBACK_COMPLETE": "ready",
    "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS": "provisioning",
    "UPDATE_ROLLBACK_FAILED": "error",
    "UPDATE_ROLLBACK_IN_PROGRESS": "provisioning",
    "IMPORT_IN_PROGRESS": "provisioning",
    "IMPORT_COMPLETE": "ready",
    "IMPORT_ROLLBACK_IN_PROGRESS": "provisioning",
    "IMPORT_ROLLBACK_FAILED": "error",
    "IMPORT_ROLLBACK_COMPLETE": "ready"
}

def handler(event, context):

    try:
        algoID = event['pathParameters']['algoID']        
        cf_client = boto3.client('cloudformation')
        stack_info = cf_client.describe_stacks(StackName=f"engine-algo-{algoID}")['Stacks'][0]
        stack_status = STATUS_MAP[stack_info['StackStatus']]

        return {
            'statusCode' : 200,
            'body' : json.dumps(stack_status)
        }

        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error: {e} "}),
        }
    