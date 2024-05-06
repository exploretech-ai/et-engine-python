import json
import boto3
import lambda_utils


def handler(event, context):

    try:
        user = event['requestContext']['authorizer']['userID']

        # vfsID as a path parameter
        vfs_id = event['pathParameters']['vfsID'] 

        # check if 'key' exists in the body
        if 'queryStringParameters' in event and event['queryStringParameters'] is not None:
            key = event['queryStringParameters']['key']
        else:
            raise Exception


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
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body' : json.dumps(presigned_url)
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

    
    