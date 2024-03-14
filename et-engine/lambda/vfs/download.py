import json
import boto3
import lambda_utils


def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']

        # vfsID as a path parameter
        vfs_id = event['pathParameters']['vfsID'] 

        # check if 'key' exists in the body
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:
            key = event['queryStringParameters']['key']
        else:
            raise Exception

        # check if vfsID exists under user
        available_vfs = lambda_utils.list_vfs(user)
        vfs_name = lambda_utils.get_vfs_name(user, vfs_id)
        if vfs_name not in available_vfs:
            return {
                'statusCode': 403,
                'body': json.dumps('VFS unavailable')
            }

        # Create presigned post
        s3 = boto3.client('s3')
        bucket_name = "vfs-" + vfs_id
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=60
        )
        return {
            'statusCode': 200,
            'body' : json.dumps(presigned_url)
        }   
    

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps(f"Error: {e}"),
        } 

    
    