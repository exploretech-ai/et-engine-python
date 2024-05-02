import json
import boto3


def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']

        # vfsID as a path parameter
        tool_id = event['pathParameters']['toolID'] 

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

    
    