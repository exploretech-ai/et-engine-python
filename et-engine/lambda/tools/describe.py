import lambda_utils
import json
import os
import boto3




def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']
        tool_id = event['pathParameters']['toolID']
        tool_parameters = lambda_utils.describe_tool(user, tool_id)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(tool_parameters)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Error: {e}')
        }
    