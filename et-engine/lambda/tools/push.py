import json
import boto3
import lambda_utils


def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']

        # vfsID as a path parameter
        tool_id = event['pathParameters']['toolID'] 

        # check if vfsID exists under user
        available_tools = lambda_utils.list_tools(user)
        tool_name = lambda_utils.get_tool_name(user, tool_id)
        if tool_name not in available_tools:
            return {
                'statusCode': 403,
                'body': json.dumps('Tool unavailable')
            }

        # Create presigned post
        s3 = boto3.client('s3')
        bucket_name = "tool-" + tool_id
        presigned_post = s3.generate_presigned_post(
            bucket_name, 
            "tool.zip",
            ExpiresIn=60
        )    
        return {
            'statusCode': 200,
            'body' : json.dumps(presigned_post)
        }   
    

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps(f"Error: {e}"),
        } 

    
    