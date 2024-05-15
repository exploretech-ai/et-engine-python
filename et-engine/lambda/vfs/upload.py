import json
import boto3
import lambda_utils


def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']

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
            'statusCode': 501,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(f"Error: {e}"),
        } 

    
    