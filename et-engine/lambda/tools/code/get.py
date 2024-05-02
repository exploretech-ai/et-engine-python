import lambda_utils
import json
import os
import boto3




def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']
        tool_id = event['pathParameters']['toolID']

        # tool_name = lambda_utils.get_tool_name(user, tool_id)
        # available_tools = lambda_utils.list_tools(user)
        # if tool_name not in available_tools:
        #     return {
        #         'statusCode': 403,
        #         'headers': {
        #             'Access-Control-Allow-Origin': '*'
        #         },
        #         'body': json.dumps('Tool unavailable')
        #     }

        s3 = boto3.client('s3')
        bucket_name = "tool-" + tool_id
        directory_contents = s3.list_objects_v2(
            Bucket=bucket_name
        )
        hierarchy = lambda_utils.to_hierarchy(directory_contents)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(hierarchy)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f'Error: {e}')
        }
    
        