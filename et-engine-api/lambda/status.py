import boto3
from databases import fetch_algo_ID
import json


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
        # params = json.loads(event['body'])
        algo_ID = event['queryStringParameters']['id'] if 'id' in event['queryStringParameters'] else None

        # algo_ID = params['id']
        
    except Exception as e:
        response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": f"Error fetching algo ID "}),
        }
    
    try:
        stack_name = f'engine-cfn-{algo_ID}'
        cf_client = boto3.client('cloudformation')
        stack_info = cf_client.describe_stacks(StackName=stack_name)['Stacks'][0]
        stack_status = stack_info['StackStatus']

        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": STATUS_MAP[stack_status]}),
        }

    except Exception as e:
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({"message": "error"}),
        }


    return response