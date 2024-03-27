import json
import boto3
import lambda_utils


def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['claims']['cognito:username']

        # vfsID as a path parameter
        vfs_id = event['pathParameters']['vfsID'] 

        # check if 'key' exists in the body
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            raise Exception
        
        if 'key' in body:
            key = body['key']
        else:
            raise Exception

        # check if vfsID exists under user
        available_vfs = lambda_utils.list_vfs(user)
        vfs_name = lambda_utils.get_vfs_name(user, vfs_id)
        if vfs_name not in available_vfs:
            return {
                'statusCode': 403,
                'headers': {
                        'Access-Control-Allow-Origin': '*'
                    },
                'body': json.dumps('VFS unavailable')
            }

        # Create presigned post
        s3 = boto3.client('s3', region_name="us-east-2")
        bucket_name = "vfs-" + vfs_id
        presigned_post = s3.generate_presigned_post(
            Bucket=bucket_name, 
            Key=key,
            # Fields={"Content-Type": "multipart/form-data"},
            ExpiresIn=3600
        )    
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps(presigned_post)
        }   
    

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f"Error: {e}"),
        } 

    
    